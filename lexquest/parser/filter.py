import re


class EditorialFilter:
    """
    Filtro para expurgo de ruído editorial:
    Capas, sumários, notas de agradecimento, índices e bloco de questões pretéritas.
    """

    NOISE_PATTERNS = [
        r"^#+\s*(sum[aá]rio|[ií]ndice|apresenta[cç][aã]o|sobre o autor|equipe|bibliografia).*",
        r"^#+\s*(quest[oõ]es|quest[oõ]es comentadas|exerc[ií]cios|gabarito).*",
    ]

    CONTENT_HEADING = r"^#+\s+[A-Z0-9].*"

    @classmethod
    def clean(cls, text: str) -> str:
        lines = text.splitlines()
        clean_lines = []
        skip_noise_block = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if not skip_noise_block:
                    clean_lines.append(line)
                continue

            # Verifica se atingiu uma seção de ruído editorial
            is_noise_header = any(
                re.match(pattern, stripped, flags=re.IGNORECASE)
                for pattern in cls.NOISE_PATTERNS
            )

            if is_noise_header:
                skip_noise_block = True
                continue

            # Se estiver dentro de bloco de ruído, verifica se encontrou um cabeçalho de conteúdo real
            if skip_noise_block:
                if stripped.startswith("#"):
                    # Checa se não é outro ruído
                    if not any(re.match(p, stripped, flags=re.IGNORECASE) for p in cls.NOISE_PATTERNS):
                        skip_noise_block = False
                        clean_lines.append(line)
                continue

            clean_lines.append(line)

        return "\n".join(clean_lines).strip()


# Alias para retrocompatibilidade
LexicalFilter = EditorialFilter
