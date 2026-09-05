"""
Script gerador do Manual Didático do LexQuest em PDF de alta qualidade visual (usando PyMuPDF)
e em Markdown completo (para leitura no editor).
"""

import os
import sys
from pathlib import Path
import pymupdf

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PDF = BASE_DIR / "Manual_Didatico_LexQuest.pdf"
OUTPUT_MD = BASE_DIR / "MANUAL_DIDATICO_LEXQUEST.md"

CSS_STYLES = """
@page {
    size: A4;
    margin: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    line-height: 1.45;
    margin: 0;
    padding: 0;
    background-color: #ffffff;
}

/* Capa */
.cover-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 55%, #1d4ed8 100%);
    color: #ffffff;
    height: 770px;
    padding: 35px;
    border-radius: 8px;
    box-sizing: border-box;
}

.cover-badge {
    display: inline-block;
    background-color: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.35);
    color: #93c5fd;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.cover-title {
    font-size: 34px;
    font-weight: 800;
    margin-top: 25px;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
    color: #ffffff;
    line-height: 1.15;
}

.cover-subtitle {
    font-size: 16px;
    color: #bfdbfe;
    margin-bottom: 25px;
    font-weight: 400;
    line-height: 1.35;
}

.cover-divider {
    height: 3px;
    background: linear-gradient(90deg, #60a5fa 0%, rgba(255,255,255,0.1) 100%);
    margin-bottom: 25px;
}

.cover-feature-box {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}

.cover-feature-title {
    font-size: 13px;
    font-weight: 700;
    color: #93c5fd;
    text-transform: uppercase;
    margin-bottom: 4px;
}

.cover-feature-desc {
    font-size: 12px;
    color: #e2e8f0;
    margin: 0;
}

.cover-footer {
    margin-top: 30px;
    font-size: 11px;
    color: #94a3b8;
    border-top: 1px solid rgba(255, 255, 255, 0.15);
    padding-top: 14px;
}

/* Páginas de Conteúdo */
.page-header {
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 6px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
}

.header-tag {
    font-size: 10px;
    font-weight: 700;
    color: #2563eb;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.h1-title {
    color: #0f172a;
    font-size: 20px;
    font-weight: 800;
    margin: 0 0 6px 0;
    letter-spacing: -0.3px;
}

.h2-title {
    color: #1e3a8a;
    font-size: 14px;
    font-weight: 700;
    margin: 12px 0 6px 0;
    border-left: 3px solid #2563eb;
    padding-left: 8px;
}

p, li {
    font-size: 11.5px;
    color: #334155;
    line-height: 1.45;
    margin-top: 0;
    margin-bottom: 8px;
}

ul, ol {
    margin-top: 0;
    margin-bottom: 8px;
    padding-left: 20px;
}

.callout-blue {
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    border-left: 4px solid #2563eb;
    padding: 10px 14px;
    border-radius: 6px;
    margin: 10px 0;
}

.callout-green {
    background-color: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 4px solid #16a34a;
    padding: 10px 14px;
    border-radius: 6px;
    margin: 10px 0;
}

.callout-amber {
    background-color: #fffbeb;
    border: 1px solid #fde68a;
    border-left: 4px solid #d97706;
    padding: 10px 14px;
    border-radius: 6px;
    margin: 10px 0;
}

.callout-title {
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 4px;
    color: #0f172a;
}

.table-box {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 11px;
}

.table-box th {
    background-color: #1e293b;
    color: #ffffff;
    text-align: left;
    padding: 6px 10px;
    font-weight: 600;
}

.table-box td {
    border-bottom: 1px solid #e2e8f0;
    padding: 6px 10px;
    color: #334155;
}

.table-box tr:nth-child(even) td {
    background-color: #f8fafc;
}

.code-block {
    background-color: #0f172a;
    color: #f8fafc;
    padding: 10px 12px;
    border-radius: 6px;
    font-family: Consolas, "Liberation Mono", Courier, monospace;
    font-size: 10px;
    line-height: 1.4;
    margin: 8px 0;
    white-space: pre-wrap;
}

.key-badge {
    background-color: #e2e8f0;
    color: #0f172a;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid #cbd5e1;
    font-family: monospace;
    font-size: 10px;
}
"""

