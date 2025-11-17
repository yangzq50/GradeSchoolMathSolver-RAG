"""
Quiz History Service
Manages quiz history using centralized database service for RAG (Retrieval-Augmented Generation)

This service provides:
- Storage of question-answer pairs
- Similarity-based search for relevant historical questions
- User history retrieval
- Graceful degradation when database is unavailable
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from config import Config
from models import QuizHistory
from services.database import get_database_service


class QuizHistoryService:
    """
    Service for managing quiz history with centralized database service

    This service handles quiz history storage and retrieval for RAG functionality.
    It gracefully degrades to limited mode when database is unavailable.

    Attributes:
        config: Configuration object
        index_name: Name of the database index
        db: DatabaseService instance for data operations
    """

    def __init__(self):
        self.config = Config()
        self.index_name = self.config.ELASTICSEARCH_INDEX
        self.db = get_database_service()
        self._create_index()

    def _create_index(self):
        """
        Create database index with appropriate mappings

        Defines unified schema for efficient storage and retrieval of quiz history.
        """
        mapping = {
            "mappings": {
                "properties": {
                    "username": {"type": "keyword"},
                    "question": {"type": "text"},
                    "equation": {"type": "text"},
                    "user_equation": {"type": "text"},  # Alias for equation (backward compatibility)
                    "user_answer": {"type": "integer"},
                    "correct_answer": {"type": "integer"},
                    "is_correct": {"type": "boolean"},
                    "category": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "reviewed": {"type": "boolean"}
                }
            }
        }

        self.db.create_collection(self.index_name, mapping)

    def add_history(self, history: QuizHistory) -> bool:
        """
        Add a quiz history record to database

        Args:
            history: QuizHistory object to store

        Returns:
            True if successful, False if database unavailable or error occurs
        """
        if not self.db.is_connected():
            return False

        try:
            doc = {
                "username": history.username,
                "question": history.question,
                "equation": history.user_equation,  # Store as equation
                "user_equation": history.user_equation,  # Keep for backward compatibility
                "user_answer": history.user_answer,
                "correct_answer": history.correct_answer,
                "is_correct": history.is_correct,
                "category": history.category,
                "timestamp": history.timestamp.isoformat(),
                "reviewed": False  # Default value for new records
            }

            doc_id = self.db.insert_record(self.index_name, doc)
            return doc_id is not None
        except Exception as e:
            print(f"Error adding history: {e}")
            return False

    def search_relevant_history(self, username: str, question: str,
                                category: Optional[str] = None,
                                top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant quiz history using semantic similarity

        Uses database text matching to find similar questions from
        the user's history, optionally filtered by category.

        Args:
            username: Username to search for
            question: Question text for similarity search
            category: Optional category filter
            top_k: Number of results to return (1-20)

        Returns:
            List of relevant history records with scores, empty if unavailable
        """
        if not self.db.is_connected():
            return []

        # Validate and clamp top_k
        top_k = max(1, min(top_k, 20))

        try:
            # Build query - this is Elasticsearch-specific but abstracted in the future
            must_clauses = [
                {"match": {"username": username}}
            ]

            should_clauses = [
                {"match": {"question": {"query": question, "boost": 2}}},
                {"match": {"user_equation": question}}
            ]

            if category:
                must_clauses.append({"term": {"category": category}})

            query = {
                "bool": {
                    "must": must_clauses,
                    "should": should_clauses
                }
            }

            sort = [
                {"_score": {"order": "desc"}},
                {"timestamp": {"order": "desc"}}
            ]

            # Use database service search
            hits = self.db.search_records(
                index_name=self.index_name,
                query=query,
                sort=sort,
                size=top_k
            )

            results = []
            for hit in hits:
                source = hit['_source']
                results.append({
                    'question': source.get('question'),
                    'user_equation': source.get('user_equation'),
                    'user_answer': source.get('user_answer'),
                    'correct_answer': source.get('correct_answer'),
                    'is_correct': source.get('is_correct'),
                    'category': source.get('category'),
                    'timestamp': source.get('timestamp'),
                    'score': hit.get('_score', 0)
                })

            return results
        except Exception as e:
            print(f"Error searching history: {e}")
            return []

    def get_user_history(self, username: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all history for a user

        Args:
            username: Username to retrieve history for
            limit: Maximum number of records (1-1000)

        Returns:
            List of history records sorted by timestamp, empty if unavailable
        """
        if not self.db.is_connected():
            return []

        # Validate and clamp limit
        limit = max(1, min(limit, 1000))

        try:
            query = {"match": {"username": username}}
            sort = [{"timestamp": {"order": "desc"}}]

            hits = self.db.search_records(
                index_name=self.index_name,
                query=query,
                sort=sort,
                size=limit
            )

            results = []
            for hit in hits:
                source = hit['_source']
                results.append(source)

            return results
        except Exception as e:
            print(f"Error getting user history: {e}")
            return []

    def is_connected(self) -> bool:
        """
        Check if database is connected and responsive

        Returns:
            True if connected and responsive, False otherwise
        """
        return self.db.is_connected()


if __name__ == "__main__":
    # Test the service
    service = QuizHistoryService()

    if service.is_connected():
        print("Connected to Elasticsearch")

        # Add test history
        history = QuizHistory(
            username="test_user",
            question="What is 5 + 3?",
            user_equation="5 + 3",
            user_answer=8,
            correct_answer=8,
            is_correct=True,
            category="addition",
            timestamp=datetime.now()
        )

        service.add_history(history)
        print("Added test history")

        # Search
        results = service.search_relevant_history(
            "test_user",
            "What is 6 + 2?",
            top_k=3
        )
        print(f"Found {len(results)} relevant records")
    else:
        print("Not connected to Elasticsearch - service in limited mode")
