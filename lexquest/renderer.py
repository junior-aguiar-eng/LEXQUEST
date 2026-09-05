from typing import List
from .models import Question, Banca, QuestionFormat


class ExamRenderer:
    """
    Renderizador de cadernos de prova e simulados em Markdown.
    Formata as questões com o cabeçalho técnico de UMTs e a folha de gabarito comentado ao final.
    """

    @classmethod
    def render_batch_markdown(
        cls,
        questions: List[Question],
        title: str = "Simulado de Questões Inéditas"
    ) -> str:
        """Gera o arquivo Markdown completo com caderno de questões + gabarito ao final."""
        lines = [
            f"# **{title.upper()}**",
            "",
            "> **Caderno de Prova Determinístico (LexQuest)**  ",
            f"> **Total de Itens:** {len(questions)} | **Banca Alvo:** {questions[0].banca.value if questions else 'N/A'}",
            "",
            "---",
            "",
            "## **CADERNO DE QUESTÕES**",
            ""
        ]

        # 1. Seção de Questões
        for q in questions:
            lines.append(f"### **QUESTÃO {q.id:02d}**")
            lines.append(f"`{q.header}`")
            lines.append("")
            lines.append(q.stem)
            lines.append("")

            if q.banca == Banca.CEBRASPE:
                lines.append("(  ) CERTO    (  ) ERRADO")
            else:
                for alt in q.alternatives:
                    lines.append(f"**({alt.letter})** {alt.text}")

            lines.append("")
            lines.append("---")
            lines.append("")

        # 2. Seção de Gabarito e Comentários Aprofundados
        lines.append("## **FOLHA DE GABARITOS E COMENTÁRIOS DETALHADOS**")
        lines.append("")

        # Tabela resumo rápida
        lines.append("| Questão | Gabarito | Formato | Dificuldade | UMT / Fonte |")
        lines.append("| :---: | :---: | :--- | :---: | :--- |")
        for q in questions:
            umt_names = ", ".join(u.title[:35] + ("..." if len(u.title) > 35 else "") for u in q.source_umts)
            lines.append(
                f"| {q.id:02d} | **{q.correct_letter}** | {q.format.value} | {q.difficulty.value} | {umt_names} |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")

        # Comentário minucioso questão a questão
        for q in questions:
            lines.append(f"### **COMENTÁRIO DA QUESTÃO {q.id:02d} — GABARITO OFICIAL: {q.correct_letter}**")
            lines.append(f"* **Ramo / Tema:** {q.topic}")
            lines.append(f"* **Nível:** {q.difficulty.value} | **Formato:** {q.format.value}")
            lines.append(f"* **Fundamentação:** {', '.join(u.title for u in q.source_umts)}")
            lines.append("")
            lines.append("#### **Análise das Alternativas e Distratores:**")

            for alt in q.alternatives:
                status = "✅ **CORRETO**" if alt.is_correct else "❌ **INCORRETO**"
                lines.append(f"- **({alt.letter})** {status}: {alt.explanation}")

            lines.append("")
            lines.append("#### **Diagnóstico Doutrinário e Jurisprudencial:**")
            lines.append(q.commentary)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)