PAGE_RECT = pymupdf.Rect(40, 35, 555, 805)


def create_page_1_cover():
    return """
    <div class="cover-container">
        <span class="cover-badge">Engenharia Ontológica Jurídica</span>
        <h1 class="cover-title">LEXQUEST v2.0</h1>
        <div class="cover-subtitle">Manual Didático &amp; Guia de Operação Prática</div>
        <div class="cover-divider"></div>
        
        <p style="color: #e2e8f0; font-size: 13px; margin-bottom: 20px;">
            Sistema Especialista de Geração Simbólica e Determinística de Questões para Concursos de Carreiras Jurídicas (Magistratura, Ministério Público, Defensoria e ENAM).
        </p>

        <div class="cover-feature-box">
            <div class="cover-feature-title">&#9679; 100% Determinístico e Sem IA Generativa</div>
            <p class="cover-feature-desc">Zero alucinações fáticas ou normativas. Cada questão, alternativa e distrator é rigorosamente amarrado ao texto estrito da lei ou ao teor do precedente vinculante.</p>
        </div>

        <div class="cover-feature-box">
            <div class="cover-feature-title">&#9679; Padrões de Bancas Examinadoras de Elite</div>
            <p class="cover-feature-desc">Simulação de casos forenses e narrativas em 3 parágrafos padrão FGV/ENAM (com trava contra letras repetidas consecutivas) e assertivas de alta precisão deôntica padrão Cebraspe.</p>
        </div>

        <div class="cover-feature-box">
            <div class="cover-feature-title">&#9679; Painel de Controle Integrado (.BAT)</div>
            <p class="cover-feature-desc">Acesso com 1 clique a simulados interativos no terminal, exportação de cadernos para Markdown/Obsidian, importação de PDFs de leis/informativos e testes de integridade.</p>
        </div>

        <div class="cover-footer">
            <strong>LexQuest Project &bull; Versão 2.0 Estável</strong><br>
            Compatível com Windows, Linux e macOS &bull; Pipeline spaCy, PyMuPDF e NetworkX
        </div>
    </div>
    """


def create_page_2_principios():
    return """
    <div class="page-header">
        <span class="header-tag">Módulo 1 &bull; Fundamentos do Sistema</span>
    </div>

    <h1 class="h1-title">1. Por que Simbólico e 100% Sem IA?</h1>
    
    <p>
        O <strong>LexQuest</strong> foi projetado a partir de uma constatação técnica crítica: <em>Modelos de Linguagem Generativos (LLMs) são estatísticos e probabilísticos, tornando-os inerentemente sujeitos a alucinações normativas</em>. Em concursos de alta performance (como a Magistratura e o ENAM), a inversão de um único termo ("prescindível" por "imprescindível") ou a invenção de uma exceção que não existe no ordenamento invalida todo o estudo.
    </p>

    <div class="callout-blue">
        <div class="callout-title">&#128737; Os Três Pilares da Arquitetura do LexQuest</div>
        <ul>
            <li><strong>Auditabilidade Absoluta:</strong> Toda questão possui vínculo de rastreabilidade (proveniência) direta com o artigo de lei ou precedente catalogado.</li>
            <li><strong>Precisão Gramatical e Deôntica:</strong> Modais jurídicos (deve, pode, é vedado) sofrem mutações controladas de acordo com as regras de colocação pronominal e sintaxe formal.</li>
            <li><strong>Independência de Conexão ou Custos de API:</strong> O sistema roda 100% local no seu computador, de forma instantânea e ilimitada.</li>
        </ul>
    </div>

    <h2 class="h2-title">2. O Pipeline Simbólico de 5 Etapas</h2>
    <p>O fluxo de processamento do LexQuest segue um pipeline computacional rigoroso:</p>

    <table class="table-box">
        <tr>
            <th>Etapa</th>
            <th>Componente</th>
            <th>Função Principal</th>
        </tr>
        <tr>
            <td><strong>1. Filtro</strong></td>
            <td><code>LexicalFilter</code></td>
            <td>Sanitiza ruídos editoriais ("atenção", notas de aula, propagandas).</td>
        </tr>
        <tr>
            <td><strong>2. Extração</strong></td>
            <td><code>UMTExtractor</code></td>
            <td>Disseca o texto em Unidades Mínimas de Transmissão com metadados.</td>
        </tr>
        <tr>
            <td><strong>3. Sintaxe</strong></td>
            <td><code>DependencyMatcher</code></td>
            <td>Mapeia orações com spaCy: [Sujeito] + [Verbo Deôntico] + [Ressalva].</td>
        </tr>
        <tr>
            <td><strong>4. Mutação</strong></td>
            <td><code>LexicalMutator</code></td>
            <td>Gera distratores invertendo ressalvas, antônimos e regras deônticas.</td>
        </tr>
        <tr>
            <td><strong>5. Grafo</strong></td>
            <td><code>LegalKnowledgeGraph</code></td>
            <td>Clusteriza conceitos conexos via NetworkX para gerar blocos de prova.</td>
        </tr>
    </table>

    <div class="callout-green">
        <div class="callout-title">&#10004; Garantia de Qualidade</div>
        <p style="margin:0;">O sistema inclui 16 testes automatizados que validam desde a próclise gramatical dos distratores até a ausência de letras consecutivas repetidas no gabarito.</p>
    </div>
    """


