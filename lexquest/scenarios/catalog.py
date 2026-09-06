from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import random
from ..models import UMT, UMTType


@dataclass
class ScenarioFrame:
    id: str
    area: str
    title: str
    stem_template: str
    prompt: str
    keywords: List[str]
    allowed_umt_types: List[UMTType]


class ScenarioCatalog:
    """
    Catálogo Dinâmico de Cenários Forenses Encorpados (Padrão FGV/ENAM).
    Proporciona narrativas fáticas densas (3 parágrafos articulados) com atores,
    conflito judicial circunstanciado e teses antagônicas, com rotação anti-repetição.
    """

    FRAMES: List[ScenarioFrame] = [
        # --- BLOCO 1: CONTROLE CONCENTRADO E AÇÕES ESTRUTURAIS PERANTE O STF ---
        ScenarioFrame(
            id="const_partido_congresso",
            area="Direito Constitucional",
            title="Ação Estrutural perante o STF promovida por Partido Político",
            stem_template=(
                "No bojo de ação de controle abstrato de constitucionalidade ajuizada por partido político com "
                "representação no Congresso Nacional perante o Supremo Tribunal Federal, sustentou-se a ocorrência "
                "de quadro de grave violação sistemática a direitos fundamentais de grupos historicamente vulnerabilizados, "
                "postulando-se a intervenção judicial estruturante sobre a formulação e execução de políticas públicas pelo Poder Executivo.\n\n"
                "A Advocacia-Geral da União defendeu a higidez da atuação estatal, destacando a existência de programas "
                "afirmativos em andamento e invocando a cláusula da reserva do possível para rechaçar a ingerência jurisdicional. "
                "Em réplica, os proponentes insistiram na caracterização de estado de coisas inconstitucional e na fixação de prazos peremptórios.\n\n"
                "Submetida a matéria à deliberação definitiva do Plenário da Corte Constitucional,"
            ),
            prompt="com esteio na jurisprudência vinculante do Supremo Tribunal Federal, assinale a afirmativa correta:",
            keywords=["racismo", "adpf", "estado de coisas", "políticas públicas", "eci", "fundamental"],
            allowed_umt_types=[UMTType.JURISPRUDENCIA, UMTType.DOUTRINA]
        ),
        ScenarioFrame(
            id="const_pgr_audiencia",
            area="Direito Constitucional",
            title="Procedimento de Fiscalização Constitucional promovido pela PGR",
            stem_template=(
                "A Procuradoria-Geral da República deflagrou processo de fiscalização constitucional perante a Suprema Corte, "
                "visando a compelir os poderes públicos à adoção de providências concretas para debelar falhas estruturais em "
                "setores sensíveis da Administração. Durante a instrução processual e após a realização de audiências públicas "
                "com a participação de acadêmicos e entidades da sociedade civil, descortinou-se a complexidade do cenário institucional.\n\n"
                "Ao proferir voto de mérito, o Ministro Relator enfrentou o dilema entre a constatação do problema social endêmico "
                "e os requisitos dogmáticos restritos para a decretação de falência generalizada do Estado (omissão absoluta).\n\n"
                "Nesse contexto, considerando as balizas jurisprudenciais vinculantes do Supremo Tribunal Federal,"
            ),
            prompt="assinale a opção que indica a conclusão jurídica correta:",
            keywords=["racismo", "adpf", "eci", "estrutural", "plano"],
            allowed_umt_types=[UMTType.JURISPRUDENCIA, UMTType.DOUTRINA]
        ),
        ScenarioFrame(
            id="const_dpu_protocolos",
            area="Direito Constitucional",
            title="Ação Civil de Providências Estruturais e Protocolos pelo Sistema de Justiça",
            stem_template=(
                "A Defensoria Pública da União, no exercício de suas prerrogativas constitucionais de salvaguarda de direitos "
                "fundamentais, ingressou com demanda perante o tribunal competente postulando a fixação compulsória de protocolos "
                "de abordagem institucional e atendimento prioritário para eliminar condutas discriminatórias e abordagens "
                "baseadas em perfilamento por agentes estatais.\n\n"
                "O Poder Público opôs contestação sustentando que a definição de diretrizes operacionais de órgãos de segurança "
                "e fiscalização insere-se no núcleo de discricionariedade do Poder Executivo, sendo imune à modulação impositiva pelo Judiciário.\n\n"
                "Diante da controvérsia instaurada e das diretrizes do Supremo Tribunal Federal,"
            ),
            prompt="é correto afirmar que a determinação judicial de protocolos e planos estruturais:",
            keywords=["protocolos", "atendimento", "policiais", "discriminação", "perfil racial", "capacitação"],
            allowed_umt_types=[UMTType.JURISPRUDENCIA, UMTType.DOUTRINA]
        ),

        # --- BLOCO 2: LEGISLAÇÃO, COMPETÊNCIAS E FAZENDA PÚBLICA ---
        ScenarioFrame(
            id="adm_fazenda_cobranca",
            area="Direito Financeiro e Administrativo",
            title="Recuperação de Créditos Públicos e Seguro de Exportação",
            stem_template=(
                "No âmbito do Ministério da Fazenda, instaurou-se procedimento administrativo para deflagração de medidas "
                "de recuperação de créditos decorrentes de garantias de seguro honradas com recursos do Fundo de Garantia "
                "à Exportação (FGE) em face de operações inadimplidas de seguro de crédito à exportação.\n\n"
                "A sociedade devedora ingressou em juízo alegando a invalidade da cobrança realizada por intermédio de mandatário "
                "designado pela Pasta da Fazenda, arguindo que a cobrança judicial e extrajudicial de haveres públicos constituiria "
                "atividade privativa de procuradores concursados, indelegável por ato infraconstitucional.\n\n"
                "Ao analisar a impugnação deduzida à luz da disciplina legal e dos parâmetros normativos aplicáveis,"
            ),
            prompt="o magistrado da causa deverá assentar que:",
            keywords=["exportação", "crédito", "fge", "união", "garantia", "fazenda", "mandatário", "cobrança"],
            allowed_umt_types=[UMTType.LEI_SECA]
        ),
        ScenarioFrame(
            id="adm_gestao_instituicao",
            area="Direito Administrativo e Econômico",
            title="Operacionalização de Fundos Garantidores e Mandato Especial",
            stem_template=(
                "A União celebrou ajuste com instituição financeira autorizada a operar no mercado de crédito com a finalidade "
                "de encarregar-lhe da gestão de operações de cobertura de riscos comerciais e políticos, inclusive a adoção de "
                "medidas de acompanhamento das garantias e de recuperação de haveres sinistrados no exterior.\n\n"
                "O Tribunal de Contas da União promoveu auditoria de conformidade para averiguar se a União detinha competência "
                "para transferir tais encargos a mandatário financeiro sem a necessidade de lei complementar específica.\n\n"
                "Considerando o regime legal positivado e a hermenêutica aplicável,"
            ),
            prompt="assinale a opção que expressa o enquadramento jurídico adequado:",
            keywords=["contratar", "instituição", "riscos", "habilitada", "mandatário", "banco do brasil"],
            allowed_umt_types=[UMTType.LEI_SECA]
        ),

        # --- BLOCO 3: PROCESSO PENAL E DIREITO SANCIONADOR ---
        ScenarioFrame(
            id="penal_caso_juri_execucao",
            area="Direito Penal e Processual Penal",
            title="Sessão Plenária do Júri e Execução da Sentença",
            stem_template=(
                "Caio foi denunciado pelo Ministério Público e pronunciado pela prática de crime doloso contra a vida. "
                "Submetido a julgamento perante o Tribunal do Júri, o Conselho de Sentença respondeu afirmativamente aos quesitos "
                "de autoria e materialidade, rejeitando a tese absolutória da legítima defesa.\n\n"
                "O Juiz Presidente proferiu sentença condenatória fixando a reprimenda privativa de liberdade em regime inicial "
                "fechado e determinou a expedição imediata do mandado de prisão. A defesa técnica de Caio interpôs apelação "
                "e impetrou habeas corpus perante o Tribunal de Justiça, sustentando violação à presunção de inocência.\n\n"
                "Submetido o pleito ao colegiado recursal à luz da jurisprudência firmada pelo STF,"
            ),
            prompt="é juridicamente correto afirmar que a ordem de prisão imediata:",
            keywords=["júri", "soberania", "vereditos", "crime", "execução", "caio"],
            allowed_umt_types=[UMTType.JURISPRUDENCIA, UMTType.LEI_SECA]
        ),
        ScenarioFrame(
            id="penal_nulidade_provas",
            area="Direito Processual Penal",
            title="Incidente de Nulidade e Teoria Geral dos Vícios Processuais",
            stem_template=(
                "Durante a instrução criminal de ação penal instaurada para apurar delitos contra a administração pública, "
                "a defesa técnica do réu arguiu incidente de nulidade absoluta dos elementos probatórios acostados aos autos, "
                "afirmando que a quebra na cadeia de custódia e a preterição de formalidades procedimentais operariam "
                "invalidade automática e contaminação de toda a persecução, independentemente de demonstração de prejuízo.\n\n"
                "O Ministério Público pugnou pelo indeferimento do pedido, salientando que a teoria das nulidades no processo "
                "penal pátrio exige a constatação inequívoca de prejuízo efetivo à ampla defesa para ensejar qualquer anulação.\n\n"
                "Em consonância com a dogmática jurídica e os precedentes vinculantes dos Tribunais Superiores,"
            ),
            prompt="o juízo competente deve fundamentar que o vício alegado:",
            keywords=["nulidade", "custódia", "prejuízo", "processo", "vício"],
            allowed_umt_types=[UMTType.JURISPRUDENCIA, UMTType.DOUTRINA]
        ),
    ]

    def __init__(self):
        self._used_frame_ids: List[str] = []

    def get_diverse_frame_for_umt(self, umt: UMT) -> ScenarioFrame:
        """
        Seleciona uma moldura narrativa fática rica que NÃO tenha sido usada recentemente,
        garantindo diversidade absoluta de inícios de frases e enredos no bloco.
        """
        umt_content_lower = (umt.title + " " + umt.content).lower()

        # Filtra molduras compatíveis
        candidates: List[ScenarioFrame] = []
        for frame in self.FRAMES:
            matches = sum(1 for kw in frame.keywords if kw in umt_content_lower)
            if matches > 0:
                candidates.append(frame)

        if not candidates:
            candidates = list(self.FRAMES)

        # Prioriza candidatos que ainda não foram usados nesta sessão/bloco
        unused_candidates = [c for c in candidates if c.id not in self._used_frame_ids]
        if not unused_candidates:
            # Se todos já foram usados, reseta o histórico
            self._used_frame_ids.clear()
            unused_candidates = candidates

        selected = random.choice(unused_candidates)
        self._used_frame_ids.append(selected.id)
        return selected
