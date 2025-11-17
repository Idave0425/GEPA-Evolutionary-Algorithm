"""
Main runner for GEPA Multi-Disease Antibody Optimization
Production-ready with error handling and clean output
"""

import yaml
import sys
from typing import Dict

from load_abibench import load_abibench_data, build_lookup_table
from evaluator import MultiDiseaseAffinityEvaluator
from llm_client import LLMClient
from adapter import AntibodyAdapter
from baselines import RandomSearchBaseline, SingleMutationBaseline, GeneticAlgorithmBaseline


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in configuration file: {e}")
        sys.exit(1)


def print_scores_table(scores: Dict[str, float], old_scores: Dict[str, float] = None):
    """
    Print scores in a clean table format
    
    Args:
        scores: Current scores
        old_scores: Previous scores (for comparison)
    """
    for antigen, score in scores.items():
        if old_scores and antigen in old_scores:
            delta = score - old_scores[antigen]
            symbol = "↑" if delta > 0 else "↓" if delta < 0 else "="
            print(f"  {antigen:8s}: {score:.4f} ({symbol} {delta:+.4f})")
        else:
            print(f"  {antigen:8s}: {score:.4f}")


def run_gepa(config: dict):
    """
    Run GEPA multi-disease optimization with error handling
    
    Args:
        config: Configuration dictionary
        
    Returns:
        History of optimization
    """
    print("\n" + "="*80)
    print("GEPA MULTI-DISEASE ANTIBODY OPTIMIZATION")
    print("="*80)
    
    try:
        # 1. Load dataset
        print("\n[1/6] Loading AbBiBench dataset...")
        dataset_name = config['dataset']['name']
        config_antigens = config.get('antigens', None)
        
        seed_sequence, antigen_to_dataset, validated_antigens = load_abibench_data(
            dataset_name, 
            config_antigens
        )
        
        print(f"\nSeed sequence (length {len(seed_sequence)}):")
        if len(seed_sequence) > 60:
            print(f"  {seed_sequence[:60]}...")
        else:
            print(f"  {seed_sequence}")
        
        # 2. Build lookup table
        print("\n[2/6] Building affinity lookup table...")
        lookup_table = build_lookup_table(antigen_to_dataset)
        
        # 3. Initialize evaluator with validated antigens
        print("\n[3/6] Initializing multi-disease evaluator...")
        evaluator = MultiDiseaseAffinityEvaluator(lookup_table, validated_antigens)
        
        # 4. Initialize LLM client
        print("\n[4/6] Initializing LLM client...")
        try:
            llm_client = LLMClient(config['llm'])
            print(f"  Connected to {config['llm']['model']}")
        except ValueError as e:
            print(f"  ERROR: {e}")
            sys.exit(1)
        
        # 5. Initialize GEPA adapter
        print("\n[5/6] Initializing GEPA adapter...")
        mutation_prompt = config['mutation_prompt_template']
        max_mutations = config['llm'].get('max_mutations', 3)
        max_feedback_tokens = config['llm'].get('max_feedback_tokens', 2000)
        
        adapter = AntibodyAdapter(
            evaluator=evaluator,
            llm_client=llm_client,
            mutation_prompt_template=mutation_prompt,
            max_mutations=max_mutations,
            max_feedback_tokens=max_feedback_tokens
        )
        
        # 6. Evaluate seed sequence
        print("\n[6/6] Evaluating seed sequence...")
        current_seq = seed_sequence
        current_scores = adapter.evaluate_multi(current_seq)
        current_agg = adapter.aggregate_score(current_scores)
        
        print("\nSeed Performance:")
        print_scores_table(current_scores)
        print(f"  Average: {current_agg:.4f}")
        
        # Run GEPA iterations
        print("\n" + "="*80)
        print("STARTING GEPA EVOLUTION")
        print("="*80)
        
        iterations = config['evolution']['iterations']
        history = [{
            'iteration': 0,
            'sequence': current_seq,
            'scores': current_scores,
            'aggregate': current_agg
        }]
        
        for i in range(1, iterations + 1):
            print(f"\n{'='*80}")
            print(f"ITERATION {i}/{iterations}")
            print(f"{'='*80}")
            
            try:
                # Perform GEPA step
                new_seq, new_scores, feedback, new_agg = adapter.step(current_seq, current_scores)
                
                # Display results
                print(f"\nNew Sequence:")
                if len(new_seq) > 60:
                    print(f"  {new_seq[:60]}...")
                else:
                    print(f"  {new_seq}")
                
                print(f"\nPerformance:")
                print_scores_table(new_scores, current_scores)
                print(f"  Average: {new_agg:.4f} ({new_agg - current_agg:+.4f})")
                
                print(f"\nFeedback:")
                print("-" * 80)
                print(feedback)
                print("-" * 80)
                
                # Update for next iteration
                current_seq = new_seq
                current_scores = new_scores
                current_agg = new_agg
                
                history.append({
                    'iteration': i,
                    'sequence': current_seq,
                    'scores': current_scores,
                    'aggregate': current_agg
                })
                
            except Exception as e:
                print(f"\n⚠️  ERROR in iteration {i}: {e}")
                print("Continuing with current sequence...")
                history.append({
                    'iteration': i,
                    'sequence': current_seq,
                    'scores': current_scores,
                    'aggregate': current_agg
                })
        
        # Final summary
        print("\n" + "="*80)
        print("OPTIMIZATION COMPLETE")
        print("="*80)
        
        print(f"\nFinal Sequence:")
        print(f"  {current_seq}")
        
        print(f"\nFinal Performance:")
        seed_scores = history[0]['scores']
        print_scores_table(current_scores, seed_scores)
        
        seed_agg = history[0]['aggregate']
        final_improvement = current_agg - seed_agg
        print(f"  Average: {current_agg:.4f} (improvement: {final_improvement:+.4f})")
        
        print(f"\nCache size: {evaluator.get_cache_size()} sequences evaluated")
        
        return history
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_baselines(config: dict, seed_sequence: str, evaluator: MultiDiseaseAffinityEvaluator):
    """
    Run baseline methods for comparison (no redundant data loading)
    
    Args:
        config: Configuration dictionary
        seed_sequence: Starting sequence
        evaluator: Initialized evaluator (reused)
        
    Returns:
        Dictionary of baseline results
    """
    print("\n" + "="*80)
    print("RUNNING BASELINE COMPARISONS")
    print("="*80)
    
    results = {}
    
    try:
        # 1. Random Search
        if 'random_search' in config['baselines']:
            rs_config = config['baselines']['random_search']
            rs = RandomSearchBaseline(
                evaluator=evaluator,
                iterations=rs_config.get('iterations', 10),
                mutations_per_iter=rs_config.get('mutations_per_iter', 3)
            )
            best_seq, best_scores, history = rs.optimize(seed_sequence)
            results['random_search'] = {
                'sequence': best_seq,
                'scores': best_scores,
                'history': history,
                'final_aggregate': history[-1]['aggregate']
            }
    except Exception as e:
        print(f"⚠️  ERROR in Random Search: {e}")
    
    try:
        # 2. Single Mutation
        if 'single_mutation' in config['baselines']:
            sm_config = config['baselines']['single_mutation']
            sm = SingleMutationBaseline(
                evaluator=evaluator,
                iterations=sm_config.get('iterations', 10)
            )
            best_seq, best_scores, history = sm.optimize(seed_sequence)
            results['single_mutation'] = {
                'sequence': best_seq,
                'scores': best_scores,
                'history': history,
                'final_aggregate': history[-1]['aggregate']
            }
    except Exception as e:
        print(f"⚠️  ERROR in Single Mutation: {e}")
    
    try:
        # 3. Genetic Algorithm
        if 'genetic_algorithm' in config['baselines']:
            ga_config = config['baselines']['genetic_algorithm']
            ga = GeneticAlgorithmBaseline(
                evaluator=evaluator,
                population_size=ga_config.get('population_size', 20),
                generations=ga_config.get('generations', 10),
                mutation_rate=ga_config.get('mutation_rate', 0.1),
                crossover_rate=ga_config.get('crossover_rate', 0.7)
            )
            best_seq, best_scores, history = ga.optimize(seed_sequence)
            results['genetic_algorithm'] = {
                'sequence': best_seq,
                'scores': best_scores,
                'history': history,
                'final_aggregate': history[-1]['aggregate']
            }
    except Exception as e:
        print(f"⚠️  ERROR in Genetic Algorithm: {e}")
    
    return results