def create_page_3_bancas():
    return """
    <div class="page-header">
        <span class="header-tag">Módulo 2 &bull; Modelagem das Bancas</span>
    </div>

    <h1 class="h1-title">2. Padrões de Bancas Examinadoras</h1>
    
    <p>
        O LexQuest não gera questões genéricas. Cada banca possui um motor de estilização específico para reproduzir fielmente a experiência da prova real.
    </p>

    <h2 class="h2-title">Padrão FGV / ENAM (Múltipla Escolha Sofisticada)</h2>
    <p>A banca Fundação Getulio Vargas é conhecida por enunciados longos e alternativas curtas. O LexQuest implementa esse padrão com rigor:</p>
    <ul>
        <li><strong>Narrativa Forense em 3 Parágrafos:</strong>
            <ol>
                <li><em>Premissa Fática:</em> Apresentação dos sujeitos em conflito (ex.: coalizão de entes, requerente de tutela de urgência).</li>
                <li><em>Trâmite Processual:</em> O incidente, recurso interposto ou controvérsia instaurada perante o juízo.</li>
                <li><em>Tese Antagônica:</em> A alegação jurídica contrária que exige do candidato o deslinde exato da controvérsia.</li>
            </ol>
        </li>
        <li><strong>Alternativas Enxutas e Simétricas:</strong> O destilador de proposições (<code>_distill_core_rule</code>) elimina o "efeito parágrafo" nas alternativas, mantendo todas com tamanho homogêneo.</li>
        <li><strong>Bloco de 5 Questões com Matriz de Complexidade:</strong> Cada bloco gera exatamente 3 questões difíceis (narrativas forenses), 1 média (proposições romanas I, II e III) e 1 fácil (conceitual/direta).</li>
        <li><strong>Trava de Gabarito:</strong> O sistema impede algoritmicamente que duas questões consecutivas tenham a mesma letra correta (ex.: A seguida de A nunca ocorre).</li>
    </ul>

    <h2 class="h2-title">Padrão Cebraspe (Julgamento de Certo ou Errado)</h2>
    <p>O padrão do Cespe/Cebraspe exige precisão cirúrgica no julgamento da assertiva:</p>
    <ul>
        <li><strong>Mutação Deôntica Pontual:</strong> O sistema identifica verbos modais e inverte a obrigatoriedade (ex.: <em>"é defeso ao magistrado"</em> vs <em>"é facultado ao magistrado"</em>).</li>
        <li><strong>Inversão e Supressão de Ressalvas:</strong> Supressão cirúrgica de condicionais cruciais (como <em>"salvo expressa autorização judicial"</em> ou <em>"desde que motivadamente"</em>).</li>
        <li><strong>Comentário Jurídico Completo:</strong> Toda assertiva errada vem acompanhada da justificativa gramatical e do trecho legal violado.</li>
    </ul>
    """


