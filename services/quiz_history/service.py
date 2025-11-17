"""
Quiz History Service
Manages quiz history using Elasticsearch for RAG (Retrieval-Augmented Generation)

This service provides:
- Storage of question-answer pairs in Elasticsearch
- Similarity-based search for relevant historical questions
- User history retrieval
- Graceful degradation when Elasticsearch is unavailable
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from elasticsearch import Elasticsearch, ConnectionError as ESConnectionError
from config import Config
from models import QuizHistory


class QuizHistoryService:
    """
    Service for managing quiz history with Elasticsearch

    This service handles quiz history storage and retrieval for RAG functionality.
    It gracefully degrades to limited mode when Elasticsearch is unavailable.

    Attributes:
        config: Configuration object
        index_name: Name of the Elasticsearch index
        es: Elasticsearch client (None if disconnected)
    """

    def __init__(self):
        self.config = Config()
        self.index_name = self.config.ELASTICSEARCH_INDEX
        self.es: Optional[Elasticsearch] = None
        self._connect()

    def _connect(self):
        """
        Connect to Elasticsearch and create index if needed

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

            # Create index if it doesn't exist
            if not self.es.indices.exists(index=self.index_name):
                self._create_index()
        except ESConnectionError as e:
            print(f"Warning: Could not connect to Elasticsearch: {e}")
            print("Quiz history service will operate in limited mode")
            self.es = None
        except Exception as e:
            print(f"Warning: Unexpected error connecting to Elasticsearch: {e}")
            print("Quiz history service will operate in limited mode")
            self.es = None

    def _create_index(self):
        """
        Create Elasticsearch index with appropriate mappings

        Defines schema for efficient storage and retrieval of quiz history.
        """
        if not self.es:
            return

        mapping = {
            "mappings": {
                "properties": {
                    "username": {"type": "keyword"},
                    "question": {"type": "text"},
                    "user_equation": {"type": "text"},
                    "user_answer": {"type": "integer"},
                    "correct_answer": {"type": "integer"},
                    "is_correct": {"type": "boolean"},
                    "category": {"type": "keyword"},
                    "timestamp": {"type": "date"}
                }
            }
        }

        try:
            self.es.indices.create(index=self.index_name, body=mapping)
            print(f"Created Elasticsearch index: {self.index_name}")
        except Exception as e:
            print(f"Error creating index (may already exist): {e}")

    def add_history(self, history: QuizHistory) -> bool:
        """
        Add a quiz history record to Elasticsearch

        Args:
            history: QuizHistory object to store

        Returns:
            True if successful, False if Elasticsearch unavailable or error occurs
        """
        if not self.es:
            return False

        try:
            doc = {
                "username": history.username,
                "question": history.question,
                "user_equation": history.user_equation,
                "user_answer": history.user_answer,
                "correct_answer": history.correct_answer,
                "is_correct": history.is_correct,
                "category": history.category,
                "timestamp": history.timestamp.isoformat()
            }

            self.es.index(index=self.index_name, document=doc)
            return True
        except ESConnectionError as e:
            print(f"Connection error adding history: {e}")
            return False
        except Exception as e:
            print(f"Error adding history: {e}")
            return False

    def search_relevant_history(self, username: str, question: str,
                                category: Optional[str] = None,
                                top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant quiz history using semantic similarity

        Uses Elasticsearch's text matching to find similar questions from
        the user's history, optionally filtered by category.

        Args:
            username: Username to search for
            question: Question text for similarity search
            category: Optional category filter
            top_k: Number of results to return (1-20)

        Returns:
            List of relevant history records with scores, empty if unavailable
        """
        if not self.es:
            return []

        # Validate and clamp top_k
        top_k = max(1, min(top_k, 20))

        try:
            # Build query
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
                "size": top_k,
                "query": {
                    "bool": {
                        "must": must_clauses,
                        "should": should_clauses
                    }
                },
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"timestamp": {"order": "desc"}}
                ]
            }

            response = self.es.search(index=self.index_name, body=query)

            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                results.append({
                    'question': source.get('question'),
                    'user_equation': source.get('user_equation'),
                    'user_answer': source.get('user_answer'),
                    'correct_answer': source.get('correct_answer'),
                    'is_correct': source.get('is_correct'),
                    'category': source.get('category'),
                    'timestamp': source.get('timestamp'),
                    'score': hit['_score']
                })

            return results
        except ESConnectionError as e:
            print(f"Connection error searching history: {e}")
            return []
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
        if not self.es:
            return []

        # Validate and clamp limit
        limit = max(1, min(limit, 1000))

        try:
            query = {
                "size": limit,
                "query": {
                    "match": {"username": username}
                },
                "sort": [
                    {"timestamp": {"order": "desc"}}
                ]
            }

            response = self.es.search(index=self.index_name, body=query)

            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                results.append(source)

            return results
        except ESConnectionError as e:
            print(f"Connection error getting user history: {e}")
            return []
        except Exception as e:
            print(f"Error getting user history: {e}")
            return []

    def is_connected(self) -> bool:
        """
        Check if Elasticsearch is connected and responsive

        Returns:
            True if connected and responsive, False otherwise
        """
        try:
            return self.es is not None and self.es.ping()
        except Exception:
            return False


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
