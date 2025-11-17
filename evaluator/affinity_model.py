"""
Multi-Disease Affinity Evaluator
Scores antibody sequences against multiple disease targets
"""

from typing import Dict, Tuple


class MultiDiseaseAffinityEvaluator:
    """Evaluates antibody binding affinity across multiple diseases"""
    
    def __init__(self, lookup_table: Dict[Tuple[str, str], float]):
        """
        Initialize evaluator with pre-computed binding scores
        
        Args:
            lookup_table: Dictionary mapping (antigen, sequence) to binding_score
        """
        self.lookup_table = lookup_table
        print(f"Initialized evaluator with {len(lookup_table)} known (antigen, sequence) pairs")
    
    def score(self, sequence: str, antigen: str) -> float:
        """
        Get binding score for a sequence against a specific antigen
        
        Args:
            sequence: Antibody amino acid sequence
            antigen: Disease target (e.g., 'HER2', 'VEGF')
            
        Returns:
            Binding score (higher is better). Returns 0.0 if not found.
        """
        key = (antigen, sequence)
        
        # Return score if found, otherwise 0.0
        score = self.lookup_table.get(key, 0.0)
        
        return score
    
    def evaluate_all_antigens(self, sequence: str, antigens: list) -> Dict[str, float]:
        """
        Evaluate a sequence against all specified antigens
        
        Args:
            sequence: Antibody amino acid sequence
            antigens: List of antigen names
            
        Returns:
            Dictionary mapping antigen names to binding scores
        """
        scores = {}
        
        for antigen in antigens:
            scores[antigen] = self.score(sequence, antigen)
        
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

