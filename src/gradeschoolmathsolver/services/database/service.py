"""
Database Service - Abstract Interface

Provides a unified interface for database operations, allowing easy switching between backends.
Currently supports Elasticsearch and MariaDB.

Embedding Generation:
The database service handles ALL embedding generation internally when inserting records.
Other services do NOT need to:
- Know which database backend is being used
- Provide source texts for embedding generation
- Handle embedding storage

The database service reads from config.py:
- EMBEDDING_SOURCE_COLUMNS: Which columns in the record to use as embedding sources
- EMBEDDING_COLUMN_NAMES: Names for embedding columns
- EMBEDDING_DIMENSIONS: Dimensions for each embedding

For MariaDB, embeddings are stored in separate tables (one per embedding column).
For Elasticsearch, embeddings are stored in the same document.

Services using database operations SHOULD NOT care about the underlying backend.
The DATABASE_BACKEND configuration should ONLY be accessed in database service.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


# Global embedding service instance (lazy-loaded)
_embedding_service = None


def get_embedding_service() -> Any:
    """
    Get the embedding service instance for generating vector embeddings.

    This is lazy-loaded to avoid circular imports and allow graceful degradation
    when the embedding service is unavailable.

    Returns:
        EmbeddingService instance or None if unavailable
    """
    global _embedding_service
    if _embedding_service is None:
        try:
            from gradeschoolmathsolver.services.embedding import EmbeddingService
            _embedding_service = EmbeddingService()
        except Exception as e:
            print(f"ERROR: Could not initialize embedding service: {e}")
            return None
    return _embedding_service


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate an embedding vector for the given text.

    This is the centralized embedding generation function used by all database
    backends. It uses the EmbeddingService to generate vectors.

    Args:
        text: The text to generate an embedding for

    Returns:
        List of floats representing the embedding vector, or None if generation fails

    Raises:
        RuntimeError: If embedding service is unavailable or generation fails
    """
    embedding_service = get_embedding_service()
    if embedding_service is None:
        raise RuntimeError(
            "Embedding service is unavailable. Cannot generate embeddings. "
            "Please ensure the embedding service is running and accessible."
        )

    try:
        embedding = embedding_service.generate_embedding(text)
        if embedding is None:
            raise RuntimeError(f"Embedding generation returned None for text: {text[:50]}...")
        return list(embedding)
    except Exception as e:
        raise RuntimeError(f"Embedding generation failed: {e}") from e


