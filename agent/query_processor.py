"""
Module for processing and understanding user queries about homework.
"""
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import re

class QueryProcessor:
    def __init__(self):
        """Initialize the query processor with common query patterns."""
        self.query_patterns = {
            'today': r'today|tonight|current|now',
            'tomorrow': r'tomorrow|next day',
            'specific_subject': r'math|english|science|computer|history|geography',
            'due_date': r'due|deadline|when',
            'all': r'all|everything|full|list',
        }

    def analyze_query(self, query: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, bool]:
        """
        Analyze the user's query to understand what they're asking about.
        
        Args:
            query: The user's question about homework
            conversation_history: Recent conversation turns for context (optional)
            
        Returns:
            Dict of identified query aspects
        """
        query = query.lower()
        
        # TODO: Use conversation_history to resolve references like "it", "that", "tomorrow"
        # For now, we'll just analyze the current query
        
        analysis = {
            'is_about_today': bool(re.search(self.query_patterns['today'], query)),
            'is_about_tomorrow': bool(re.search(self.query_patterns['tomorrow'], query)),
            'wants_all_homework': bool(re.search(self.query_patterns['all'], query)),
            'is_subject_specific': bool(re.search(self.query_patterns['specific_subject'], query)),
            'is_about_due_date': bool(re.search(self.query_patterns['due_date'], query)),
        }
        
        # Extract specific subject if mentioned
        subject_match = re.search(self.query_patterns['specific_subject'], query)
        analysis['specific_subject'] = subject_match.group(0) if subject_match else None
        
        return analysis

    def filter_homework(self, homework_data: Dict, analysis: Dict) -> Dict:
        """
        Filter homework data based on query analysis.
        
        Args:
            homework_data: Dictionary containing all homework information
            analysis: Dictionary containing query analysis results
            
        Returns:
            Filtered homework data relevant to the query
        """
        filtered_data = {}
        today = datetime.now().date()
        
        for subject, assignments in homework_data.items():
            if analysis['is_subject_specific'] and subject.lower() != analysis.get('specific_subject'):
                continue
                
            relevant_assignments = {}
            for date, assignment in assignments.items():
                assignment_date = datetime.strptime(date, '%Y-%m-%d').date()
                
                # Filter based on time reference
                if analysis['is_about_today'] and assignment_date != today:
                    continue
                if analysis['is_about_tomorrow'] and assignment_date != today + timedelta(days=1):
                    continue
                    
                relevant_assignments[date] = assignment
                
            if relevant_assignments:
                filtered_data[subject] = relevant_assignments
                
        return filtered_data or homework_data  # Return all data if no filters match