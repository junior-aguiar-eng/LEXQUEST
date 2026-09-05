import os
import sys
from .models import Banca
from .cli import cmd_gerar, cmd_resolver, cmd_importar_pdf
import argparse


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    clear_screen()
    print("=" * 75)
    print("             LEXQUEST - PAINEL DETERMINÍSTICO DE QUESTÕES")
    print("                 (Padrão FGV/ENAM e Cebraspe - Sem IA)")
    print("=" * 75)
    print()
    print("  [1] Resolver Questões no Terminal (FGV - Múltipla Escolha Interativa)")
    print("  [2] Resolver Questões no Terminal (Cebraspe - Certo/Errado Interativo)")
    print()
    print("  [3] Gerar Caderno Completo em Markdown (FGV / Bloco de 5 Questões)")
    print("  [4] Gerar Caderno Completo em Markdown (Cebraspe / Certo ou Errado)")
    print()
    print("  [5] Importar PDF Jurídico para Markdown (PyMuPDF - Leis e Julgados)")
    print("  [6] Executar Testes Automatizados do Sistema (16 testes pytest)")
    print("  [7] Abrir / Gerar Manual Didático do Usuário (PDF & Markdown)")
    print("  [8] Iniciar Web App no Navegador (Streamlit)")
    print()
    print("  [0] Sair")
    print()
    print("=" * 75)


