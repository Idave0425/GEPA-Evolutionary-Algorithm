"""
Genetic Algorithm Baseline
Classic GA with mutation, crossover, and selection with validation
"""

import random
from typing import Dict, List, Tuple
from evaluator.affinity_model import MultiDiseaseAffinityEvaluator
from utils.validation import validate_sequence, VALID_AMINO_ACIDS


class GeneticAlgorithmBaseline:
    """Genetic algorithm baseline for antibody optimization"""
    
    def __init__(
        self,
        evaluator: MultiDiseaseAffinityEvaluator,
        population_size: int = 20,
        generations: int = 10,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7
    ):
        """
        Initialize genetic algorithm baseline
        
        Args:
            evaluator: Multi-disease evaluator (has antigens internally)
            population_size: Size of population
            generations: Number of generations
            mutation_rate: Probability of mutation per amino acid
            crossover_rate: Probability of crossover
        """
        self.evaluator = evaluator
        self.antigens = evaluator.antigens
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        # Valid amino acids
        self.amino_acids = list(VALID_AMINO_ACIDS)
    
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
    
    def mutate(self, sequence: str) -> str:
        """
        Apply random mutations with validation
        
        Args:
            sequence: Input sequence
            
        Returns:
            Mutated sequence
        """
        seq_list = list(sequence)
        
        for i in range(len(seq_list)):
            if random.random() < self.mutation_rate:
                current_aa = seq_list[i]
                possible_aa = [aa for aa in self.amino_acids if aa != current_aa]
                if possible_aa:
                    seq_list[i] = random.choice(possible_aa)
        
        mutated = ''.join(seq_list)
        
        # Validate
        is_valid, _ = validate_sequence(mutated, expected_length=len(sequence), strict=False)
        if not is_valid:
            return sequence  # Return original if validation fails
        
        return mutated
    
    def crossover(self, parent1: str, parent2: str) -> Tuple[str, str]:
        """
        Single-point crossover with validation
        
        Args:
            parent1: First parent sequence
            parent2: Second parent sequence
            
        Returns:
            Tuple of two offspring sequences
        """
        if len(parent1) != len(parent2):
            return parent1, parent2
        
        if random.random() > self.crossover_rate:
            return parent1, parent2
        
        # Single-point crossover
        point = random.randint(1, len(parent1) - 1)
        
        offspring1 = parent1[:point] + parent2[point:]
        offspring2 = parent2[:point] + parent1[point:]
        
        # Validate offspring
        is_valid1, _ = validate_sequence(offspring1, expected_length=len(parent1), strict=False)
        is_valid2, _ = validate_sequence(offspring2, expected_length=len(parent2), strict=False)
        
        if not is_valid1:
            offspring1 = parent1
        if not is_valid2:
            offspring2 = parent2
        
        return offspring1, offspring2
    
    def tournament_selection(self, population: List[Tuple[str, float]], k: int = 3) -> str:
        """
        Select individual via tournament selection
        
        Args:
            population: List of (sequence, fitness) tuples
            k: Tournament size
            
        Returns:
            Selected sequence
        """
        tournament = random.sample(population, min(k, len(population)))
        winner = max(tournament, key=lambda x: x[1])
        return winner[0]
    
    def optimize(self, seed_sequence: str) -> Tuple[str, Dict[str, float], List[Dict]]:
        """
        Run genetic algorithm optimization
        
        Args:
            seed_sequence: Starting sequence
            
        Returns:
            Tuple of (best_sequence, best_scores, history)
        """
        print(f"\n{'='*60}")
        print("Running Genetic Algorithm Baseline")
        print(f"{'='*60}")
        print(f"Population: {self.population_size}, Generations: {self.generations}")
        print(f"Mutation rate: {self.mutation_rate}, Crossover rate: {self.crossover_rate}")
        
        # Initialize population with mutated versions of seed
        population = [seed_sequence]
        for _ in range(self.population_size - 1):
            mutant = self.mutate(seed_sequence)
            population.append(mutant)
        
        history = []
        
        # Evolution loop
        for gen in range(self.generations):
            # Evaluate population
            fitness_scores = []
            for seq in population:
                _, agg_score = self.evaluate(seq)
                fitness_scores.append((seq, agg_score))
            
            # Find best individual
            best_seq, best_agg = max(fitness_scores, key=lambda x: x[1])
            best_scores, _ = self.evaluate(best_seq)
            
            print(f"Generation {gen}: Best score = {best_agg:.4f}")
            
            history.append({
                'iteration': gen,  # Use 'iteration' for consistency
                'sequence': best_seq,
                'scores': best_scores,
                'aggregate': best_agg
            })
            
            # Create next generation
            new_population = []
            
            # Elitism: keep best individual
            new_population.append(best_seq)
            
            # Generate offspring
            while len(new_population) < self.population_size:
                # Selection
                parent1 = self.tournament_selection(fitness_scores)
                parent2 = self.tournament_selection(fitness_scores)
                
                # Crossover
                offspring1, offspring2 = self.crossover(parent1, parent2)
                
                # Mutation
                offspring1 = self.mutate(offspring1)
                offspring2 = self.mutate(offspring2)
                
                new_population.append(offspring1)
                if len(new_population) < self.population_size:
                    new_population.append(offspring2)
            
            population = new_population
        
        # Final evaluation
        final_fitness = []
        for seq in population:
            _, agg_score = self.evaluate(seq)
            final_fitness.append((seq, agg_score))
        
        best_seq, best_agg = max(final_fitness, key=lambda x: x[1])
        best_scores, _ = self.evaluate(best_seq)
        
        print(f"\nFinal best score: {best_agg:.4f}")
        
        return best_seq, best_scores, history
