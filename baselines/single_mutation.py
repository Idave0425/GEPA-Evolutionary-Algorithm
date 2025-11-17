"""
Single Mutation Baseline
Systematically tries single mutations and keeps the best (hill climbing)
"""

from typing import Dict, List, Tuple
from evaluator.affinity_model import MultiDiseaseAffinityEvaluator
from utils.validation import validate_sequence, VALID_AMINO_ACIDS


class SingleMutationBaseline:
    """Single mutation hill climbing baseline with consistent interface"""
    
    def __init__(
        self,
        evaluator: MultiDiseaseAffinityEvaluator,
        iterations: int = 10,
        sample_size: int = None
    ):
        """
        Initialize single mutation baseline
        
        Args:
            evaluator: Multi-disease evaluator (has antigens internally)
            iterations: Number of optimization iterations
            sample_size: If set, sample this many mutations instead of trying all
        """
        self.evaluator = evaluator
        self.antigens = evaluator.antigens
        self.iterations = iterations
        self.sample_size = sample_size
        
        # Valid amino acids
        self.amino_acids = list(VALID_AMINO_ACIDS)
    
    def generate_single_mutations(self, sequence: str) -> List[str]:
        """
        Generate all possible single-point mutations
        
        Args:
            sequence: Input sequence
            
        Returns:
            List of mutated sequences
        """
        mutations = []
        
        for pos in range(len(sequence)):
            current_aa = sequence[pos]
            
            for new_aa in self.amino_acids:
                if new_aa != current_aa:
                    # Create mutated sequence
                    mutant = sequence[:pos] + new_aa + sequence[pos+1:]
                    
                    # Validate
                    is_valid, _ = validate_sequence(mutant, expected_length=len(sequence), strict=False)
                    if is_valid:
                        mutations.append(mutant)
        
        return mutations
    
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
        Run single mutation hill climbing
        
        Args:
            seed_sequence: Starting sequence
            
        Returns:
            Tuple of (best_sequence, best_scores, history)
        """
        print(f"\n{'='*60}")
        print("Running Single Mutation Baseline")
        print(f"{'='*60}")
        print(f"Iterations: {self.iterations}")
        if self.sample_size:
            print(f"Sampling: {self.sample_size} mutations per iteration")
        
        # Evaluate seed
        current_sequence = seed_sequence
        current_scores, current_agg = self.evaluate(seed_sequence)
        
        print(f"Seed aggregate score: {current_agg:.4f}")
        
        history = [{
            'iteration': 0,
            'sequence': seed_sequence,
            'scores': current_scores,
            'aggregate': current_agg
        }]
        
        # Hill climbing iterations
        for i in range(1, self.iterations + 1):
            print(f"\nIteration {i}: Testing single mutations...")
            
            # Generate all single mutations
            mutations = self.generate_single_mutations(current_sequence)
            
            # Sample if requested
            if self.sample_size and len(mutations) > self.sample_size:
                import random
                mutations = random.sample(mutations, self.sample_size)
                print(f"  Sampled {len(mutations)} mutations")
            else:
                print(f"  Generated {len(mutations)} single-point mutations")
            
            # Find best mutation
            best_mutant = current_sequence
            best_mutant_scores = current_scores
            best_mutant_agg = current_agg
            
            for mutant in mutations:
                mutant_scores, mutant_agg = self.evaluate(mutant)
                
                if mutant_agg > best_mutant_agg:
                    best_mutant = mutant
                    best_mutant_scores = mutant_scores
                    best_mutant_agg = mutant_agg
            
            # Update if improvement found
            if best_mutant_agg > current_agg:
                improvement = best_mutant_agg - current_agg
                current_sequence = best_mutant
                current_scores = best_mutant_scores
                current_agg = best_mutant_agg
                print(f"  ✓ Improvement found! New score: {current_agg:.4f} (+{improvement:.4f})")
            else:
                print(f"  ✗ No improvement found. Stuck at: {current_agg:.4f}")
            
            history.append({
                'iteration': i,
                'sequence': current_sequence,
                'scores': current_scores,
                'aggregate': current_agg
            })
        
        print(f"\nFinal aggregate score: {current_agg:.4f}")
        
        return current_sequence, current_scores, history
