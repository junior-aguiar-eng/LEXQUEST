import pytest
from lexquest.engine import LexicalMutator
from lexquest.models import Complexity


def test_mutator_facil_inversion():
    mutator = LexicalMutator()
    text = "Em relação ao procedimento administrativo, é vedado o acesso a terceiros."
    res = mutator.mutate(text, desired_complexity=Complexity.FACIL)
    assert res.success
    assert "é permitido" in res.mutated_text or "não é vedado" in res.mutated_text
    assert len(res.explanation) > 10


def test_mutator_medio_condition():
    mutator = LexicalMutator()
    text = "O ato de cobrança independe de autorização judicial prévia."
    res = mutator.mutate(text, desired_complexity=Complexity.MEDIO)
    assert res.success
    assert "depende de prévia autorização judicial" in res.mutated_text


def test_mutator_dificil_dogmatic():
    mutator = LexicalMutator()
    text = "Diante das políticas existentes, afasta-se o estado de coisas inconstitucional."
    res = mutator.mutate(text, desired_complexity=Complexity.DIFICIL)
    assert res.success
    assert "reconhece-se a configuração do estado de coisas inconstitucional" in res.mutated_text
    assert "ADPF 973" in res.explanation or "ECI" in res.explanation


def test_mutator_number_alteration():
    mutator = LexicalMutator()
    text = "A autoridade deverá fixar o plano no prazo de 12 meses após a decisão."
    res = mutator.mutate(text, desired_complexity=Complexity.FACIL)
    assert res.success
    assert ("24 meses" in res.mutated_text) or ("6 meses" in res.mutated_text) or ("prazo de" in res.mutated_text)
