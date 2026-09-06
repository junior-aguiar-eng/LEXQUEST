import re
from typing import List, Tuple
from ..models import UMT, UMTType, Complexity
from .filter import EditorialFilter


class UMTExtractor:
    """
    Extrator de Unidades Mínimas de Testabilidade (UMTs).
    Varre o texto em Markdown e identifica blocos substantivos autônomos.
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
        if re.search(r"\bArt\.\s*\d+", clean_text, re.IGNORECASE):
            return self._extract_lei_seca(clean_text, default_topic)
        else:
            return self._extract_jurisprudencia_e_doutrina(clean_text, default_topic)

    def _extract_jurisprudencia_e_doutrina(self, text: str, topic: str) -> List[UMT]:
        umts = []
        lines = text.splitlines()

        current_topic = topic
        current_case_title = ""
        case_thesis_summary = ""
        source_ref = ""

        # Encontra rodapé com referência do julgado
        source_match = re.search(r"\(([A-Z0-9\s/]+,\s*Relator.+?Informativo\s*\d+/\d{4})\)", text)
        if source_match:
            source_ref = source_match.group(1)

        # Identifica tópicos gerais (# Título) e casos (## Título - Processo)
        paragraphs = []
        curr_p = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if curr_p:
                    paragraphs.append("\n".join(curr_p))
                    curr_p = []
                continue

            if stripped.startswith("# ") and not stripped.startswith("## "):
                current_topic = stripped.replace("#", "").replace("*", "").strip()
                continue
            elif stripped.startswith("## "):
                if not re.search(r"coment[aá]rios?", stripped, re.IGNORECASE):
                    current_case_title = stripped.replace("##", "").replace("*", "").strip()
                continue

            # Ignora linha de referência final na formação de parágrafos normais
            if stripped.startswith("(") and ("Informativo" in stripped or "Relator" in stripped):
                source_ref = stripped.strip("()")
                continue

            curr_p.append(stripped)

        if curr_p:
            paragraphs.append("\n".join(curr_p))

        # Se houver parágrafos, processa cada um como candidato a UMT
        for idx, p in enumerate(paragraphs):
            # Limpa qualquer resíduo de PII ou sumário
            p = EditorialFilter.clean_pii(p).strip()
            p = re.sub(r"(?:\.{3,}|…{2,}|_{3,}|\-{3,})\s*\d+\s*$", "", p).strip()

            # Ignora se for linha de sumário, pontilhado, ou texto curtíssimo sem substância
            if EditorialFilter.is_toc_line(p) or len(p) < 40 or p.lower().startswith("ementa"):
                continue

            # Garante que não é apenas números ou pontuação
            if not re.search(r"[a-zA-ZáéíóúÁÉÍÓÚãõÃÕçÇ]{4,}", p):
                continue

            # Título da UMT
            title = current_case_title if current_case_title else f"Tópico {idx + 1}"
            
            # Extrai termos em negrito como pontos-chave
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
                source_ref=source_ref or "Jurisprudência / Julgados",
                highlighted_terms=highlights,
                tags=[current_topic, title]
            )
            self._current_id += 1
            umts.append(umt)

        return umts

    def _extract_lei_seca(self, text: str, topic: str) -> List[UMT]:
        umts = []
        
        # Encontra o diploma legal no topo
        title_match = re.search(r"#\s*(LEI\s*N[ºo]?\s*[\d\.]+.*?)(?=\n|$)", text, re.IGNORECASE)
        diploma = title_match.group(1).strip() if title_match else topic

        # Divide o texto por artigos, parágrafos e incisos
        # Procura por **Art. X**, **" Art. X**, **I** -, **§ Xº**, **Parágrafo único**
        pattern = re.compile(
            r"(\*\*(?:\"?\s*Art\.\s*\d+[ºo]?|§\s*\d+[ºo]?|Parágrafo único|I{1,3}|IV|V|VI|VII|VIII|IX|X)\*\*.*?)(?=(\*\*(?:\"?\s*Art\.\s*\d+[ºo]?|§\s*\d+[ºo]?|Parágrafo único|I{1,3}|IV|V|VI|VII|VIII|IX|X)\*\*)|$)",
            re.DOTALL
        )

        matches = pattern.findall(text)
        if not matches:
            # Fallback por linhas se regex complexa não casar
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
            if EditorialFilter.is_toc_line(block) or len(block) < 25:
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

        # Difícil: termos dogmáticos pesados ou dupla negação
        for dw in self.DOGMATIC_WORDS:
            if dw in lower:
                return Complexity.DIFICIL

        # Médio: exceções, condicionantes ou prazos
        for ew in self.EXCEPTION_WORDS:
            if ew in lower:
                return Complexity.MEDIO

        if re.search(r"\b\d+\s*(dias|meses|anos)\b", lower):
            return Complexity.MEDIO

        return Complexity.FACIL
