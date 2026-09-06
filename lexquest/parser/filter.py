"""
Filtro Editorial e Higienizador de Dados Jurídicos e Sensíveis.
Inspirado na arquitetura do Conversor NexoJuris (junior-aguiar-eng/Conversor-de-PDF-Para-MD-e-Editor).
Realiza expurgo de dados sensíveis (PII: CPF, telefone, e-mail, marcas d'água),
remoção de sumários/índices, metadados de arquivos (.pdf) e normalização hierárquica.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Set


def _strip_accents(text: str) -> str:
    """Remove acentos para comparação uniforme de ramos e títulos."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


# Ramos do Direito reconhecidos como cabeçalho de primeiro nível (#)
DIREITO_BRANCH_HEADINGS: frozenset[str] = frozenset(
    {
        "DIREITO CONSTITUCIONAL",
        "DIREITO ADMINISTRATIVO",
        "DIREITO CIVIL",
        "DIREITO PROCESSUAL CIVIL",
        "DIREITO PREVIDENCIÁRIO",
        "DIREITO DA CRIANÇA E DO ADOLESCENTE",
        "DIREITO DIGITAL",
        "DIREITO INTERNACIONAL",
        "DIREITO AMBIENTAL",
        "DIREITO EMPRESARIAL",
        "EXECUÇÃO PENAL",
        "DIREITO PENAL",
        "DIREITO PROCESSUAL PENAL",
        "DIREITO TRIBUTÁRIO",
        "DIREITO DO CONSUMIDOR",
        "DIREITO ELEITORAL",
        "DIREITO FINANCEIRO",
        "DIREITO URBANÍSTICO",
        "DIREITOS HUMANOS",
    }
)
_DIREITO_BRANCHES_NORMALIZED = frozenset(_strip_accents(name).upper() for name in DIREITO_BRANCH_HEADINGS)

# Seções fixas jurisprudenciais e doutrinárias
SECTION_LABEL_HEADINGS: frozenset[str] = frozenset(
    {"COMENTÁRIO", "COMENTÁRIOS", "TESE", "EMENTA", "RELATÓRIO", "VOTO", "DISPOSITIVO", "JURISPRUDÊNCIA EM TESES"}
)
_SECTION_LABELS_NORMALIZED = frozenset(_strip_accents(name).upper() for name in SECTION_LABEL_HEADINGS)


