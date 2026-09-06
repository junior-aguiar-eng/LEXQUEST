import re
from typing import List, Tuple
from ..models import UMT, UMTType, Complexity
from .filter import EditorialFilter, _strip_accents, _DIREITO_BRANCHES_NORMALIZED


class UMTExtractor:
    """
    Extrator de Unidades Mínimas de Testabilidade (UMTs).
    Varre o texto em Markdown sanitizado e identifica blocos substantivos autônomos.
    Aplica validação ontológica estrita para impedir que metadados, sumários ou fragmentos
    virem questões de prova.
    """

    EXCEPTION_WORDS = [
        "salvo", "exceto", "ressalvado", "ainda que", "contudo", "todavia",
        "embora", "não obstante", "prescinde", "vedado", "proibido",
        "desde que", "a menos que", "inconstitucional", "inconstitucionalidade"
    ]

    DOGMATIC_WORDS = [
        "prescinde", "imprescinde", "ex tunc", "ex nunc", "nulidade absoluta",
        "nulidade relativa", "estado de coisas inconstitucional", "soberania dos veredictos",
        "reserva de lei", "repercussão geral", "distinguishing", "overruling"
    ]

    def __init__(self):
        self._current_id = 1

    def extract_from_file(self, file_path: str) -> List[UMT]:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        return self.extract_from_text(raw_text, default_topic=file_path)

    def extract_from_text(self, text: str, default_topic: str = "Geral") -> List[UMT]:
        clean_text = EditorialFilter.clean(text)
        
        # Detecta se é predominantemente lei seca ou jurisprudência/doutrina
        has_lei_title = bool(re.search(r"#\s*(?:LEI\s*N[ºo]?|DECRETO|CÓDIGO|CONSTITUIÇÃO)", clean_text, re.IGNORECASE))
        has_juris_markers = bool(re.search(r"\b(informativo|súmula|tema\s+\d+|adpf|adi|resp|re\s+\d+|relator|habeas corpus)\b", clean_text, re.IGNORECASE))
        art_count = len(re.findall(r"\bArt\.\s*\d+", clean_text, re.IGNORECASE))

        if has_lei_title or (art_count >= 2 and not has_juris_markers):
            return self._extract_lei_seca(clean_text, default_topic)
        else:
            return self._extract_jurisprudencia_e_doutrina(clean_text, default_topic)

    def _is_valid_legal_content(self, text: str) -> bool:
        """Valida se o parágrafo possui substância jurídica real e não é ruído ou metadado."""
        if not text or len(text.strip()) < 30:
            return False

        lower = text.lower()

        # Rejeita metadados de arquivo, upload ou sumário
        blacklisted_tokens = [
            ".pdf", "documento importado", "sumário", "sumario", "índice", "indice",
            "página", "pagina", "fls.", "fl.", "licenciado para", "venda proibida",
            "todos os direitos reservados"
        ]
        if any(token in lower for token in blacklisted_tokens):
            return False

        # Rejeita sequências de pontilhados de índice
        if re.search(r"(\.{3,}|…{2,}|_{3,}|\-{3,})", text):
            return False

        # Deve conter ao menos uma menção a termo normativo, dogmático ou verbo jurídico
        has_legal_indicator = bool(re.search(
            r"\b(art|artigo|parágrafo|inciso|alínea|lei|decreto|código|súmula|tema|informativo|"
            r"recurso|ação|stf|stj|tribunal|juiz|corte|ministro|unanimidade|plenário|acórdão|"
            r"direito|norma|ordem|regra|princípio|crime|pena|tutela|prazo|competência|"
            r"constitucional|inconstitucional|legal|ilegal|jurídic[oa]|nulo|nulidade|"
            r"é|são|será|serão|foi|foram|não|deve|devem|deverá|deverão|pode|podem|poderá|poderão|"
            r"cabe|cabem|caberá|descabe|descabem|descaberá|reconhece|reconheceu|reconhecem|"
            r"firmou|fixou|declarou|declara|declarar|vedado|vedada|permitido|permitida|admissível|"
            r"inadmissível|aplicável|inaplicável|prescinde|imprescinde|assegura|determina|"
            r"determinou|dispõe|dispõem|estabelece|estabeleceu|julga|julgou|processa|compete|"
            r"responde|responderá|transmite|exige|pressupõe|sujeita|autoriza|autorizou|"
            r"impõe|impôs|comete|pratica|prevê|previsto|prevista|conceder|contratar|adotar)\b",
            lower
        ))
        if not has_legal_indicator:
            return False

        return True

    def _extract_jurisprudencia_e_doutrina(self, text: str, topic: str) -> List[UMT]:
        umts = []
        lines = text.splitlines()

        current_topic = topic
        current_case_title = ""
        source_ref = ""

        # Encontra rodapé com referência do julgado
        source_match = re.search(r"\(([A-Z0-9\s/]+,\s*Relator.+?Informativo\s*\d+/\d{4})\)", text)
        if source_match:
            source_ref = source_match.group(1)

        paragraphs = []
        curr_p = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if curr_p:
                    paragraphs.append("\n".join(curr_p))
                    curr_p = []
                continue

            # Detecta título de ramo do direito (# DIREITO ...)
            if stripped.startswith("# ") and not stripped.startswith("## "):
                raw_topic = stripped.replace("#", "").replace("*", "").strip()
                norm_topic = _strip_accents(raw_topic).upper()
                if norm_topic in _DIREITO_BRANCHES_NORMALIZED:
                    current_topic = raw_topic
                elif not current_case_title:
                    current_case_title = raw_topic
                continue

            # Detecta título do caso (## Título do Caso / Tema)
            elif stripped.startswith("## "):
                # Não substitui caso por "COMENTÁRIOS" ou "RELATÓRIO"
                if not re.search(r"coment[aá]rios?|relat[oó]rio|ementa|voto", stripped, re.IGNORECASE):
                    current_case_title = stripped.replace("##", "").replace("*", "").strip()
                continue

            # Ignora linha de referência de julgado no corpo (armazena como fonte)
            if stripped.startswith("(") and ("Informativo" in stripped or "Relator" in stripped or "STF" in stripped or "STJ" in stripped):
                source_ref = stripped.strip("()")
                continue

            curr_p.append(stripped)

        if curr_p:
            paragraphs.append("\n".join(curr_p))

        for idx, p in enumerate(paragraphs):
            # Limpa resíduos de PII, sumários ou metadados
            p = EditorialFilter.clean_pii(p).strip()
            p = re.sub(r"(?:\.{3,}|…{2,}|_{3,}|\-{3,})\s*\d+\s*$", "", p).strip()

            # Remove marcadores residuais de seção no início (ex: "COMENTÁRIO:", "COMENTÁRIOS:")
            p = re.sub(r"(?i)^(?:coment[aá]rios?|relat[oó]rio|ementa|tese)\s*:?\s*", "", p).strip()

            # Remove citações soltas isoladas no final (ex: "Constituição Federal (redação vigente).")
            citation_end = re.search(r"(?i)\n*(?:Constituição Federal|CF/88|CPC|CP|STF|STJ)\s*\(redação vigente\)\.?\s*$", p)
            if citation_end:
                p = p[:citation_end.start()].strip()

            # Unifica quebras de linha em parágrafo coeso (sem linhas quebradas no meio da frase)
            p_lines = [l.strip() for l in p.splitlines() if l.strip()]
            p = " ".join(p_lines)
            p = re.sub(r"\s+", " ", p).strip()

            # Valida densidade semântica da UMT
            if not self._is_valid_legal_content(p):
                continue

            title = current_case_title if current_case_title else f"{current_topic} - Tópico {idx + 1}"
            highlights = re.findall(r"\*\*(.+?)\*\*", p)
            complexity = self._evaluate_complexity(p)

            umt = UMT(
                id=self._current_id,
                title=f"{title} - Ponto {idx + 1}",
                topic=current_topic,
                content=p,
                original_text=p,
                umt_type=UMTType.JURISPRUDENCIA,
                complexity=complexity,
                source_ref=source_ref or f"{current_topic} - Jurisprudência",
                highlighted_terms=highlights,
                tags=[current_topic, title]
            )
            self._current_id += 1
            umts.append(umt)

        return umts

    def _extract_lei_seca(self, text: str, topic: str) -> List[UMT]:
        umts = []
        
        title_match = re.search(r"#\s*(LEI\s*N[ºo]?\s*[\d\.]+.*?)(?=\n|$)", text, re.IGNORECASE)
        diploma = title_match.group(1).strip() if title_match else topic

        pattern = re.compile(
            r"(\*\*(?:\"?\s*Art\.\s*\d+[ºo]?|§\s*\d+[ºo]?|Parágrafo único|I{1,3}|IV|V|VI|VII|VIII|IX|X)\*\*.*?)(?=(\*\*(?:\"?\s*Art\.\s*\d+[ºo]?|§\s*\d+[ºo]?|Parágrafo único|I{1,3}|IV|V|VI|VII|VIII|IX|X)\*\*)|$)",
            re.DOTALL
        )

        matches = pattern.findall(text)
        if not matches:
            lines = text.splitlines()
            current_block = []
            for l in lines:
                if re.match(r"^\*\*(Art\.|§|Parágrafo|[IVXLCDM]+\b)", l.strip()):
                    if current_block:
                        matches.append(("\n".join(current_block), ""))
                        current_block = []
                current_block.append(l)
            if current_block:
                matches.append(("\n".join(current_block), ""))

        for m in matches:
            block = m[0].strip() if isinstance(m, tuple) else m.strip()
            block = EditorialFilter.clean_pii(block).strip()
            block = re.sub(r"(?:\.{3,}|…{2,}|_{3,}|\-{3,})\s*\d+\s*$", "", block).strip()

            # Unifica quebras de linha em texto fluido
            b_lines = [l.strip() for l in block.splitlines() if l.strip()]
            block = " ".join(b_lines)
            block = re.sub(r"\s+", " ", block).strip()

            if not self._is_valid_legal_content(block):
                continue

            first_line = block.splitlines()[0]
            header_clean = re.sub(r"[*\"#]", "", first_line).strip()
            complexity = self._evaluate_complexity(block)

            umt = UMT(
                id=self._current_id,
                title=f"{diploma} - {header_clean[:50]}",
                topic=diploma,
                content=block,
                original_text=block,
                umt_type=UMTType.LEI_SECA,
                complexity=complexity,
                source_ref=diploma,
                tags=[diploma, "Lei Seca"]
            )
            self._current_id += 1
            umts.append(umt)

        return umts

    def _evaluate_complexity(self, text: str) -> Complexity:
        lower = text.lower()

        for dw in self.DOGMATIC_WORDS:
            if dw in lower:
                return Complexity.DIFICIL

        for ew in self.EXCEPTION_WORDS:
            if ew in lower:
                return Complexity.MEDIO

        return Complexity.FACIL
