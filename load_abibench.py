"""
AbBiBench Dataset Loader
Loads and processes antibody-antigen binding data from HuggingFace
"""

from datasets import load_dataset
from typing import Dict, List, Tuple


def load_abibench_data(dataset_name: str = "Exscientia/AbBiBench"):
    """
    Load AbBiBench dataset and extract wildtype seed sequence
    
    Args:
        dataset_name: HuggingFace dataset identifier
        
    Returns:
        Tuple of (seed_sequence, antigen_to_dataset)
        - seed_sequence: The wildtype antibody sequence
        - antigen_to_dataset: Dictionary mapping antigen names to their data entries
    """
    print(f"Loading dataset: {dataset_name}...")
    
    # Load dataset from HuggingFace
    dataset = load_dataset(dataset_name, split="train")
    
    print(f"Dataset loaded with {len(dataset)} entries")
    
    # Find wildtype (WT) seed sequence
    seed_sequence = None
    for entry in dataset:
        if entry.get('mutation_type') == 'WT':
            seed_sequence = entry['sequence']
            print(f"Found wildtype seed sequence (length: {len(seed_sequence)})")
            break
    
    if seed_sequence is None:
        # Fallback: use the first sequence
        seed_sequence = dataset[0]['sequence']
        print("Warning: No WT sequence found, using first sequence as seed")
    
    # Build antigen-specific datasets
    antigen_to_dataset = {}
    
    for entry in dataset:
        antigen = entry.get('antigen', 'Unknown')
        
        if antigen not in antigen_to_dataset:
            antigen_to_dataset[antigen] = []
        
        antigen_to_dataset[antigen].append(entry)
    
    print(f"Organized data for {len(antigen_to_dataset)} antigens:")
    for antigen, entries in antigen_to_dataset.items():
        print(f"  - {antigen}: {len(entries)} sequences")
    
    return seed_sequence, antigen_to_dataset


def build_lookup_table(antigen_to_dataset: Dict[str, List[Dict]]) -> Dict[Tuple[str, str], float]:
    """
    Build a fast lookup table for (antigen, sequence) -> binding_score
    
    Args:
        antigen_to_dataset: Dictionary mapping antigens to their entries
        
    Returns:
        Dictionary mapping (antigen, sequence) tuples to binding scores
    """
    lookup = {}
    
    for antigen, entries in antigen_to_dataset.items():
        for entry in entries:
            sequence = entry['sequence']
            binding_score = entry.get('binding_score', 0.0)
            
            key = (antigen, sequence)
            lookup[key] = binding_score
    
    print(f"Built lookup table with {len(lookup)} (antigen, sequence) pairs")
    
    return lookup

