import os
import pytest
from lexquest.parser import UMTExtractor
from lexquest.engine import BlockManager
from lexquest.models import Banca, QuestionFormat, Complexity


@pytest.fixture
def sample_umts():
    extractor = UMTExtractor()
    sample_path = os.path.join("exemplos", "adpf_973_exemplo.md")
    return extractor.extract_from_file(sample_path)


def test_fgv_block_structure(sample_umts):
    manager = BlockManager()
    block = manager.generate_fgv_block(sample_umts, block_index=1)
    
    assert len(block) == 5
    
    # 1. Checa formatos: exatamente 3 casos, 1 proposições e 1 conceitual
    formats = [q.format for q in block]
    assert formats.count(QuestionFormat.CASO_NARRATIVO) == 3
    assert formats.count(QuestionFormat.PROPOSICOES_ROMANAS) == 1
    assert formats.count(QuestionFormat.CONCEITUAL_DIRETA) == 1

    # 2. Checa complexidades: 3 difíceis, 1 média, 1 fácil
    complexities = [q.difficulty for q in block]
    assert complexities.count(Complexity.DIFICIL) == 3
    assert complexities.count(Complexity.MEDIO) == 1
    assert complexities.count(Complexity.FACIL) == 1

    # 3. Checa regra de não repetição de letras consecutivas no gabarito
    letters = [q.correct_letter for q in block]
    for i in range(len(letters) - 1):
        assert letters[i] != letters[i + 1], f"Letras consecutivas iguais: {letters[i]} e {letters[i+1]}"

    # 4. Checa se cada questão tem 5 alternativas (A a E)
    for q in block:
        assert len(q.alternatives) == 5
        alt_letters = [a.letter for a in q.alternatives]
        assert alt_letters == ["A", "B", "C", "D", "E"]
        assert sum(1 for a in q.alternatives if a.is_correct) == 1


def test_cebraspe_battery_balance(sample_umts):
    manager = BlockManager()
    items = manager.generate_cebraspe_battery(sample_umts, total_items=10)
    
    assert len(items) == 10
    gabaritos = [q.correct_letter for q in items]
    
    assert gabaritos.count("CERTO") == 5
    assert gabaritos.count("ERRADO") == 5
    
    # Não pode ter mais de 3 seguidos iguais
    for i in range(len(gabaritos) - 3):
        assert not (gabaritos[i] == gabaritos[i+1] == gabaritos[i+2] == gabaritos[i+3])
