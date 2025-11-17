"""
Example usage of GEPA Multi-Disease Antibody Optimization
Demonstrates how to use the system programmatically
"""

import yaml
from load_abibench import load_abibench_data, build_lookup_table
from evaluator import MultiDiseaseAffinityEvaluator
from llm_client import LLMClient
from adapter import AntibodyAdapter


def quick_example():
    """
    Quick example showing basic usage
    """
    print("="*60)
    print("GEPA Quick Example")
    print("="*60)
    
    # 1. Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # 2. Load dataset
    print("\nLoading dataset...")
    seed_sequence, antigen_to_dataset = load_abibench_data(config['dataset']['name'])
    lookup_table = build_lookup_table(antigen_to_dataset)
    
    # 3. Initialize components
    print("Initializing components...")
    evaluator = MultiDiseaseAffinityEvaluator(lookup_table)
    llm_client = LLMClient(config['llm'])
    
    adapter = AntibodyAdapter(
        evaluator=evaluator,
        llm_client=llm_client,
        antigens=config['antigens'],
        mutation_prompt_template=config['mutation_prompt_template']
    )
    
    # 4. Evaluate seed
    print("\nEvaluating seed sequence...")
    current_seq = seed_sequence[:100]  # Use shorter sequence for demo
    current_scores = adapter.evaluate_multi(current_seq)
    
    print(f"\nSeed sequence: {current_seq}")
    print("\nInitial scores:")
    for antigen, score in current_scores.items():
        print(f"  {antigen}: {score:.4f}")
    
    # 5. Run one GEPA iteration
    print("\n" + "="*60)
    print("Running one GEPA iteration...")
    print("="*60)
    
    new_seq, new_scores, feedback, agg_score = adapter.step(current_seq, current_scores)
    
    print(f"\nNew sequence: {new_seq}")
    print("\nNew scores:")
    for antigen, score in new_scores.items():
        old_score = current_scores[antigen]
        delta = score - old_score
        print(f"  {antigen}: {score:.4f} (Δ {delta:+.4f})")
    
    print(f"\nAggregate score: {agg_score:.4f}")
    
    print("\n" + "="*60)
    print("Example complete!")
    print("="*60)


def custom_antigens_example():
    """
    Example with custom antigen selection
    """
    print("\n" + "="*60)
    print("Custom Antigens Example")
    print("="*60)
    
    # Load config but override antigens
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Use only specific antigens
    custom_antigens = ["HER2", "VEGF"]
    print(f"\nUsing custom antigens: {custom_antigens}")
    
    # Load and initialize
    seed_sequence, antigen_to_dataset = load_abibench_data(config['dataset']['name'])
    lookup_table = build_lookup_table(antigen_to_dataset)
    evaluator = MultiDiseaseAffinityEvaluator(lookup_table)
    llm_client = LLMClient(config['llm'])
    
    adapter = AntibodyAdapter(
        evaluator=evaluator,
        llm_client=llm_client,
        antigens=custom_antigens,
        mutation_prompt_template=config['mutation_prompt_template']
    )
    
    # Evaluate
    scores = adapter.evaluate_multi(seed_sequence[:100])
    print("\nScores:")
    for antigen, score in scores.items():
        print(f"  {antigen}: {score:.4f}")


def evaluation_only_example():
    """
    Example of just evaluating sequences without LLM
    """
    print("\n" + "="*60)
    print("Evaluation Only Example")
    print("="*60)
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Setup evaluator
    seed_sequence, antigen_to_dataset = load_abibench_data(config['dataset']['name'])
    lookup_table = build_lookup_table(antigen_to_dataset)
    evaluator = MultiDiseaseAffinityEvaluator(lookup_table)
    
    # Evaluate multiple sequences
    test_sequences = [
        seed_sequence[:100],
        seed_sequence[50:150],
        seed_sequence[100:200]
    ]
    
    print(f"\nEvaluating {len(test_sequences)} sequences...")
    
    for i, seq in enumerate(test_sequences, 1):
        scores = evaluator.evaluate_all_antigens(seq, config['antigens'])
        avg_score = evaluator.aggregate_score(scores)
        print(f"\nSequence {i}: avg score = {avg_score:.4f}")
        for antigen, score in scores.items():
            print(f"  {antigen}: {score:.4f}")


if __name__ == "__main__":
    import sys
    
    print("\nGEPA Multi-Disease Antibody Optimization - Examples")
    print("="*60)
    print("\nAvailable examples:")
    print("  1. Quick example (default)")
    print("  2. Custom antigens")
    print("  3. Evaluation only (no LLM)")
    print()
    
    choice = input("Select example (1-3) or press Enter for default: ").strip()
    
    if choice == "2":
        custom_antigens_example()
    elif choice == "3":
        evaluation_only_example()
    else:
        quick_example()
    
    print("\nFor full optimization, run: python main.py")

