"""
Feedback Generator for GEPA
Generates concise textual feedback about sequence mutations and performance changes
"""

from typing import List, Tuple, Dict


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
        return "pos-charged"
    elif aa in charged_negative:
        return "neg-charged"
    elif aa in special:
        return "special"
    else:
        return "unknown"


def categorize_change(delta: float, old_score: float) -> str:
    """
    Categorize score change qualitatively
    
    Args:
        delta: Score change
        old_score: Original score
        
    Returns:
        Qualitative description
    """
    if old_score == 0:
        if delta > 0:
            return "new binding detected"
        return "no change"
    
    pct = abs(delta / old_score) if old_score != 0 else 0
    
    if delta > 0:
        if pct > 0.2:
            return "strong improvement"
        elif pct > 0.05:
            return "moderate improvement"
        else:
            return "slight improvement"
    elif delta < 0:
        if pct > 0.2:
            return "strong decrease"
        elif pct > 0.05:
            return "moderate decrease"
        else:
            return "slight decrease"
    else:
        return "unchanged"


def format_mutation_compact(pos: int, old_aa: str, new_aa: str) -> str:
    """
    Format mutation in compact notation (e.g., 'P31W')
    
    Args:
        pos: Position (0-indexed)
        old_aa: Old amino acid
        new_aa: New amino acid
        
    Returns:
        Compact mutation string
    """
    return f"{old_aa}{pos+1}{new_aa}"


def generate_multidisease_feedback(
    old_seq: str,
    new_seq: str,
    old_scores: Dict[str, float],
    new_scores: Dict[str, float],
    antigens: List[str]
) -> str:
    """
    Generate consolidated multi-disease feedback (concise format)
    
    Args:
        old_seq: Original sequence
        new_seq: Mutated sequence
        old_scores: Original scores per antigen
        new_scores: New scores per antigen
        antigens: List of antigen names
        
    Returns:
        Concise multi-disease feedback string
    """
    # Check for length mismatch
    if len(old_seq) != len(new_seq):
        return (f"⚠️  SEQUENCE LENGTH MISMATCH\n"
                f"Old: {len(old_seq)} aa, New: {len(new_seq)} aa\n"
                f"Cannot analyze mutations.")
    
    # Find mutations
    mutations = find_mutations(old_seq, new_seq)
    
    # Build compact feedback
    feedback_lines = []
    
    # Mutation summary (compact)
    if mutations:
        mutation_strs = [format_mutation_compact(pos, old, new) for pos, old, new in mutations]
        feedback_lines.append(f"Mutations: {', '.join(mutation_strs)}")
        
        # Add property changes for first few mutations
        if len(mutations) <= 3:
            for pos, old_aa, new_aa in mutations:
                old_type = classify_amino_acid(old_aa)
                new_type = classify_amino_acid(new_aa)
                if old_type != new_type:
                    feedback_lines.append(f"  {old_aa}{pos+1}{new_aa}: {old_type} → {new_type}")
    else:
        feedback_lines.append("No mutations detected")
    
    feedback_lines.append("")
    feedback_lines.append("Per-Antigen Performance:")
    
    # Per-antigen scores (concise table)
    improvements = 0
    decreases = 0
    
    for antigen in antigens:
        old_score = old_scores.get(antigen, 0.0)
        new_score = new_scores.get(antigen, 0.0)
        delta = new_score - old_score
        
        # Track improvements
        if delta > 0:
            improvements += 1
        elif delta < 0:
            decreases += 1
        
        # Format: HER2: 0.51 → 0.64 (+0.13, moderate improvement)
        category = categorize_change(delta, old_score)
        symbol = "↑" if delta > 0 else "↓" if delta < 0 else "="
        
        feedback_lines.append(
            f"  {antigen:8s}: {old_score:.3f} → {new_score:.3f} "
            f"({symbol} {delta:+.3f}, {category})"
        )
    
    # Overall summary
    old_avg = sum(old_scores.values()) / len(old_scores) if old_scores else 0
    new_avg = sum(new_scores.values()) / len(new_scores) if new_scores else 0
    avg_delta = new_avg - old_avg
    
    feedback_lines.append("")
    feedback_lines.append(f"Average: {old_avg:.3f} → {new_avg:.3f} ({avg_delta:+.3f})")
    feedback_lines.append(f"Improved: {improvements}/{len(antigens)} diseases")
    
    # Strategic guidance
    if improvements == 0 and decreases > 0:
        feedback_lines.append("⚠️  No improvements. Try different mutation strategy.")
    elif improvements > 0 and decreases == 0:
        feedback_lines.append("✓ All-around improvement. Continue this direction.")
    elif improvements > decreases:
        feedback_lines.append("✓ Net positive. Focus on weak antigens.")
    
    return "\n".join(feedback_lines)


def generate_initial_feedback(
    sequence: str,
    scores: Dict[str, float],
    antigens: List[str]
) -> str:
    """
    Generate feedback for initial sequence (no comparison)
    
    Args:
        sequence: Current sequence
        scores: Current scores per antigen
        antigens: List of antigens
        
    Returns:
        Feedback string for LLM
    """
    feedback_lines = []
    feedback_lines.append("Current Performance:")
    
    weak_antigens = []
    moderate_antigens = []
    strong_antigens = []
    
    for antigen in antigens:
        score = scores.get(antigen, 0.0)
        
        if score < 0.3:
            status = "WEAK"
            weak_antigens.append(antigen)
        elif score < 0.6:
            status = "MODERATE"
            moderate_antigens.append(antigen)
        else:
            status = "STRONG"
            strong_antigens.append(antigen)
        
        feedback_lines.append(f"  {antigen:8s}: {score:.3f} ({status})")
    
    # Strategic priorities
    feedback_lines.append("")
    if weak_antigens:
        feedback_lines.append(f"Priority: Improve {', '.join(weak_antigens)}")
    if strong_antigens:
        feedback_lines.append(f"Maintain: {', '.join(strong_antigens)}")
    
    avg_score = sum(scores.values()) / len(scores) if scores else 0
    feedback_lines.append(f"\nAverage: {avg_score:.3f}")
    
    return "\n".join(feedback_lines)
