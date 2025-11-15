"""
Rate limiting middleware for WhatsApp service
"""
from typing import Dict, List
from datetime import datetime, timedelta
from loguru import logger


class RateLimiter:
    def __init__(self, max_per_minute: int = 10, max_per_hour: int = 100):
        """Initialize rate limiter with per-minute and per-hour limits."""
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.requests: Dict[str, List[datetime]] = {}

    def is_allowed(self, user_id: str) -> bool:
        """
        Check if user is within rate limits.
        
        Args:
            user_id: Unique identifier for the user (phone number)
            
        Returns:
            bool: True if request is allowed, False if rate limited
        """
        now = datetime.now()
        
        # Initialize user's request history if not exists
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        user_requests = self.requests[user_id]
        
        # Remove requests older than 1 hour
        cutoff_hour = now - timedelta(hours=1)
        user_requests[:] = [req_time for req_time in user_requests if req_time > cutoff_hour]
        
        # Check hourly limit
        if len(user_requests) >= self.max_per_hour:
            logger.warning(f"User {user_id} exceeded hourly limit ({self.max_per_hour})")
            return False
        
        # Check per-minute limit
        cutoff_minute = now - timedelta(minutes=1)
        recent_requests = [req_time for req_time in user_requests if req_time > cutoff_minute]
        
        if len(recent_requests) >= self.max_per_minute:
            logger.warning(f"User {user_id} exceeded per-minute limit ({self.max_per_minute})")
            return False
        
        # Add current request
        user_requests.append(now)
        
        return True

    def get_reset_time(self, user_id: str) -> datetime:
        """Get the time when rate limit will reset for user."""
        if user_id not in self.requests or not self.requests[user_id]:
            return datetime.now()
        
        # Find the oldest request in the current window
        now = datetime.now()
        cutoff_minute = now - timedelta(minutes=1)
        recent_requests = [req_time for req_time in self.requests[user_id] if req_time > cutoff_minute]
        
        if len(recent_requests) >= self.max_per_minute and recent_requests:
            # Reset time is 1 minute after oldest recent request
            return recent_requests[0] + timedelta(minutes=1)
        
        return datetime.now()