"""
Engine de mutação léxica, gestão de blocos e construção de distratores do LexQuest.
"""

from .mutator import LexicalMutator, MutationResult
from .distractor_builder import DistractorBuilder
from .block_manager import BlockManager

__all__ = ["LexicalMutator", "MutationResult", "DistractorBuilder", "BlockManager"]
