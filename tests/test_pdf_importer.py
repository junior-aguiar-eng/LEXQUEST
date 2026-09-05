import os
import pytest
from lexquest.parser import PDFImporter, UMTExtractor


def test_pdf_import_and_extraction():
    importer = PDFImporter()
    if not importer.available:
        pytest.skip("PyMuPDF (fitz) não disponível.")

    temp_dir = os.path.join("tests", "_temp_test")
    os.makedirs(temp_dir, exist_ok=True)

    test_pdf = os.path.join(temp_dir, "amostra_direito.pdf")
    test_md = os.path.join(temp_dir, "amostra_direito.md")

    try:
        # 1. Cria um PDF de teste
        importer.create_sample_pdf(test_pdf)
        assert os.path.isfile(test_pdf)

    # 2. Converte PDF para Markdown
        # 2. Converte PDF para Markdown
        md_content = importer.convert_pdf_to_markdown(test_pdf, output_md_path=test_md)
        assert os.path.isfile(test_md)
        assert "DIREITO PENAL" in md_content
        assert "Art. 312" in md_content
        assert "Súmula 599" in md_content

        # 3. Testa pipeline completo: Alimenta o UMTExtractor com o Markdown gerado do PDF
        extractor = UMTExtractor()
        umts = extractor.extract_from_file(test_md)
        assert len(umts) >= 1
        assert any("312" in u.title or "INSIGNIFICÂNCIA" in u.title or "DIREITO PENAL" in u.topic for u in umts)
    finally:
        if os.path.exists(test_pdf):
            os.remove(test_pdf)
        if os.path.exists(test_md):
            os.remove(test_md)
        if os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass
