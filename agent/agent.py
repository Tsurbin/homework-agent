"""
Main module for the homework agent that integrates LLM and query processing.
"""
from typing import Dict, Optional
import asyncio
from datetime import datetime
from .llm_handler import LLMHandler
from .query_processor import QueryProcessor
from scraper.db import HomeworkDB

class HomeworkAgent:
    def __init__(self):
        """Initialize the homework agent with its components."""
        self.llm = LLMHandler()
        self.query_processor = QueryProcessor()
        self.db = HomeworkDB()

    async def process_question(self, question: str) -> str:
        """
        Process a question about homework and return a response.
        
        Args:
            question: The user's question about homework
            
        Returns:
            str: A natural language response answering the question
        """
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get homework data from database
        homework_items = self.db.list_by_date(today)
        
        # Convert homework items to the expected format
        homework_data = {}
        for item in homework_items:
            if item.subject not in homework_data:
                homework_data[item.subject] = {}
            
            homework_data[item.subject][item.date] = {
                'description': item.description,
                'due_date': item.due_date,
                'subject': item.subject
            }
        
        # Analyze the query to understand what's being asked
        query_analysis = self.query_processor.analyze_query(question)
        
        # Filter homework data based on the query analysis
        filtered_homework = self.query_processor.filter_homework(homework_data, query_analysis)
        
        # Get response from LLM
        response = await self.llm.get_response(question, filtered_homework)
        
        return response

    async def handle_conversation(self, question: str) -> str:
        """
        Handle a conversation turn with the user.
        
        Args:
            question: The user's question or message
            
        Returns:
            str: The agent's response
        """
        try:
            response = await self.process_question(question)
            return response
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"

# Example usage
async def main():
    agent = HomeworkAgent()
    
    # Example questions
    questions = [
        "What's my homework for today?",
        # "Do I have any computer assignments?",
        # "What's due tomorrow in math?",
        # "Can you list all my current homework?"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        response = await agent.handle_conversation(question)
        print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())