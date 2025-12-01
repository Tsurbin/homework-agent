"""
Main module for the homework agent that integrates LLM and query processing.
"""
from typing import Dict, Optional, List
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.llm_handler import LLMHandler
from agent.query_processor import QueryProcessor
from database.dynamodb_handler import DynamoDBHandler

class HomeworkAgent:
    def __init__(self, max_history: int = 5):
        """Initialize the homework agent with its components.
        
        Args:
            max_history: Maximum number of recent conversation turns to keep
        """
        import os
        self.llm = LLMHandler()
        self.query_processor = QueryProcessor()
        table_name = os.getenv('DYNAMODB_TABLE_NAME', 'homework-items')
        self.db = DynamoDBHandler(table_name=table_name)
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = max_history

    async def process_question(self, question: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Process a question about homework and return a response.
        
        Args:
            question: The user's question about homework
            conversation_history: Recent conversation turns for context
            
        Returns:
            str: A natural language response answering the question
        """
        # Get date from 10 days ago
        last_10_days_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        
        # Get homework data from database
        homework_items = self.db.get_all_items_from_date(last_10_days_date)
        
        # Convert homework items to the expected format
        homework_data = {}
        for item in homework_items:
            subject = item.get('subject', 'Unknown')
            date = item.get('date', '')
            
            if subject not in homework_data:
                homework_data[subject] = {}
            
            homework_data[subject][date] = {
                'description': item.get('description', ''),
                'due_date': item.get('due_date', ''),
                'subject': subject
            }
        
        # Analyze the query with conversation context
        query_analysis = self.query_processor.analyze_query(
            question, 
            conversation_history=conversation_history or []
        )
        
        # Filter homework data based on the query analysis
        filtered_homework = self.query_processor.filter_homework(homework_data, query_analysis)
        
        # Get response from LLM with conversation history
        response = await self.llm.get_response(
            question, 
            filtered_homework, 
            conversation_history=conversation_history or []
        )
        
        return response

    async def handle_conversation(self, question: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Handle a conversation turn with the user.
        
        Args:
            question: The user's question or message
            
        Returns:
            str: The agent's response
        """
        try:
            # Process question with conversation history
            response = await self.process_question(question, conversation_history)
            
            # Add this turn to history
            self.conversation_history.append({
                "role": "user",
                "content": question
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Keep only the most recent turns
            if len(self.conversation_history) > self.max_history * 2:  # *2 for user+assistant pairs
                self.conversation_history = self.conversation_history[-self.max_history * 2:]
            
            return response
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history."""
        return self.conversation_history.copy()

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