def create_page_4_como_usar():
    return """
    <div class="page-header">
        <span class="header-tag">Módulo 3 &bull; Guia Prático de Operação</span>
    </div>

    <h1 class="h1-title">3. Como Utilizar o Painel Interativo</h1>
    
    <p>
        Para utilizar o LexQuest, <strong>você não precisa digitar comandos complexos no terminal</strong>. O sistema conta com um inicializador que abre o menu numérico interativo.
    </p>

    <div class="callout-amber">
        <div class="callout-title">&#128640; Inicialização Rápida no Windows</div>
        <p style="margin:0;">
            Basta dar um <strong>duplo clique no arquivo <code>lexquest.bat</code></strong> (ou <code>iniciar.bat</code>) na pasta raiz do projeto, ou executar <code>.\\lexquest.bat</code> no PowerShell.
        </p>
    </div>

    <h2 class="h2-title">Menu Principal de Opções</h2>

    <table class="table-box">
        <tr>
            <th style="width: 15%;">Opção</th>
            <th>Descrição e Como Usar</th>
        </tr>
        <tr>
            <td><span class="key-badge">[ 1 ]</span></td>
            <td>
                <strong>Resolver Questões FGV Interativamente:</strong><br>
                Abre o simulador no próprio terminal. Apresenta o caso em 3 parágrafos, exibe as alternativas de A a E, recebe sua resposta e exibe o gabarito comentado imediatamente.
            </td>
        </tr>
        <tr>
            <td><span class="key-badge">[ 2 ]</span></td>
            <td>
                <strong>Resolver Questões Cebraspe Interativamente:</strong><br>
                Apresenta itens assertivos numerados. Você digita <strong>C</strong> (Certo) ou <strong>E</strong> (Errado) e confere o feedback instantâneo de pontuação.
            </td>
        </tr>
        <tr>
            <td><span class="key-badge">[ 3 ]</span></td>
            <td>
                <strong>Gerar Caderno Completo FGV (.MD):</strong><br>
                Gera um simulado completo formatado em Markdown, com bloco equilibrado de questões, índice, gabarito no final e comentários jurídicos. Perfeito para Obsidian ou impressão.
            </td>
        </tr>
        <tr>
            <td><span class="key-badge">[ 4 ]</span></td>
            <td>
                <strong>Gerar Caderno Completo Cebraspe (.MD):</strong><br>
                Gera uma bateria de itens no formato Certo/Errado com folhas de resposta e espelho de correção.
            </td>
        </tr>
        <tr>
            <td><span class="key-badge">[ 5 ]</span></td>
            <td>
                <strong>Importar PDF Jurídico para Markdown:</strong><br>
                Converte apostilas, Leis Secas ou Informativos do STF/STJ em formato de estudo limpo e estruturado para o LexQuest.
            </td>
        </tr>
        <tr>
            <td><span class="key-badge">[ 6 ]</span></td>
            <td>
                <strong>Executar Bateria de Testes (Pytest):</strong><br>
                Roda a suíte completa de 16 testes unitários para certificar a higidez dos motores sintáticos e geradores.
            </td>
        </tr>
    </table>
    """


