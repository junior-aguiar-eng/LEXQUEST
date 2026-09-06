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
