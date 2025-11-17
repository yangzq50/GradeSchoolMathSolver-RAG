"""
Database Service - Abstract Interface

Provides a unified interface for database operations, allowing easy switching between backends.
Currently supports Elasticsearch, but can be extended to support other databases.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class DatabaseService(ABC):
    """
    Abstract base class for database operations

    This interface defines common database operations that all backend
    implementations must support. This allows the application to switch
    between different database backends (Elasticsearch, MongoDB, PostgreSQL, etc.)
    without changing business logic.
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
    def create_index(self, index_name: str, mapping: Dict[str, Any]) -> bool:
        """
        Create a new index/collection/table

        Args:
            index_name: Name of the index to create
            mapping: Schema/mapping definition for the index

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def index_exists(self, index_name: str) -> bool:
        """
        Check if an index/collection/table exists

        Args:
            index_name: Name of the index

        Returns:
            bool: True if exists, False otherwise
        """
        pass

    @abstractmethod
    def create_document(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """
        Create a new document (must not exist)

        Args:
            index_name: Name of the index
            doc_id: Unique identifier for the document
            document: Document data

        Returns:
            bool: True if successful, False if document already exists or error
        """
        pass

    @abstractmethod
    def index_document(self, index_name: str, document: Dict[str, Any], doc_id: Optional[str] = None) -> Optional[str]:
        """
        Index a document (create or update)

        Args:
            index_name: Name of the index
            document: Document data
            doc_id: Optional document ID

        Returns:
            str: Document ID if successful, None otherwise
        """
        pass

    @abstractmethod
    def get_document(self, index_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID

        Args:
            index_name: Name of the index
            doc_id: Document ID

        Returns:
            dict: Document data if found, None otherwise
        """
        pass

    @abstractmethod
    def search_documents(
        self,
        index_name: str,
        query: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        size: int = 10,
        from_: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for documents

        Args:
            index_name: Name of the index
            query: Search query (database-specific format)
            filters: Filter conditions
            sort: Sort specifications
            size: Maximum number of results
            from_: Offset for pagination

        Returns:
            list: List of matching documents with _id and _source
        """
        pass

    @abstractmethod
    def update_document(self, index_name: str, doc_id: str, partial_doc: Dict[str, Any]) -> bool:
        """
        Update a document partially

        Args:
            index_name: Name of the index
            doc_id: Document ID
            partial_doc: Fields to update

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """
        Delete a document

        Args:
            index_name: Name of the index
            doc_id: Document ID

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def count_documents(self, index_name: str, query: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching a query

        Args:
            index_name: Name of the index
            query: Search query (database-specific format)

        Returns:
            int: Number of matching documents
        """
        pass


# Global database service instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """
    Get the global database service instance

    Returns:
        DatabaseService: The configured database service

    Raises:
        RuntimeError: If database service hasn't been initialized
    """
    global _db_service
    if _db_service is None:
        # Auto-initialize with Elasticsearch backend
        from .elasticsearch_backend import ElasticsearchDatabaseService
        _db_service = ElasticsearchDatabaseService()

    return _db_service


def set_database_service(service: DatabaseService):
    """
    Set the global database service instance

    This allows injecting a different database backend for testing or switching databases.

    Args:
        service: Database service instance to use
    """
    global _db_service
    _db_service = service
