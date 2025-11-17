"""
Random Search Baseline
Simple baseline that randomly mutates sequences with validation
"""

import random
from typing import Dict, List, Tuple
from evaluator.affinity_model import MultiDiseaseAffinityEvaluator
from utils.validation import validate_sequence, VALID_AMINO_ACIDS


class RandomSearchBaseline:
    """Random search baseline for antibody optimization"""
    
    def __init__(
        self,
        evaluator: MultiDiseaseAffinityEvaluator,
        iterations: int = 10,
        mutations_per_iter: int = 3,
        sample_from_best: bool = True
    ):
        """
        Initialize random search baseline
        
        Args:
            evaluator: Multi-disease evaluator (has antigens internally)
            iterations: Number of search iterations
            mutations_per_iter: Number of random mutations per iteration
            sample_from_best: If True, mutate from best; if False, mutate from seed
        """
        self.evaluator = evaluator
        self.antigens = evaluator.antigens
        self.iterations = iterations
        self.mutations_per_iter = mutations_per_iter
        self.sample_from_best = sample_from_best
        
        # Valid amino acids
        self.amino_acids = list(VALID_AMINO_ACIDS)
    
    def mutate_random(self, sequence: str, num_mutations: int = 1) -> str:
        """
        Randomly mutate a sequence with validation
        
        Args:
            sequence: Input sequence
            num_mutations: Number of positions to mutate
            
        Returns:
            Mutated sequence
        """
        # Validate input
        is_valid, error_msg = validate_sequence(sequence, strict=False)
        if not is_valid:
            print(f"⚠️  WARNING: Invalid input for mutation: {error_msg}")
            return sequence
        
        seq_list = list(sequence)
        positions = random.sample(range(len(sequence)), min(num_mutations, len(sequence)))
        
        for pos in positions:
            # Choose a different amino acid
            current_aa = seq_list[pos]
            possible_aa = [aa for aa in self.amino_acids if aa != current_aa]
            seq_list[pos] = random.choice(possible_aa)
        
        return ''.join(seq_list)
    
    def evaluate(self, sequence: str) -> Tuple[Dict[str, float], float]:
        """
        Evaluate sequence across all antigens
        
        Args:
            sequence: Antibody sequence
            
        Returns:
            Tuple of (scores_dict, aggregate_score)
        """
        scores = self.evaluator.evaluate_all_antigens(sequence)
        agg_score = self.evaluator.aggregate_score(scores)
        return scores, agg_score
    
    def optimize(self, seed_sequence: str) -> Tuple[str, Dict[str, float], List[Dict]]:
        """
        Run random search optimization
        
        Args:
            seed_sequence: Starting sequence
            
        Returns:
            Tuple of (best_sequence, best_scores, history)
        """
        print(f"\n{'='*60}")
        print("Running Random Search Baseline")
        print(f"{'='*60}")
        print(f"Iterations: {self.iterations}, Mutations per iter: {self.mutations_per_iter}")
        print(f"Strategy: {'sample from best' if self.sample_from_best else 'sample from seed'}")
        
        # Evaluate seed
        best_sequence = seed_sequence
        best_scores, best_agg = self.evaluate(seed_sequence)
        
        print(f"Seed aggregate score: {best_agg:.4f}")
        
        history = [{
            'iteration': 0,
            'sequence': seed_sequence,
            'scores': best_scores,
            'aggregate': best_agg
        }]
        
        # Random search iterations
        for i in range(1, self.iterations + 1):
            # Generate random mutation
            if self.sample_from_best:
                base_seq = best_sequence
            else:
                base_seq = seed_sequence
            
            candidate = self.mutate_random(base_seq, self.mutations_per_iter)
            candidate_scores, candidate_agg = self.evaluate(candidate)
            
            # Keep if better
            if candidate_agg > best_agg:
                improvement = candidate_agg - best_agg
                best_sequence = candidate
                best_scores = candidate_scores
                best_agg = candidate_agg
                print(f"Iteration {i}: New best! Score: {best_agg:.4f} (+{improvement:.4f})")
            else:
                print(f"Iteration {i}: No improvement (score: {candidate_agg:.4f})")
            
            history.append({
                'iteration': i,
                'sequence': best_sequence,
                'scores': best_scores,
                'aggregate': best_agg
            })
        
        print(f"\nFinal aggregate score: {best_agg:.4f}")
        
        return best_sequence, best_scores, history
