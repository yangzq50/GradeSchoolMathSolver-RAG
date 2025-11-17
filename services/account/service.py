"""
Account Service
Manages user accounts and statistics using SQLite with proper error handling and validation
"""
import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config import Config
from models import UserStats

Base = declarative_base()


class User(Base):  # type: ignore[valid-type,misc]
    """User account table"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnswerHistory(Base):  # type: ignore[valid-type,misc]
    """Answer history table"""
    __tablename__ = 'answer_history'

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    question = Column(String(500), nullable=False)
    equation = Column(String(200), nullable=False)
    user_answer = Column(Integer, nullable=False)
    correct_answer = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    category = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    reviewed = Column(Boolean, default=False, nullable=False)


class AccountService:
    """
    Service for managing user accounts and statistics

    This service handles:
    - User creation and management
    - Answer history tracking
    - Performance statistics calculation
    - Database connection management

    Attributes:
        config: Configuration object
        engine: SQLAlchemy database engine
        session: SQLAlchemy database session
    """

    def __init__(self):
        self.config = Config()
        self._setup_database()

    def _setup_database(self):
        """Initialize database connection and create tables"""
        # Ensure data directory exists
        db_dir = os.path.dirname(self.config.DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        # Create engine and tables
        self.engine = create_engine(f'sqlite:///{self.config.DATABASE_PATH}')
        Base.metadata.create_all(self.engine)

        # Create session maker
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def _validate_username(self, username: str) -> bool:
        """
        Validate username format

        Args:
            username: Username to validate

        Returns:
            True if valid, False otherwise
        """
        if not username or not isinstance(username, str):
            return False
        # Allow alphanumeric, underscores, hyphens, max 100 chars
        if len(username) > 100:
            return False
        return username.replace('_', '').replace('-', '').isalnum()

    def create_user(self, username: str) -> bool:
        """
        Create a new user account with validation

        Args:
            username: Username to create (alphanumeric, underscore, hyphen only)

        Returns:
            True if successful, False if user already exists or validation fails
        """
        if not self._validate_username(username):
            print(f"Invalid username format: {username}")
            return False

        try:
            existing = self.session.query(User).filter_by(username=username).first()
            if existing:
                return False

            user = User(username=username)
            self.session.add(user)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Database error creating user: {e}")
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Unexpected error creating user: {e}")
            return False

    def get_user(self, username: str) -> Optional[User]:
        """
        Get user by username

        Args:
            username: Username to retrieve

        Returns:
            User object or None if not found
        """
        if not self._validate_username(username):
            return None
        try:
            return self.session.query(User).filter_by(username=username).first()
        except SQLAlchemyError as e:
            print(f"Database error retrieving user: {e}")
            return None

    def list_users(self) -> List[str]:
        """
        Get list of all usernames

        Returns:
            List of usernames, empty list on error
        """
        try:
            users = self.session.query(User).all()
            return [user.username for user in users]
        except SQLAlchemyError as e:
            print(f"Database error listing users: {e}")
            return []

    def record_answer(self, username: str, question: str, equation: str,
                      user_answer: int, correct_answer: int,
                      category: str) -> bool:
        """
        Record a user's answer with validation

        Args:
            username: Username
            question: Question text (max 500 chars)
            equation: Equation (max 200 chars)
            user_answer: User's answer
            correct_answer: Correct answer
            category: Question category (max 50 chars)

        Returns:
            True if successful, False otherwise
        """
        # Validate inputs
        if not self._validate_username(username):
            print(f"Invalid username: {username}")
            return False
        if not question or len(question) > 500:
            print("Invalid question length")
            return False
        if not equation or len(equation) > 200:
            print("Invalid equation length")
            return False
        if not category or len(category) > 50:
            print("Invalid category length")
            return False

        try:
            # Ensure user exists
            if not self.get_user(username):
                self.create_user(username)

            is_correct = user_answer == correct_answer

            answer = AnswerHistory(
                username=username,
                question=question,
                equation=equation,
                user_answer=user_answer,
                correct_answer=correct_answer,
                is_correct=is_correct,
                category=category
            )

            self.session.add(answer)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Database error recording answer: {e}")
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Unexpected error recording answer: {e}")
            return False

    def get_user_stats(self, username: str) -> Optional[UserStats]:
        """
        Get statistics for a user

        Args:
            username: Username

        Returns:
            UserStats object or None if user doesn't exist or error occurs
        """
        if not self._validate_username(username):
            return None

        try:
            user = self.get_user(username)
            if not user:
                return None

            # Get all answers
            all_answers = self.session.query(AnswerHistory).filter_by(username=username).all()

            if not all_answers:
                return UserStats(
                    username=username,
                    total_questions=0,
                    correct_answers=0,
                    overall_correctness=0.0,
                    recent_100_score=0.0
                )

            total_questions = len(all_answers)
            correct_answers = sum(1 for a in all_answers if a.is_correct)
            overall_correctness = (correct_answers / total_questions) * 100 if total_questions > 0 else 0.0

            # Get recent 100 answers
            recent_answers = self.session.query(AnswerHistory)\
                .filter_by(username=username)\
                .order_by(AnswerHistory.timestamp.desc())\
                .limit(100)\
                .all()

            recent_correct = sum(1 for a in recent_answers if a.is_correct)
            recent_100_score = (recent_correct / len(recent_answers)) * 100 if recent_answers else 0.0

            return UserStats(
                username=username,
                total_questions=total_questions,
                correct_answers=correct_answers,
                overall_correctness=round(overall_correctness, 2),
                recent_100_score=round(recent_100_score, 2)
            )
        except SQLAlchemyError as e:
            print(f"Database error getting user stats: {e}")
            return None

    def get_answer_history(self, username: str, limit: int = 100) -> List[AnswerHistory]:
        """
        Get answer history for a user

        Args:
            username: Username
            limit: Maximum number of records to return (1-1000)

        Returns:
            List of AnswerHistory objects, empty list on error
        """
        if not self._validate_username(username):
            return []

        # Validate limit
        limit = max(1, min(limit, 1000))

        try:
            return self.session.query(AnswerHistory)\
                .filter_by(username=username)\
                .order_by(AnswerHistory.timestamp.desc())\
                .limit(limit)\
                .all()
        except SQLAlchemyError as e:
            print(f"Database error getting answer history: {e}")
            return []


if __name__ == "__main__":
    # Test the service
    service = AccountService()

    # Create test user
    username = "test_user"
    service.create_user(username)

    # Record some answers
    service.record_answer(username, "What is 2 + 2?", "2 + 2", 4, 4, "addition")
    service.record_answer(username, "What is 5 - 3?", "5 - 3", 2, 2, "subtraction")
    service.record_answer(username, "What is 3 * 4?", "3 * 4", 11, 12, "multiplication")

    # Get stats
    stats = service.get_user_stats(username)
    if stats:
        print(f"User: {stats.username}")
        print(f"Total: {stats.total_questions}, Correct: {stats.correct_answers}")
        print(f"Overall: {stats.overall_correctness}%, Recent 100: {stats.recent_100_score}%")
