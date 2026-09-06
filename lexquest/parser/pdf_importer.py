import os
import re
from typing import Optional, Dict, Any, List
from .filter import EditorialFilter, DIREITO_BRANCH_HEADINGS, _DIREITO_BRANCHES_NORMALIZED, _strip_accents

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
    Inspirado na arquitetura do Conversor NexoJuris (junior-aguiar-eng/Conversor-de-PDF-Para-MD-e-Editor).
    Possui filtro ativo contra dados sensíveis (LGPD), marcas d'água de comprador,
    artefatos de sumários com pontilhados e cabeçalhos de páginas.
    """

    def __init__(self):
        self.available = fitz is not None

    def convert_pdf_to_markdown(
        self,
        pdf_path: str,
        output_md_path: Optional[str] = None
    ) -> str:
        """
        Extrai o texto do PDF estruturando títulos, artigos e eliminando ruídos.
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
            page_height = page.rect.height

            # Extrai blocos de texto com coordenadas
            # (x0, y0, x1, y1, text, block_no, block_type)
            blocks = page.get_text("blocks")

            for block in blocks:
                if len(block) < 5 or block[6] != 0:  # Apenas blocos de texto
                    continue

                x0, y0, x1, y1, text = block[0], block[1], block[2], block[3], block[4]

                # 1. Ignora cabeçalhos e rodapés extremos se forem pequenos números de página ou ruído
                is_header_or_footer = (y0 < page_height * 0.04) or (y1 > page_height * 0.96)

                raw_block_lines = text.splitlines()
                clean_block_lines = []

                for raw_line in raw_block_lines:
                    line = raw_line.strip()
                    if not line:
                        continue

                    # Se for rodapé/cabeçalho com apenas número de página ou dado pessoal, descarta
                    if is_header_or_footer:
                        if re.match(r"^\d{1,4}$", line) or EditorialFilter.is_toc_line(line):
                            continue
                        if any(p.search(line) for p in EditorialFilter.PII_PATTERNS):
                            continue

                    # 2. Expurgo de Linhas de Sumário com Pontilhados (ex: "... 134", "EXECUÇÃO PENAL ... 153")
                    if EditorialFilter.is_toc_line(line):
                        continue

                    # 3. Expurgo de Dados Pessoais (CPF, Telefone, Email, Licenciado para...)
                    cleaned_line = EditorialFilter.clean_pii(line).strip()
                    if not cleaned_line:
                        continue

                    # 4. Detecção e Normalização de Ramos do Direito (ex: DIREITO EMPRESARIAL, EXECUÇÃO PENAL)
                    norm_line = _strip_accents(cleaned_line.replace("**", "").replace("#", "")).upper().strip()
                    if norm_line in _DIREITO_BRANCHES_NORMALIZED:
                        clean_block_lines.append(f"\n# {norm_line}\n")
                        continue

                    # 5. Detecção de cabeçalhos de julgados, artigos e seções
                    if re.match(r"^(INFORMATIVO|SÚMULA\s+\d+|TEMA\s+\d+|ADPF\s+\d+|ADI\s+\d+|RE\s+\d+)", cleaned_line, re.IGNORECASE):
                        clean_block_lines.append(f"\n# **{cleaned_line}**\n")
                    elif re.match(r"^Art\.\s*\d+", cleaned_line, re.IGNORECASE):
                        clean_block_lines.append(f"\n**{cleaned_line}**\n")
                    elif re.match(r"^(COMENTÁRIOS|TESE|EMENTA|RELATÓRIO|VOTO):?$", cleaned_line, re.IGNORECASE):
                        clean_block_lines.append(f"\n## **{cleaned_line}**\n")
                    else:
                        clean_block_lines.append(cleaned_line)

                if clean_block_lines:
                    # Une linhas do bloco reconstruindo parágrafos coerentes (desfaz quebra por hifenização)
                    block_text = "\n".join(clean_block_lines)
                    # Desfaz hifenização no final de linha (ex: "constitu- \n cional" -> "constitucional")
                    block_text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", block_text)
                    md_lines.append(f"{block_text}\n")

        full_md = "\n".join(md_lines)
        # Aplica o filtro editorial completo para garantir conformidade
        sanitized_md = EditorialFilter.clean(full_md)

        if output_md_path:
            with open(output_md_path, "w", encoding="utf-8") as f:
                f.write(sanitized_md)

        return sanitized_md

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

        rect = fitz.Rect(50, 50, 550, 750)
        page.insert_textbox(rect, text_content, fontsize=12)
        doc.save(output_pdf_path)
        doc.close()


def extract_umts_from_pdf(pdf_path: str) -> List[Any]:
    """Extrai UMTs diretamente de um arquivo PDF sanitizado."""
    importer = PDFImporter()
    md_text = importer.convert_pdf_to_markdown(pdf_path)
    from .umt_extractor import UMTExtractor
    return UMTExtractor().extract_from_text(md_text)