def main():
    """Main entry point with clean flow"""
    # Load configuration
    config = load_config()
    
    # Run GEPA
    gepa_history = run_gepa(config)
    
    # Check if baselines should be run
    run_baselines_flag = config.get('run_baselines', False)
    
    if run_baselines_flag:
        print("\n" + "="*80)
        print("Baselines enabled in config. Running comparisons...")
        print("="*80)
        
        # Reload necessary components (reuse evaluator)
        dataset_name = config['dataset']['name']
        config_antigens = config.get('antigens', None)
        seed_sequence, antigen_to_dataset, validated_antigens = load_abibench_data(
            dataset_name,
            config_antigens
        )
        lookup_table = build_lookup_table(antigen_to_dataset)
        evaluator = MultiDiseaseAffinityEvaluator(lookup_table, validated_antigens)
        
        baseline_results = run_baselines(config, seed_sequence, evaluator)
        
        # Compare results
        print("\n" + "="*80)
        print("FINAL COMPARISON")
        print("="*80)
        
        gepa_final = gepa_history[-1]['aggregate']
        print(f"\nGEPA:                    {gepa_final:.4f}")
        
        for method, result in baseline_results.items():
            final_agg = result['final_aggregate']
            method_name = method.replace('_', ' ').title()
            print(f"{method_name:24s} {final_agg:.4f}")
        
        print("\n" + "="*80)
    else:
        print("\n" + "="*80)
        print("Baselines disabled. To enable, set 'run_baselines: true' in config.yaml")
        print("="*80)


if __name__ == "__main__":
    main()
