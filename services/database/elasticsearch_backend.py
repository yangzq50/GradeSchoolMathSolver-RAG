"""
Elasticsearch Database Backend

Implementation of DatabaseService interface using Elasticsearch.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from elasticsearch import Elasticsearch, ConnectionError as ESConnectionError, NotFoundError, ConflictError
from config import Config
from .service import DatabaseService


class ElasticsearchDatabaseService(DatabaseService):
    """
    Elasticsearch implementation of DatabaseService

    Provides database operations using Elasticsearch as the backend.
    Handles connection management, index creation, and CRUD operations.
    """

    def __init__(self):
        """Initialize Elasticsearch database service"""
        self.config = Config()
        self.es: Optional[Elasticsearch] = None
        self.connect()

    def connect(self) -> bool:
        """
        Establish connection to Elasticsearch

        Returns:
            bool: True if connection successful, False otherwise
        """
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
                print("Warning: Elasticsearch ping failed")
                self.es = None
                return False

            print("Elasticsearch connected successfully")
            return True

        except ESConnectionError as e:
            print(f"Warning: Could not connect to Elasticsearch: {e}")
            print("Database service will operate in limited mode")
            self.es = None
            return False
        except Exception as e:
            print(f"Warning: Unexpected error connecting to Elasticsearch: {e}")
            print("Database service will operate in limited mode")
            self.es = None
            return False

    def is_connected(self) -> bool:
        """
        Check if Elasticsearch is currently connected

        Returns:
            bool: True if connected, False otherwise
        """
        return self.es is not None and self.es.ping()

    def create_index(self, index_name: str, mapping: Dict[str, Any]) -> bool:
        """
        Create an Elasticsearch index

        Args:
            index_name: Name of the index to create
            mapping: Elasticsearch mapping definition

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.es:
            return False

        try:
            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name, body=mapping)
                print(f"Created Elasticsearch index: {index_name}")
            return True
        except Exception as e:
            print(f"Error creating index {index_name}: {e}")
            return False

    def index_exists(self, index_name: str) -> bool:
        """
        Check if an Elasticsearch index exists

        Args:
            index_name: Name of the index

        Returns:
            bool: True if exists, False otherwise
        """
        if not self.es:
            return False

        try:
            return self.es.indices.exists(index=index_name)
        except Exception:
            return False

    def create_document(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """
        Create a new document in Elasticsearch (must not exist)

        Args:
            index_name: Name of the index
            doc_id: Unique identifier for the document
            document: Document data

        Returns:
            bool: True if successful, False if document already exists or error
        """
        if not self.es:
            return False

        try:
            self.es.create(index=index_name, id=doc_id, document=document)
            return True
        except ConflictError:
            # Document already exists
            return False
        except Exception as e:
            print(f"Error creating document: {e}")
            return False

    def index_document(self, index_name: str, document: Dict[str, Any], doc_id: Optional[str] = None) -> Optional[str]:
        """
        Index a document in Elasticsearch (create or update)

        Args:
            index_name: Name of the index
            document: Document data
            doc_id: Optional document ID

        Returns:
            str: Document ID if successful, None otherwise
        """
        if not self.es:
            return None

        try:
            if doc_id:
                result = self.es.index(index=index_name, id=doc_id, document=document)
            else:
                result = self.es.index(index=index_name, document=document)
            return result.get('_id')
        except Exception as e:
            print(f"Error indexing document: {e}")
            return None

    def get_document(self, index_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document from Elasticsearch by ID

        Args:
            index_name: Name of the index
            doc_id: Document ID

        Returns:
            dict: Document data if found, None otherwise
        """
        if not self.es:
            return None

        try:
            result = self.es.get(index=index_name, id=doc_id)
            return result.get('_source')
        except NotFoundError:
            return None
        except Exception as e:
            print(f"Error getting document: {e}")
            return None

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
        Search for documents in Elasticsearch

        Args:
            index_name: Name of the index
            query: Elasticsearch query DSL
            filters: Additional filter conditions
            sort: Sort specifications
            size: Maximum number of results
            from_: Offset for pagination

        Returns:
            list: List of matching documents with _id and _source
        """
        if not self.es:
            return []

        try:
            body: Dict[str, Any] = {
                "size": size,
                "from": from_
            }

            # Build query
            if query or filters:
                bool_query = {"bool": {}}

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

            response = self.es.search(index=index_name, body=body)
            return response['hits']['hits']
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []

    def update_document(self, index_name: str, doc_id: str, partial_doc: Dict[str, Any]) -> bool:
        """
        Update a document partially in Elasticsearch

        Args:
            index_name: Name of the index
            doc_id: Document ID
            partial_doc: Fields to update

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.es:
            return False

        try:
            self.es.update(index=index_name, id=doc_id, body={"doc": partial_doc})
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False

    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """
        Delete a document from Elasticsearch

        Args:
            index_name: Name of the index
            doc_id: Document ID

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.es:
            return False

        try:
            self.es.delete(index=index_name, id=doc_id)
            return True
        except NotFoundError:
            return False
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False

    def count_documents(self, index_name: str, query: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching a query in Elasticsearch

        Args:
            index_name: Name of the index
            query: Elasticsearch query DSL

        Returns:
            int: Number of matching documents
        """
        if not self.es:
            return 0

        try:
            body = {"query": query} if query else {"query": {"match_all": {}}}
            response = self.es.count(index=index_name, body=body)
            return response.get('count', 0)
        except Exception as e:
            print(f"Error counting documents: {e}")
            return 0

    def refresh_index(self, index_name: str) -> bool:
        """
        Refresh an Elasticsearch index (make recent changes visible)

        This is useful for testing to ensure documents are immediately searchable.

        Args:
            index_name: Name of the index to refresh

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.es:
            return False

        try:
            self.es.indices.refresh(index=index_name)
            return True
        except Exception as e:
            print(f"Error refreshing index: {e}")
            return False
