"""
LexQuest v2.0 - Interface Web Streamlit
Aplicação Web Interativa para Resolução e Geração Simbólica de Questões Jurídicas.
100% Determinístico, Auditável e Sem IA Generativa.
"""

import os
import sys
import tempfile
from pathlib import Path
import streamlit as st

# Garante que o pacote lexquest seja importável da raiz
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from lexquest.models import Banca, QuestionFormat, Complexity, Question, UMT
from lexquest.parser.filter import EditorialFilter, LexicalFilter
from lexquest.parser.umt_extractor import UMTExtractor
from lexquest.parser.pdf_importer import extract_umts_from_pdf
from lexquest.engine.block_manager import BlockManager
from lexquest.graph.legal_graph import LegalKnowledgeGraph
from lexquest.renderer import ExamRenderer

# Configuração da Página
st.set_page_config(
    page_title="LexQuest v2.0 - Simulado Jurídico Inteligente",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização CSS personalizada (Rich Aesthetics, Dark/Light equilibrado, tipografia refinada)
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Top banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 60%, #2563eb 100%);
        padding: 24px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }
    .hero-title {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        color: #ffffff;
    }
    .hero-sub {
        font-size: 14px;
        color: #bfdbfe;
        margin-top: 6px;
        margin-bottom: 0;
    }
    .hero-tag {
        display: inline-block;
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        color: #93c5fd;
        margin-bottom: 8px;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        margin-right: 6px;
    }
    .badge-dificil { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
    .badge-medio { background-color: #fef3c7; color: #b45309; border: 1px solid #fcd34d; }
    .badge-facil { background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; }
    .badge-topic { background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
    .badge-format { background-color: #f3e8ff; color: #7e22ce; border: 1px solid #d8b4fe; }

    /* Enunciado */
    .enunciado-text {
        font-size: 15px;
        line-height: 1.6;
        color: #1e293b;
        margin: 14px 0 18px 0;
        white-space: pre-line;
    }

    /* Caixas de Explicação e Feedback */
    .feedback-box-correct {
        background-color: #f0fdf4;
        border: 1px solid #86efac;
        border-left: 5px solid #16a34a;
        padding: 14px 18px;
        border-radius: 8px;
        margin-top: 14px;
    }
    .feedback-box-wrong {
        background-color: #fef2f2;
        border: 1px solid #fca5a5;
        border-left: 5px solid #dc2626;
        padding: 14px 18px;
        border-radius: 8px;
        margin-top: 14px;
    }
    .feedback-title {
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .feedback-desc {
        font-size: 13px;
        color: #334155;
        line-height: 1.45;
        margin: 0;
    }

    /* Placar */
    .score-container {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 24px;
    }
    .score-number {
        font-size: 38px;
        font-weight: 800;
        margin: 4px 0;
    }
    .score-label {
        font-size: 13px;
        color: #dbeafe;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Funções de Carregamento e Extração
@st.cache_data
def load_default_material(file_path: str):
    """Carrega UMTs de arquivos nativos em disco."""
    full_path = BASE_DIR / file_path
    if not full_path.exists():
        return []
    content = full_path.read_text(encoding="utf-8")
    extractor = UMTExtractor()
    return extractor.extract_from_text(content)


def extract_umts_from_uploaded_markdown(content: str):
    extractor = UMTExtractor()
    return extractor.extract_from_text(content)


def extract_umts_from_uploaded_pdf(pdf_bytes: bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    try:
        umts = extract_umts_from_pdf(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return umts


# Inicialização de Estado da Sessão
if "questions" not in st.session_state:
    st.session_state.questions = []
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "current_banca" not in st.session_state:
    st.session_state.current_banca = "fgv"
if "current_material_title" not in st.session_state:
    st.session_state.current_material_title = ""
if "active_umts" not in st.session_state:
    st.session_state.active_umts = []


# ==============================================================================
# SIDEBAR - Configurações e Gerador de Simulado
# ==============================================================================
with st.sidebar:
    st.title("⚖️ Painel LexQuest")
    st.markdown("**Gerador Simbólico & Determinístico**")
    st.caption("Sem IA Generativa • Zero Alucinação")
    st.divider()

    st.subheader("1. Escolha a Banca")
    banca_choice = st.radio(
        "Padrão de Exame:",
        options=["FGV / ENAM (Múltipla Escolha)", "Cebraspe (Certo ou Errado)"],
        index=0,
    )
    banca_enum = Banca.FGV if "FGV" in banca_choice else Banca.CEBRASPE

    st.subheader("2. Quantidade de Questões")
    if banca_enum == Banca.FGV:
        qtd_questoes = st.selectbox("Bloco de Questões:", options=[5, 10, 15], index=0)
    else:
        qtd_questoes = st.slider("Itens para Julgamento:", min_value=3, max_value=20, value=5, step=1)

    st.subheader("3. Material Jurídico de Base")
    material_source = st.selectbox(
        "Fonte de Conteúdo:",
        options=[
            "ADPF 973 - Prisional (Jurisprudência STF)",
            "Lei 11.281 - Portos e Servidões (Lei Seca)",
            "Fazer Upload de Arquivo Próprio (.md ou .pdf)",
        ],
        index=0,
    )

    loaded_umts = []
    mat_title = ""

    if material_source == "ADPF 973 - Prisional (Jurisprudência STF)":
        loaded_umts = load_default_material("exemplos/adpf_973_exemplo.md")
        mat_title = "ADPF 973 (STF)"
    elif material_source == "Lei 11.281 - Portos e Servidões (Lei Seca)":
        loaded_umts = load_default_material("exemplos/lei_11281_exemplo.md")
        mat_title = "Lei Federal nº 11.281"
    else:
        uploaded_file = st.file_uploader("Envie seu PDF ou Markdown:", type=["pdf", "md"])
        if uploaded_file is not None:
            mat_title = uploaded_file.name
            if uploaded_file.name.endswith(".pdf"):
                with st.spinner("Processando PDF com PyMuPDF..."):
                    loaded_umts = extract_umts_from_uploaded_pdf(uploaded_file.getvalue())
            else:
                md_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
                loaded_umts = extract_umts_from_uploaded_markdown(md_text)

            if loaded_umts:
                st.success(f"Extraídas {len(loaded_umts)} UMTs com sucesso!")
            else:
                st.warning("Nenhuma UMT pôde ser extraída do arquivo enviado.")

    st.divider()

    # Botão para gerar simulado
    if st.button("🚀 Gerar Simulado Agora", type="primary", use_container_width=True):
        if not loaded_umts:
            st.error("Nenhum material carregado. Escolha uma opção válida acima.")
        else:
            with st.spinner("Construindo grafo e mutações deônticas..."):
                manager = BlockManager()
                if banca_enum == Banca.FGV:
                    num_blocos = max(1, qtd_questoes // 5)
                    generated_q = []
                    last_letter = None
                    for b_idx in range(1, num_blocos + 1):
                        block_qs = manager.generate_fgv_block(loaded_umts, block_index=b_idx, prev_last_letter=last_letter)
                        generated_q.extend(block_qs)
                        if block_qs:
                            last_letter = block_qs[-1].correct_letter
                    st.session_state.questions = generated_q
                else:
                    st.session_state.questions = manager.generate_cebraspe_battery(loaded_umts, total_items=qtd_questoes)

                st.session_state.user_answers = {}
                st.session_state.submitted = False
                st.session_state.current_banca = "fgv" if banca_enum == Banca.FGV else "cebraspe"
                st.session_state.current_material_title = mat_title
                st.session_state.active_umts = loaded_umts
                st.success(f"Simulado de {len(st.session_state.questions)} questões gerado com sucesso!")


# ==============================================================================
# CABEÇALHO HERO BANNER
# ==============================================================================
st.markdown(
    """
    <div class="hero-banner">
        <span class="hero-tag">Engenharia Ontológica Jurídica • v2.0</span>
        <h1 class="hero-title">LexQuest — Simulador Jurídico Especialista</h1>
        <p class="hero-sub">
            Geração determinística baseada em análise sintática de dependências (spaCy) e grafos de conhecimento (NetworkX).
            Padrão oficial FGV/ENAM e Cebraspe.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# ABAS PRINCIPAIS
# ==============================================================================
tab_simulado, tab_exportar, tab_pdf, tab_metodo = st.tabs([
    "📝 Simulado Interativo",
    "📥 Baixar Caderno & Manual",
    "📄 Extrator de PDFs",
    "ℹ️ Metodologia Sem IA",
])


# ------------------------------------------------------------------------------
# ABA 1: SIMULADO INTERATIVO
# ------------------------------------------------------------------------------
with tab_simulado:
    if not st.session_state.questions:
        st.info("👈 Selecione as opções na barra lateral à esquerda e clique em **'Gerar Simulado Agora'** para iniciar sua sessão de estudos.")
    else:
        q_list: list[Question] = st.session_state.questions
        is_fgv = st.session_state.current_banca == "fgv"

        col_top1, col_top2 = st.columns([3, 1])
        with col_top1:
            banca_label = "FGV / ENAM (Múltipla Escolha)" if is_fgv else "Cebraspe (Certo ou Errado)"
            st.subheader(f"Caderno de Estudos — {banca_label}")
            st.caption(f"Material de Referência: **{st.session_state.current_material_title}** • {len(q_list)} itens")

        with col_top2:
            if st.session_state.submitted:
                total = len(q_list)
                acertos = sum(
                    1 for i, q in enumerate(q_list)
                    if st.session_state.user_answers.get(i) == q.correct_letter
                )
                pct = (acertos / total) * 100 if total > 0 else 0
                st.markdown(
                    f"""
                    <div class="score-container">
                        <div class="score-label">Desempenho</div>
                        <div class="score-number">{acertos}/{total}</div>
                        <div class="score-label">{pct:.1f}% de Acertos</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()

        # Renderização de Cada Questão
        for i, q in enumerate(q_list):
            diff_class = f"badge-{q.difficulty.value.lower()}"
            diff_label = q.difficulty.value

            # Cabeçalho da Questão
            badge_html = f"""
            <div style="margin-bottom: 10px;">
                <span class="badge {diff_class}">{diff_label}</span>
                <span class="badge badge-topic">{q.topic}</span>
                <span class="badge badge-format">{q.format.value}</span>
                <span style="font-size: 11px; color: #64748b; font-weight: 600;">Questão #{q.id} (Bloco {q.block_index})</span>
            </div>
            """
            st.markdown(badge_html, unsafe_allow_html=True)

            # Enunciado
            st.markdown(f'<div class="enunciado-text">{q.stem}</div>', unsafe_allow_html=True)

            # Proposições Romanas (se houver)
            if q.propositions:
                for prop in q.propositions:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**{prop}**")
                st.write("")

            # Opções de Resposta
            if is_fgv:
                options_dict = {alt.letter: f"({alt.letter}) {alt.text}" for alt in q.alternatives}
                current_choice = st.session_state.user_answers.get(i, None)

                selected_key = st.radio(
                    f"Sua resposta para a Questão {i + 1}:",
                    options=list(options_dict.keys()),
                    format_func=lambda k: options_dict[k],
                    index=list(options_dict.keys()).index(current_choice) if current_choice in options_dict else None,
                    key=f"q_radio_{i}",
                    disabled=st.session_state.submitted,
                )
                if selected_key:
                    st.session_state.user_answers[i] = selected_key
            else:
                # Cebraspe Certo ou Errado
                ce_options = ["C", "E"]
                format_map = {"C": "CERTO", "E": "ERRADO"}
                current_choice = st.session_state.user_answers.get(i, None)

                selected_key = st.radio(
                    f"Julgue o item {i + 1}:",
                    options=ce_options,
                    format_func=lambda k: format_map[k],
                    index=ce_options.index(current_choice) if current_choice in ce_options else None,
                    key=f"q_radio_ce_{i}",
                    disabled=st.session_state.submitted,
                    horizontal=True,
                )
                if selected_key:
                    st.session_state.user_answers[i] = selected_key

            # Se já foi submetido, exibe feedback detalhado
            if st.session_state.submitted:
                user_ans = st.session_state.user_answers.get(i)
                is_correct = (user_ans == q.correct_letter)
                fontes_str = ", ".join(u.source_ref for u in q.source_umts) if q.source_umts else "Jurisprudência / Lei Seca"

                if is_correct:
                    st.markdown(
                        f"""
                        <div class="feedback-box-correct">
                            <div class="feedback-title" style="color: #15803d;">✔ RESPOSTA CORRETA! (Gabarito Oficial: {q.correct_letter})</div>
                            <p class="feedback-desc"><strong>Fundamento Jurídico:</strong> {q.commentary}</p>
                            <p class="feedback-desc" style="margin-top: 4px; font-size: 11.5px; color: #475569;"><em>Fonte Normativa:</em> {fontes_str}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    user_str = user_ans if user_ans else "Não respondida"
                    st.markdown(
                        f"""
                        <div class="feedback-box-wrong">
                            <div class="feedback-title" style="color: #b91c1c;">✖ RESPOSTA INCORRETA (Você marcou: {user_str} • Gabarito Oficial: {q.correct_letter})</div>
                            <p class="feedback-desc"><strong>Fundamento Jurídico:</strong> {q.commentary}</p>
                            <p class="feedback-desc" style="margin-top: 4px; font-size: 11.5px; color: #475569;"><em>Fonte Normativa:</em> {fontes_str}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.write("")
            st.divider()

        # Botão de Envio / Correção
        if not st.session_state.submitted:
            if st.button("🏁 Finalizar Simulado e Ver Gabarito Comentado", type="primary", use_container_width=True):
                st.session_state.submitted = True
                st.rerun()
        else:
            if st.button("🔄 Reiniciar Este Simulado", use_container_width=True):
                st.session_state.submitted = False
                st.session_state.user_answers = {}
                st.rerun()


# ------------------------------------------------------------------------------
# ABA 2: EXPORTAR CADERNO & MANUAL
# ------------------------------------------------------------------------------
with tab_exportar:
    st.subheader("📥 Exportação de Materiais Prontos")
    st.caption("Baixe simulados formatados para imprimir ou importar em ferramentas de notas como Obsidian e Notion.")

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        st.markdown("### 📝 Caderno do Simulado Atual")
        if st.session_state.questions:
            q_list = st.session_state.questions
            md_content = ExamRenderer.render_batch_markdown(
                q_list,
                title=f"Simulado {st.session_state.current_banca.upper()} - {st.session_state.current_material_title}"
            )

            st.download_button(
                label="📄 Baixar Simulado em Markdown (.md)",
                data=md_content,
                file_name=f"simulado_{st.session_state.current_banca}.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.info(f"O arquivo contém {len(q_list)} questões com folhas de resposta e gabarito comentado ao final.")
        else:
            st.warning("Gere um simulado primeiro na aba anterior para habilitar o download.")

    with col_exp2:
        st.markdown("### 📘 Manual Didático do Usuário")
        pdf_manual_path = BASE_DIR / "Manual_Didatico_LexQuest.pdf"
        if pdf_manual_path.exists():
            with open(pdf_manual_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label="📕 Baixar Manual Didático Oficial em PDF",
                data=pdf_bytes,
                file_name="Manual_Didatico_LexQuest.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.success("Manual diagramado em 6 páginas A4 cobrindo do zero à operação avançada.")
        else:
            st.warning("O arquivo PDF do manual não foi encontrado na raiz do projeto.")


# ------------------------------------------------------------------------------
# ABA 3: EXTRATOR DE PDFS
# ------------------------------------------------------------------------------
with tab_pdf:
    st.subheader("📄 Extrator e Conversor de PDFs Jurídicos (PyMuPDF)")
    st.markdown(
        """
        Envie informativos do STF/STJ, acórdãos ou o texto de uma nova lei em PDF.
        O motor do LexQuest analisa a estrutura de tópicos, seções e preceitos normativos,
        transformando-os em **UMTs (Unidades Mínimas de Transmissão)** limpas.
        """
    )

    pdf_drop = st.file_uploader("Arraste e solte o documento PDF:", type=["pdf"], key="tab_pdf_uploader")
    if pdf_drop is not None:
        with st.spinner("Processando e estruturando documento..."):
            extracted = extract_umts_from_uploaded_pdf(pdf_drop.getvalue())

        if extracted:
            st.success(f"Foram identificadas **{len(extracted)} Unidades Normativas (UMTs)** no documento!")
            for idx, u in enumerate(extracted, start=1):
                with st.expander(f"UMT {idx}: {u.title} ({u.topic} • {u.complexity.value})"):
                    st.markdown(f"**Fonte:** `{u.source_ref}` | **Tema:** `{u.topic}`")
                    st.write(u.content)

            # Botão para salvar como markdown de estudo
            all_md = "\n\n---\n\n".join([
                f"<!-- RAMO: {u.topic} -->\n<!-- TEMA: {u.topic} -->\n<!-- FONTE: {u.source_ref} -->\n### {u.title}\n{u.content}"
                for u in extracted
            ])
            st.download_button(
                label="💾 Baixar Material Estruturado em Markdown",
                data=all_md,
                file_name=f"{Path(pdf_drop.name).stem}_estruturado.md",
                mime="text/markdown",
            )
        else:
            st.error("Não foi possível identificar teses jurídicas estruturadas neste PDF.")


# ------------------------------------------------------------------------------
# ABA 4: METODOLOGIA SEM IA
# ------------------------------------------------------------------------------
with tab_metodo:
    st.subheader("ℹ️ Por que o LexQuest é 100% Determinístico?")
    st.markdown(
        """
        Diferente de sistemas que utilizam modelos generativos (como ChatGPT ou Claude) sujeitos a **alucinações fáticas**
        e **inversões normativas indevidas**, o LexQuest v2.0 opera com **Engenharia Ontológica** e **Computação Simbólica**:

        1. **Análise Sintática de Dependências (spaCy):**
           Mapeia a árvore sintática de cada frase (*Sujeito + Modal Deôntico + Objeto + Condição/Ressalva*), identificando com precisão matemática onde estão as exceções legais.
        2. **Mutações Deônticas Normadas:**
           Inverte regras deônticas (*deve / pode / é defeso*) respeitando as normas gramaticais de próclise e mesóclise da língua portuguesa formal.
        3. **Grafos de Conhecimento Jurídico (NetworkX):**
           Clusteriza conceitos e precedentes conexos, garantindo que os distratores em questões de bloco pertençam ao mesmo domínio de conhecimento.
        4. **Auditabilidade Plena:**
           Toda alternativa incorreta possui rastreabilidade exata até o fundamento legal violado.
        """
    )
