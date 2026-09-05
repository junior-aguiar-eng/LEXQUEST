from typing import List, Dict, Any, Optional, Tuple
import spacy
from spacy.matcher import DependencyMatcher
from spacy.tokens import Doc
from ..models import Complexity
from .mutator import MutationResult


class LegalSyntaxMatcher:
    """
    Análise Sintática e Desconstrução de Dependências (spaCy DependencyMatcher).
    Identifica na árvore sintática:
    - Sujeito Normativo (nsubj)
    - Verbo Modal / Deôntico (aux / root)
    - Condicionantes e Ressalvas Subordinadas (advcl / mark: salvo, desde que, a menos que)
    """

    def __init__(self, model_name: str = "pt_core_news_sm"):
        try:
            self.nlp = spacy.load(model_name)
        except Exception:
            try:
                from spacy.cli import download
                download(model_name)
                self.nlp = spacy.load(model_name)
            except Exception:
                self.nlp = None

        self.matcher = None
        if self.nlp:
            self.matcher = DependencyMatcher(self.nlp.vocab)
            self._register_patterns()

    def _register_patterns(self):
        # 1. Padrão: Verbo modal deôntico (dever/poder) + verbo principal
        modal_pattern = [
            {
                "RIGHT_ID": "modal_aux",
                "RIGHT_ATTRS": {"LEMMA": {"IN": ["dever", "poder", "caber", "vedar", "proibir"]}}
            },
            {
                "LEFT_ID": "modal_aux",
                "REL_OP": "<",
                "RIGHT_ID": "main_verb",
                "RIGHT_ATTRS": {"POS": "VERB"}
            }
        ]

        # 2. Padrão: Oração subordinada condicional (ressalva com 'salvo', 'desde que', 'se')
        condition_pattern = [
            {
                "RIGHT_ID": "condition_mark",
                "RIGHT_ATTRS": {"LOWER": {"IN": ["salvo", "exceto", "se", "caso", "embora"]}}
            },
            {
                "LEFT_ID": "condition_mark",
                "REL_OP": "<",
                "RIGHT_ID": "subordinate_verb",
                "RIGHT_ATTRS": {"DEP": "advcl"}
            }
        ]

        self.matcher.add("MODAL_DEONTIC", [modal_pattern])
        self.matcher.add("CONDITIONAL_EXCEPTION", [condition_pattern])

    @property
    def is_available(self) -> bool:
        return self.nlp is not None

    def analyze_sentence(self, text: str) -> Dict[str, Any]:
        """Extrai elementos estruturais da oração com base em árvore sintática."""
        if not self.nlp:
            return {"available": False}

        doc: Doc = self.nlp(text)
        subjects = []
        verbs = []
        exceptions = []

        for token in doc:
            # Sujeito
            if "subj" in token.dep_:
                subjects.append(token.subtree)
            # Verbos principais e modais
            if token.pos_ in ["VERB", "AUX"]:
                verbs.append(token)
            # Conjunções de ressalva
            if token.lower_ in ["salvo", "exceto", "ressalvado", "desde", "contudo", "todavia"]:
                # Subárvore da ressalva
                exceptions.append("".join([t.text_with_ws for t in token.subtree]).strip())

        return {
            "available": True,
            "token_count": len(doc),
            "subjects": ["".join([t.text_with_ws for t in s]).strip() for s in subjects],
            "verbs": [v.text for v in verbs],
            "exceptions": exceptions
        }

    def mutate_syntactic_condition(self, text: str) -> Optional[MutationResult]:
        """
        Aplica mutação sintática cirúrgica:
        Localiza a oração subordinada adverbial condicional e inverte a condicionante.
        """
        if not self.nlp:
            return None

        doc: Doc = self.nlp(text)

        # Procura marcadores de condição como 'desde que' ou 'salvo se'
        for token in doc:
            if token.lower_ in ["salvo", "exceto"]:
                # Poda ou inverte a exceção
                target = token.text
                mutated = text.replace(target, "inclusive")
                return MutationResult(
                    original_text=text,
                    mutated_text=mutated,
                    target_term=target,
                    replacement_term="inclusive",
                    difficulty=Complexity.MEDIO,
                    explanation=(
                        "Análise Sintática (spaCy): A regra possui ressalva condicional expressa ('salvo/exceto'), "
                        "tendo sido indevidamente convertida em aplicação irrestrita ('inclusive')."
                    ),
                    success=True
                )
            elif token.lower_ == "desde" and token.i + 1 < len(doc) and doc[token.i + 1].lower_ == "que":
                target = "desde que"
                mutated = text.replace("desde que", "mesmo que não haja")
                return MutationResult(
                    original_text=text,
                    mutated_text=mutated,
                    target_term=target,
                    replacement_term="mesmo que não haja",
                    difficulty=Complexity.DIFICIL,
                    explanation=(
                        "Análise Sintática (spaCy): Suprimiu-se a oração subordinada adverbial condicional necessária ('desde que'), "
                        "desconsiderando requisito indispensável de validade."
                    ),
                    success=True
                )
            elif token.lower_ in ["deverá", "devem"]:
                mutated = text.replace(token.text, "poderá a seu exclusivo critério")
                return MutationResult(
                    original_text=text,
                    mutated_text=mutated,
                    target_term=token.text,
                    replacement_term="poderá a seu exclusivo critério",
                    difficulty=Complexity.FACIL,
                    explanation=(
                        f"Análise Sintática (spaCy): O verbo modal '{token.text}' impõe dever cogente vinculado, "
                        "sendo errôneo atribuir mera discricionariedade administrativa."
                    ),
                    success=True
                )

        return None
