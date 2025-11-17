"""
AbBiBench Dataset Loader
Loads and processes antibody-antigen binding data from HuggingFace
"""

from datasets import load_dataset
from typing import Dict, List, Tuple
from collections import Counter
from utils.validation import validate_antigen


def load_abibench_data(dataset_name: str = "Exscientia/AbBiBench", config_antigens: List[str] = None):
    """
    Load AbBiBench dataset and extract wildtype seed sequence
    
    Args:
        dataset_name: HuggingFace dataset identifier
        config_antigens: List of antigens from config (for validation)
        
    Returns:
        Tuple of (seed_sequence, antigen_to_dataset, validated_antigens)
    """
    print(f"Loading dataset: {dataset_name}...")
    
    # Load dataset from HuggingFace
    dataset = load_dataset(dataset_name, split="train")
    
    print(f"Dataset loaded with {len(dataset)} entries")
    
    # Extract all antigens from dataset
    dataset_antigens = set()
    for entry in dataset:
        antigen = entry.get('antigen')
        if antigen:
            dataset_antigens.add(antigen)
    
    dataset_antigens = sorted(list(dataset_antigens))
    print(f"Dataset contains {len(dataset_antigens)} antigens: {dataset_antigens}")
    
    # Validate config antigens against dataset
    validated_antigens = []
    if config_antigens:
        for antigen in config_antigens:
            is_valid, error_msg = validate_antigen(antigen, dataset_antigens)
            if is_valid:
                validated_antigens.append(antigen)
            else:
                print(f"⚠️  WARNING: {error_msg}")
                print(f"   Skipping antigen: {antigen}")
        
        if not validated_antigens:
            print("⚠️  WARNING: No valid antigens from config. Using first 3 from dataset.")
            validated_antigens = dataset_antigens[:3]
    else:
        # Use first few antigens from dataset
        validated_antigens = dataset_antigens[:3]
    
    print(f"Using antigens: {validated_antigens}")
    
    # Find wildtype seed sequence
    # WT sequences may differ per antigen, so we find the most common one
    wt_sequences = []
    wt_by_antigen = {}
    
    for entry in dataset:
        if entry.get('mutation_type') == 'WT':
            seq = entry['sequence']
            antigen = entry.get('antigen')
            wt_sequences.append(seq)
            if antigen:
                wt_by_antigen[antigen] = seq
    
    # Choose the most common WT sequence
    if wt_sequences:
        seq_counter = Counter(wt_sequences)
        seed_sequence, count = seq_counter.most_common(1)[0]
        print(f"Found wildtype seed sequence (appears {count} times, length: {len(seed_sequence)})")
        
        # Check for inconsistent WT sequences
        if len(seq_counter) > 1:
            print(f"⚠️  WARNING: Found {len(seq_counter)} different WT sequences. Using most common.")
    else:
        # Fallback: use first sequence
        seed_sequence = dataset[0]['sequence']
        print("⚠️  WARNING: No WT sequence found, using first sequence as seed")
    
    # Build antigen-specific datasets
    antigen_to_dataset = {}
    
    for entry in dataset:
        antigen = entry.get('antigen')
        
        if not antigen:
            raise ValueError(f"Entry missing 'antigen' field: {entry}")
        
        if antigen not in antigen_to_dataset:
            antigen_to_dataset[antigen] = []
        
        antigen_to_dataset[antigen].append(entry)
    
    print(f"Organized data for {len(antigen_to_dataset)} antigens")
    for antigen in validated_antigens:
        if antigen in antigen_to_dataset:
            print(f"  - {antigen}: {len(antigen_to_dataset[antigen])} sequences")
    
    return seed_sequence, antigen_to_dataset, validated_antigens


def build_lookup_table(antigen_to_dataset: Dict[str, List[Dict]]) -> Dict[Tuple[str, str], float]:
    """
    Build a fast lookup table for (antigen, sequence) -> binding_score
    Handles multiple possible score field names and detects duplicates
    
    Args:
        antigen_to_dataset: Dictionary mapping antigens to their entries
        
    Returns:
        Dictionary mapping (antigen, sequence) tuples to binding scores
    """
    lookup = {}
    duplicate_count = 0
    
    for antigen, entries in antigen_to_dataset.items():
        for entry in entries:
            sequence = entry['sequence']
            
            # Try multiple possible score field names
            binding_score = (
                entry.get('binding_score')
                or entry.get('ddG')
                or entry.get('deltaG')
                or entry.get('affinity')
                or entry.get('score')
                or 0.0
            )
            
            key = (antigen, sequence)
            
            # Warn on duplicates
            if key in lookup and lookup[key] != binding_score:
                duplicate_count += 1
                if duplicate_count <= 5:  # Only show first few warnings
                    print(f"⚠️  WARNING: Duplicate entry for {antigen}, overwriting score "
                          f"{lookup[key]:.4f} -> {binding_score:.4f}")
            
            lookup[key] = binding_score
    
    if duplicate_count > 5:
        print(f"⚠️  WARNING: Total {duplicate_count} duplicate entries detected")
    
    print(f"Built lookup table with {len(lookup)} (antigen, sequence) pairs")
    
    return lookup
