import re
from typing import List, Dict, Any, Set, Tuple, Optional
import networkx as nx
from ..models import UMT, Complexity


class LegalKnowledgeGraph:
    """
    Grafo de Conhecimento Jurídico (Ontologia Simbólica com NetworkX).
    Conecta UMTs, Entidades Institucionais, Teses e Conceitos Jurídicos
    por arestas tipadas (ex: RECONHECE, AFASTA, COMPETENCIA, FISCALIZA, PRAZO).
    """

    KNOWN_ORGANS = [
        "Supremo Tribunal Federal", "STF",
        "Superior Tribunal de Justiça", "STJ",
        "Conselho Nacional de Justiça", "CNJ",
        "Ministério da Fazenda", "Ministério Público",
        "Defensoria Pública", "Presidente da República",
        "Banco do Brasil", "União"
    ]

    KNOWN_CONCEPTS = [
        "Racismo Estrutural",
        "Estado de Coisas Inconstitucional",
        "Plano Nacional",
        "Seguro de Crédito à Exportação",
        "Fundo de Garantia à Exportação",
        "Cobrança Judicial e Extrajudicial",
        "Cadeia de Custódia",
        "Tribunal do Júri",
        "Nulidade Relativa",
        "Nulidade Absoluta"
    ]

    RELATION_PATTERNS = [
        (r"\breconhece-se a existência de\b", "RECONHECE"),
        (r"\bafasta-se\b", "AFASTA"),
        (r"\brejeitou o pedido de declaração\b", "REJEITA"),
        (r"\bdeterminou a elaboração\b", "DETERMINA"),
        (r"\bfiscalizado pelo\b", "FISCALIZADO_POR"),
        (r"\bcompetências previstas.*?exercidas por intermédio\b", "COMPETENCIA_DE"),
        (r"\bcobrará judicial e extrajudicialmente.*?por intermédio\b", "EXECUTA_COBRANCA"),
        (r"\bprazo de (\d+)\s+(meses|dias)\b", "FIXA_PRAZO"),
    ]

    OPPOSITE_RELATIONS = {
        "RECONHECE": "AFASTA",
        "AFASTA": "RECONHECE",
        "REJEITA": "ACOLHE",
        "ACOLHE": "REJEITA",
    }

    CONTRASTING_ORGANS = {
        "STF": "STJ",
        "Supremo Tribunal Federal": "Superior Tribunal de Justiça",
        "STJ": "STF",
        "Superior Tribunal de Justiça": "Supremo Tribunal Federal",
        "Ministério da Fazenda": "Presidente da República",
        "Conselho Nacional de Justiça": "Tribunal de Contas da União",
        "CNJ": "TCU",
    }

    def __init__(self):
        self.graph: nx.DiGraph = nx.DiGraph()
        self.umt_map: Dict[int, UMT] = {}

    def build_from_umts(self, umts: List[UMT]):
        """Popula o grafo relacionando cada UMT com suas entidades e conceitos."""
        self.graph.clear()
        self.umt_map.clear()

        for umt in umts:
            self.umt_map[umt.id] = umt
            umt_node = f"UMT_{umt.id}"
            self.graph.add_node(
                umt_node,
                type="UMT",
                title=umt.title,
                complexity=umt.complexity.value,
                umt_id=umt.id
            )

            text_full = f"{umt.title} {umt.content}"

            # 1. Conecta Órgãos e Entidades
            for organ in self.KNOWN_ORGANS:
                if re.search(r"\b" + re.escape(organ) + r"\b", text_full, flags=re.IGNORECASE):
                    organ_node = f"ORGAN_{organ.upper().replace(' ', '_')}"
                    if not self.graph.has_node(organ_node):
                        self.graph.add_node(organ_node, type="ORGAN", name=organ)
                    self.graph.add_edge(umt_node, organ_node, relation="MENCIONA_ORGAO")

            # 2. Conecta Conceitos Dogmáticos
            for concept in self.KNOWN_CONCEPTS:
                if re.search(r"\b" + re.escape(concept) + r"\b", text_full, flags=re.IGNORECASE):
                    concept_node = f"CONCEPT_{concept.upper().replace(' ', '_')}"
                    if not self.graph.has_node(concept_node):
                        self.graph.add_node(concept_node, type="CONCEPT", name=concept)
                    
                    # Detecta a relação deôntica específica com esse conceito
                    matched_relation = "ABRANGENCIA"
                    for pattern, rel_name in self.RELATION_PATTERNS:
                        if re.search(pattern, text_full, flags=re.IGNORECASE):
                            matched_relation = rel_name
                            break

                    self.graph.add_edge(umt_node, concept_node, relation=matched_relation)

    def get_correlated_umts(self, base_umt: UMT, max_count: int = 2) -> List[UMT]:
        """
        Localiza UMTs que compartilham o mesmo cluster temático via caminhos no grafo
        (2-hop search: UMT_A -> Concept/Organ -> UMT_B).
        Garante que proposições em questões I, II, III tenham conexão dogmática real.
        """
        base_node = f"UMT_{base_umt.id}"
        if not self.graph.has_node(base_node):
            return []

        correlated_ids: Set[int] = set()

        # Encontra vizinhos diretos (conceitos/órgãos vinculados à UMT base)
        neighbors = list(self.graph.successors(base_node)) + list(self.graph.predecessors(base_node))

        for n in neighbors:
            # Encontra outras UMTs conectadas a esses mesmos nós
            other_umts = [
                pred for pred in self.graph.predecessors(n)
                if pred.startswith("UMT_") and pred != base_node
            ]
            for o in other_umts:
                u_id = self.graph.nodes[o].get("umt_id")
                if u_id and u_id in self.umt_map:
                    correlated_ids.add(u_id)

        result = [self.umt_map[uid] for uid in correlated_ids if uid != base_umt.id]
        return result[:max_count]

    def get_ontology_distractor_hints(self, umt: UMT) -> List[Dict[str, str]]:
        """
        Gera sugestões de distratores baseados na inversão das arestas do grafo ontológico.
        Ex: se UMT -> AFASTA -> ECI, sugere trocar por UMT -> RECONHECE -> ECI.
        Ex: se UMT -> FISCALIZADO_POR -> CNJ, sugere trocar por TCU.
        """
        umt_node = f"UMT_{umt.id}"
        if not self.graph.has_node(umt_node):
            return []

        hints: List[Dict[str, str]] = []

        for _, target, data in self.graph.out_edges(umt_node, data=True):
            rel = data.get("relation")
            target_data = self.graph.nodes[target]

            # Inversão de relação opositiva
            if rel in self.OPPOSITE_RELATIONS:
                hints.append({
                    "type": "RELATION_INVERSION",
                    "original_relation": rel,
                    "mutated_relation": self.OPPOSITE_RELATIONS[rel],
                    "target_name": target_data.get("name", target)
                })

            # Inversão de órgão
            if target_data.get("type") == "ORGAN":
                organ_name = target_data.get("name", "")
                if organ_name in self.CONTRASTING_ORGANS:
                    hints.append({
                        "type": "ORGAN_SWAP",
                        "original_organ": organ_name,
                        "swapped_organ": self.CONTRASTING_ORGANS[organ_name]
                    })

        return hints

    def summary(self) -> Dict[str, Any]:
        """Estatísticas do Grafo de Conhecimento."""
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "umt_nodes": sum(1 for _, d in self.graph.nodes(data=True) if d.get("type") == "UMT"),
            "concept_nodes": sum(1 for _, d in self.graph.nodes(data=True) if d.get("type") == "CONCEPT"),
            "organ_nodes": sum(1 for _, d in self.graph.nodes(data=True) if d.get("type") == "ORGAN"),
            "connected_components": nx.number_weakly_connected_components(self.graph) if self.graph.is_directed() else 0
        }
