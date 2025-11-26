"""
Quiz History Service
Manages quiz history using centralized database service for RAG (Retrieval-Augmented Generation)

This service provides:
- Storage of question-answer pairs with vector embeddings
- Similarity-based search for relevant historical questions
- User history retrieval
- Graceful degradation when database is unavailable

Embedding Generation:
The service generates embeddings for configured source columns (e.g., 'question', 'equation')
and stores them in corresponding embedding columns for vector similarity search.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from gradeschoolmathsolver.config import Config
from gradeschoolmathsolver.models import QuizHistory
from gradeschoolmathsolver.services.database import get_database_service
from gradeschoolmathsolver.services.database.schemas import (
    get_answer_history_schema_for_backend,
    get_embedding_source_mapping
)


class QuizHistoryService:
    """
    Service for managing quiz history with centralized database service

    This service handles quiz history storage and retrieval for RAG functionality.
    It gracefully degrades to limited mode when database is unavailable.

    Embedding Support:
    The service automatically generates embeddings for source text columns
    (configured via EMBEDDING_SOURCE_COLUMNS) when adding history records.
    These embeddings enable vector similarity search for RAG.

    Attributes:
        config: Configuration object
        index_name: Name of the database index
        db: DatabaseService instance for data operations
        embedding_service: EmbeddingService for generating vector embeddings
        source_to_embedding_map: Mapping from source columns to embedding columns
    """

    def __init__(self):
        self.config = Config()
        self.index_name = self.config.ELASTICSEARCH_INDEX
        self.db = get_database_service()
        self.embedding_service = None
        self.source_to_embedding_map = get_embedding_source_mapping()
        self._create_index()

    def _get_embedding_service(self):
        """
        Lazy-load the embedding service to avoid circular imports
        and allow graceful degradation when service is unavailable.

        Returns:
            EmbeddingService instance or None if unavailable
        """
        if self.embedding_service is None:
            try:
                from gradeschoolmathsolver.services.embedding import EmbeddingService
                self.embedding_service = EmbeddingService()
            except Exception as e:
                print(f"Warning: Could not initialize embedding service: {e}")
                return None
        return self.embedding_service

    def _create_index(self):
        """
        Create database index with appropriate mappings including embedding columns

        Uses the centralized schema definition from schemas.py which includes
        both standard fields and embedding columns for vector search.
        """
        # Get the full schema with embeddings for the configured backend
        schema = get_answer_history_schema_for_backend(
            self.config.DATABASE_BACKEND,
            include_embeddings=True
        )

        self.db.create_collection(self.index_name, schema)

    def add_history(self, history: QuizHistory) -> bool:
        """
        Add a quiz history record to database with vector embeddings

        This method generates embeddings from configured source text columns
        (e.g., 'question' and 'equation') and stores them in the corresponding
        embedding columns for vector similarity search.

        The source-to-embedding mapping is configured via:
        - EMBEDDING_SOURCE_COLUMNS: Source text columns (default: 'question,equation')
        - EMBEDDING_COLUMN_NAMES: Embedding columns (default: 'question_embedding,equation_embedding')

        Args:
            history: QuizHistory object to store

        Returns:
            True if successful, False if database unavailable or error occurs
        """
        if not self.db.is_connected():
            return False

        try:
            # Build the base document
            doc: Dict[str, Any] = {
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

            # Generate embeddings for configured source columns
            self._add_embeddings_to_doc(doc, history)

            doc_id = self.db.insert_record(self.index_name, doc)
            return doc_id is not None
        except Exception as e:
            print(f"Error adding history: {e}")
            return False

    def _add_embeddings_to_doc(self, doc: Dict[str, Any], history: QuizHistory) -> None:
        """
        Generate and add embeddings to the document from source columns.

        Extracts text from source columns specified in configuration,
        generates embeddings using the embedding service, and adds
        them to the document for vector similarity search.

        Args:
            doc: Document dictionary to add embeddings to (modified in-place)
            history: QuizHistory object containing source text data

        Note:
            If the embedding service is unavailable or generation fails,
            the embeddings are set to zero vectors to maintain schema compatibility
            with NOT NULL constraints on VECTOR columns.
        """
        embedding_service = self._get_embedding_service()

        # Map source column names to their values from the history object
        # Note: 'equation' and 'user_equation' both map to the same value for
        # backward compatibility (user_equation is the legacy field name)
        source_values = {
            'question': history.question,
            'equation': history.user_equation,
        }

        # Get embedding config once before the loop for efficiency
        from gradeschoolmathsolver.services.database.schemas import get_embedding_config
        embedding_config = get_embedding_config()
        col_names = embedding_config['column_names']
        dimensions = embedding_config['dimensions']

        # Generate embeddings for each configured source column
        for source_col, embedding_col in self.source_to_embedding_map.items():
            # Get the source text value
            source_text = source_values.get(source_col, '')
            if not source_text:
                # Also check if source column is in the doc itself
                source_text = doc.get(source_col, '')

            embedding = None
            if embedding_service and source_text:
                try:
                    embedding = embedding_service.generate_embedding(source_text)
                except Exception as e:
                    print(f"Warning: Failed to generate embedding for {source_col}: {e}")

            if embedding:
                doc[embedding_col] = embedding
            else:
                # Use zero vector as default for NOT NULL constraint compatibility
                # Find the dimension for this embedding column
                dim = dimensions[0]  # Default to first dimension
                if embedding_col in col_names:
                    idx = col_names.index(embedding_col)
                    if idx < len(dimensions):
                        dim = dimensions[idx]

                doc[embedding_col] = [0.0] * dim

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