def run_menu():
    while True:
        print_banner()
        try:
            choice = input("Escolha uma opção [0-8]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando...")
            break

        if choice == "0":
            print("\nBons estudos! Até a próxima sessão.")
            break

        elif choice == "1":
            clear_screen()
            print("=" * 75)
            print("   SESSÃO INTERATIVA - MÚLTIPLA ESCOLHA (PADRÃO FGV / ENAM)")
            print("=" * 75)
            print("\nPressione [ENTER] para usar o material padrão (exemplos/adpf_973_exemplo.md)")
            mat = input("Arquivo de estudo (.md): ").strip().strip('"').strip("'")
            if not mat:
                mat = "exemplos/adpf_973_exemplo.md"

            args = argparse.Namespace(material=mat, banca="fgv", qtd=5)
            cmd_resolver(args)
            input("\nPressione [ENTER] para voltar ao menu principal...")

        elif choice == "2":
            clear_screen()
            print("=" * 75)
            print("   SESSÃO INTERATIVA - CERTO OU ERRADO (PADRÃO CEBRASPE)")
            print("=" * 75)
            print("\nPressione [ENTER] para usar o material padrão (exemplos/lei_11281_exemplo.md)")
            mat = input("Arquivo de estudo (.md): ").strip().strip('"').strip("'")
            if not mat:
                mat = "exemplos/lei_11281_exemplo.md"

            qtd_str = input("Quantidade de itens [padrão: 5]: ").strip()
            qtd = int(qtd_str) if qtd_str.isdigit() else 5

            args = argparse.Namespace(material=mat, banca="cebraspe", qtd=qtd)
            cmd_resolver(args)
            input("\nPressione [ENTER] para voltar ao menu principal...")

        elif choice == "3":
            clear_screen()
            print("=" * 75)
            print("   GERAÇÃO DE CADERNO EM MARKDOWN (PADRÃO FGV / ENAM)")
            print("=" * 75)
            print("\nPressione [ENTER] para usar o material padrão (exemplos/adpf_973_exemplo.md)")
            mat = input("Arquivo de estudo (.md): ").strip().strip('"').strip("'")
            if not mat:
                mat = "exemplos/adpf_973_exemplo.md"

            out = input("Nome do arquivo de saída [padrão: simulado_fgv.md]: ").strip()
            if not out:
                out = "simulado_fgv.md"

            qtd_str = input("Quantidade de questões [múltiplo de 5, padrão: 5]: ").strip()
            qtd = int(qtd_str) if qtd_str.isdigit() else 5

            args = argparse.Namespace(material=mat, banca="fgv", qtd=qtd, out=out)
            cmd_gerar(args)
            input("\nPressione [ENTER] para voltar ao menu principal...")

        elif choice == "4":
            clear_screen()
            print("=" * 75)
            print("   GERAÇÃO DE CADERNO EM MARKDOWN (PADRÃO CEBRASPE)")
            print("=" * 75)
            print("\nPressione [ENTER] para usar o material padrão (exemplos/lei_11281_exemplo.md)")
            mat = input("Arquivo de estudo (.md): ").strip().strip('"').strip("'")
            if not mat:
                mat = "exemplos/lei_11281_exemplo.md"

            out = input("Nome do arquivo de saída [padrão: simulado_cebraspe.md]: ").strip()
            if not out:
                out = "simulado_cebraspe.md"

            qtd_str = input("Quantidade de itens [padrão: 10]: ").strip()
            qtd = int(qtd_str) if qtd_str.isdigit() else 10

            args = argparse.Namespace(material=mat, banca="cebraspe", qtd=qtd, out=out)
            cmd_gerar(args)
            input("\nPressione [ENTER] para voltar ao menu principal...")

        elif choice == "5":
            clear_screen()
            print("=" * 75)
            print("   IMPORTAÇÃO E CONVERSÃO DE PDF JURÍDICO PARA MARKDOWN")
            print("=" * 75)
            print("\nArraste e solte o arquivo PDF aqui ou digite o caminho completo:")
            pdf_path = input("Arquivo PDF: ").strip().strip('"').strip("'")
            if not pdf_path:
                print("[!] Nenhum arquivo especificado.")
                input("\nPressione [ENTER] para continuar...")
                continue

            out_md = input("Arquivo Markdown de saída [padrão: material_importado.md]: ").strip()
            if not out_md:
                out_md = "material_importado.md"

            args = argparse.Namespace(arquivo=pdf_path, out=out_md)
            cmd_importar_pdf(args)
            input("\nPressione [ENTER] para voltar ao menu principal...")

        elif choice == "6":
            clear_screen()
            print("=" * 75)
            print("   BATERIA DE TESTES AUTOMATIZADOS (PYTEST)")
            print("=" * 75)
            print("\nExecutando testes no ambiente virtual...\n")
            os.system(f'"{sys.executable}" -m pytest -v')
            input("\nPressione [ENTER] para voltar ao menu principal...")

        elif choice == "7":
            clear_screen()
            print("=" * 75)
            print("   MANUAL DIDÁTICO DO USUÁRIO (PDF & MARKDOWN)")
            print("=" * 75)
            print("\nGerando / Atualizando o manual em PDF...")
            os.system(f'"{sys.executable}" scripts/generate_manual_pdf.py')
            pdf_path = os.path.abspath("Manual_Didatico_LexQuest.pdf")
            print(f"\n[OK] Arquivo disponível em:\n{pdf_path}")
            print("\nAbrindo o arquivo no visualizador padrão do Windows...")
            try:
                os.startfile(pdf_path)
            except Exception:
                pass
            input("\nPressione [ENTER] para voltar ao menu principal...")

        elif choice == "8":
            clear_screen()
            print("=" * 75)
            print("   INICIANDO WEB APP STREAMLIT NO NAVEGADOR")
            print("=" * 75)
            print("\nIniciando servidor local do LexQuest...")
            print("O navegador abrirá automaticamente em alguns segundos (http://localhost:8501).")
            print("Pressione Ctrl+C nesta janela para parar o servidor.\n")
            os.system(f'"{sys.executable}" -m streamlit run app.py')
            input("\nPressione [ENTER] para voltar ao menu principal...")

        else:
            print("\n[!] Opção inválida! Escolha um número entre 0 e 8.")
            input("Pressione [ENTER] para tentar novamente...")


if __name__ == "__main__":
    run_menu()
