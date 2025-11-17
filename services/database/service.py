"""
Database Service - Abstract Interface

Provides a unified interface for database operations, allowing easy switching between backends.
Currently supports Elasticsearch and MariaDB.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class DatabaseService(ABC):
    """
    Abstract base class for database operations

    This interface defines common database operations that all backend
    implementations must support. This allows the application to switch
    between different database backends (Elasticsearch, MariaDB, etc.)
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
    def insert_record(self, collection_name: str, record: Dict[str, Any], record_id: Optional[str] = None) -> Optional[str]:
        """
        Insert a record (create or update)

        Args:
            collection_name: Name of the collection
            record: Record data
            record_id: Optional record ID

        Returns:
            str: Record ID if successful, None otherwise
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
    def count_records(self, collection_name: str, query: Optional[Dict[str, Any]] = None,
                     filters: Optional[Dict[str, Any]] = None) -> int:
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


# Global database service instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """
    Get the global database service instance

    Auto-initializes based on DATABASE_BACKEND environment variable.
    Supported backends: 'elasticsearch' (default), 'mariadb'

    Returns:
        DatabaseService: The configured database service

    Raises:
        RuntimeError: If database service hasn't been initialized
    """
    global _db_service
    if _db_service is None:
        import os
        backend = os.getenv('DATABASE_BACKEND', 'elasticsearch').lower()

        if backend == 'mariadb':
            from .mariadb_backend import MariaDBDatabaseService
            _db_service = MariaDBDatabaseService()
        else:  # Default to elasticsearch
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
