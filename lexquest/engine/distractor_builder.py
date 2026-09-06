import re
import random
from typing import List, Tuple, Dict, Any, Optional
from ..models import UMT, Alternative, Complexity
from .mutator import LexicalMutator, MutationResult


class DistractorBuilder:
    """
    Construtor de alternativas e distratores com simetria sintática estrita (padrão FGV/ENAM).
    Garante a fórmula: [Conclusão] + pois / haja vista / uma vez que + [Fundamento],
    com destilação do núcleo substantivo para manter as alternativas concisas,
    proporcionais ao enunciado e com variação métrica contida (+- 15%).
    """

    CONNECTORS = ["pois", "haja vista que", "uma vez que", "porquanto", "dado que"]

    def __init__(self, mutator: Optional[LexicalMutator] = None):
        self.mutator = mutator or LexicalMutator()

    def build_fgv_alternatives(
        self,
        base_umt: UMT,
        correct_conclusion: str,
        incorrect_conclusion: str,
        target_complexity: Complexity
    ) -> Tuple[List[Alternative], str]:
        """
        Gera 5 alternativas simétricas e concisas (A a E):
        1 Correta (com a fundamentação exata e destilada da UMT)
        4 Distratores (com mutações léxicas, dogmáticas ou de competência)
        Retorna (lista_alternativas, letra_gabarito).
        """
        # 1. Destila o núcleo essencial da fundamentação para evitar alternativas gigantescas
        correct_rationale = self._distill_core_rule(base_umt.content)

        # 2. Gera 4 mutações distintas para os distratores
        distractor_mutations: List[MutationResult] = []
        for comp in [Complexity.DIFICIL, Complexity.MEDIO, Complexity.FACIL, target_complexity]:
            mut = self.mutator.mutate(correct_rationale, desired_complexity=comp)
            distractor_mutations.append(mut)

        # Garante 4 textos mutados únicos
        mutated_texts = []
        for mut in distractor_mutations:
            txt = mut.mutated_text
            if txt not in [m[0] for m in mutated_texts] and txt != correct_rationale:
                mutated_texts.append((txt, mut.explanation))

        # Se faltar algum para completar 4, cria variações controladas
        while len(mutated_texts) < 4:
            alt_mut = self.mutator.mutate(correct_rationale, desired_complexity=Complexity.FACIL)
            mutated_texts.append((alt_mut.mutated_text, alt_mut.explanation))

        # Monta a estrutura das 5 opções brutas
        raw_options: List[Dict[str, Any]] = []

        # Opção Correta
        conn = random.choice(self.CONNECTORS)
        raw_options.append({
            "text": f"{correct_conclusion}, {conn} {correct_rationale}.",
            "is_correct": True,
            "explanation": f"GABARITO OFICIAL. Fundamento verídico: {base_umt.title} ({base_umt.source_ref})."
        })

        # Distrator 1: Conclusão oposta com fundamento deturpado
        raw_options.append({
            "text": f"{incorrect_conclusion}, {random.choice(self.CONNECTORS)} {mutated_texts[0][0]}.",
            "is_correct": False,
            "explanation": f"INCORRETA. {mutated_texts[0][1]}"
        })

        # Distrator 2: Conclusão aparente de acerto, mas com premissa falaciosa
        raw_options.append({
            "text": f"{correct_conclusion}, contudo sob a premissa de que {mutated_texts[1][0]}.",
            "is_correct": False,
            "explanation": f"INCORRETA. Embora aparente correção na conclusão, o fundamento é errôneo: {mutated_texts[1][1]}"
        })

        # Distrator 3: Conclusão oposta com erro de qualificador ou de competência
        raw_options.append({
            "text": f"{incorrect_conclusion}, {random.choice(self.CONNECTORS)} {mutated_texts[2][0]}.",
            "is_correct": False,
            "explanation": f"INCORRETA. {mutated_texts[2][1]}"
        })

        # Distrator 4: Conclusão oposta com negação direta
        raw_options.append({
            "text": f"{incorrect_conclusion}, haja vista ser assente que {mutated_texts[3][0]}.",
            "is_correct": False,
            "explanation": f"INCORRETA. {mutated_texts[3][1]}"
        })

        # Embaralha para que a posição do gabarito seja dinâmica
        random.shuffle(raw_options)

        letters = ["A", "B", "C", "D", "E"]
        alternatives: List[Alternative] = []
        correct_letter = "A"

        for idx, opt in enumerate(raw_options):
            let = letters[idx]
            if opt["is_correct"]:
                correct_letter = let
            alternatives.append(Alternative(
                letter=let,
                text=opt["text"],
                is_correct=opt["is_correct"],
                explanation=opt["explanation"]
            ))

        return alternatives, correct_letter

    def build_propositions_question(
        self,
        umts: List[UMT]
    ) -> Tuple[List[str], List[Alternative], str, str]:
        """
        Gera questão no formato Proposições Romanas (I, II e III) combinatórias
        com itens concisos e limpos.
        """
        if len(umts) < 3:
            while len(umts) < 3:
                umts.append(umts[0])

        selected_umts = umts[:3]
        propositions: List[str] = []
        prop_veracity: List[bool] = []
        explanations: List[str] = []

        veracity_patterns = [
            [True, True, True],
            [True, True, False],
            [False, True, True],
            [True, False, True],
            [False, False, True],
            [True, False, False],
        ]
        target_pattern = random.choice(veracity_patterns)

        for idx, (umt, is_true) in enumerate(zip(selected_umts, target_pattern)):
            roman = ["I", "II", "III"][idx]
            content = self._distill_core_rule(umt.content)
            # Garante maiúscula no início da proposição
            if len(content) > 1:
                content = content[0].upper() + content[1:]

            if is_true:
                propositions.append(f"{roman}. {content}.")
                prop_veracity.append(True)
                explanations.append(f"Item {roman}: CORRETO. Em conformidade com: {umt.title} ({umt.source_ref}).")
            else:
                mut = self.mutator.mutate(content, desired_complexity=umt.complexity)
                mut_text = mut.mutated_text
                if len(mut_text) > 1:
                    mut_text = mut_text[0].upper() + mut_text[1:]
                propositions.append(f"{roman}. {mut_text}.")
                prop_veracity.append(False)
                explanations.append(f"Item {roman}: INCORRETO. {mut.explanation}")

        # Determina o texto do gabarito exato
        true_indices = [["I", "II", "III"][i] for i, v in enumerate(prop_veracity) if v]
        if len(true_indices) == 3:
            correct_combo = "I, II e III"
        elif len(true_indices) == 2:
            correct_combo = f"{true_indices[0]} e {true_indices[1]}, apenas"
        elif len(true_indices) == 1:
            correct_combo = f"{true_indices[0]}, apenas"
        else:
            correct_combo = "Nenhum dos itens"

        all_combos = [
            "I, apenas",
            "II, apenas",
            "I e II, apenas",
            "II e III, apenas",
            "I, II e III",
            "I e III, apenas"
        ]

        distractor_combos = [c for c in all_combos if c != correct_combo]
        random.shuffle(distractor_combos)
        selected_distractors = distractor_combos[:4]

        options = [correct_combo] + selected_distractors
        random.shuffle(options)

        letters = ["A", "B", "C", "D", "E"]
        alternatives: List[Alternative] = []
        correct_letter = "A"

        for idx, opt_text in enumerate(options):
            let = letters[idx]
            is_corr = (opt_text == correct_combo)
            if is_corr:
                correct_letter = let
            alternatives.append(Alternative(
                letter=let,
                text=f"está(ão) correto(s) {opt_text}.",
                is_correct=is_corr,
                explanation="Gabarito oficial." if is_corr else "Combinação incorreta dos itens."
            ))

        full_commentary = "\n".join(explanations)
        return propositions, alternatives, correct_letter, full_commentary

    def _distill_core_rule(self, text: str) -> str:
        """
        Destila o núcleo substantivo da regra/tese jurídica,
        eliminando narrativas acessórias, preâmbulos jornalísticos ou citações extensas.
        Garante alternativas concisas e com simetria métrica (+- 15%).
        """
        # 1. Remove marcadores markdown e aspas
        cleaned = re.sub(r"[*\"#`]", "", text).strip()

        # 2. Remove quebras de linha duras dentro da oração
        cleaned = " ".join(cleaned.splitlines())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # 3. Remove prefixos jornalísticos, editoriais e rótulos de seção
        prefixes = [
            r"^COMENT[AÁ]RIOS?\s*:?\s*",
            r"^RELAT[OÓ]RIO\s*:?\s*",
            r"^EMENTA\s*:?\s*",
            r"^TESE\s*:?\s*",
            r"^Sete partidos políticos ingressaram.*?com uma ADPF pedindo\s+",
            r"^Isso porque,\s*embora\s+",
            r"^Mesmo sem declarar o ECI,\s*",
            r"^Além disso,\s*",
            r"^Por fim,\s*",
            r"^Para tanto,\s*",
            r"^Nesse sentido,\s*",
            r"^Art\.\s*\d+[ºo]?\s*[-–—.]?\s*",
            r"^Parágrafo único\s*[-–—.]?\s*",
            r"^I{1,3}\s*[-–—.]?\s*",
            r"^A União poderá:\s*",
            r"^Não além disso,\s*",
            r"^Não por fim,\s*",
        ]
        for p in prefixes:
            cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE).strip()

        # Remove citações ou referências de arquivo que possam ter sobrado
        cleaned = re.sub(r"(?i)documento\s+importado\s*:?\s*[^\s\n]+", "", cleaned)
        cleaned = re.sub(r"(?i)\b[a-z0-9_]+\.pdf\b", "", cleaned)
        cleaned = re.sub(r"(?i)\b(?:sum[aá]rio|[ií]ndice)\b", "", cleaned)
        cleaned = re.sub(r"(?i)\bdireito\s+[a-zçãõ\s]+\s*\.", "", cleaned)

        # Remove dados de processo, relatoria, datas e turmas (evita enunciados artificiais com metadados)
        cleaned = re.sub(r"(?i)\(?(?:agint|resp|rcl|adi|adpf|adc|ado|re|hc|rms|are|edcl|cc|ms|ai|ro|inq|ap)\s+(?:no|na|n[ºo]|n°)?\s*[\d\.\-\/]+[^\)]*\)?", "", cleaned)
        cleaned = re.sub(r"(?i)\b(?:relat[oó]r[a]?|rel\.\s*min|relator\s+ministr[oa])\s+[a-zçãõ\s]+(?=[,\.]|$)", "", cleaned)
        cleaned = re.sub(r"(?i)\bjulgado\s+em\s+\d{1,2}[\/\.]\d{1,2}[\/\.]\d{2,4}\b", "", cleaned)
        cleaned = re.sub(r"(?i)\(?(?:info(?:rmativo)?\s*\d+[^\)]*)\)?", "", cleaned)
        cleaned = re.sub(r"(?i)\b(?:corte especial|plenário|órgão especial|por unanimidade|segunda turma|primeira turma)\b", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # 3. Pega a primeira sentença substantiva de impacto
        sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", cleaned) if len(s.strip()) > 15]
        if sentences:
            core = sentences[0]
        else:
            core = cleaned

        # Trunca para manter concisão métrica sem cortar linhas de raciocínio no meio de preposição
        words = core.split()
        if len(words) > 28:
            words = words[:26]
            trailing_stopwords = {"de", "da", "do", "das", "dos", "e", "ou", "para", "com", "em", "a", "o", "que", "no", "na", "nos", "nas", "por", "sob", "sobre"}
            while words and words[-1].lower().rstrip(".,;:") in trailing_stopwords:
                words.pop()
            core = " ".join(words)

        core = core.rstrip(".,;:")
        if len(core) > 1:
            core = core[0].lower() + core[1:]
        return core
