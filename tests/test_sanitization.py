"""
Testes de Sanitização de Dados Pessoais (PII), Marcas d'Água e Sumários com Pontilhados.
Garante a conformidade da extração de documentos jurídicos com a LGPD e a ausência de ruídos de índice.
"""

from lexquest.parser.filter import EditorialFilter, DIREITO_BRANCH_HEADINGS
from lexquest.parser.umt_extractor import UMTExtractor


SAMPLE_USER_POLLUTED_TEXT = """
# SUMÁRIO
DIREITO CONSTITUCIONAL .................................................... 10
DIREITO ADMINISTRATIVO .................................................... 45
DIREITO EMPRESARIAL ....................................................... 134
............ 134
............ 142
EXECUÇÃO PENAL ............................................................ 153

CPF: 02662253576
CPF: 02662253576
Telefone: 82981559589
E-mail: junior-aguiar@hotmail.com.br
Licenciado para uso exclusivo de João da Silva - Venda Proibida

# DIREITO EMPRESARIAL

## TÍTULO DE CRÉDITO - ENDOSSO E AVAL
O endosso transmite todos os direitos resultantes do título de crédito. 
O endossante, salvo cláusula em contrário, responde pelo pagamento.
É vedado o endosso parcial, considerando-se nula qualquer estipulação nesse sentido.

CPF: 02662253576
Telefone: 82981559589

## RECUPERAÇÃO JUDICIAL
Estão sujeitos à recuperação judicial todos os créditos existentes na data do pedido, 
ainda que não vencidos. Não se sujeitam à recuperação judicial os créditos de natureza 
estritamente fiduciária sobre bens móveis ou imóveis.
"""


def test_pii_sanitization():
    clean = EditorialFilter.clean_pii(SAMPLE_USER_POLLUTED_TEXT)
    
    assert "02662253576" not in clean
    assert "82981559589" not in clean
    assert "junior-aguiar@hotmail.com.br" not in clean
    assert "Venda Proibida" not in clean
    assert "Licenciado para" not in clean


def test_toc_cleaning():
    clean = EditorialFilter.clean(SAMPLE_USER_POLLUTED_TEXT)
    
    # Não deve conter linhas pontilhadas de sumário
    assert "............ 134" not in clean
    assert "............ 142" not in clean
    assert "..................................................." not in clean
    
    # Deve conter o ramo reconhecido e o conteúdo substancial
    assert "DIREITO EMPRESARIAL" in clean
    assert "endosso transmite todos os direitos" in clean
    assert "sujeitos à recuperação judicial" in clean


def test_umt_extraction_purity():
    extractor = UMTExtractor()
    umts = extractor.extract_from_text(SAMPLE_USER_POLLUTED_TEXT)
    
    assert len(umts) >= 2
    for u in umts:
        # Nenhuma UMT pode conter dados do proprietário do arquivo
        assert "02662253576" not in u.content
        assert "82981559589" not in u.content
        assert "junior-aguiar@hotmail.com.br" not in u.content
        assert "..." not in u.title
        assert "134" not in u.title
        assert "142" not in u.title
        assert len(u.content) >= 40


def test_court_metadata_isolation_and_natural_topics():
    from lexquest.engine.block_manager import BlockManager

    sample_court_clipping = """
    # EXECUCAO PENAL

    ## Reclamação dirigida contra ato do próprio tribunal

    Não é cabível reclamação contra ato proferido por órgão julgador do próprio Superior Tribunal de Justiça.

    AgInt na Rcl 49.398-DF, Rel. Ministra Maria Thereza de Assis Moura, Corte Especial, por unanimidade, julgado em 11/11/2025 (Info 875-STJ).

    COMENTÁRIO:
    A reclamação é um instrumento de hierarquia destinado a fazer cumprir decisões de tribunal superior.
    """

    extractor = UMTExtractor()
    umts = extractor.extract_from_text(sample_court_clipping)

    # 1. Deve extrair as teses substanciais, e JAMAIS a linha de citação como UMT autônoma
    assert len(umts) == 2
    for u in umts:
        assert "AgInt na Rcl" not in u.content
        assert "Maria Thereza" not in u.content
        assert "Info 875-STJ" not in u.content

    # 2. A citação processual deve ter sido capturada como fonte de referência (source_ref)
    assert any("AgInt na Rcl 49.398-DF" in u.source_ref for u in umts)

    # 3. Na geração de itens, não pode haver 'EXECUCAO PENAL' em caixa alta e nem 'AgInt' nas alternativas
    bm = BlockManager()
    cebraspe_questions = bm.generate_cebraspe_battery(umts, total_items=2)
    for q in cebraspe_questions:
        assert "EXECUCAO PENAL" not in q.stem
        assert "Execução Penal" in q.stem
        assert ".." not in q.stem
        assert "AgInt na Rcl" not in q.stem


def test_clitic_repair_and_legal_concepts():
    from lexquest.parser.filter import EditorialFilter
    from lexquest.graph.legal_graph import LegalKnowledgeGraph
    from lexquest.models import UMT, UMTType, Complexity

    # 1. Teste de reparo de ênclises e mesóclises quebradas por OCR/colunas de PDF
    raw_text = "O princípio aplica - se imediatamente. Determinou - se a prisão e caber - lhe - á recurso. Ordem consti- tucional."
    repaired = EditorialFilter.repair_clitics_and_hyphens(raw_text)
    
    assert "aplica-se" in repaired
    assert "Determinou-se" in repaired
    assert "caber-lhe-á" in repaired
    assert "constitucional" in repaired

    # 2. Teste de reconhecimento de conceitos/bigramas jurídicos enriquecidos
    kg = LegalKnowledgeGraph()
    test_umt = UMT(
        id=99,
        title="Reclamação e Presunção de Inocência",
        topic="Direito Processual Civil",
        content="A reclamação constitucional não serve como sucedâneo recursal quando há trânsito em julgado e respeito à presunção de inocência.",
        original_text="A reclamação constitucional não serve como sucedâneo recursal quando há trânsito em julgado e respeito à presunção de inocência.",
        umt_type=UMTType.JURISPRUDENCIA,
        complexity=Complexity.MEDIO,
        source_ref="STF"
    )
    kg.build_from_umts([test_umt])
    
    # Deve conectar aos nós de conceitos jurídicos mapeados
    nodes = list(kg.graph.nodes)
    assert any("PRESUNÇÃO_DE_INOCÊNCIA" in n.upper() or "PRESUNCAO_DE_INOCENCIA" in n.upper() for n in nodes)
    assert any("TRÂNSITO_EM_JULGADO" in n.upper() or "TRANSITO_EM_JULGADO" in n.upper() for n in nodes)
