"""
LLM Client for GEPA Framework
Handles interaction with OpenAI API with retry logic and validation
"""

import os
import time
from openai import OpenAI
from utils.validation import clean_sequence


class LLMClient:
    """Client for interacting with Large Language Models with robust error handling"""
    
    # Valid OpenAI model names
    VALID_MODELS = [
        'gpt-4', 'gpt-4-turbo', 'gpt-4-turbo-preview',
        'gpt-3.5-turbo', 'gpt-3.5-turbo-16k',
        'gpt-4-1106-preview', 'gpt-4-0125-preview'
    ]
    
    def __init__(self, config):
        """
        Initialize LLM client with configuration and validation
        
        Args:
            config: Dictionary containing llm configuration
        """
        self.config = config
        self.model = config.get('model', 'gpt-4')
        self.temperature = config.get('temperature', 0.2)
        self.max_tokens = config.get('max_tokens', 500)
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
        # Validate model name
        if self.model not in self.VALID_MODELS:
            print(f"⚠️  WARNING: Model '{self.model}' not in known models list")
            print(f"   Known models: {self.VALID_MODELS}")
            print(f"   Proceeding anyway, but may fail...")
        
        # Load API key from environment
        api_key_env = config.get('api_key_env', 'OPENAI_API_KEY')
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            raise ValueError(
                f"API key not found in environment variable: {api_key_env}\n"
                f"Please set it with: export {api_key_env}='your-key-here'"
            )
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        print(f"Initialized LLM client: {self.model} (temp={self.temperature})")
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using the LLM with retry logic
        
        Args:
            prompt: Input prompt for the LLM
            
        Returns:
            Generated text string
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "text"}
                )
                
                # Extract the generated text
                generated_text = response.choices[0].message.content.strip()
                
                # Clean non-amino acid characters
                cleaned = self._clean_output(generated_text)
                
                return cleaned
                
            except Exception as e:
                last_error = e
                print(f"⚠️  LLM call attempt {attempt + 1}/{self.max_retries} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"   Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    print(f"⚠️  All {self.max_retries} attempts failed")
        
        # All retries exhausted
        raise Exception(f"LLM generation failed after {self.max_retries} attempts: {last_error}")
    
    def _get_system_prompt(self) -> str:
        """
        Get strengthened system prompt for sequence generation
        
        Returns:
            System prompt string
        """
        return (
            "You are an expert protein engineer specializing in antibody optimization.\n"
            "\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Return ONLY a mutated amino acid sequence\n"
            "2. The sequence must be the EXACT SAME LENGTH as the input\n"
            "3. Make 1-3 strategic mutations only\n"
            "4. Use only valid amino acid codes: A C D E F G H I K L M N P Q R S T V W Y\n"
            "5. NO explanations, NO labels, NO formatting, NO punctuation\n"
            "6. Just the raw sequence\n"
            "\n"
            "OUTPUT FORMAT: A single line with only amino acid letters"
        )
    
    def _clean_output(self, text: str) -> str:
        """
        Clean LLM output to extract only amino acid sequence
        
        Args:
            text: Raw LLM output
            
        Returns:
            Cleaned text
        """
        # Remove common labels and formatting
        text = text.replace("Sequence:", "")
        text = text.replace("Mutated sequence:", "")
        text = text.replace("Output:", "")
        text = text.replace("```", "")
        text = text.replace("`", "")
        text = text.strip()
        
        # If multiple lines, take the first non-empty line
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            text = lines[0]
        
        return text
