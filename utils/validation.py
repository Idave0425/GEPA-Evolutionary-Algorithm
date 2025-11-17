"""
Global validation utilities for GEPA framework
Provides sequence and antigen validation across all modules
"""

from typing import List, Set, Optional

# Valid amino acid single-letter codes
VALID_AMINO_ACIDS: Set[str] = set('ACDEFGHIKLMNPQRSTVWY')


def is_valid_amino_acid_sequence(sequence: str) -> bool:
    """
    Check if a sequence contains only valid amino acid codes
    
    Args:
        sequence: Amino acid sequence string
        
    Returns:
        True if all characters are valid amino acids
    """
    if not sequence:
        return False
    return all(aa in VALID_AMINO_ACIDS for aa in sequence.upper())


def validate_sequence_length(sequence: str, expected_length: Optional[int] = None) -> bool:
    """
    Validate sequence length
    
    Args:
        sequence: Amino acid sequence
        expected_length: Expected length (if None, just checks non-empty)
        
    Returns:
        True if length is valid
    """
    if not sequence:
        return False
    
    if expected_length is not None:
        return len(sequence) == expected_length
    
    return len(sequence) > 0


def validate_sequence(
    sequence: str,
    expected_length: Optional[int] = None,
    strict: bool = True
) -> tuple[bool, str]:
    """
    Comprehensive sequence validation
    
    Args:
        sequence: Amino acid sequence to validate
        expected_length: Expected sequence length
        strict: If True, enforce all checks; if False, be lenient
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check empty
    if not sequence:
        return False, "Sequence is empty"
    
    # Check length
    if expected_length is not None and len(sequence) != expected_length:
        return False, f"Sequence length {len(sequence)} != expected {expected_length}"
    
    # Check valid amino acids
    if not is_valid_amino_acid_sequence(sequence):
        invalid_chars = [c for c in sequence if c not in VALID_AMINO_ACIDS]
        return False, f"Invalid amino acids: {set(invalid_chars)}"
    
    # Check reasonable length
    if strict and (len(sequence) < 10 or len(sequence) > 10000):
        return False, f"Sequence length {len(sequence)} outside reasonable range [10, 10000]"
    
    return True, ""


def validate_antigen(antigen: str, available_antigens: List[str]) -> tuple[bool, str]:
    """
    Validate antigen name against available antigens
    
    Args:
        antigen: Antigen name to validate
        available_antigens: List of valid antigen names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not antigen:
        return False, "Antigen name is empty"
    
    if antigen not in available_antigens:
        return False, f"Antigen '{antigen}' not in dataset. Available: {available_antigens}"
    
    return True, ""


def clean_sequence(sequence: str) -> str:
    """
    Clean a sequence by removing non-amino acid characters
    
    Args:
        sequence: Raw sequence string
        
    Returns:
        Cleaned sequence with only valid amino acids
    """
    return ''.join(c for c in sequence.upper() if c in VALID_AMINO_ACIDS)


def count_mutations(seq1: str, seq2: str) -> int:
    """
    Count number of mutations between two sequences
    
    Args:
        seq1: First sequence
        seq2: Second sequence
        
    Returns:
        Number of differing positions
    """
    if len(seq1) != len(seq2):
        return -1
    
    return sum(1 for a, b in zip(seq1, seq2) if a != b)


def validate_mutation_count(
    old_seq: str,
    new_seq: str,
    max_mutations: int = 3
) -> tuple[bool, str]:
    """
    Validate that mutation count is within acceptable range
    
    Args:
        old_seq: Original sequence
        new_seq: Mutated sequence
        max_mutations: Maximum allowed mutations
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(old_seq) != len(new_seq):
        return False, f"Length mismatch: {len(old_seq)} vs {len(new_seq)}"
    
    num_mutations = count_mutations(old_seq, new_seq)
    
    if num_mutations == 0:
        return False, "No mutations detected"
    
    if num_mutations > max_mutations:
        return False, f"Too many mutations: {num_mutations} > {max_mutations}"
    
    return True, ""

