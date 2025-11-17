"""
Multi-Disease Affinity Evaluator
Scores antibody sequences against multiple disease targets with caching
"""

from typing import Dict, Tuple, List
from functools import lru_cache
from utils.validation import validate_sequence


class MultiDiseaseAffinityEvaluator:
    """Evaluates antibody binding affinity across multiple diseases with memoization"""
    
    def __init__(self, lookup_table: Dict[Tuple[str, str], float], antigens: List[str]):
        """
        Initialize evaluator with pre-computed binding scores and target antigens
        
        Args:
            lookup_table: Dictionary mapping (antigen, sequence) to binding_score
            antigens: List of target antigen names
        """
        self.lookup_table = lookup_table
        self.antigens = antigens
        
        # Memoization cache for evaluated sequences
        self._cache: Dict[str, Dict[str, float]] = {}
        
        print(f"Initialized evaluator with {len(lookup_table)} known (antigen, sequence) pairs")
        print(f"Target antigens: {', '.join(antigens)}")
    
    def score(self, sequence: str, antigen: str) -> float:
        """
        Get binding score for a sequence against a specific antigen
        
        Args:
            sequence: Antibody amino acid sequence
            antigen: Disease target (e.g., 'HER2', 'VEGF')
            
        Returns:
            Binding score (higher is better). Returns 0.0 if not found.
        """
        # Validate sequence before scoring
        is_valid, error_msg = validate_sequence(sequence, strict=False)
        if not is_valid:
            print(f"⚠️  WARNING: Invalid sequence for scoring: {error_msg}")
            return 0.0
        
        key = (antigen, sequence)
        score = self.lookup_table.get(key, 0.0)
        
        return score
    
    def evaluate_all_antigens(self, sequence: str) -> Dict[str, float]:
        """
        Evaluate a sequence against all target antigens (with caching)
        
        Args:
            sequence: Antibody amino acid sequence
            
        Returns:
            Dictionary mapping antigen names to binding scores
        """
        # Check cache first
        if sequence in self._cache:
            return self._cache[sequence].copy()
        
        # Validate sequence
        is_valid, error_msg = validate_sequence(sequence, strict=False)
        if not is_valid:
            print(f"⚠️  WARNING: Cannot evaluate invalid sequence: {error_msg}")
            # Return zeros for all antigens
            return {antigen: 0.0 for antigen in self.antigens}
        
        # Compute scores
        scores = {}
        for antigen in self.antigens:
            scores[antigen] = self.score(sequence, antigen)
        
        # Cache result
        self._cache[sequence] = scores.copy()
        
        return scores
    
    def aggregate_score(self, scores: Dict[str, float]) -> float:
        """
        Compute aggregate score across all diseases
        
        Args:
            scores: Dictionary of per-disease scores
            
        Returns:
            Mean score across all diseases
        """
        if not scores:
            return 0.0
        
        return sum(scores.values()) / len(scores)
    
    def clear_cache(self):
        """Clear the memoization cache"""
        self._cache.clear()
    
    def get_cache_size(self) -> int:
        """Get number of cached evaluations"""
        return len(self._cache)
