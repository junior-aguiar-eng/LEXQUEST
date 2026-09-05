import os
import re
from typing import Optional, Dict, Any, List
try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class PDFImporter:
    """
    Importador e Minerador de Documentos Jurídicos em PDF (via PyMuPDF / fitz).
    Converte acórdãos, informativos do STF/STJ, apostilas e códigos em PDF
    diretamente no formato estruturado de Markdown compatível com o LexQuest.
    """

    def __init__(self):
        self.available = fitz is not None

    def convert_pdf_to_markdown(
        self,
        pdf_path: str,
        output_md_path: Optional[str] = None
    ) -> str:
        """
        Extrai o texto do PDF preservando blocos estruturados e gera um documento Markdown.
        """
        if not self.available:
            raise RuntimeError("Biblioteca PyMuPDF não está instalada no ambiente.")

        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")

        doc = fitz.open(pdf_path)
        md_lines = []
        md_lines.append(f"# **DOCUMENTO IMPORTADO: {os.path.basename(pdf_path)}**\n")

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            
            for raw_line in page_text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue

                # Normalização e detecção de cabeçalhos jurídicos
                if re.match(r"^(DIREITO\s+[A-ZÇÃÕ]+|INFORMATIVO|SÚMULA\s+\d+|TEMA\s+\d+|ADPF\s+\d+|ADI\s+\d+|RE\s+\d+)", line, re.IGNORECASE):
                    md_lines.append(f"\n# **{line}**\n")
                elif re.match(r"^Art\.\s*\d+", line, re.IGNORECASE):
                    # Destaca artigos de lei seca
                    md_lines.append(f"\n**{line}**\n")
                elif re.match(r"^(COMENTÁRIOS|TESE|EMENTA|RELATÓRIO|VOTO):?$", line, re.IGNORECASE):
                    md_lines.append(f"\n## **{line}**\n")
                else:
                    md_lines.append(f"{line}\n")

        full_md = "\n".join(md_lines)

        if output_md_path:
            with open(output_md_path, "w", encoding="utf-8") as f:
                f.write(full_md)

        return full_md

    def create_sample_pdf(self, output_pdf_path: str):
        """Cria um PDF de amostra para testes automatizados da extração."""
        if not self.available:
            return

        doc = fitz.open()
        page = doc.new_page()

        text_content = (
            "DIREITO PENAL\n"
            "TEMA 123 - PRINCÍPIO DA INSIGNIFICÂNCIA\n"
            "O princípio da insignificância é inaplicável aos crimes contra a administração pública.\n"
            "COMENTÁRIOS\n"
            "O Superior Tribunal de Justiça consolidou entendimento por meio da Súmula 599. "
            "A prática de crimes funcionais tutela a moralidade administrativa, "
            "sendo inviável afastar a tipicidade material pelo reduzido valor patrimonial da lesão.\n"
            "Art. 312 O funcionário público que apropriar-se de dinheiro ou valor de que tem a posse em razão do cargo..."
        )

        # Insere texto na página
        rect = fitz.Rect(50, 50, 550, 750)
        page.insert_textbox(rect, text_content, fontsize=12)
        doc.save(output_pdf_path)
        doc.close()


def extract_umts_from_pdf(pdf_path: str) -> List[Any]:
    """Extrai UMTs diretamente de um arquivo PDF."""
    importer = PDFImporter()
    md_text = importer.convert_pdf_to_markdown(pdf_path)
    from .umt_extractor import UMTExtractor
    return UMTExtractor().extract_from_text(md_text)