def create_page_5_materiais_pdf():
    return """
    <div class="page-header">
        <span class="header-tag">Módulo 4 &bull; Criação de Conteúdo e Importação de PDFs</span>
    </div>

    <h1 class="h1-title">4. Estruturando seus Arquivos de Estudo</h1>
    
    <p>
        O LexQuest se alimenta de notas de estudo escritas em <strong>Markdown</strong>. O formato é simples, limpo e legível. Você pode criar arquivos em <code>exemplos/</code> ou em qualquer pasta do seu computador.
    </p>

    <h2 class="h2-title">Anatomia de uma UMT (Unidade Mínima de Transmissão)</h2>
    <div class="code-block">
# DIREITO CONSTITUCIONAL

<!-- RAMO: Direito Constitucional -->
<!-- TEMA: Controle Concentrado de Constitucionalidade -->
<!-- FONTE: STF - ADPF 973 -->

### ADPF 973 - Estado de Coisas Inconstitucional
O Supremo Tribunal Federal reconheceu expressamente a existência de um 
estado de coisas inconstitucional no sistema prisional brasileiro. 
O Poder Executivo da União deve elaborar plano nacional para superar as 
falhas estruturais no prazo determinado, cabendo aos Estados a elaboração 
de planos locais correlatos.
    </div>

    <h2 class="h2-title">Importando PDFs com 1 Clique (Módulo PyMuPDF)</h2>
    <p>
        Caso você possua julgados ou leis em arquivos PDF (por exemplo, <em>Informativos do STF</em> ou o texto de uma nova lei federal), você pode usar a opção <strong>[5]</strong> do menu ou arrastar o arquivo PDF para o terminal:
    </p>

    <div class="callout-blue">
        <div class="callout-title">&#128196; Passos da Importação de PDF:</div>
        <ol>
            <li>Selecione a opção <strong>[5]</strong> no menu do <code>lexquest.bat</code>;</li>
            <li>Arraste o arquivo PDF da sua pasta para a janela do terminal (o caminho será preenchido automaticamente);</li>
            <li>Defina o nome do arquivo Markdown de saída (ex.: <code>informativo_stf.md</code>);</li>
            <li>O LexQuest extrai os cabeçalhos, títulos de teses e preceitos normativos, gerando um material pronto para resolver e simular!</li>
        </ol>
    </div>

    <h2 class="h2-title">Comandos Avançados no Terminal (Modo CLI)</h2>
    <p>Se preferir disparar execuções automatizadas ou integrar em scripts, utilize o comando nativo:</p>
    <div class="code-block">
# Resolver simulado FGV de material específico:
python -m lexquest.cli resolver --material meu_estudo.md --banca fgv

# Gerar arquivo com 10 questões Cebraspe:
python -m lexquest.cli gerar --material meu_estudo.md --banca cebraspe --qtd 10 --out simulado.md
    </div>
    """


def create_page_6_dicas():
    return """
    <div class="page-header">
        <span class="header-tag">Módulo 5 &bull; Metodologia de Estudo Ativo &amp; FAQ</span>
    </div>

    <h1 class="h1-title">5. Como Maximizar sua Retenção Jurídica</h1>
    
    <p>
        O método do LexQuest baseia-se na teoria da <strong>Recuperação Ativa (Active Recall)</strong> e no <strong>Efeito Testagem</strong>. Ao invés de apenas reler passivamente a lei seca ou o resumo doutrinário, você é confrontado com distratores cirúrgicos criados pelas mesmas regras lógicas das bancas examinadoras.
    </p>

    <div class="callout-green">
        <div class="callout-title">&#128218; Roteiro Recomendado de Sessão de Estudo</div>
        <ol>
            <li><strong>Importação ou Escrita:</strong> Crie seu arquivo <code>.md</code> com a jurisprudência ou artigos da semana.</li>
            <li><strong>Sessão Flash (Opção 2):</strong> Resolva 10 itens Cebraspe no terminal para fixar as ressalvas da lei seca e os verbos deônticos.</li>
            <li><strong>Sessão Forense (Opção 1):</strong> Resolva um bloco FGV para treinar raciocínio sob pressão em casos hipotéticos longos.</li>
            <li><strong>Revisão dos Comentários:</strong> Leia atentamente a fundamentação de cada alternativa incorreta para mapear onde a banca tenta induzir o erro.</li>
        </ol>
    </div>

    <h2 class="h2-title">Perguntas Frequentes (FAQ)</h2>
    
    <p><strong>1. As questões podem se repetir?</strong><br>
    O algoritmo rotaciona os quadros fáticos (Ação Direta, Ação Civil Pública, Fazenda Pública, Tribunal do Júri) e embaralha as alternativas de forma dinâmica a cada execução.</p>

    <p><strong>2. Posso usar com qualquer matéria?</strong><br>
    Sim. O motor sintático e o extrator de UMTs operam sobre a gramática do português formal e são compatíveis com Direito Constitucional, Civil, Processual, Penal, Administrativo, Tributário, etc.</p>

    <p><strong>3. É necessário estar conectado à internet?</strong><br>
    Não. Todo o processamento (spaCy, NetworkX, PyMuPDF e geração de questões) ocorre de forma 100% offline no seu computador.</p>

    <div class="callout-blue" style="margin-top: 25px; text-align: center;">
        <strong style="font-size: 13px; color: #1e3a8a;">Bons estudos e excelentes resultados com o LexQuest v2.0!</strong>
    </div>
    """