class EditorialFilter:
    """
    Filtro e Sanitizador Avançado de Textos e PDFs Jurídicos.
    Garante que nenhum dado sensível (LGPD/privacidade), metadados de upload (.pdf)
    ou ruído estrutural (sumários, números de página, linhas pontilhadas)
    contamine o banco de UMTs e os simulados gerados.
    """

    # 1. Padrões de Dados Pessoais (PII) e Marcas d'Água
    PII_PATTERNS = [
        # CPF com ou sem máscara (ex: CPF: 02662253576 ou 026.622.535-76)
        re.compile(r"(?i)\b(?:cpf\s*:?\s*)?\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
        re.compile(r"(?i)\bcpf\s*:?\s*\d{11}\b"),
        # CNPJ
        re.compile(r"(?i)\b(?:cnpj\s*:?\s*)?\d{2}\.?\d{3}\.?\d{3}/\d{4}-?\d{2}\b"),
        # Telefone (ex: Telefone: 82981559589 ou (82) 98155-9589)
        re.compile(r"(?i)\b(?:telefone|tel|celular|whatsapp|fone)\s*:?\s*[\d\(\)\s+-]{8,20}\b"),
        re.compile(r"\b(?:\+55\s*)?(?:\(?\d{2}\)?\s*)?(?:9\d{4}|\d{4})[-.\s]?\d{4}\b"),
        # E-mail (ex: junior-aguiar@hotmail.com.br)
        re.compile(r"(?i)\b(?:e-mail|email|mail)\s*:?\s*[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"),
        re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"),
        # Marcas d'água de proteção de apostilas e identificação de comprador
        re.compile(
            r"(?im)^.*?(?:licenciado para|adquirido por|venda proibida|uso exclusivo|assinante|comprador|usu[aá]rio registrado|direitos autorais reservados|todos os direitos reservados|material protegido).*?$"
        ),
        # Metadados de importação de arquivo ou nomes de arquivos PDF temporários
        re.compile(r"(?im)^.*?(?:documento importado|arquivo tempor[aá]rio|tmp[a-z0-9_]+\.pdf).*?$"),
    ]

    # 2. Padrões de Sumário e Linhas com Pontilhados
    TOC_PATTERNS = [
        # Linhas de sumário com pontos ou traços e número de página no final
        # Ex: "EXECUÇÃO PENAL .................... 153" ou "............ 134" ou "DIREITO EMPRESARIAL ..... 142"
        re.compile(r"^.*?(?:\.{3,}|…{2,}|_{3,}|\-{3,})\s*\d+\s*$"),
        # Linhas que consistem apenas de pontos e/ou traços
        re.compile(r"^[\s.…_-]{3,}\s*$"),
        # Linha contendo ramo com ponto no final (ex: "DIREITO CONSTITUCIONAL .")
        re.compile(r"(?i)^(?:direito\s+[a-zçãõ]+|execu[cç][aã]o\s+penal)\s*[\.\…\-_]+\s*$"),
        # Palavra isolada "SUMÁRIO" ou "ÍNDICE"
        re.compile(r"(?i)^\s*(?:#+\s*)?(?:sum[aá]rio|[ií]ndice|sumario|indice)\s*:?\s*$"),
        # Linha isolada contendo apenas número de página (ex: "134", "142", "2")
        re.compile(r"^\s*\d{1,4}\s*$"),
        # Número de página no padrão "Página X de Y"
        re.compile(r"(?i)^\s*(?:p[aá]gina|p[aá]g\.?|fls?\.?)\s*\d+(?:\s*(?:de|/)\s*\d+)?\s*$"),
    ]

    # 3. Cabeçalhos de Seções Inúteis para Estudo de Questões
    NOISE_SECTIONS = [
        re.compile(r"^#+\s*(sum[aá]rio|[ií]ndice|apresenta[cç][aã]o|sobre o autor|equipe|bibliografia|pref[aá]cio).*", re.IGNORECASE),
        re.compile(r"^#+\s*(quest[oõ]es|exerc[ií]cios|gabarito).*", re.IGNORECASE),
    ]

    @classmethod
    def clean_pii(cls, text: str) -> str:
        """Expurga CPFs, telefones, e-mails, metadados de PDF e marcas d'água do texto."""
        result = text
        for pattern in cls.PII_PATTERNS:
            result = pattern.sub("", result)
        return result

    @classmethod
    def is_toc_line(cls, line: str) -> bool:
        """Verifica se a linha é um elemento de sumário, pontilhado ou numeração avulsa."""
        stripped = line.strip()
        if not stripped:
            return False
        return any(pattern.match(stripped) for pattern in cls.TOC_PATTERNS)

    @classmethod
    def clean(cls, text: str) -> str:
        """
        Executa a higienização completa em múltiplos estágios:
        1. Expurgo de PII e marcas d'água
        2. Supressão de blocos de sumário/índices e pontilhados
        3. Normalização dos ramos do direito como títulos principais
        4. Junção de quebras artificiais de linha mantendo parágrafos fluidos
        """
        # Estágio 1: Limpeza de dados pessoais e metadados em todo o texto
        text = cls.clean_pii(text)

        lines = text.splitlines()
        clean_lines = []
        skip_noise_block = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if not skip_noise_block:
                    clean_lines.append("")
                continue

            # Estágio 2: Detecção de cabeçalho de ruído editorial (sumário, índice, exercícios, bibliografia)
            if any(p.match(stripped) for p in cls.NOISE_SECTIONS) or re.match(r"(?i)^\s*sum[aá]rio\s*$", stripped):
                skip_noise_block = True
                continue

            # Se encontrou um novo título substantivo de conteúdo real, encerra o bloco de ruído
            if skip_noise_block:
                clean_title = stripped.replace("#", "").replace("*", "").strip()
                norm_title = _strip_accents(clean_title).upper()
                if (norm_title in _DIREITO_BRANCHES_NORMALIZED or re.match(r"^Art\.\s*\d+", clean_title)) and not cls.is_toc_line(stripped):
                    skip_noise_block = False
                else:
                    continue

            # Estágio 3: Expurgo de linhas pontilhadas de sumário, números soltos ou "DIREITO CONSTITUCIONAL ."
            if cls.is_toc_line(stripped):
                continue

            # Se a linha contiver metadado .pdf ou documento importado, descarta
            if ".pdf" in stripped.lower() or "documento importado" in stripped.lower():
                continue

            # Estágio 4: Normalização de Ramos do Direito (apenas se for ramo substantivo)
            clean_line_text = stripped.replace("**", "").replace("#", "").strip()
            norm_name = _strip_accents(clean_line_text).upper()

            if norm_name in _DIREITO_BRANCHES_NORMALIZED and not stripped.startswith("##"):
                clean_lines.append(f"\n# {norm_name}\n")
                continue

            clean_lines.append(line)

        raw_clean = "\n".join(clean_lines)

        # Estágio 5: Reconstrução fluida de parágrafos
        # Divide em blocos separados por linhas em branco duplas
        raw_paragraphs = raw_clean.split("\n\n")
        normalized_paragraphs = []

        for p in raw_paragraphs:
            p_lines = [l.strip() for l in p.splitlines() if l.strip()]
            if not p_lines:
                continue

            # Se for cabeçalho (#) ou citação (>) ou lista (- / 1.), mantém como está
            if p_lines[0].startswith(("#", ">", "-", "*", "1.", "I.", "Art.")):
                normalized_paragraphs.append("\n".join(p_lines))
            else:
                # É parágrafo corrido: une linhas com espaço simples desfazendo quebras artificiais de PDF
                joined_p = " ".join(p_lines)
                # Normaliza espaços múltiplos
                joined_p = re.sub(r"[ \t]+", " ", joined_p).strip()
                if joined_p:
                    normalized_paragraphs.append(joined_p)

        unified = "\n\n".join(normalized_paragraphs)
        return unified.strip()


# Alias para retrocompatibilidade total
LexicalFilter = EditorialFilter
