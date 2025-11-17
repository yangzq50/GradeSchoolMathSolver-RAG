"""
Account Service
Manages user accounts and statistics using Elasticsearch with proper error handling and validation
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from elasticsearch import Elasticsearch, ConnectionError as ESConnectionError, NotFoundError
from config import Config
from models import UserStats


class AccountService:
    """
    Service for managing user accounts and statistics

    This service handles:
    - User creation and management
    - Answer history tracking
    - Performance statistics calculation
    - Elasticsearch connection management

    Attributes:
        config: Configuration object
        es: Elasticsearch client (None if disconnected)
        users_index: Name of the Elasticsearch users index
        answers_index: Name of the Elasticsearch answers index
    """

    def __init__(self):
        self.config = Config()
        self.users_index = "users"
        self.answers_index = self.config.ELASTICSEARCH_INDEX
        self.es: Optional[Elasticsearch] = None
        self._connect()

    def _connect(self):
        """
        Connect to Elasticsearch and create indices if needed
        
        Gracefully handles connection failures by operating in limited mode.
        """
        try:
            self.es = Elasticsearch(
                [{'host': self.config.ELASTICSEARCH_HOST,
                  'port': self.config.ELASTICSEARCH_PORT,
                  'scheme': 'http'}],
                basic_auth=None,
                verify_certs=False,
                request_timeout=10,
                max_retries=3,
                retry_on_timeout=True
            )

            # Verify connection
            if not self.es.ping():
                print("Warning: Elasticsearch ping failed")
                self.es = None
                return

            # Create indices if they don't exist
            self._create_indices()
        except ESConnectionError as e:
            print(f"Warning: Could not connect to Elasticsearch: {e}")
            print("Account service will operate in limited mode")
            self.es = None
        except Exception as e:
            print(f"Warning: Unexpected error connecting to Elasticsearch: {e}")
            print("Account service will operate in limited mode")
            self.es = None

    def _create_indices(self):
        """
        Create Elasticsearch indices with appropriate mappings
        
        Defines schema for efficient storage and retrieval of user data and answer history.
        """
        if not self.es:
            return

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

        try:
            # Create users index
            if not self.es.indices.exists(index=self.users_index):
                self.es.indices.create(index=self.users_index, body=users_mapping)
                print(f"Created Elasticsearch index: {self.users_index}")
        except Exception as e:
            print(f"Error creating users index (may already exist): {e}")

        try:
            # Create answers index
            if not self.es.indices.exists(index=self.answers_index):
                self.es.indices.create(index=self.answers_index, body=answers_mapping)
                print(f"Created Elasticsearch index: {self.answers_index}")
        except Exception as e:
            print(f"Error creating answers index (may already exist): {e}")

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

        if not self.es:
            print("Elasticsearch not connected")
            return False

        try:
            # Check if user already exists
            existing = self.get_user(username)
            if existing:
                return False

            # Create user document
            doc = {
                "username": username,
                "created_at": datetime.utcnow().isoformat()
            }

            self.es.index(index=self.users_index, id=username, document=doc)
            return True
        except ESConnectionError as e:
            print(f"Connection error creating user: {e}")
            return False
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
            
        if not self.es:
            return None
            
        try:
            result = self.es.get(index=self.users_index, id=username)
            return result['_source']
        except NotFoundError:
            return None
        except ESConnectionError as e:
            print(f"Connection error retrieving user: {e}")
            return None
        except Exception as e:
            print(f"Error retrieving user: {e}")
            return None

    def list_users(self) -> List[str]:
        """
        Get list of all usernames

        Returns:
            List of usernames, empty list on error
        """
        if not self.es:
            return []
            
        try:
            # Use scroll API for potentially large result sets
            query = {
                "size": 1000,
                "query": {"match_all": {}},
                "_source": ["username"]
            }
            
            response = self.es.search(index=self.users_index, body=query)
            users = [hit['_source']['username'] for hit in response['hits']['hits']]
            return users
        except ESConnectionError as e:
            print(f"Connection error listing users: {e}")
            return []
        except Exception as e:
            print(f"Error listing users: {e}")
            return []

    def record_answer(self, username: str, question: str, equation: str,
                      user_answer: Optional[int], correct_answer: int,
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

        if not self.es:
            print("Elasticsearch not connected")
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

            self.es.index(index=self.answers_index, document=doc)
            return True
        except ESConnectionError as e:
            print(f"Connection error recording answer: {e}")
            return False
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

        if not self.es:
            return None

        try:
            user = self.get_user(username)
            if not user:
                return None

            # Get all answers for the user
            query = {
                "size": 10000,  # Large limit to get all answers
                "query": {
                    "term": {"username": username}
                },
                "sort": [{"timestamp": {"order": "desc"}}]
            }

            response = self.es.search(index=self.answers_index, body=query)
            all_answers = response['hits']['hits']

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
        except ESConnectionError as e:
            print(f"Connection error getting user stats: {e}")
            return None
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

        if not self.es:
            return []

        # Validate limit
        limit = max(1, min(limit, 1000))

        try:
            query = {
                "size": limit,
                "query": {
                    "term": {"username": username}
                },
                "sort": [{"timestamp": {"order": "desc"}}]
            }

            response = self.es.search(index=self.answers_index, body=query)
            
            # Convert to list of dicts with id included
            results = []
            for hit in response['hits']['hits']:
                answer = hit['_source'].copy()
                answer['id'] = hit['_id']
                results.append(answer)
            
            return results
        except ESConnectionError as e:
            print(f"Connection error getting answer history: {e}")
            return []
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
