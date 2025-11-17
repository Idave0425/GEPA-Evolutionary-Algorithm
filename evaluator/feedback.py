"""
Feedback Generator for GEPA
Generates textual feedback about sequence mutations and performance changes
"""

from typing import List, Tuple


def find_mutations(old_seq: str, new_seq: str) -> List[Tuple[int, str, str]]:
    """
    Find mutations between two sequences
    
    Args:
        old_seq: Original sequence
        new_seq: Mutated sequence
        
    Returns:
        List of (position, old_aa, new_aa) tuples
    """
    if len(old_seq) != len(new_seq):
        return []
    
    mutations = []
    for i, (old_aa, new_aa) in enumerate(zip(old_seq, new_seq)):
        if old_aa != new_aa:
            mutations.append((i, old_aa, new_aa))
    
    return mutations


def classify_amino_acid(aa: str) -> str:
    """
    Classify amino acid by chemical property
    
    Args:
        aa: Single letter amino acid code
        
    Returns:
        Classification string
    """
    hydrophobic = set('AILMFWYV')
    polar = set('STNQ')
    charged_positive = set('KRH')
    charged_negative = set('DE')
    special = set('CGP')
    
    if aa in hydrophobic:
        return "hydrophobic"
    elif aa in polar:
        return "polar"
    elif aa in charged_positive:
        return "positively charged"
    elif aa in charged_negative:
        return "negatively charged"
    elif aa in special:
        return "special"
    else:
        return "unknown"


def generate_feedback(old_seq: str, new_seq: str, old_score: float, new_score: float, antigen: str = None) -> str:
    """
    Generate textual feedback about a mutation's effect
    
    Args:
        old_seq: Original sequence
        new_seq: Mutated sequence
        old_score: Original binding score
        new_score: New binding score
        antigen: Optional antigen name for context
        
    Returns:
        Textual feedback string
    """
    # Calculate score change
    score_delta = new_score - old_score
    score_change_pct = (score_delta / old_score * 100) if old_score != 0 else 0
    
    # Find mutations
    mutations = find_mutations(old_seq, new_seq)
    
    # Build feedback
    feedback_parts = []
    
    # Header
    if antigen:
        feedback_parts.append(f"=== {antigen} ===")
    
    # Score change
    if score_delta > 0:
        feedback_parts.append(f"✓ Binding IMPROVED: {old_score:.4f} → {new_score:.4f} (+{score_delta:.4f}, +{score_change_pct:.1f}%)")
    elif score_delta < 0:
        feedback_parts.append(f"✗ Binding DECREASED: {old_score:.4f} → {new_score:.4f} ({score_delta:.4f}, {score_change_pct:.1f}%)")
    else:
        feedback_parts.append(f"= Binding UNCHANGED: {old_score:.4f}")
    
    # Mutation details
    if mutations:
        feedback_parts.append(f"Mutations ({len(mutations)}):")
        for pos, old_aa, new_aa in mutations:
            old_type = classify_amino_acid(old_aa)
            new_type = classify_amino_acid(new_aa)
            feedback_parts.append(f"  • Position {pos+1}: {old_aa} ({old_type}) → {new_aa} ({new_type})")
    else:
        feedback_parts.append("No mutations detected (sequence unchanged)")
    
    # Interpretation
    if mutations and score_delta != 0:
        if score_delta > 0:
            feedback_parts.append("Interpretation: These mutations positively affected binding. Consider similar changes.")
        else:
            feedback_parts.append("Interpretation: These mutations negatively affected binding. Avoid similar changes.")
    
    return "\n".join(feedback_parts)


def generate_multi_disease_feedback(old_seq: str, new_seq: str, old_scores: dict, new_scores: dict) -> str:
    """
    Generate combined feedback for multiple diseases
    
    Args:
        old_seq: Original sequence
        new_seq: Mutated sequence
        old_scores: Dictionary of old scores per antigen
        new_scores: Dictionary of new scores per antigen
        
    Returns:
        Combined feedback string
    """
    feedback_blocks = []
    
    for antigen in old_scores.keys():
        old_score = old_scores.get(antigen, 0.0)
        new_score = new_scores.get(antigen, 0.0)
        
        antigen_feedback = generate_feedback(old_seq, new_seq, old_score, new_score, antigen)
        feedback_blocks.append(antigen_feedback)
    
    # Add summary
    old_avg = sum(old_scores.values()) / len(old_scores) if old_scores else 0
    new_avg = sum(new_scores.values()) / len(new_scores) if new_scores else 0
    
    summary = f"\n{'='*50}\nOVERALL SUMMARY\n{'='*50}\n"
    summary += f"Average binding: {old_avg:.4f} → {new_avg:.4f}\n"
    
    improvements = sum(1 for antigen in old_scores if new_scores.get(antigen, 0) > old_scores[antigen])
    summary += f"Improved on {improvements}/{len(old_scores)} diseases\n"
    
    feedback_blocks.append(summary)
    
    return "\n\n".join(feedback_blocks)

