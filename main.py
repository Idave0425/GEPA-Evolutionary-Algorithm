"""
Main runner for GEPA Multi-Disease Antibody Optimization
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
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def run_gepa(config: dict):
    """
    Run GEPA multi-disease optimization
    
    Args:
        config: Configuration dictionary
    """
    print("\n" + "="*80)
    print("GEPA MULTI-DISEASE ANTIBODY OPTIMIZATION")
    print("="*80)
    
    # 1. Load dataset
    print("\n[1/6] Loading AbBiBench dataset...")
    dataset_name = config['dataset']['name']
    seed_sequence, antigen_to_dataset = load_abibench_data(dataset_name)
    
    print(f"\nSeed sequence (length {len(seed_sequence)}):")
    print(f"  {seed_sequence[:60]}..." if len(seed_sequence) > 60 else f"  {seed_sequence}")
    
    # 2. Build lookup table
    print("\n[2/6] Building affinity lookup table...")
    lookup_table = build_lookup_table(antigen_to_dataset)
    
    # 3. Initialize evaluator
    print("\n[3/6] Initializing multi-disease evaluator...")
    evaluator = MultiDiseaseAffinityEvaluator(lookup_table)
    
    # 4. Initialize LLM client
    print("\n[4/6] Initializing LLM client...")
    try:
        llm_client = LLMClient(config['llm'])
        print(f"  Connected to {config['llm']['model']}")
    except ValueError as e:
        print(f"  ERROR: {e}")
        print(f"  Please set the {config['llm']['api_key_env']} environment variable")
        sys.exit(1)
    
    # 5. Initialize GEPA adapter
    print("\n[5/6] Initializing GEPA adapter...")
    antigens = config['antigens']
    mutation_prompt = config['mutation_prompt_template']
    
    adapter = AntibodyAdapter(
        evaluator=evaluator,
        llm_client=llm_client,
        antigens=antigens,
        mutation_prompt_template=mutation_prompt
    )
    
    # 6. Evaluate seed sequence
    print("\n[6/6] Evaluating seed sequence...")
    current_seq = seed_sequence
    current_scores = adapter.evaluate_multi(current_seq)
    current_agg = adapter.aggregate_score(current_scores)
    
    print("\nSeed Performance:")
    for antigen, score in current_scores.items():
        print(f"  {antigen}: {score:.4f}")
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
        
        # Perform GEPA step
        new_seq, new_scores, feedback, new_agg = adapter.step(current_seq, current_scores)
        
        # Display results
        print(f"\nNew Sequence:")
        print(f"  {new_seq[:60]}..." if len(new_seq) > 60 else f"  {new_seq}")
        
        print(f"\nPerformance:")
        for antigen, score in new_scores.items():
            old_score = current_scores[antigen]
            delta = score - old_score
            symbol = "↑" if delta > 0 else "↓" if delta < 0 else "="
            print(f"  {antigen}: {score:.4f} ({symbol} {delta:+.4f})")
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
    
    # Final summary
    print("\n" + "="*80)
    print("OPTIMIZATION COMPLETE")
    print("="*80)
    
    print(f"\nFinal Sequence:")
    print(f"  {current_seq}")
    
    print(f"\nFinal Performance:")
    for antigen, score in current_scores.items():
        seed_score = history[0]['scores'][antigen]
        improvement = score - seed_score
        print(f"  {antigen}: {score:.4f} (improvement: {improvement:+.4f})")
    
    seed_agg = history[0]['aggregate']
    final_improvement = current_agg - seed_agg
    print(f"  Average: {current_agg:.4f} (improvement: {final_improvement:+.4f})")
    
    return history


def run_baselines(config: dict, seed_sequence: str, lookup_table: Dict):
    """
    Run baseline methods for comparison
    
    Args:
        config: Configuration dictionary
        seed_sequence: Starting sequence
        lookup_table: Affinity lookup table
    """
    print("\n" + "="*80)
    print("RUNNING BASELINE COMPARISONS")
    print("="*80)
    
    # Initialize evaluator
    evaluator = MultiDiseaseAffinityEvaluator(lookup_table)
    antigens = config['antigens']
    
    results = {}
    
    # 1. Random Search
    if 'random_search' in config['baselines']:
        rs_config = config['baselines']['random_search']
        rs = RandomSearchBaseline(
            evaluator=evaluator,
            antigens=antigens,
            iterations=rs_config['iterations'],
            mutations_per_iter=rs_config['mutations_per_iter']
        )
        best_seq, best_scores, history = rs.optimize(seed_sequence)
        results['random_search'] = {
            'sequence': best_seq,
            'scores': best_scores,
            'history': history
        }
    
    # 2. Single Mutation
    if 'single_mutation' in config['baselines']:
        sm_config = config['baselines']['single_mutation']
        sm = SingleMutationBaseline(
            evaluator=evaluator,
            antigens=antigens,
            iterations=sm_config['iterations']
        )
        best_seq, best_scores, history = sm.optimize(seed_sequence)
        results['single_mutation'] = {
            'sequence': best_seq,
            'scores': best_scores,
            'history': history
        }
    
    # 3. Genetic Algorithm
    if 'genetic_algorithm' in config['baselines']:
        ga_config = config['baselines']['genetic_algorithm']
        ga = GeneticAlgorithmBaseline(
            evaluator=evaluator,
            antigens=antigens,
            population_size=ga_config['population_size'],
            generations=ga_config['generations'],
            mutation_rate=ga_config['mutation_rate'],
            crossover_rate=ga_config['crossover_rate']
        )
        best_seq, best_scores, history = ga.optimize(seed_sequence)
        results['genetic_algorithm'] = {
            'sequence': best_seq,
            'scores': best_scores,
            'history': history
        }
    
    return results


def main():
    """Main entry point"""
    # Load configuration
    config = load_config()
    
    # Run GEPA
    gepa_history = run_gepa(config)
    
    # Optionally run baselines
    print("\n" + "="*80)
    run_baselines_flag = input("Run baseline comparisons? (y/n): ").strip().lower()
    
    if run_baselines_flag == 'y':
        # Reload dataset for baselines
        dataset_name = config['dataset']['name']
        seed_sequence, antigen_to_dataset = load_abibench_data(dataset_name)
        lookup_table = build_lookup_table(antigen_to_dataset)
        
        baseline_results = run_baselines(config, seed_sequence, lookup_table)
        
        # Compare results
        print("\n" + "="*80)
        print("FINAL COMPARISON")
        print("="*80)
        
        gepa_final = gepa_history[-1]
        print(f"\nGEPA: {gepa_final['aggregate']:.4f}")
        
        for method, result in baseline_results.items():
            final_agg = result['history'][-1]['aggregate']
            print(f"{method.replace('_', ' ').title()}: {final_agg:.4f}")


if __name__ == "__main__":
    main()