class DatabaseService(ABC):
    """
    Abstract base class for database operations

    This interface defines common database operations that all backend
    implementations must support. This allows the application to switch
    between different database backends (Elasticsearch, MariaDB, etc.)
    without changing business logic.

    Embedding Generation:
    The database service handles ALL embedding generation internally.
    It reads EMBEDDING_SOURCE_COLUMNS from config to determine which columns
    in the record to use as embedding sources. Callers do NOT need to:
    - Know about embedding columns or source columns
    - Provide source texts for embedding generation
    - Handle embedding storage

    The database service uses config.py to determine:
    - EMBEDDING_SOURCE_COLUMNS: Source columns in record for embedding generation
    - EMBEDDING_COLUMN_NAMES: Names for embedding columns
    - EMBEDDING_DIMENSIONS: Dimensions for each embedding
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the database

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if database is currently connected

        Returns:
            bool: True if connected, False otherwise
        """
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, schema: Dict[str, Any]) -> bool:
        """
        Create a new collection/table

        Args:
            collection_name: Name of the collection to create
            schema: Schema/mapping definition for the collection

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection/table exists

        Args:
            collection_name: Name of the collection

        Returns:
            bool: True if exists, False otherwise
        """
        pass

    @abstractmethod
    def create_record(self, collection_name: str, record_id: str, record: Dict[str, Any]) -> bool:
        """
        Create a new record (must not exist)

        Args:
            collection_name: Name of the collection
            record_id: Unique identifier for the record
            record: Record data

        Returns:
            bool: True if successful, False if record already exists or error
        """
        pass

    @abstractmethod
    def insert_record(
        self, collection_name: str, record: Dict[str, Any]
    ) -> Optional[str]:
        """
        Insert a record (create or update), with automatic embedding generation.

        The database service handles all embedding operations internally:
        - Generates a UUID for record_id automatically
        - Reads EMBEDDING_SOURCE_COLUMNS from config to determine source text columns
        - Generates embeddings from source columns in the record
        - Stores embeddings appropriately for the backend

        For Elasticsearch: Embeddings are added to the document
        For MariaDB: Embeddings are stored in separate tables (one per embedding column)

        Args:
            collection_name: Name of the collection
            record: Record data (must contain all source columns defined in config)

        Returns:
            str: Record ID if successful, None otherwise

        Raises:
            RuntimeError: If embedding generation fails
        """
        pass

    @abstractmethod
    def get_record(self, collection_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a record by ID

        Args:
            collection_name: Name of the collection
            record_id: Record ID

        Returns:
            dict: Record data if found, None otherwise
        """
        pass

    @abstractmethod
    def search_records(
        self,
        collection_name: str,
        query: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for records

        Args:
            collection_name: Name of the collection
            query: Search query (database-specific format)
            filters: Filter conditions
            sort: Sort specifications
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            list: List of matching records with id and data
        """
        pass

    @abstractmethod
    def update_record(self, collection_name: str, record_id: str, partial_record: Dict[str, Any]) -> bool:
        """
        Update a record partially

        Args:
            collection_name: Name of the collection
            record_id: Record ID
            partial_record: Fields to update

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_record(self, collection_name: str, record_id: str) -> bool:
        """
        Delete a record

        Args:
            collection_name: Name of the collection
            record_id: Record ID

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def count_records(
        self, collection_name: str, query: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count records matching a query

        Args:
            collection_name: Name of the collection
            query: Search query (database-specific format)
            filters: Simple filters for compatibility (key-value pairs)

        Returns:
            int: Number of matching records
        """
        pass

    def create_quiz_history_collection(
        self, collection_name: str, include_embeddings: bool = True
    ) -> bool:
        """
        Create the quiz history collection with embedding support.

        This method creates the main collection and any additional structures
        needed for embedding storage based on the database backend:
        - For Elasticsearch: Embeddings are stored in the same document
        - For MariaDB: Separate embedding tables are created (one per embedding column)

        The default implementation uses get_answer_history_schema_for_backend()
        to get the schema and creates the collection. Backend-specific implementations
        may override this to create additional structures.

        Args:
            collection_name: Name of the collection (e.g., 'quiz_history')
            include_embeddings: Whether to include embedding columns (default: True)

        Returns:
            bool: True if successful, False otherwise
        """
        from gradeschoolmathsolver.config import Config
        from .schemas import get_answer_history_schema_for_backend

        config = Config()
        backend = config.DATABASE_BACKEND

        schema = get_answer_history_schema_for_backend(backend, include_embeddings)
        return self.create_collection(collection_name, schema)


# Global database service instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """
    Get the global database service instance

    Auto-initializes based on DATABASE_BACKEND configuration.
    Supported backends: 'elasticsearch', 'mariadb' (default)

    Returns:
        DatabaseService: The configured database service

    Raises:
        RuntimeError: If database service hasn't been initialized
    """
    global _db_service
    if _db_service is None:
        from gradeschoolmathsolver.config import Config
        config = Config()
        backend = config.DATABASE_BACKEND.lower()

        if backend == 'mariadb':
            from .mariadb_backend import MariaDBDatabaseService
            _db_service = MariaDBDatabaseService()
        else:  # Default to elasticsearch
            from .elasticsearch_backend import ElasticsearchDatabaseService
            _db_service = ElasticsearchDatabaseService()

    return _db_service


def set_database_service(service: DatabaseService) -> None:
    """
    Set the global database service instance

    This allows injecting a different database backend for testing or switching databases.

    Args:
        service: Database service instance to use
    """
    global _db_service
    _db_service = service
