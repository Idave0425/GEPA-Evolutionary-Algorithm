"""
Custom Antibody Dataset Loader
Works with datasets containing:
- heavy_chain_seq
- light_chain_seq
- binding_score
"""

from datasets import load_dataset
from typing import Dict, List, Tuple


def combine_sequences(entry):
    """Combine heavy + light chain into one sequence string."""
    heavy = entry.get("heavy_chain_seq")
    light = entry.get("light_chain_seq")

    if not heavy or not light:
        raise ValueError(f"Entry missing heavy/light chain fields: {entry}")

    return heavy + light


def load_abibench_data(
    dataset_name: str,
    config_antigens: List[str] = None
):
    """
    Load antibody dataset and convert into GEPA-compatible format.

    Returns:
        seed_sequence: WT-like starting point (first sequence)
        antigen_to_dataset: {"BINDING": [entries]}
        validated_antigens: ["BINDING"]
    """

    print(f"Loading dataset: {dataset_name}...")
    dataset = load_dataset(dataset_name, split="train")
    print(f"Dataset loaded with {len(dataset)} entries")

    # -----------------------------
    # 1. Extract combined sequences
    # -----------------------------
    processed_entries = []

    for entry in dataset:
        combined_seq = combine_sequences(entry)
        score = entry.get("binding_score", None)

        if score is None:
            raise ValueError(f"Entry missing binding_score: {entry}")

        processed_entries.append({
            "sequence": combined_seq,
            "binding_score": float(score)
        })

    # -----------------------------
    # 2. Choose seed sequence
    # -----------------------------
    seed_sequence = processed_entries[0]["sequence"]
    print(f"Using first combined sequence as seed (length {len(seed_sequence)})")

    # -----------------------------
    # 3. Create artificial antigen
    # -----------------------------
    antigen_to_dataset = {"BINDING": processed_entries}

    # If user tries to specify antigens, ignore it but warn
    if config_antigens:
        print("⚠️  WARNING: Dataset has no real antigens.")
        print("➡️  Overriding with default antigen: ['BINDING']")

    validated_antigens = ["BINDING"]

    print("Dataset ready for single-target optimization.")
    print(f"Total sequences processed: {len(processed_entries)}")

    return seed_sequence, antigen_to_dataset, validated_antigens


def build_lookup_table(antigen_to_dataset: Dict[str, List[Dict]]):
    """
    Build lookup table: (antigen, sequence) -> binding_score
    """

    lookup = {}

    for antigen, entries in antigen_to_dataset.items():
        for entry in entries:
            seq = entry["sequence"]
            score = entry["binding_score"]
            lookup[(antigen, seq)] = score

    print(f"Lookup table built with {len(lookup)} entries")
    return lookup

