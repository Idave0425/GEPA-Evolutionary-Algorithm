"""
Evaluator module for multi-disease antibody affinity assessment
"""

from .affinity_model import MultiDiseaseAffinityEvaluator
from .feedback import generate_feedback

__all__ = ['MultiDiseaseAffinityEvaluator', 'generate_feedback']

