import random
from typing import List, Dict, Any, Optional, Tuple
from ..models import (
    UMT, Question, Alternative, QuestionFormat, Complexity, Banca
)
from .mutator import LexicalMutator
from .distractor_builder import DistractorBuilder
from ..scenarios.catalog import ScenarioCatalog
from ..graph.legal_graph import LegalKnowledgeGraph
from ..parser.filter import _strip_accents


class BlockManager:
    """
    Orquestrador de Blocos de Questões e Algoritmo Anti-Repetição.
    Aplica as regras rígidas da FGV/ENAM (bloco fixo de 5 questões: 3-1-1 formato e 3-1-1 dificuldade)
    e do Cebraspe (Certo/Errado com distribuição equilibrada), potencializado
    por Grafo de Conhecimento Jurídico (NetworkX) para agrupamento conceitual de UMTs.
    """

    FGV_FORMAT_RECIPE = [
        QuestionFormat.CASO_NARRATIVO,
        QuestionFormat.CASO_NARRATIVO,
        QuestionFormat.CASO_NARRATIVO,
        QuestionFormat.PROPOSICOES_ROMANAS,
        QuestionFormat.CONCEITUAL_DIRETA
    ]

    FGV_DIFFICULTY_RECIPE = [
        Complexity.DIFICIL,
        Complexity.DIFICIL,
        Complexity.DIFICIL,
        Complexity.MEDIO,
        Complexity.FACIL
    ]

    def __init__(self):
        self.mutator = LexicalMutator()
        self.distractor_builder = DistractorBuilder(self.mutator)
        self.knowledge_graph = LegalKnowledgeGraph()
        self.scenario_catalog = ScenarioCatalog()

    def _format_topic_natural(self, topic: str) -> str:
        """Formata o nome da disciplina/tópico de forma elegante e gramaticalmente correta."""
        if not topic or topic.strip().lower() in ["geral", "amostra", "documento", "documento importado"]:
            return "ao Direito brasileiro"

        t = topic.strip()
        norm = _strip_accents(t).upper()

        mapping = {
            "EXECUCAO PENAL": "Execução Penal",
            "DIREITO CONSTITUCIONAL": "Direito Constitucional",
            "DIREITO ADMINISTRATIVO": "Direito Administrativo",
            "DIREITO PENAL": "Direito Penal",
            "DIREITO PROCESSUAL PENAL": "Direito Processual Penal",
            "DIREITO PROCESSUAL CIVIL": "Direito Processual Civil",
            "DIREITO CIVIL": "Direito Civil",
            "DIREITO TRIBUTARIO": "Direito Tributário",
            "DIREITO EMPRESARIAL": "Direito Empresarial",
            "DIREITO DO TRABALHO": "Direito do Trabalho",
            "DIREITO PROCESSUAL DO TRABALHO": "Direito Processual do Trabalho",
            "DIREITO ELEITORAL": "Direito Eleitoral",
            "DIREITO AMBIENTAL": "Direito Ambiental",
            "DIREITOS HUMANOS": "Direitos Humanos",
            "DIREITO FINANCEIRO": "Direito Financeiro",
            "DIREITO PREVIDENCIARIO": "Direito Previdenciário",
            "DIREITO DO CONSUMIDOR": "Direito do Consumidor",
            "DIREITO DA CRIANCA E DO ADOLESCENTE": "Direito da Criança e do Adolescente",
            "DIREITO INTERNACIONAL": "Direito Internacional",
        }
        if norm in mapping:
            return mapping[norm]

        words = t.split()
        clean = []
        lowercase_words = {"de", "da", "do", "das", "dos", "e", "em", "para", "com", "a", "o", "no", "na", "nos", "nas"}
        for idx, w in enumerate(words):
            lw = w.lower()
            if idx > 0 and lw in lowercase_words:
                clean.append(lw)
            else:
                clean.append(w.capitalize())
        return " ".join(clean)

    def generate_fgv_block(
        self,
        umts: List[UMT],
        block_index: int = 1,
        prev_last_letter: Optional[str] = None
    ) -> List[Question]:
        """
        Gera um bloco exato de 5 questões no padrão FGV/ENAM a partir das UMTs fornecidas.
        Garante:
        - 3 Casos Concretos + 1 Proposições + 1 Conceitual
        - 3 Difíceis + 1 Média + 1 Fácil
        - Sem repetição de letras consecutivas no gabarito
        - Rotação equilibrada de alternativas (A a E)
        """
        if not umts:
            return []

        # Constrói o Grafo de Conhecimento Jurídico com as UMTs do material
        self.knowledge_graph.build_from_umts(umts)

        # Embaralha os formatos e dificuldades garantindo não ter 3 consecutivos iguais
        formats = self._shuffle_without_triple_streak(self.FGV_FORMAT_RECIPE)
        difficulties = self._shuffle_without_triple_streak(self.FGV_DIFFICULTY_RECIPE)

        questions: List[Question] = []
        last_letter = prev_last_letter
        umt_pool_index = 0
        total_umts = len(umts)

        for q_idx in range(5):
            fmt = formats[q_idx]
            diff = difficulties[q_idx]

            # Seleciona UMT primária
            primary_umt = umts[umt_pool_index % total_umts]
            umt_pool_index += 1

            if fmt == QuestionFormat.PROPOSICOES_ROMANAS:
                # Utiliza o Grafo de Conhecimento para buscar UMTs que compartilham o mesmo cluster temático/entidades
                correlated = self.knowledge_graph.get_correlated_umts(primary_umt, max_count=2)
                prop_umts = [primary_umt] + [u for u in correlated if u.id != primary_umt.id]
                
                # Fallback determinístico para garantir exatamente 3 UMTs sem loop infinito
                offset = 1
                attempts = 0
                while len(prop_umts) < 3:
                    cand = umts[(umt_pool_index + offset) % total_umts]
                    if cand not in prop_umts or attempts >= total_umts:
                        prop_umts.append(cand)
                    offset += 1
                    attempts += 1

                propositions, alts, correct_letter, commentary = (
                    self.distractor_builder.build_propositions_question(prop_umts)
                )

                # Ajusta para não repetir a letra anterior
                if correct_letter == last_letter:
                    alts, correct_letter = self._rotate_to_avoid_letter(alts, last_letter)

                topic_lbl = self._format_topic_natural(primary_umt.topic)
                if topic_lbl == "ao Direito brasileiro":
                    intro = "Com base no ordenamento jurídico pátrio e na jurisprudência dos Tribunais Superiores, analise as afirmativas a seguir:"
                else:
                    intro = f"Em relação à matéria de {topic_lbl} e às balizas normativas e jurisprudenciais aplicáveis, analise as afirmativas a seguir:"

                stem = (
                    f"{intro}\n\n" +
                    "\n\n".join(propositions) +
                    "\n\nAssinale a opção correta:"
                )

                q = Question(
                    id=q_idx + 1 + (block_index - 1) * 5,
                    banca=Banca.FGV,
                    format=fmt,
                    difficulty=diff,
                    topic=primary_umt.topic,
                    stem=stem,
                    alternatives=alts,
                    correct_letter=correct_letter,
                    source_umts=prop_umts,
                    commentary=commentary,
                    propositions=propositions,
                    block_index=block_index,
                    question_in_block=q_idx + 1,
                    total_in_block=5
                )

            elif fmt == QuestionFormat.CASO_NARRATIVO:
                frame = self.scenario_catalog.get_diverse_frame_for_umt(primary_umt)
                stem = f"{frame.stem_template}\n\n{frame.prompt}"

                conclusion_pairs = [
                    ("Está em consonância com a ordem constitucional", "Não encontra amparo na ordem constitucional"),
                    ("Harmoniza-se com a jurisprudência vinculante", "Contraria o entendimento pacificado dos Tribunais Superiores"),
                    ("É juridicamente legítima e exigível", "Padece de invalidade substancial perante a ordem jurídica"),
                    ("Deve ser integralmente acolhida", "Deve ser categoricamente rejeitada")
                ]
                pair = conclusion_pairs[q_idx % len(conclusion_pairs)]
                correct_conc, incorrect_conc = pair

                alts, correct_letter = self.distractor_builder.build_fgv_alternatives(
                    base_umt=primary_umt,
                    correct_conclusion=correct_conc,
                    incorrect_conclusion=incorrect_conc,
                    target_complexity=diff
                )

                if correct_letter == last_letter:
                    alts, correct_letter = self._rotate_to_avoid_letter(alts, last_letter)

                commentary = (
                    f"QUESTÃO DE CASO CONCRETO NARRATIVO.\n"
                    f"A tese exigida ancora-se em: {primary_umt.title} ({primary_umt.source_ref}).\n"
                    f"Dispositivo / Tese integral:\n> {primary_umt.original_text}\n"
                )

                q = Question(
                    id=q_idx + 1 + (block_index - 1) * 5,
                    banca=Banca.FGV,
                    format=fmt,
                    difficulty=diff,
                    topic=primary_umt.topic,
                    stem=stem,
                    alternatives=alts,
                    correct_letter=correct_letter,
                    source_umts=[primary_umt],
                    commentary=commentary,
                    block_index=block_index,
                    question_in_block=q_idx + 1,
                    total_in_block=5
                )

            else:  # QuestionFormat.CONCEITUAL_DIRETA
                topic_lbl = self._format_topic_natural(primary_umt.topic)
                if topic_lbl == "ao Direito brasileiro":
                    stem = "Com esteio no ordenamento jurídico pátrio e nos precedentes dos Tribunais Superiores, assinale a afirmativa correta:"
                else:
                    stem = (
                        f"No que concerne à disciplina de {topic_lbl}, com esteio na dogmática jurídica "
                        f"e nos precedentes dos Tribunais Superiores, assinale a afirmativa correta:"
                    )

                correct_conc = "É juridicamente correto afirmar que"
                incorrect_conc = "É incorreto sustentar que"

                alts, correct_letter = self.distractor_builder.build_fgv_alternatives(
                    base_umt=primary_umt,
                    correct_conclusion=correct_conc,
                    incorrect_conclusion=incorrect_conc,
                    target_complexity=diff
                )

                if correct_letter == last_letter:
                    alts, correct_letter = self._rotate_to_avoid_letter(alts, last_letter)

                commentary = (
                    f"QUESTÃO CONCEITUAL / DOGMÁTICA DIRETA.\n"
                    f"Fundamento jurídico de referência: {primary_umt.title} ({primary_umt.source_ref}).\n"
                    f"Dispositivo / Tese integral:\n> {primary_umt.original_text}\n"
                )

                q = Question(
                    id=q_idx + 1 + (block_index - 1) * 5,
                    banca=Banca.FGV,
                    format=fmt,
                    difficulty=diff,
                    topic=primary_umt.topic,
                    stem=stem,
                    alternatives=alts,
                    correct_letter=correct_letter,
                    source_umts=[primary_umt],
                    commentary=commentary,
                    block_index=block_index,
                    question_in_block=q_idx + 1,
                    total_in_block=5
                )

            questions.append(q)
            last_letter = correct_letter

        return questions

    def generate_cebraspe_battery(
        self,
        umts: List[UMT],
        total_items: int = 5
    ) -> List[Question]:
        """
        Gera bateria de itens no padrão CEBRASPE (Certo/Errado).
        Distribui veracidade de forma equilibrada sem permitir sequências de 3 itens iguais.
        """
        if not umts:
            return []

        # Gera padrão de gabarito equilibrado
        veracities = [True] * (total_items // 2) + [False] * (total_items - total_items // 2)
        veracities = self._shuffle_without_triple_streak(veracities)

        questions: List[Question] = []
        umt_idx = 0
        total_umts = len(umts)

        for i, is_certo in enumerate(veracities):
            umt = umts[umt_idx % total_umts]
            umt_idx += 1

            topic_lbl = self._format_topic_natural(umt.topic)
            if topic_lbl == "ao Direito brasileiro":
                preambles = [
                    "A respeito do ordenamento jurídico pátrio e da jurisprudência dos Tribunais Superiores, julgue o item a seguir.",
                    "Com base no entendimento jurisprudencial consolidado e nas normas aplicáveis, julgue o item subsequente.",
                    "Considerando as balizas normativas e a hermenêutica das cortes superiores, julgue o item."
                ]
            else:
                preambles = [
                    f"A respeito da disciplina de {topic_lbl} e da jurisprudência das Cortes Superiores, julgue o item a seguir.",
                    f"Com base na jurisprudência do Supremo Tribunal Federal e do Superior Tribunal de Justiça relativa a {topic_lbl}, julgue o item subsequente.",
                    f"Considerando o ordenamento jurídico pátrio e a hermenêutica das cortes superiores sobre {topic_lbl}, julgue o item."
                ]
            preamble = random.choice(preambles)

            raw_body = umt.content.strip()
            if is_certo:
                correct_val = "CERTO"
                commentary = (
                    f"ITEM CERTO.\n"
                    f"Espelha com exatidão a literalidade do precedente/diploma: {umt.title} ({umt.source_ref})."
                )
            else:
                mut = self.mutator.mutate(raw_body, desired_complexity=umt.complexity)
                raw_body = mut.mutated_text.strip()
                correct_val = "ERRADO"
                commentary = (
                    f"ITEM ERRADO.\n"
                    f"{mut.explanation}\n"
                    f"Redação autêntica de referência:\n> {umt.original_text}"
                )
            # Normaliza pontuação e garante início com letra maiúscula
            clean_body = raw_body.rstrip(". \t\n") + "."
            if len(clean_body) > 1:
                clean_body = clean_body[0].upper() + clean_body[1:]

            statement = f"{preamble}\n\n{clean_body}"

            alts = [
                Alternative(letter="C", text="( ) CERTO", is_correct=(correct_val == "CERTO"), explanation="Assertiva correta."),
                Alternative(letter="E", text="( ) ERRADO", is_correct=(correct_val == "ERRADO"), explanation="Assertiva incorreta.")
            ]

            q = Question(
                id=i + 1,
                banca=Banca.CEBRASPE,
                format=QuestionFormat.CEBRASPE_ISOLADO,
                difficulty=umt.complexity,
                topic=umt.topic,
                stem=statement,
                alternatives=alts,
                correct_letter=correct_val,
                source_umts=[umt],
                commentary=commentary,
                block_index=1,
                question_in_block=i + 1,
                total_in_block=total_items
            )
            questions.append(q)

        return questions

    def _shuffle_without_triple_streak(self, items: List[Any]) -> List[Any]:
        """Embaralha uma lista impedindo que 3 itens consecutivos sejam idênticos."""
        shuffled = list(items)
        for _ in range(50):
            random.shuffle(shuffled)
            has_triple = False
            for idx in range(len(shuffled) - 2):
                if shuffled[idx] == shuffled[idx + 1] == shuffled[idx + 2]:
                    has_triple = True
                    break
            if not has_triple:
                return shuffled
        return shuffled

    def _rotate_to_avoid_letter(
        self,
        alts: List[Alternative],
        forbidden_letter: Optional[str]
    ) -> Tuple[List[Alternative], str]:
        """Garante que o gabarito não seja igual à letra proibida."""
        if not forbidden_letter:
            for a in alts:
                if a.is_correct:
                    return alts, a.letter
            return alts, "A"

        # Se a correta coincide com a proibida, rotaciona a lista
        correct_idx = next(i for i, a in enumerate(alts) if a.is_correct)
        if alts[correct_idx].letter == forbidden_letter:
            # Troca de posição com outra alternativa
            swap_idx = (correct_idx + 1) % len(alts)
            # Troca apenas os conteúdos preservando as letras A, B, C, D, E fixas
            temp_text = alts[correct_idx].text
            temp_exp = alts[correct_idx].explanation
            alts[correct_idx].text = alts[swap_idx].text
            alts[correct_idx].explanation = alts[swap_idx].explanation
            alts[correct_idx].is_correct = False

            alts[swap_idx].text = temp_text
            alts[swap_idx].explanation = temp_exp
            alts[swap_idx].is_correct = True
            return alts, alts[swap_idx].letter

        return alts, alts[correct_idx].letter