def generate_markdown_manual():
    """Gera a versão completa em Markdown do manual."""
    md_content = """# LEXQUEST v2.0 — MANUAL DIDÁTICO E OPERACIONAL
**Engenharia Ontológica e Geração Simbólica de Questões Jurídicas**  
*(Padrão FGV/ENAM e Cebraspe — 100% Determinístico, Rastreável e Sem Inteligência Artificial Generativa)*

---

## 1. Visão Geral e Filosofia do Projeto

### O Problema das IAs Generativas em Concursos Jurídicos
Modelos de linguagem generativos (LLMs) operam com probabilidade estatística de palavras seguintes. Em provas de alta complexidade jurídica (como Magistratura Estadual, Federal, Ministério Público, Defensoria e o Exame Nacional da Magistratura — ENAM), isso acarreta riscos críticos:
1. **Alucinações Normativas:** Invenção de artigos, número de súmulas inexistentes ou fusão indevida de teses.
2. **Inversões Sutis Incorretas:** Troca errônea de termos deônticos ("imprescindível" por "prescindível") sem suporte normativo.
3. **Falta de Rastreabilidade:** Incapacidade de provar qual trecho literal originou a assertiva.

### A Solução LexQuest: Arquitetura 100% Simbólica
O **LexQuest v2.0** adota os fundamentos clássicos da Ciência da Computação e Linguística Computacional:
* **Rule-Based Automatic Question Generation (AQG)**
* **Análise Sintática por Dependência (spaCy com DependencyMatcher)**
* **Teoria dos Grafos Jurídicos (NetworkX)**
* **Processamento de PDFs Oficiais (PyMuPDF)**

---

## 2. Padrões de Bancas Examinadoras Simuladas

### A. Padrão FGV / ENAM (Múltipla Escolha com Casos Forenses)
* **Narrativa Forense em 3 Parágrafos:**
  1. *Premissa Fática:* Qualificação das partes e cenário de litígio concreto.
  2. *Trâmite Processual:* A ação ajuizada, a decisão interlocutória proferida ou o incidente processual suscitado.
  3. *Tese Oposta:* O argumento contrário levantado pela parte adversa.
* **Alternativas Enxutas e Homogêneas:** O destilador de proposições (`_distill_core_rule`) impede alternativas prolixas, garantindo simetria de leitura.
* **Matriz de Dificuldade por Bloco de 5 Questões:** 3 Difíceis (casos forenses), 1 Média (proposições romanas I, II e III) e 1 Fácil (conceitual direta).
* **Trava Algorítmica de Gabarito:** Impede a ocorrência de letras consecutivas idênticas (A após A, B após B, etc.).

### B. Padrão Cebraspe (Itens de Certo ou Errado)
* **Mutações Deônticas Cirúrgicas:** Inversão precisa de permissões, proibições e deveres com respeito às regras de colocação pronominal do português formal.
* **Poda e Inversão de Ressalvas:** Manipulação sistemática de condicionais ("salvo se", "desde que", "salvo prévia autorização judicial").
* **Gabarito com Justificativa Imediata:** Cada erro aponta o dispositivo legal e a regra violada.

---

## 3. Como Usar (Passo a Passo com o Inicializador)

### Inicialização com 1 Clique:
Basta dar um **duplo clique no arquivo `lexquest.bat`** (ou `iniciar.bat`) na raiz da pasta do projeto.

### Opções do Menu:
* **`[1]` Resolver Questões FGV no Terminal:** Sessão interativa para responder casos com alternativas de A a E.
* **`[2]` Resolver Questões Cebraspe no Terminal:** Julgamento de itens Certo ou Errado no terminal com escore imediato.
* **`[3]` Gerar Caderno FGV em Markdown:** Cria um arquivo simulado formatado para abrir no Obsidian, Notion ou imprimir.
* **`[4]` Gerar Caderno Cebraspe em Markdown:** Cria simulado em itens Certo/Errado com gabarito no final.
* **`[5]` Importar PDF Jurídico:** Converte informativos, acórdãos ou leis em PDF para o formato de estudo do LexQuest.
* **`[6]` Executar Testes:** Roda a suíte completa de testes unitários (Pytest) para checagem rápida.
* **`[0]` Sair:** Finaliza a sessão.

---

## 4. Estrutura dos Arquivos de Estudo (.md)

Para alimentar o sistema com novos conteúdos, crie arquivos Markdown seguindo este modelo simples:

```markdown
<!-- RAMO: Direito Constitucional -->
<!-- TEMA: Controle de Constitucionalidade -->
<!-- FONTE: STF - ADI 5.543 -->

### Título da Tese ou Preceito Legal
Texto do artigo da lei ou tese fixada pelo tribunal superior. 
O texto deve ser claro, afirmativo e conter regras de conduta ou deveres jurídicos.
```

---

## 5. Guia de Linha de Comando (CLI Avançado)

Você também pode invocar os módulos diretamente pelo terminal:

```powershell
# Resolver simulado FGV no terminal:
python -m lexquest.cli resolver --material exemplos/adpf_973_exemplo.md --banca fgv

# Resolver simulado Cebraspe de 10 itens:
python -m lexquest.cli resolver --material exemplos/lei_11281_exemplo.md --banca cebraspe --qtd 10

# Gerar arquivo de simulado Markdown:
python -m lexquest.cli gerar --material exemplos/adpf_973_exemplo.md --banca fgv --qtd 5 --out meu_simulado.md

# Importar PDF para Markdown:
python -m lexquest.cli importar-pdf --arquivo documento.pdf --out material_extraido.md
```

---

## 6. Integridade Técnica e Licença
* **Linguagem:** Python 3.12+ (testado em 3.14)
* **Bibliotecas Centrais:** `spaCy` (`pt_core_news_sm`/`pt_core_news_lg`), `PyMuPDF`, `NetworkX`, `Jinja2`, `pytest`.
* **Natureza:** Código aberto, modular e 100% determinístico.
"""
    OUTPUT_MD.write_text(md_content, encoding="utf-8")
    print(f"[OK] Manual em Markdown gerado em: {OUTPUT_MD}")


