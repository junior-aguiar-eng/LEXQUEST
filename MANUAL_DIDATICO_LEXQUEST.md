# LEXQUEST v2.0 — MANUAL DIDÁTICO E OPERACIONAL
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
