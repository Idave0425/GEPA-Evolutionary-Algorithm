"""
LLM Client for GEPA Framework
Handles interaction with OpenAI API for sequence generation
"""

import os
from openai import OpenAI


class LLMClient:
    """Client for interacting with Large Language Models"""
    
    def __init__(self, config):
        """
        Initialize LLM client with configuration
        
        Args:
            config: Dictionary containing llm configuration
        """
        self.config = config
        self.model = config.get('model', 'gpt-4')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 500)
        
        # Load API key from environment
        api_key_env = config.get('api_key_env', 'OPENAI_API_KEY')
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {api_key_env}")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using the LLM
        
        Args:
            prompt: Input prompt for the LLM
            
        Returns:
            Generated text string
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert protein engineer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract the generated text
            generated_text = response.choices[0].message.content.strip()
            
            return generated_text
            
        except Exception as e:
            print(f"Error generating with LLM: {e}")
            raise

