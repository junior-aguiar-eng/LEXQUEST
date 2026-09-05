import re
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple
from ..models import Complexity


@dataclass
class MutationResult:
    original_text: str
    mutated_text: str
    target_term: str
    replacement_term: str
    difficulty: Complexity
    explanation: str
    success: bool = True


class LexicalMutator:
    """
    Motor de mutação léxica e deôntica determinística.
    Aplica inversões pontuais em dispositivos legais e teses jurisprudenciais
    de acordo com a matriz de complexidade (Fácil, Média e Difícil),
    integrado com spaCy DependencyMatcher para análise de árvores sintáticas.
    """

    def __init__(self):
        try:
            from .syntax_matcher import LegalSyntaxMatcher
            self.syntax_matcher = LegalSyntaxMatcher()
        except Exception:
            self.syntax_matcher = None

    # Mutações Fáceis: Inversões deônticas diretas e óbvias
    FACIL_RULES: List[Tuple[str, str, str]] = [
        (r"\bé vedado\b", "é permitido", "A regra original proíbe a conduta (é vedado), e não permite."),
        (r"\bé vedada\b", "é permitida", "A regra original proíbe a conduta (é vedada), e não permite."),
        (r"\bé proibido\b", "é autorizado", "O ordenamento veda a prática, sendo incorreto afirmar que é autorizada."),
        (r"\bé proibida\b", "é autorizada", "O ordenamento veda a prática, sendo incorreto afirmar que é autorizada."),
        (r"\bé permitido\b", "é vedado", "A norma expressamente autoriza a hipótese, sendo incorreto apontar proibição."),
        (r"\bé facultado\b", "é obrigatório", "Trata-se de faculdade/discricionariedade, e não de obrigação vinculada."),
        (r"\bé obrigatório\b", "é facultativo", "A conduta é de observância obrigatória e cogente, e não mera faculdade."),
        (r"\bdeverá\b", "poderá a seu critério", "O preceito é imperativo (deverá), inexistindo discricionariedade."),
        (r"\bsempre\b", "em nenhuma hipótese", "A regra impõe aplicação sistemática, sendo errôneo afastar completamente a hipótese."),
        (r"\bnunca\b", "obrigatoriamente", "A regra impõe vedação absoluta, sendo incorreto afirmar a obrigatoriedade."),
    ]

    # Mutações Médias: Supressão de condicionantes, troca de qualificadores e órgãos próximos
    MEDIO_RULES: List[Tuple[str, str, str]] = [
        (r"\bsalvo se\b", "inclusive se", "A hipótese possui ressalva expressa (salvo se), não incidindo irrestritamente."),
        (r"\bdesde que\b", "mesmo que não", "Há condicionante necessária legal (desde que), que foi indevidamente suprimida."),
        (r"\bindepende de autorização\b", "depende de prévia autorização judicial", "A ordem constitucional ou legal dispensa autorização prévia para o ato."),
        (r"\bdepende de prévia autorização\b", "independe de qualquer autorização", "Exige-se autorização como requisito indispensável de validade."),
        (r"\bmediante autorização judicial\b", "independentemente de ordem judicial", "A cláusula de reserva de jurisdição impõe prévia chancela judicial."),
        (r"\bSupremo Tribunal Federal\b", "Superior Tribunal de Justiça", "A competência originária/recursal descrita é privativa do STF, e não do STJ."),
        (r"\bSuperior Tribunal de Justiça\b", "Supremo Tribunal Federal", "A competência/jurisprudência citada pertence ao STJ, e não ao STF."),
        (r"\bMinistro de Estado da Fazenda\b", "Presidente da República exclusivamente", "A competência administrativa é atribuída ao Ministro da Fazenda, e não privativa do Presidente."),
        (r"\bprazo de (\d+) meses\b", r"prazo de 24 meses", "O prazo fixado pelo precedente/norma é divergente do indicado na assertiva."),
        (r"\bprazo de (\d+) dias\b", r"prazo de 30 dias", "O prazo legalmente cominado difere daquele apresentado na assertiva."),
    ]

    # Mutações Difíceis: Inversões dogmáticas e jurisprudenciais sutis
    DIFICIL_RULES: List[Tuple[str, str, str]] = [
        (r"\bprescinde de\b", "imprescinde de", "O instituto prescinde (dispensa) o elemento, sendo incorreto exigir sua imprescindibilidade."),
        (r"\bimprescinde de\b", "prescinde de", "O instituto imprescinde (exige obrigatoriamente) o requisito apontado."),
        (r"\bnulidade relativa\b", "nulidade absoluta", "A jurisprudência consolidada reconhece hipótese de nulidade apenas relativa, que exige demonstração de efetivo prejuízo."),
        (r"\bnulidade absoluta\b", "mera irregularidade procedimental", "O vício viola garantia substancial, configurando nulidade absoluta insanável."),
        (r"\bé imprescritível\b", "sujeita-se ao prazo prescricional quinquenal", "Por expressa previsão constitucional/jurisprudencial, a hipótese é imprescritível."),
        (r"\bafasta-se o estado de coisas inconstitucional\b", "reconhece-se a configuração do estado de coisas inconstitucional", "O STF expressamente rejeitou a declaração do estado de coisas inconstitucional (ECI) em razão de políticas existentes (ADPF 973)."),
        (r"\brejeitou o pedido de declaração do estado de coisas inconstitucional\b", "declarou formalmente o estado de coisas inconstitucional", "O STF reconheceu o racismo estrutural, mas afastou a caracterização do ECI ante a ausência de omissão absoluta estatal."),
        (r"\bnão se configura a omissão absoluta do Estado\b", "restou demonstrada a inércia absoluta e generalizada dos três poderes", "O tribunal entendeu inexistir omissão absoluta, haja vista a existência de programas afirmativos em curso."),
        (r"\bex tunc\b", "ex nunc", "Os efeitos da decisão/ato retroagem à origem (ex tunc), não operando apenas prospectivamente."),
        (r"\bex nunc\b", "ex tunc", "A modulação conferiu efeitos puramente prospectivos (ex nunc), não retroativos."),
        (r"\bcompetência privativa da União\b", "competência concorrente entre União e Estados", "A matéria é de competência legislativa privativa da União, sendo vedada lei estadual sem lei complementar autorizadora."),
    ]

    def mutate(
        self,
        text: str,
        desired_complexity: Optional[Complexity] = None
    ) -> MutationResult:
        """
        Aplica mutação em um trecho de texto com base no nível de complexidade desejado.
        Se não for especificado ou não houver casamento no nível exato, faz fallback inteligente.
        """
        rules_order = []
        if desired_complexity == Complexity.DIFICIL:
            rules_order = [self.DIFICIL_RULES, self.MEDIO_RULES, self.FACIL_RULES]
        elif desired_complexity == Complexity.MEDIO:
            rules_order = [self.MEDIO_RULES, self.DIFICIL_RULES, self.FACIL_RULES]
        else:
            rules_order = [self.FACIL_RULES, self.MEDIO_RULES, self.DIFICIL_RULES]

        for rule_set in rules_order:
            comp_level = (
                Complexity.DIFICIL if rule_set is self.DIFICIL_RULES
                else (Complexity.MEDIO if rule_set is self.MEDIO_RULES else Complexity.FACIL)
            )
            # Embaralha as regras para não aplicar sempre a primeira que casar
            shuffled_rules = list(rule_set)
            random.shuffle(shuffled_rules)

            for pattern, replacement, explanation in shuffled_rules:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    # Aplica substituição
                    mutated = re.sub(pattern, replacement, text, count=1, flags=re.IGNORECASE)
                    return MutationResult(
                        original_text=text,
                        mutated_text=mutated,
                        target_term=match.group(0),
                        replacement_term=replacement,
                        difficulty=comp_level,
                        explanation=explanation,
                        success=True
                    )

        # Se nenhuma regra de dicionário casou, tenta mutação numérica determinística
        num_result = self._mutate_numbers(text)
        if num_result:
            return num_result

        # Tenta mutação de árvore sintática via spaCy (DependencyMatcher)
        if self.syntax_matcher and self.syntax_matcher.is_available:
            syntax_result = self.syntax_matcher.mutate_syntactic_condition(text)
            if syntax_result:
                return syntax_result

        # Fallback de negação básica
        return self._mutate_fallback_negation(text)

    def _mutate_numbers(self, text: str) -> Optional[MutationResult]:
        """Altera prazos, quóruns ou anos caso existam no texto."""
        match = re.search(r"\b(\d+)\s+(dias|meses|anos|horas)\b", text, flags=re.IGNORECASE)
        if match:
            num = int(match.group(1))
            unit = match.group(2)
            altered_num = num * 2 if num <= 15 else max(5, num // 2)
            mutated = text[:match.start()] + f"{altered_num} {unit}" + text[match.end():]
            return MutationResult(
                original_text=text,
                mutated_text=mutated,
                target_term=f"{num} {unit}",
                replacement_term=f"{altered_num} {unit}",
                difficulty=Complexity.FACIL,
                explanation=f"O prazo cominado é de {num} {unit}, sendo incorreto afirmar que é de {altered_num} {unit}.",
                success=True
            )
        return None

    def _mutate_fallback_negation(self, text: str) -> MutationResult:
        """Inversão léxica básica de polaridade quando não há regra específica."""
        if " não " in text.lower():
            mutated = re.sub(r"\b[Nn]ão\s+", "", text, count=1)
            explanation = "A assertiva suprimiu a vedação/negativa original constante do texto jurídico."
        else:
            # 1. Trata casos especiais de enclise que exigem próclise com a negação
            enclisis_map = [
                (r"\breconhece-se\b", "não se reconhece"),
                (r"\bdeterminou-se\b", "não se determinou"),
                (r"\bafasta-se\b", "não se afasta"),
                (r"\baplica-se\b", "não se aplica"),
                (r"\badmite-se\b", "não se admite"),
                (r"\bexige-se\b", "não se exige"),
            ]
            mutated = text
            explanation = "A assertiva inverteu o sentido do preceito mediante inserção de negativa indevida."
            applied = False
            for pat, repl in enclisis_map:
                if re.search(pat, mutated, flags=re.IGNORECASE):
                    mutated = re.sub(pat, repl, mutated, count=1, flags=re.IGNORECASE)
                    applied = True
                    break

            if not applied:
                # 2. Insere 'não' antes do verbo principal/modal mais comum
                verbs = [
                    r"\bdeverão\b", r"\bdeverá\b", r"\bdeve\b", r"\bdevem\b",
                    r"\bpoderão\b", r"\bpoderá\b", r"\bpode\b", r"\bpodem\b",
                    r"\bcaberá\b", r"\bcabe\b", r"\bé\b", r"\bsão\b", r"\bterá\b"
                ]
                for v in verbs:
                    if re.search(v, mutated, flags=re.IGNORECASE):
                        mutated = re.sub(v, lambda m: f"não {m.group(0)}", mutated, count=1, flags=re.IGNORECASE)
                        applied = True
                        break

            if not applied:
                # Se ainda não casou, introduz negação no início de forma elegante
                mutated = "descabe sustentar que " + text[:1].lower() + text[1:]

        return MutationResult(
            original_text=text,
            mutated_text=mutated,
            target_term="polaridade",
            replacement_term="negação",
            difficulty=Complexity.FACIL,
            explanation=explanation,
            success=True
        )
