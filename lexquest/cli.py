import argparse
import os
import sys
from typing import List
from .models import Banca, Question, Complexity
from .parser import UMTExtractor
from .engine import BlockManager
from .renderer import ExamRenderer


def parse_args():
    parser = argparse.ArgumentParser(
        prog="lexquest",
        description="LexQuest: Gerador Determinístico de Questões Jurídicas de Concurso (sem IA)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Subcomando: gerar (Modo Batch)
    parser_gerar = subparsers.add_parser("gerar", help="Compila um caderno de prova em Markdown com gabarito comentado")
    parser_gerar.add_argument("--material", "-m", required=True, help="Caminho do arquivo Markdown de estudo (.md)")
    parser_gerar.add_argument("--banca", "-b", choices=["fgv", "cebraspe"], default="fgv", help="Banca examinadora alvo")
    parser_gerar.add_argument("--qtd", "-q", type=int, default=5, help="Quantidade de questões (FGV em blocos de 5; Cebraspe itens individuais)")
    parser_gerar.add_argument("--out", "-o", default="simulado_gerado.md", help="Arquivo de saída Markdown")

    # Subcomando: resolver (Modo Sessão Interativa de Estudo Ativo)
    parser_resolver = subparsers.add_parser("resolver", help="Inicia uma sessão interativa no terminal estilo examinador")
    parser_resolver.add_argument("--material", "-m", required=True, help="Caminho do arquivo Markdown de estudo (.md)")
    parser_resolver.add_argument("--banca", "-b", choices=["fgv", "cebraspe"], default="fgv", help="Banca examinadora alvo")
    parser_resolver.add_argument("--qtd", "-q", type=int, default=5, help="Quantidade de questões na sessão")

    # Subcomando: importar-pdf (Mineração via PyMuPDF / fitz)
    parser_importar = subparsers.add_parser("importar-pdf", help="Converte acórdãos, informativos ou leis em PDF diretamente para Markdown")
    parser_importar.add_argument("--arquivo", "-a", required=True, help="Caminho do arquivo PDF a ser importado")
    parser_importar.add_argument("--out", "-o", default="material_importado.md", help="Arquivo Markdown de saída")

    return parser.parse_args()


def load_umts_from_material(material_path: str):
    extractor = UMTExtractor()
    if os.path.isfile(material_path):
        return extractor.extract_from_file(material_path)
    elif os.path.isdir(material_path):
        all_umts = []
        for root, _, files in os.walk(material_path):
            for file in files:
                if file.endswith(".md"):
                    p = os.path.join(root, file)
                    all_umts.extend(extractor.extract_from_file(p))
        return all_umts
    else:
        print(f"[ERRO] Material '{material_path}' não encontrado.", file=sys.stderr)
        sys.exit(1)


def cmd_gerar(args):
    print(f"[*] Carregando material em: {args.material}...")
    umts = load_umts_from_material(args.material)
    if not umts:
        print("[ERRO] Nenhuma UMT substantiva pôde ser extraída do material fornecido.", file=sys.stderr)
        sys.exit(1)

    print(f"[+] {len(umts)} Unidade(s) Mínima(s) de Testabilidade (UMTs) mapeadas.")
    banca_enum = Banca.FGV if args.banca == "fgv" else Banca.CEBRASPE
    manager = BlockManager()

    questions: List[Question] = []
    if banca_enum == Banca.FGV:
        num_blocks = max(1, args.qtd // 5)
        print(f"[*] Gerando {num_blocks} bloco(s) de 5 questões no padrão FGV/ENAM...")
        last_letter = None
        for b_idx in range(1, num_blocks + 1):
            block_qs = manager.generate_fgv_block(umts, block_index=b_idx, prev_last_letter=last_letter)
            questions.extend(block_qs)
            if block_qs:
                last_letter = block_qs[-1].correct_letter
    else:
        print(f"[*] Gerando {args.qtd} itens no padrão Cebraspe (Certo/Errado)...")
        questions = manager.generate_cebraspe_battery(umts, total_items=args.qtd)

    # Exibe diagnóstico do Grafo de Conhecimento
    g_stats = manager.knowledge_graph.summary()
    print(f"[+] Grafo Ontológico Ativo: {g_stats['total_nodes']} nós ({g_stats['concept_nodes']} conceitos, {g_stats['organ_nodes']} órgãos) e {g_stats['total_edges']} arestas relacionais.")

    print(f"[*] Renderizando caderno em formato Markdown...")
    title = f"Simulado Oficial Inédito - Padrão {banca_enum.value}"
    md_content = ExamRenderer.render_batch_markdown(questions, title=title)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n[SUCESSO] Caderno de prova gerado com êxito em: {args.out}")
    print(f"          Total de questões: {len(questions)}")
    print(f"          Banca: {banca_enum.value}")


def cmd_resolver(args):
    print(f"[*] Preparando sessão de estudo ativo com base em: {args.material}...")
    umts = load_umts_from_material(args.material)
    if not umts:
        print("[ERRO] Nenhuma UMT encontrada.", file=sys.stderr)
        sys.exit(1)

    banca_enum = Banca.FGV if args.banca == "fgv" else Banca.CEBRASPE
    manager = BlockManager()

    if banca_enum == Banca.FGV:
        questions = manager.generate_fgv_block(umts, block_index=1)[:args.qtd]
    else:
        questions = manager.generate_cebraspe_battery(umts, total_items=args.qtd)

    acertos = 0
    erros = 0

    print("\n" + "=" * 70)
    print(f"   SESSÃO DE RESOLUÇÃO INTERATIVA — BANCA {banca_enum.value}")
    print("=" * 70 + "\n")

    for idx, q in enumerate(questions, start=1):
        print(f"\n--- [ QUESTÃO {idx} DE {len(questions)} ] ---")
        print(f"Tema: {q.topic} | Nível: {q.difficulty.value} | Formato: {q.format.value}")
        print("-" * 50)
        print(q.stem)
        print("")

        valid_answers = []
        if q.banca == Banca.CEBRASPE:
            print("[C] CERTO")
            print("[E] ERRADO")
            valid_answers = ["C", "E", "CERTO", "ERRADO"]
        else:
            for alt in q.alternatives:
                print(f"({alt.letter}) {alt.text}")
            valid_answers = [a.letter for a in q.alternatives]

        print("")
        while True:
            user_ans = input(">> Sua resposta: ").strip().upper()
            if not user_ans:
                continue
            if q.banca == Banca.CEBRASPE:
                if user_ans.startswith("C"):
                    user_ans = "CERTO"
                elif user_ans.startswith("E"):
                    user_ans = "ERRADO"
            if user_ans in [q.correct_letter] or user_ans in valid_answers or (q.banca == Banca.CEBRASPE and user_ans in ["CERTO", "ERRADO"]):
                break
            print(f"Opção inválida! Escolha entre: {', '.join(valid_answers)}")

        # Correção
        is_correct = (user_ans == q.correct_letter)
        print("\n" + "#" * 60)
        if is_correct:
            acertos += 1
            print(f"🎯 RESPOSTA CORRETA! Gabarito Oficial: [{q.correct_letter}]")
        else:
            erros += 1
            print(f"❌ RESPOSTA INCORRETA! Você marcou [{user_ans}], mas o Gabarito é [{q.correct_letter}]")
        print("#" * 60)

        print("\n[DIAGNÓSTICO PEDAGÓGICO E DISTRATORES]:")
        for alt in q.alternatives:
            marker = "➡️" if alt.letter == q.correct_letter else "  "
            print(f"{marker} ({alt.letter}): {alt.explanation}")

        print(f"\n[FUNDAMENTAÇÃO ORIGINAL]:")
        for u in q.source_umts:
            print(f"> {u.title} ({u.source_ref})")

        print("\n" + "-" * 60)
        if idx < len(questions):
            input("Pressione [ENTER] para ir para a próxima questão...")

    print("\n" + "=" * 60)
    print("   RESULTADO FINAL DO SIMULADO")
    print("=" * 60)
    total = acertos + erros
    pct = (acertos / total * 100) if total > 0 else 0
    print(f"Total de questões: {total}")
    print(f"Acertos: {acertos}  |  Erros: {erros}")
    print(f"Aproveitamento: {pct:.1f}%\n")


def cmd_importar_pdf(args):
    print(f"[*] Minerando e estruturando documento PDF: {args.arquivo}...")
    from .parser.pdf_importer import PDFImporter
    importer = PDFImporter()
    if not importer.available:
        print("[ERRO] Biblioteca PyMuPDF (fitz) não está instalada no ambiente.", file=sys.stderr)
        sys.exit(1)
    
    try:
        importer.convert_pdf_to_markdown(args.arquivo, output_md_path=args.out)
        print(f"\n[SUCESSO] Documento PDF convertido com êxito para Markdown: {args.out}")
    except Exception as e:
        print(f"[ERRO] Falha ao processar o PDF: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    args = parse_args()
    if args.command == "gerar":
        cmd_gerar(args)
    elif args.command == "resolver":
        cmd_resolver(args)
    elif args.command == "importar-pdf":
        cmd_importar_pdf(args)
    else:
        print("Comando não especificado. Use 'python -m lexquest.cli --help'.")


if __name__ == "__main__":
    main()
