"""
Quiz History Service
Manages quiz history using centralized database service for RAG (Retrieval-Augmented Generation)

This service provides:
- Storage of question-answer pairs with vector embeddings
- Similarity-based search for relevant historical questions
- User history retrieval
- Graceful degradation when database is unavailable

Embedding Generation:
All embedding generation and storage is handled by the database service.
This service does NOT know or care about:
- Which database backend is being used (MariaDB, Elasticsearch, etc.)
- How embeddings are generated or stored
- Source-to-embedding column mapping

The database service determines everything from config.py:
- EMBEDDING_SOURCE_COLUMNS: Which columns to use as embedding sources
- EMBEDDING_COLUMN_NAMES: Names for embedding columns
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from gradeschoolmathsolver.config import Config
from gradeschoolmathsolver.models import QuizHistory
from gradeschoolmathsolver.services.database import get_database_service


class QuizHistoryService:
    """
    Service for managing quiz history with centralized database service

    This service handles quiz history storage and retrieval for RAG functionality.
    It gracefully degrades to limited mode when database is unavailable.

    Embedding Support:
    All embedding operations are handled internally by the database service.
    This service does NOT provide source texts or embedding configuration -
    the database service determines everything from config.py.

    Attributes:
        config: Configuration object
        index_name: Name of the database index
        db: DatabaseService instance for data operations
    """

    def __init__(self) -> None:
        self.config = Config()
        self.index_name = self.config.ELASTICSEARCH_INDEX
        self.db = get_database_service()
        self._create_index()

    def _create_index(self) -> None:
        """
        Create database index with appropriate mappings including embedding columns

        Uses the centralized database service to create the collection with
        appropriate embedding support based on the backend.
        """
        # Use database service to create quiz history collection with embeddings
        self.db.create_quiz_history_collection(self.index_name, include_embeddings=True)

    def add_history(self, history: QuizHistory) -> bool:
        """
        Add a quiz history record to database with vector embeddings

        The database service handles all embedding generation and storage internally.
        It determines source columns from EMBEDDING_SOURCE_COLUMNS config and
        generates embeddings automatically.

        Args:
            history: QuizHistory object to store

        Returns:
            True if successful, False if database unavailable or error occurs

        Raises:
            RuntimeError: Propagated from database service if embedding generation fails
        """
        if not self.db.is_connected():
            return False

        try:
            # Build the document
            # The database service will generate embeddings from source columns
            # as configured in EMBEDDING_SOURCE_COLUMNS (e.g., 'question', 'equation')
            doc: Dict[str, Any] = {
                "username": history.username,
                "question": history.question,
                "equation": history.user_equation,
                "user_equation": history.user_equation,
                "user_answer": history.user_answer,
                "correct_answer": history.correct_answer,
                "is_correct": history.is_correct,
                "category": history.category,
                "timestamp": history.timestamp.isoformat(),
                "reviewed": False
            }

            # Database service handles all embedding generation internally
            # No record_id or source_texts parameters needed - database decides everything
            doc_id = self.db.insert_record(self.index_name, doc)

            return doc_id is not None
        except RuntimeError as e:
            # Embedding generation or insertion failed - propagate with error logging
            print(f"ERROR: Failed to add history: {e}")
            raise
        except Exception as e:
            print(f"ERROR: Failed to add history: {e}")
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
                collection_name=self.index_name,
                query=query,
                sort=sort,
                limit=top_k
            )

            return self._format_search_results(hits)
        except Exception as e:
            print(f"Error searching history: {e}")
            return []

    def _format_search_results(self, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format search hits into result dictionaries."""
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
                collection_name=self.index_name,
                query=query,
                sort=sort,
                limit=limit
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
        return bool(self.db.is_connected())


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
