"""
Elasticsearch Database Backend

Implementation of DatabaseService interface using Elasticsearch.
"""
from typing import List, Optional, Dict, Any
import os
import time
from elasticsearch import Elasticsearch, ConnectionError as ESConnectionError, NotFoundError, ConflictError
from config import Config
from .service import DatabaseService


class ElasticsearchDatabaseService(DatabaseService):
    """
    Elasticsearch implementation of DatabaseService

    Provides database operations using Elasticsearch as the backend.
    Maps generic database operations to Elasticsearch-specific operations (indices, documents, etc.).
    """

    def __init__(self, max_retries: Optional[int] = None, retry_delay: Optional[float] = None) -> None:
        """
        Initialize Elasticsearch database service with retry logic

        Args:
            max_retries: Maximum number of connection attempts (default: 12, or from env DB_MAX_RETRIES)
            retry_delay: Initial delay between retries in seconds (default: 5.0, or from env DB_RETRY_DELAY)
        """
        self.config = Config()
        self.es: Optional[Elasticsearch] = None

        # Allow environment variables to override defaults for testing/CI
        if max_retries is None:
            max_retries = int(os.getenv('DB_MAX_RETRIES', '12'))
        if retry_delay is None:
            retry_delay = float(os.getenv('DB_RETRY_DELAY', '5.0'))

        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connect()

    def connect(self) -> bool:
        """
        Establish connection to Elasticsearch with retry logic

        Attempts to connect to Elasticsearch with exponential backoff retry logic.
        This ensures the application can recover from temporary unavailability,
        such as during Docker container startup.

        Returns:
            bool: True if connection successful, False otherwise
        """
        attempt = 0

        while attempt < self.max_retries:
            try:
                # Elasticsearch 9.x uses URL-based initialization
                es_url = f"http://{self.config.ELASTICSEARCH_HOST}:{self.config.ELASTICSEARCH_PORT}"
                self.es = Elasticsearch(
                    [es_url],
                    request_timeout=10,
                    max_retries=3,
                    retry_on_timeout=True
                )

                # Verify connection
                if not self.es.ping():
                    raise ESConnectionError("Elasticsearch ping failed")

                if attempt > 0:
                    print(f"Elasticsearch connected successfully after {attempt + 1} attempt(s)")
                else:
                    print("Elasticsearch connected successfully")
                return True

            except ESConnectionError as e:
                attempt += 1
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    print(f"Elasticsearch connection attempt {attempt}/{self.max_retries} failed: {e}")
                    print(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"ERROR: Could not connect to Elasticsearch after {self.max_retries} attempts")
                    print(f"Last error: {e}")
                    print("Please ensure:")
                    print("  1. Elasticsearch container is running")
                    print("  2. Elasticsearch host and port are correct")
                    print("  3. Network connectivity is established")
                self.es = None
            except Exception as e:
                attempt += 1
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    print(f"Unexpected error connecting to Elasticsearch (attempt {attempt}/{self.max_retries}): {e}")
                    print(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"ERROR: Unexpected error connecting to Elasticsearch after {self.max_retries} attempts: {e}")
                self.es = None

        return False

    def is_connected(self) -> bool:
        """
        Check if Elasticsearch is currently connected

        Returns:
            bool: True if connected, False otherwise
        """
        return self.es is not None and self.es.ping()

    def create_collection(self, collection_name: str, schema: Dict[str, Any]) -> bool:
        """
        Create an Elasticsearch index (collection)

        Args:
            collection_name: Name of the index to create
            schema: Elasticsearch mapping definition

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.es:
            return False

        try:
            if not self.es.indices.exists(index=collection_name):
                self.es.indices.create(index=collection_name, body=schema)
                print(f"Created Elasticsearch index: {collection_name}")
            return True
        except Exception as e:
            print(f"Error creating index {collection_name}: {e}")
            return False

    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if an Elasticsearch index (collection) exists

        Args:
            collection_name: Name of the index

        Returns:
            bool: True if exists, False otherwise
        """
        if not self.es:
            return False

        try:
            return bool(self.es.indices.exists(index=collection_name))
        except Exception:
            return False

    def create_record(self, collection_name: str, record_id: str, record: Dict[str, Any]) -> bool:
        """
        Create a new document (record) in Elasticsearch (must not exist)

        Args:
            collection_name: Name of the index
            record_id: Unique identifier for the document
            record: Document data

        Returns:
            bool: True if successful, False if document already exists or error
        """
        if not self.es:
            return False

        try:
            self.es.create(index=collection_name, id=record_id, document=record)
            return True
        except ConflictError:
            # Document already exists
            return False
        except Exception as e:
            print(f"Error creating document: {e}")
            return False

    def insert_record(
        self, collection_name: str, record: Dict[str, Any],
        record_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Index a document (record) in Elasticsearch (create or update)

        Args:
            collection_name: Name of the index
            record: Document data
            record_id: Optional document ID

        Returns:
            str: Document ID if successful, None otherwise
        """
        if not self.es:
            return None

        try:
            if record_id:
                result = self.es.index(index=collection_name, id=record_id, document=record)
            else:
                result = self.es.index(index=collection_name, document=record)
            return result.get('_id')
        except Exception as e:
            print(f"Error indexing document: {e}")
            return None

    def get_record(self, collection_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document (record) from Elasticsearch by ID

        Args:
            collection_name: Name of the index
            record_id: Document ID

        Returns:
            dict: Document data if found, None otherwise
        """
        if not self.es:
            return None

        try:
            result = self.es.get(index=collection_name, id=record_id)
            return result.get('_source')
        except NotFoundError:
            return None
        except Exception as e:
            print(f"Error getting document: {e}")
            return None

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
        Search for documents (records) in Elasticsearch

        Args:
            collection_name: Name of the index
            query: Elasticsearch query DSL
            filters: Additional filter conditions
            sort: Sort specifications
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            list: List of matching documents with _id and _source
        """
        if not self.es:
            return []

        try:
            body: Dict[str, Any] = {
                "size": limit,
                "from": offset
            }

            # Build query
            if query or filters:
                bool_query: Dict[str, Any] = {"bool": {}}

                if query:
                    bool_query["bool"]["must"] = [query]

                if filters:
                    filter_clauses = []
                    for field, value in filters.items():
                        filter_clauses.append({"term": {field: value}})
                    bool_query["bool"]["filter"] = filter_clauses

                body["query"] = bool_query
            else:
                body["query"] = {"match_all": {}}

            if sort:
                body["sort"] = sort

            response = self.es.search(index=collection_name, body=body)
            return response['hits']['hits']
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []

    def update_record(self, collection_name: str, record_id: str, partial_record: Dict[str, Any]) -> bool:
        """
        Update a document (record) partially in Elasticsearch

        Args:
            collection_name: Name of the index
            record_id: Document ID
            partial_record: Fields to update

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.es:
            return False

        try:
            self.es.update(index=collection_name, id=record_id, body={"doc": partial_record})
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False

    def delete_record(self, collection_name: str, record_id: str) -> bool:
        """
        Delete a document (record) from Elasticsearch

        Args:
            collection_name: Name of the index
            record_id: Document ID

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.es:
            return False

        try:
            self.es.delete(index=collection_name, id=record_id)
            return True
        except NotFoundError:
            return False
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False

    def count_records(
        self, collection_name: str, query: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count documents (records) matching a query in Elasticsearch

        Args:
            collection_name: Name of the index
            query: Elasticsearch query DSL
            filters: Simple filters (converted to term queries if query is None)

        Returns:
            int: Number of matching documents
        """
        if not self.es:
            return 0

        try:
            # If filters provided and no query, build a simple term query
            if filters and not query:
                must_clauses = [{"term": {k: v}} for k, v in filters.items()]
                query = {"bool": {"must": must_clauses}}

            body = {"query": query} if query else {"query": {"match_all": {}}}
            response = self.es.count(index=collection_name, body=body)
            return response.get('count', 0)
        except Exception as e:
            print(f"Error counting documents: {e}")
            return 0

    def refresh_index(self, collection_name: str) -> bool:
        """
        Refresh an Elasticsearch index (make recent changes visible)

        This is useful for testing to ensure documents are immediately searchable.

        Args:
            collection_name: Name of the index to refresh

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.es:
            return False

        try:
            self.es.indices.refresh(index=collection_name)
            return True
        except Exception as e:
            print(f"Error refreshing index: {e}")
            return False
