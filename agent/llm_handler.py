"""
Module for handling interactions with the language model (Claude/Anthropic API).
"""
import os
from typing import Dict, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

class LLMHandler:
    def __init__(self):
        """Initialize the LLM handler with API credentials."""
        load_dotenv()
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.context = []

    def _create_prompt(self, question: str, homework_data: Dict) -> str:
        """Create a prompt for the LLM with context about homework."""
        prompt = f"""
        You are a helpful homework assistant. Here is the current homework data:
        {homework_data}

        Question: Please respond in Hebrew: {question}

        Please provide a clear and concise response focusing on relevant homework information.
        """
        return prompt

    async def get_response(self, question: str, homework_data: Dict) -> str:
        """
        Get a response from the LLM for a homework-related question.
        
        Args:
            question: The user's question about homework
            homework_data: Dictionary containing current homework information
            
        Returns:
            str: The LLM's response to the question
        """
        prompt = self._create_prompt(question, homework_data)
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="Please respond in Hebrew.",
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return response.content[0].text

    def clear_context(self):
        """Clear the conversation context."""
        self.context = []