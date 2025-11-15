"""
Message formatter for WhatsApp responses
"""
from typing import List, Dict, Any
from datetime import datetime


class WhatsAppFormatter:
    """Format homework agent responses for WhatsApp."""
    
    @staticmethod
    def format_homework_list(homework_items: List[Dict[str, Any]]) -> str:
        """
        Format a list of homework items for WhatsApp display.
        
        Args:
            homework_items: List of homework dictionaries
            
        Returns:
            str: Formatted WhatsApp message
        """
        if not homework_items:
            return "📚 No homework found! You're all caught up! 🎉"
        
        message = "📚 *Your Homework:*\n\n"
        
        # Group by subject
        subjects = {}
        for item in homework_items:
            subject = item.get('subject', 'Unknown')
            if subject not in subjects:
                subjects[subject] = []
            subjects[subject].append(item)
        
        for subject, items in subjects.items():
            message += f"📖 *{subject}:*\n"
            for item in items:
                description = item.get('description', 'No description')
                due_date = item.get('due_date')
                
                message += f"  • {description}\n"
                if due_date:
                    message += f"    ⏰ Due: {due_date}\n"
            message += "\n"
        
        return message.strip()
    
    @staticmethod
    def format_error_message(error_type: str = "general") -> str:
        """
        Format error messages for WhatsApp.
        
        Args:
            error_type: Type of error (general, network, auth, etc.)
            
        Returns:
            str: Formatted error message
        """
        error_messages = {
            "general": "🤖 Oops! Something went wrong. Please try again.",
            "network": "🌐 Connection issue. Please check your internet and try again.",
            "auth": "🔐 Authentication error. Please contact support.",
            "rate_limit": "⏱️ Too many messages! Please wait a moment before sending another.",
            "not_found": "🔍 No homework found for your request.",
            "invalid_date": "📅 Invalid date format. Please use YYYY-MM-DD format."
        }
        
        return error_messages.get(error_type, error_messages["general"])
    
    @staticmethod
    def format_due_dates(homework_items: List[Dict[str, Any]]) -> str:
        """
        Format homework items with focus on due dates.
        
        Args:
            homework_items: List of homework dictionaries
            
        Returns:
            str: Formatted message with due date emphasis
        """
        if not homework_items:
            return "📅 No upcoming due dates! 🎉"
        
        # Sort by due date
        sorted_items = sorted(
            homework_items, 
            key=lambda x: x.get('due_date', '9999-12-31')
        )
        
        message = "⏰ *Upcoming Due Dates:*\n\n"
        
        current_date = None
        for item in sorted_items:
            due_date = item.get('due_date')
            if not due_date:
                continue
                
            # Group by date
            if due_date != current_date:
                current_date = due_date
                # Format date nicely
                try:
                    date_obj = datetime.strptime(due_date, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%A, %B %d')
                    message += f"📅 *{formatted_date}:*\n"
                except:
                    message += f"📅 *{due_date}:*\n"
            
            subject = item.get('subject', 'Unknown')
            description = item.get('description', 'No description')
            message += f"  • {subject}: {description}\n"
        
        return message.strip()
    
    @staticmethod
    def format_subject_homework(subject: str, homework_items: List[Dict[str, Any]]) -> str:
        """
        Format homework for a specific subject.
        
        Args:
            subject: Subject name
            homework_items: List of homework for this subject
            
        Returns:
            str: Formatted subject-specific homework
        """
        if not homework_items:
            return f"📖 No {subject} homework found! 🎉"
        
        message = f"📖 *{subject} Homework:*\n\n"
        
        for item in homework_items:
            description = item.get('description', 'No description')
            due_date = item.get('due_date')
            date = item.get('date')
            
            message += f"• {description}\n"
            if date:
                message += f"  📅 Assigned: {date}\n"
            if due_date:
                message += f"  ⏰ Due: {due_date}\n"
            message += "\n"
        
        return message.strip()
    
    @staticmethod
    def truncate_message(message: str, max_length: int = 1500) -> str:
        """
        Truncate message if too long for WhatsApp.
        
        Args:
            message: Original message
            max_length: Maximum allowed length
            
        Returns:
            str: Truncated message if needed
        """
        if len(message) <= max_length:
            return message
        
        truncated = message[:max_length - 50]
        last_newline = truncated.rfind('\n')
        
        if last_newline > 0:
            truncated = truncated[:last_newline]
        
        return truncated + "\n\n... (message truncated, ask for specific details)"