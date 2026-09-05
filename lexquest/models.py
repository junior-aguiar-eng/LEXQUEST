from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class UMTType(Enum):
    LEI_SECA = "LEI_SECA"
    JURISPRUDENCIA = "JURISPRUDENCIA"
    DOUTRINA = "DOUTRINA"


class Complexity(Enum):
    FACIL = "FACIL"
    MEDIO = "MEDIO"
    DIFICIL = "DIFICIL"


class QuestionFormat(Enum):
    CASO_NARRATIVO = "CASO_NARRATIVO"
    PROPOSICOES_ROMANAS = "PROPOSICOES_ROMANAS"
    CONCEITUAL_DIRETA = "CONCEITUAL_DIRETA"
    CEBRASPE_ISOLADO = "CEBRASPE_ISOLADO"
    CEBRASPE_COMPARTILHADO = "CEBRASPE_COMPARTILHADO"


class Banca(Enum):
    FGV = "FGV"
    CEBRASPE = "CEBRASPE"
    FCC = "FCC"
    VUNESP = "VUNESP"


@dataclass
class UMT:
    """
    Unidade Mínima de Testabilidade (UMT):
    Representa uma regra, exceção ou precedente qualificado autônomo.
    """
    id: int
    title: str
    topic: str
    content: str
    original_text: str
    umt_type: UMTType
    complexity: Complexity
    source_ref: str
    tags: List[str] = field(default_factory=list)
    highlighted_terms: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alternative:
    letter: str
    text: str
    is_correct: bool
    explanation: str


@dataclass
class Question:
    id: int
    banca: Banca
    format: QuestionFormat
    difficulty: Complexity
    topic: str
    stem: str
    alternatives: List[Alternative]
    correct_letter: str
    source_umts: List[UMT]
    commentary: str
    propositions: Optional[List[str]] = None
    block_index: int = 1
    question_in_block: int = 1
    total_in_block: int = 5

    @property
    def header(self) -> str:
        # Sanitiza disciplina/tema removendo caminhos ou extensões
        clean_topic = self.topic.replace(".md", "").replace("_", " ")
        if "/" in clean_topic or "\\" in clean_topic:
            import os
            clean_topic = os.path.basename(clean_topic)
        clean_topic = clean_topic.strip().title()

        # Sanitiza títulos de UMTs para exibição elegante e limpa
        clean_umts = []
        for u in self.source_umts:
            raw_title = u.title.split(" - ")[0] if " - " in u.title else u.title
            raw_title = raw_title.replace("#", "").replace("*", "").strip()
            if len(raw_title) > 35:
                raw_title = raw_title[:32] + "..."
            clean_umts.append(raw_title)
        umt_label = ", ".join(clean_umts)

        format_names = {
            QuestionFormat.CASO_NARRATIVO: "Caso Prático Forense",
            QuestionFormat.PROPOSICOES_ROMANAS: "Proposições Romanas (I, II, III)",
            QuestionFormat.CONCEITUAL_DIRETA: "Conceitual / Dogmática",
            QuestionFormat.CEBRASPE_ISOLADO: "Item Certo/Errado (Isolado)",
            QuestionFormat.CEBRASPE_COMPARTILHADO: "Situação Hipotética Compartilhada"
        }
        fmt_name = format_names.get(self.format, self.format.value)

        return (
            f"[Disciplina: {clean_topic} | UMT: {umt_label} | "
            f"Bloco {self.block_index} (Questão {self.question_in_block} de {self.total_in_block}) | "
            f"Formato: {fmt_name} | Nível: {self.difficulty.value}]"
        )
