"""
Antibody Adapter - Core GEPA Component
Orchestrates multi-disease evaluation and LLM-driven evolution
"""

from typing import Dict, Tuple
from evaluator.affinity_model import MultiDiseaseAffinityEvaluator
from evaluator.feedback import generate_feedback
from llm_client import LLMClient


class AntibodyAdapter:
    """
    Core GEPA adapter for antibody sequence optimization
    Handles multi-disease evaluation and LLM-driven mutation
    """
    
    def __init__(
        self,
        evaluator: MultiDiseaseAffinityEvaluator,
        llm_client: LLMClient,
        antigens: list,
        mutation_prompt_template: str
    ):
        """
        Initialize the antibody adapter
        
        Args:
            evaluator: Multi-disease affinity evaluator
            llm_client: LLM client for generating mutations
            antigens: List of target antigens (diseases)
            mutation_prompt_template: Template for mutation prompts
        """
        self.evaluator = evaluator
        self.llm_client = llm_client
        self.antigens = antigens
        self.mutation_prompt_template = mutation_prompt_template
        
        print(f"Initialized AntibodyAdapter for {len(antigens)} antigens: {', '.join(antigens)}")
    
    def evaluate_multi(self, sequence: str) -> Dict[str, float]:
        """
        Evaluate a sequence across all target antigens
        
        Args:
            sequence: Antibody amino acid sequence
            
        Returns:
            Dictionary mapping antigen names to binding scores
        """
        return self.evaluator.evaluate_all_antigens(sequence, self.antigens)
    
    def aggregate_score(self, scores: Dict[str, float]) -> float:
        """
        Compute aggregate score across all diseases
        
        Args:
            scores: Dictionary of per-disease scores
            
        Returns:
            Mean score
        """
        return self.evaluator.aggregate_score(scores)
    
    def build_multitask_feedback(
        self,
        old_seq: str,
        new_seq: str,
        old_scores: Dict[str, float],
        new_scores: Dict[str, float]
    ) -> str:
        """
        Build combined feedback across all diseases
        
        Args:
            old_seq: Previous sequence
            new_seq: Current sequence
            old_scores: Previous scores per antigen
            new_scores: Current scores per antigen
            
        Returns:
            Combined feedback string
        """
        feedback_blocks = []
        
        for antigen in self.antigens:
            old_score = old_scores.get(antigen, 0.0)
            new_score = new_scores.get(antigen, 0.0)
            
            # Generate per-antigen feedback
            antigen_feedback = generate_feedback(
                old_seq, new_seq, old_score, new_score, antigen
            )
            feedback_blocks.append(antigen_feedback)
        
        # Combine all feedback
        combined = "\n\n".join(feedback_blocks)
        
        # Add summary
        old_avg = self.aggregate_score(old_scores)
        new_avg = self.aggregate_score(new_scores)
        
        summary = f"\n{'='*60}\nOVERALL PERFORMANCE\n{'='*60}\n"
        summary += f"Average binding: {old_avg:.4f} → {new_avg:.4f}\n"
        
        improvements = sum(
            1 for antigen in self.antigens
            if new_scores.get(antigen, 0) > old_scores.get(antigen, 0)
        )
        summary += f"Improved: {improvements}/{len(self.antigens)} diseases\n"
        
        combined += "\n" + summary
        
        return combined
    
    def propose_mutation(self, sequence: str, feedback: str) -> str:
        """
        Use LLM to propose a new mutated sequence
        
        Args:
            sequence: Current antibody sequence
            feedback: Combined multi-disease feedback
            
        Returns:
            New proposed sequence
        """
        # Build prompt from template
        prompt = self.mutation_prompt_template.format(
            sequence=sequence,
            feedback=feedback
        )
        
        # Generate new sequence with LLM
        raw_response = self.llm_client.generate(prompt)
        
        # Extract sequence (clean up response)
        new_sequence = self._extract_sequence(raw_response)
        
        # Validate sequence
        if len(new_sequence) != len(sequence):
            print(f"Warning: LLM returned sequence of different length. Keeping original.")
            return sequence
        
        # Check if it's a valid amino acid sequence
        valid_aa = set('ACDEFGHIKLMNPQRSTVWY')
        if not all(aa in valid_aa for aa in new_sequence):
            print(f"Warning: LLM returned invalid amino acids. Keeping original.")
            return sequence
        
        return new_sequence
    
    def _extract_sequence(self, raw_text: str) -> str:
        """
        Extract clean amino acid sequence from LLM response
        
        Args:
            raw_text: Raw LLM output
            
        Returns:
            Cleaned sequence
        """
        # Remove whitespace and newlines
        text = raw_text.strip().replace('\n', '').replace(' ', '')
        
        # If the response contains multiple lines, take the first valid one
        lines = raw_text.strip().split('\n')
        for line in lines:
            line = line.strip().replace(' ', '')
            if line and all(c in 'ACDEFGHIKLMNPQRSTVWY' for c in line):
                return line
        
        # Otherwise return cleaned full text
        return text
    
    def step(
        self,
        current_seq: str,
        current_scores: Dict[str, float]
    ) -> Tuple[str, Dict[str, float], str, float]:
        """
        Perform one GEPA iteration step
        
        Args:
            current_seq: Current antibody sequence
            current_scores: Current scores per antigen
            
        Returns:
            Tuple of (new_sequence, new_scores, feedback, aggregate_score)
        """
        # Step 1: Build feedback based on current performance
        feedback = self._build_improvement_feedback(current_seq, current_scores)
        
        # Step 2: Use LLM to propose mutation
        new_seq = self.propose_mutation(current_seq, feedback)
        
        # Step 3: Evaluate new sequence
        new_scores = self.evaluate_multi(new_seq)
        
        # Step 4: Generate comprehensive feedback
        full_feedback = self.build_multitask_feedback(
            current_seq, new_seq, current_scores, new_scores
        )
        
        # Step 5: Compute aggregate score
        agg_score = self.aggregate_score(new_scores)
        
        return new_seq, new_scores, full_feedback, agg_score
    
    def _build_improvement_feedback(
        self,
        sequence: str,
        scores: Dict[str, float]
    ) -> str:
        """
        Build feedback for improvement without comparison to previous sequence
        
        Args:
            sequence: Current sequence
            scores: Current scores
            
        Returns:
            Feedback string
        """
        feedback_parts = []
        
        feedback_parts.append("Current Performance Analysis:")
        feedback_parts.append("="*60)
        
        for antigen in self.antigens:
            score = scores.get(antigen, 0.0)
            feedback_parts.append(f"\n{antigen}: {score:.4f}")
            
            if score < 0.5:
                feedback_parts.append(f"  → Status: WEAK binding - needs improvement")
            elif score < 0.7:
                feedback_parts.append(f"  → Status: MODERATE binding - can be improved")
            else:
                feedback_parts.append(f"  → Status: STRONG binding - maintain or enhance")
        
        # Overall guidance
        avg_score = self.aggregate_score(scores)
        feedback_parts.append(f"\nAverage Score: {avg_score:.4f}")
        
        weak_antigens = [a for a in self.antigens if scores.get(a, 0) < 0.5]
        if weak_antigens:
            feedback_parts.append(f"\nPriority: Focus on improving {', '.join(weak_antigens)}")
        
        return "\n".join(feedback_parts)

