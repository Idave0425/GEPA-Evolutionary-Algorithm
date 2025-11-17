"""
Baseline optimization methods for comparison with GEPA
"""

from .random_search import RandomSearchBaseline
from .single_mutation import SingleMutationBaseline
from .genetic_algorithm import GeneticAlgorithmBaseline

__all__ = [
    'RandomSearchBaseline',
    'SingleMutationBaseline',
    'GeneticAlgorithmBaseline'
]

