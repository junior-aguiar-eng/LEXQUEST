import os
import pytest
from lexquest.parser import UMTExtractor
from lexquest.graph import LegalKnowledgeGraph


@pytest.fixture
def sample_umts():
    extractor = UMTExtractor()
    sample_path = os.path.join("exemplos", "adpf_973_exemplo.md")
    return extractor.extract_from_file(sample_path)


def test_legal_knowledge_graph_construction(sample_umts):
    kg = LegalKnowledgeGraph()
    kg.build_from_umts(sample_umts)
    summary = kg.summary()

    # Checa se o grafo possui nós e arestas
    assert summary["total_nodes"] > len(sample_umts)
    assert summary["concept_nodes"] >= 2  # Deve ter Racismo Estrutural e Estado de Coisas Inconstitucional
    assert summary["organ_nodes"] >= 1    # Deve ter STF / CNJ
    assert summary["total_edges"] >= 4


def test_graph_correlated_umts(sample_umts):
    kg = LegalKnowledgeGraph()
    kg.build_from_umts(sample_umts)

    base_umt = sample_umts[0]
    correlated = kg.get_correlated_umts(base_umt, max_count=2)

    # As UMTs correlatas devem existir e ser diferentes da base
    for u in correlated:
        assert u.id != base_umt.id


def test_ontology_distractor_hints(sample_umts):
    kg = LegalKnowledgeGraph()
    kg.build_from_umts(sample_umts)

    base_umt = sample_umts[0]
    hints = kg.get_ontology_distractor_hints(base_umt)

    # Deve identificar relação a inverter (ex: AFASTA -> RECONHECE ou órgão STF -> STJ)
    assert len(hints) >= 1
    rel_types = [h["type"] for h in hints]
    assert "RELATION_INVERSION" in rel_types or "ORGAN_SWAP" in rel_types
