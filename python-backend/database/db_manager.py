"""
Database manager for homework storage and retrieval.
"""
from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from database.models import Base, Homework, ScrapingLog
from config.settings import get_settings


class DatabaseManager:
    """Manages database operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = create_engine(
            self.settings.database_url,
            connect_args={"check_same_thread": False}  # For SQLite
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def init_db(self):
        """Initialize database tables."""
        Base.metadata.create_all(bind=self.engine)
        print("✓ Database initialized successfully")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session context manager."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def add_homework(self, homework_data: dict) -> Homework:
        """Add or update homework assignment."""
        with self.get_session() as session:
            # Check if homework already exists by source_id
            if homework_data.get('source_id'):
                existing = session.query(Homework).filter_by(
                    source_id=homework_data['source_id']
                ).first()
                
                if existing:
                    # Update existing homework
                    for key, value in homework_data.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    existing.scraped_at = datetime.utcnow()
                    session.flush()
                    return existing
            
            # Create new homework
            homework = Homework(**homework_data)
            session.add(homework)
            session.flush()
            return homework
    
    def get_homework_by_date(self, target_date: date) -> List[Homework]:
        """Get homework due on a specific date."""
        with self.get_session() as session:
            return session.query(Homework).filter_by(
                due_date=target_date
            ).order_by(Homework.subject).all()
    
    def get_homework_today(self) -> List[Homework]:
        """Get homework due today."""
        return self.get_homework_by_date(date.today())
    
    def get_homework_range(self, start_date: date, end_date: date) -> List[Homework]:
        """Get homework within a date range."""
        with self.get_session() as session:
            return session.query(Homework).filter(
                and_(
                    Homework.due_date >= start_date,
                    Homework.due_date <= end_date
                )
            ).order_by(Homework.due_date, Homework.subject).all()
    
    def get_upcoming_homework(self, days: int = 7) -> List[Homework]:
        """Get homework due in the next N days."""
        today = date.today()
        end_date = today + timedelta(days=days)
        return self.get_homework_range(today, end_date)
    
    def get_homework_by_subject(self, subject: str) -> List[Homework]:
        """Get all homework for a specific subject."""
        with self.get_session() as session:
            return session.query(Homework).filter(
                Homework.subject.ilike(f'%{subject}%')
            ).order_by(Homework.due_date).all()
    
    def mark_completed(self, homework_id: int, completed: bool = True):
        """Mark homework as completed or incomplete."""
        with self.get_session() as session:
            homework = session.query(Homework).get(homework_id)
            if homework:
                homework.is_completed = completed
                homework.updated_at = datetime.utcnow()
    
    def log_scraping(self, status: str, items_scraped: int = 0, 
                    error_message: Optional[str] = None, 
                    duration_seconds: Optional[int] = None):
        """Log a scraping attempt."""
        with self.get_session() as session:
            log = ScrapingLog(
                status=status,
                items_scraped=items_scraped,
                error_message=error_message,
                duration_seconds=duration_seconds
            )
            session.add(log)
    
    def get_recent_logs(self, limit: int = 10) -> List[ScrapingLog]:
        """Get recent scraping logs."""
        with self.get_session() as session:
            return session.query(ScrapingLog).order_by(
                ScrapingLog.timestamp.desc()
            ).limit(limit).all()
    
    def clear_all_homework(self):
        """Clear all homework from database (for testing)."""
        with self.get_session() as session:
            session.query(Homework).delete()
            print("✓ All homework cleared")