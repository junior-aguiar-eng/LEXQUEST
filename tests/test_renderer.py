import os
import pytest
from lexquest.parser import UMTExtractor
from lexquest.engine import BlockManager
from lexquest.renderer import ExamRenderer


def test_markdown_rendering():
    extractor = UMTExtractor()
    sample_path = os.path.join("exemplos", "adpf_973_exemplo.md")
    umts = extractor.extract_from_file(sample_path)

    manager = BlockManager()
    questions = manager.generate_fgv_block(umts, block_index=1)

    rendered_md = ExamRenderer.render_batch_markdown(questions, title="Simulado FGV Teste")
    
    assert "# **SIMULADO FGV TESTE**" in rendered_md
    assert "## **CADERNO DE QUESTÕES**" in rendered_md
    assert "## **FOLHA DE GABARITOS E COMENTÁRIOS DETALHADOS**" in rendered_md
    assert "QUESTÃO 01" in rendered_md
    assert "QUESTÃO 05" in rendered_md
    assert "GABARITO OFICIAL" in rendered_md