def generate_pdf_manual():
    """Gera o documento PDF multi-página diagramado com PyMuPDF."""
    doc = pymupdf.open()

    pages_content = [
        create_page_1_cover(),
        create_page_2_principios(),
        create_page_3_bancas(),
        create_page_4_como_usar(),
        create_page_5_materiais_pdf(),
        create_page_6_dicas(),
    ]

    for idx, page_html in enumerate(pages_content, start=1):
        page = doc.new_page(width=595, height=842)  # Formato A4
        
        # Insere conteúdo estilizado
        spare_height, scale = page.insert_htmlbox(PAGE_RECT, page_html, css=CSS_STYLES)

        # Se não for a capa (página 1), insere rodapé elegante com número de página
        if idx > 1:
            footer_rect = pymupdf.Rect(40, 810, 555, 830)
            footer_text = f"LexQuest v2.0 &bull; Manual Didático do Usuário &mdash; Página {idx} de {len(pages_content)}"
            footer_html = f'<div style="font-family:sans-serif; font-size:9px; color:#94a3b8; text-align:center; border-top:1px solid #e2e8f0; padding-top:4px;">{footer_text}</div>'
            page.insert_htmlbox(footer_rect, footer_html)

    doc.save(str(OUTPUT_PDF))
    doc.close()
    print(f"[OK] Manual em PDF gerado com sucesso em: {OUTPUT_PDF}")


if __name__ == "__main__":
    generate_markdown_manual()
    generate_pdf_manual()
