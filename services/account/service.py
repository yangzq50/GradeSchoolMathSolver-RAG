"""
Account Service
Manages user accounts and statistics using centralized database service
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from config import Config
from models import UserStats
from services.database import get_database_service


class AccountService:
    """
    Service for managing user accounts and statistics

    This service handles:
    - User creation and management
    - Answer history tracking
    - Performance statistics calculation
    - Database connection management through DatabaseService

    Attributes:
        config: Configuration object
        db: DatabaseService instance for data operations
        users_index: Name of the users index
        answers_index: Name of the answers index
    """

    def __init__(self):
        self.config = Config()
        self.users_index = "users"
        self.answers_index = self.config.ELASTICSEARCH_INDEX
        self.db = get_database_service()
        self._create_indices()

    def _is_connected(self) -> bool:
        """
        Check if database is connected

        Returns:
            bool: True if connected, False otherwise
        """
        return self.db.is_connected()

    def _create_indices(self):
        """
        Create database indices with appropriate mappings

        Defines schema for efficient storage and retrieval of user data and answer history.
        """
        # Users index mapping
        users_mapping = {
            "mappings": {
                "properties": {
                    "username": {"type": "keyword"},
                    "created_at": {"type": "date"}
                }
            }
        }

        # Answer history index mapping (unified schema)
        answers_mapping = {
            "mappings": {
                "properties": {
                    "username": {"type": "keyword"},
                    "question": {"type": "text"},
                    "equation": {"type": "text"},
                    "user_answer": {"type": "integer"},
                    "correct_answer": {"type": "integer"},
                    "is_correct": {"type": "boolean"},
                    "category": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "reviewed": {"type": "boolean"}
                }
            }
        }

        # Create indices using database service
        self.db.create_index(self.users_index, users_mapping)
        self.db.create_index(self.answers_index, answers_mapping)

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

        if not self._is_connected():
            print("Database not connected")
            return False

        try:
            # Create user document (will fail if user already exists)
            doc = {
                "username": username,
                "created_at": datetime.utcnow().isoformat()
            }

            # Use create_document() which ensures it fails if user exists
            return self.db.create_document(self.users_index, username, doc)
        except Exception as e:
            print(f"Unexpected error creating user: {e}")
            return False

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username

        Args:
            username: Username to retrieve

        Returns:
            User document dict or None if not found
        """
        if not self._validate_username(username):
            return None

        if not self._is_connected():
            return None

        return self.db.get_document(self.users_index, username)

    def list_users(self) -> List[str]:
        """
        Get list of all usernames

        Returns:
            List of usernames, empty list on error
        """
        if not self._is_connected():
            return []

        try:
            results = self.db.search_documents(
                index_name=self.users_index,
                size=1000
            )
            users = [hit['_source']['username'] for hit in results]
            return users
        except Exception as e:
            print(f"Error listing users: {e}")
            return []

    def record_answer(self, username: str, question: str, equation: str,
                      user_answer: Optional[int], correct_answer: int,
                      category: str, refresh: bool = False) -> bool:
        """
        Record a user's answer with validation

        Args:
            username: Username
            question: Question text (max 500 chars)
            equation: Equation (max 200 chars)
            user_answer: User's answer
            correct_answer: Correct answer
            category: Question category (max 50 chars)
            refresh: Whether to refresh the index immediately (for testing)

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

        if not self._is_connected():
            print("Database not connected")
            return False

        try:
            # Ensure user exists
            if not self.get_user(username):
                self.create_user(username)

            is_correct = user_answer is not None and user_answer == correct_answer

            doc = {
                "username": username,
                "question": question,
                "equation": equation,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "category": category,
                "timestamp": datetime.utcnow().isoformat(),
                "reviewed": False
            }

            doc_id = self.db.index_document(self.answers_index, doc)

            # Refresh index if requested (useful for testing)
            if refresh and doc_id:
                from services.database.elasticsearch_backend import ElasticsearchDatabaseService
                if isinstance(self.db, ElasticsearchDatabaseService):
                    self.db.refresh_index(self.answers_index)

            return doc_id is not None
        except Exception as e:
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

        if not self._is_connected():
            return None

        try:
            user = self.get_user(username)
            if not user:
                return None

            # Get all answers for the user
            query = {"term": {"username": username}}
            sort = [{"timestamp": {"order": "desc"}}]

            all_answers = self.db.search_documents(
                index_name=self.answers_index,
                query=query,
                sort=sort,
                size=10000
            )

            if not all_answers:
                return UserStats(
                    username=username,
                    total_questions=0,
                    correct_answers=0,
                    overall_correctness=0.0,
                    recent_100_score=0.0
                )

            total_questions = len(all_answers)
            correct_answers = sum(1 for hit in all_answers if hit['_source'].get('is_correct', False))
            overall_correctness = (correct_answers / total_questions) * 100 if total_questions > 0 else 0.0

            # Get recent 100 answers
            recent_answers = all_answers[:100]
            recent_correct = sum(1 for hit in recent_answers if hit['_source'].get('is_correct', False))
            recent_100_score = (recent_correct / len(recent_answers)) * 100 if recent_answers else 0.0

            return UserStats(
                username=username,
                total_questions=total_questions,
                correct_answers=correct_answers,
                overall_correctness=round(overall_correctness, 2),
                recent_100_score=round(recent_100_score, 2)
            )
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return None

    def get_answer_history(self, username: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get answer history for a user

        Args:
            username: Username
            limit: Maximum number of records to return (1-1000)

        Returns:
            List of answer history dicts, empty list on error
        """
        if not self._validate_username(username):
            return []

        if not self._is_connected():
            return []

        # Validate limit
        limit = max(1, min(limit, 1000))

        try:
            query = {"term": {"username": username}}
            sort = [{"timestamp": {"order": "desc"}}]

            hits = self.db.search_documents(
                index_name=self.answers_index,
                query=query,
                sort=sort,
                size=limit
            )

            # Convert to list of dicts with id included and timestamp parsed
            results = []
            for hit in hits:
                answer = hit['_source'].copy()
                answer['id'] = hit['_id']

                # Convert timestamp string to datetime object for template compatibility
                if 'timestamp' in answer and isinstance(answer['timestamp'], str):
                    try:
                        answer['timestamp'] = datetime.fromisoformat(answer['timestamp'].replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        # If parsing fails, keep as string or use current time
                        answer['timestamp'] = datetime.utcnow()

                results.append(answer)

            return results
        except Exception as e:
            print(f"Error getting answer history: {e}")
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
