import pytest
from lexquest.engine.syntax_matcher import LegalSyntaxMatcher


def test_syntax_matcher_analysis():
    matcher = LegalSyntaxMatcher()
    if not matcher.is_available:
        pytest.skip("spaCy modelo pt_core_news_sm não disponível.")

    text = "O magistrado deverá homologar o plano nacional, salvo se houver vício formal."
    res = matcher.analyze_sentence(text)

    assert res["available"] is True
    assert res["token_count"] > 5
    assert any("magistrado" in s for s in res["subjects"])
    assert any("deverá" in v or "homologar" in v for v in res["verbs"])
    assert len(res["exceptions"]) >= 1


def test_syntax_matcher_mutation_exception():
    matcher = LegalSyntaxMatcher()
    if not matcher.is_available:
        pytest.skip("spaCy modelo pt_core_news_sm não disponível.")

    text = "O ato de nomeação produz efeitos imediatos, salvo se pendente de recurso."
    mut = matcher.mutate_syntactic_condition(text)

    assert mut is not None
    assert mut.success is True
    assert "inclusive" in mut.mutated_text
    assert "spaCy" in mut.explanation
