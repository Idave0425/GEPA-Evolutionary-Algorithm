"""
Antibody Adapter - Core GEPA Component
Orchestrates multi-disease evaluation and LLM-driven evolution with validation
"""

from typing import Dict, Tuple
from evaluator.affinity_model import MultiDiseaseAffinityEvaluator
from evaluator.feedback import generate_multidisease_feedback, generate_initial_feedback
from llm_client import LLMClient
from utils.validation import (
    validate_sequence,
    validate_mutation_count,
    clean_sequence,
    count_mutations,
    VALID_AMINO_ACIDS
)


class AntibodyAdapter:
    """
    Core GEPA adapter for antibody sequence optimization
    Handles multi-disease evaluation and LLM-driven mutation with strict validation
    """
    
    def __init__(
        self,
        evaluator: MultiDiseaseAffinityEvaluator,
        llm_client: LLMClient,
        mutation_prompt_template: str,
        max_mutations: int = 3,
        max_feedback_tokens: int = 2000
    ):
        """
        Initialize the antibody adapter
        
        Args:
            evaluator: Multi-disease affinity evaluator (already has antigens)
            llm_client: LLM client for generating mutations
            mutation_prompt_template: Template for mutation prompts
            max_mutations: Maximum allowed mutations per step
            max_feedback_tokens: Maximum feedback length
        """
        self.evaluator = evaluator
        self.llm_client = llm_client
        self.antigens = evaluator.antigens  # Get antigens from evaluator
        self.mutation_prompt_template = mutation_prompt_template
        self.max_mutations = max_mutations
        self.max_feedback_tokens = max_feedback_tokens
        
        # Track recent sequences to avoid loops
        self.recent_sequences = []
        self.max_recent = 5
        
        print(f"Initialized AntibodyAdapter for {len(self.antigens)} antigens")
        print(f"Max mutations per step: {max_mutations}")
    
    def evaluate_multi(self, sequence: str) -> Dict[str, float]:
        """
        Evaluate a sequence across all target antigens
        
        Args:
            sequence: Antibody amino acid sequence
            
        Returns:
            Dictionary mapping antigen names to binding scores
        """
        return self.evaluator.evaluate_all_antigens(sequence)
    
    def aggregate_score(self, scores: Dict[str, float]) -> float:
        """
        Compute aggregate score across all diseases
        
        Args:
            scores: Dictionary of per-disease scores
            
        Returns:
            Mean score
        """
        return self.evaluator.aggregate_score(scores)
    
    def _truncate_feedback(self, feedback: str) -> str:
        """
        Truncate feedback if too long
        
        Args:
            feedback: Full feedback string
            
        Returns:
            Truncated feedback
        """
        # Rough token estimate (4 chars per token)
        if len(feedback) > self.max_feedback_tokens * 4:
            # Keep last portion (most recent)
            truncated = feedback[-(self.max_feedback_tokens * 4):]
            return "...[truncated]...\n" + truncated
        return feedback
    
    def propose_mutation(self, sequence: str, current_scores: Dict[str, float]) -> str:
        """
        Use LLM to propose a new mutated sequence with validation
        
        Args:
            sequence: Current antibody sequence
            current_scores: Current performance scores
            
        Returns:
            New proposed sequence (or original if validation fails)
        """
        # Validate input sequence
        is_valid, error_msg = validate_sequence(sequence)
        if not is_valid:
            print(f"⚠️  WARNING: Invalid input sequence: {error_msg}")
            return sequence
        
        # Generate initial feedback for the LLM
        feedback = generate_initial_feedback(sequence, current_scores, self.antigens)
        feedback = self._truncate_feedback(feedback)
        
        # Build structured prompt
        prompt = self._build_mutation_prompt(sequence, feedback)
        
        # Call LLM
        try:
            raw_response = self.llm_client.generate(prompt)
        except Exception as e:
            print(f"⚠️  ERROR: LLM call failed: {e}")
            return sequence
        
        # Extract and validate new sequence
        new_sequence = self._extract_sequence(raw_response, expected_length=len(sequence))
        
        # Validate new sequence
        is_valid, error_msg = validate_sequence(new_sequence, expected_length=len(sequence))
        if not is_valid:
            print(f"⚠️  WARNING: LLM returned invalid sequence: {error_msg}")
            return sequence
        
        # Validate mutation count
        is_valid, error_msg = validate_mutation_count(
            sequence, new_sequence, max_mutations=self.max_mutations
        )
        if not is_valid:
            print(f"⚠️  WARNING: Invalid mutation: {error_msg}")
            return sequence
        
        # Check for repetition (avoid loops)
        if new_sequence in self.recent_sequences:
            print(f"⚠️  WARNING: LLM generated previously seen sequence. Using original.")
            return sequence
        
        # Track this sequence
        self.recent_sequences.append(new_sequence)
        if len(self.recent_sequences) > self.max_recent:
            self.recent_sequences.pop(0)
        
        # Count and report mutations
        num_muts = count_mutations(sequence, new_sequence)
        print(f"LLM proposed {num_muts} mutation(s)")
        
        return new_sequence
    
    def _build_mutation_prompt(self, sequence: str, feedback: str) -> str:
        """
        Build structured mutation prompt for LLM
        
        Args:
            sequence: Current sequence
            feedback: Performance feedback
            
        Returns:
            Formatted prompt
        """
        # Use the template from config
        prompt = self.mutation_prompt_template.format(
            sequence=sequence,
            feedback=feedback
        )
        
        # Add explicit formatting constraint
        prompt += f"\n\nIMPORTANT: Return ONLY the mutated sequence ({len(sequence)} amino acids)."
        prompt += "\nNo explanations, no labels, just the sequence."
        prompt += f"\nMake 1-{self.max_mutations} strategic mutations."
        
        return prompt
    
    def _extract_sequence(self, raw_text: str, expected_length: int) -> str:
        """
        Extract clean amino acid sequence from LLM response with robust parsing
        
        Args:
            raw_text: Raw LLM output
            expected_length: Expected sequence length
            
        Returns:
            Cleaned sequence
        """
        if not raw_text:
            return ""
        
        # Remove common formatting
        text = raw_text.strip()
        text = text.replace('```', '')
        text = text.replace('`', '')
        text = text.replace('Sequence:', '')
        text = text.replace('Mutated sequence:', '')
        text = text.replace('New sequence:', '')
        text = text.replace('Output:', '')
        
        # Split into lines and try each
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Clean the line
            cleaned = clean_sequence(line)
            
            # Check if it matches expected length
            if len(cleaned) == expected_length:
                # Verify all valid amino acids
                if all(c in VALID_AMINO_ACIDS for c in cleaned):
                    return cleaned
        
        # Fallback: try to clean the entire text
        cleaned_full = clean_sequence(text)
        if len(cleaned_full) == expected_length:
            return cleaned_full
        
        # If we have something close to the right length, try to extract it
        if abs(len(cleaned_full) - expected_length) <= 5:
            # Take the first expected_length characters if too long
            if len(cleaned_full) > expected_length:
                return cleaned_full[:expected_length]
        
        print(f"⚠️  WARNING: Could not extract valid sequence from LLM output")
        print(f"   Expected length: {expected_length}, Got: {len(cleaned_full)}")
        print(f"   Raw output preview: {raw_text[:100]}...")
        
        return ""
    
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
        # Step 1: Use LLM to propose mutation
        new_seq = self.propose_mutation(current_seq, current_scores)
        
        # Step 2: Evaluate new sequence
        new_scores = self.evaluate_multi(new_seq)
        
        # Step 3: Generate comprehensive feedback
        full_feedback = generate_multidisease_feedback(
            current_seq, new_seq, current_scores, new_scores, self.antigens
        )
        
        # Step 4: Compute aggregate score
        agg_score = self.aggregate_score(new_scores)
        
        return new_seq, new_scores, full_feedback, agg_score
