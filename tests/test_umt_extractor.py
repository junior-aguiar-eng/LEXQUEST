import os
import pytest
from lexquest.parser import UMTExtractor, EditorialFilter
from lexquest.models import UMTType, Complexity


def test_editorial_filter_clean():
    dirty_text = (
        "# Sumário\n"
        "- Item 1\n"
        "- Item 2\n"
        "## Apresentação\n"
        "Texto de introdução\n"
        "# DIREITO CONSTITUCIONAL\n"
        "Texto do artigo importante.\n"
        "## Exercícios\n"
        "1. Questão antiga que deve ser ignorada."
    )
    clean = EditorialFilter.clean(dirty_text)
    assert "Sumário" not in clean
    assert "Exercícios" not in clean
    assert "DIREITO CONSTITUCIONAL" in clean
    assert "Texto do artigo importante." in clean


def test_extract_adpf_973_jurisprudencia():
    extractor = UMTExtractor()
    sample_path = os.path.join("exemplos", "adpf_973_exemplo.md")
    assert os.path.exists(sample_path)

    umts = extractor.extract_from_file(sample_path)
    assert len(umts) >= 4
    # Primeira UMT deve ser a tese central da ADPF
    assert "RACISMO ESTRUTURAL NO BRASIL - ADPF 973/DF" in umts[0].title
    assert umts[0].umt_type == UMTType.JURISPRUDENCIA
    assert any("ADPF 973" in u.source_ref for u in umts)


def test_extract_lei_11281_normas():
    extractor = UMTExtractor()
    sample_path = os.path.join("exemplos", "lei_11281_exemplo.md")
    assert os.path.exists(sample_path)

    umts = extractor.extract_from_file(sample_path)
    assert len(umts) >= 5
    assert all(u.umt_type == UMTType.LEI_SECA for u in umts)
    titles = [u.title for u in umts]
    assert any("Art. 1" in t or "Art. 2" in t for t in titles)
