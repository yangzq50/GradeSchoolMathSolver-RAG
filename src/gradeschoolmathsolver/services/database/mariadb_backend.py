"""
MariaDB Database Backend

Implementation of DatabaseService interface using MariaDB 11.8 LTS.
Uses MySQL Connector/Python for database access (MariaDB is MySQL-compatible).

This backend creates proper relational tables with typed columns
based on schema definitions. All columns use proper SQL types - no JSON storage.

Embedding Storage:
For MariaDB, embeddings are stored in separate tables (one per embedding column)
because MariaDB doesn't support multiple VECTOR indexes on the same table.
"""
from typing import List, Optional, Dict, Any
import time
import mysql.connector
from mysql.connector import Error as MySQLError
from gradeschoolmathsolver.config import Config
from .service import DatabaseService, generate_embedding


class MariaDBDatabaseService(DatabaseService):
    """
    MariaDB implementation of DatabaseService

    Provides database operations using MariaDB as the backend.
    Maps generic database operations to SQL operations (tables, rows, etc.).
    """

    connection: Optional[Any]

    def __init__(self, max_retries: Optional[int] = None, retry_delay: Optional[float] = None):
        """
        Initialize MariaDB database service with retry logic

        Args:
            max_retries: Maximum number of connection attempts (default: from Config.DB_MAX_RETRIES)
            retry_delay: Initial delay between retries in seconds (default: from Config.DB_RETRY_DELAY)
        """
        self.config = Config()
        self.connection = None

        # Use config values if not explicitly provided (for testing override)
        if max_retries is None:
            max_retries = self.config.DB_MAX_RETRIES
        if retry_delay is None:
            retry_delay = self.config.DB_RETRY_DELAY

        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connect()

    def connect(self) -> bool:
        """
        Establish connection to MariaDB with retry logic

        Attempts to connect to MariaDB with exponential backoff retry logic.
        This ensures the application can recover from temporary unavailability,
        such as during Docker container startup.

        Returns:
            bool: True if connection successful, False otherwise
        """
        attempt = 0

        while attempt < self.max_retries:
            try:
                self.connection = mysql.connector.connect(
                    host=self.config.MARIADB_HOST,
                    port=self.config.MARIADB_PORT,
                    user=self.config.MARIADB_USER,
                    password=self.config.MARIADB_PASSWORD,
                    database=self.config.MARIADB_DATABASE,
                    autocommit=True,
                    connect_timeout=10
                )

                if self.connection is not None and self.connection.is_connected():
                    if attempt > 0:
                        print(f"MariaDB connected successfully after {attempt + 1} attempt(s)")
                    else:
                        print("MariaDB connected successfully")
                    return True
                else:
                    print("Warning: MariaDB connection failed")
                    self.connection = None
                    return False

            except MySQLError as e:
                attempt += 1
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    print(f"MariaDB connection attempt {attempt}/{self.max_retries} failed: {e}")
                    print(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"ERROR: Could not connect to MariaDB after {self.max_retries} attempts")
                    print(f"Last error: {e}")
                    print("Please ensure:")
                    print("  1. MariaDB container is running")
                    print("  2. Database credentials are correct")
                    print("  3. Network connectivity is established")
                self.connection = None
            except Exception as e:
                attempt += 1
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    print(f"Unexpected error connecting to MariaDB (attempt {attempt}/{self.max_retries}): {e}")
                    print(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"ERROR: Unexpected error connecting to MariaDB after {self.max_retries} attempts: {e}")
                self.connection = None

        return False

    def is_connected(self) -> bool:
        """
        Check if MariaDB is currently connected

        Returns:
            bool: True if connected, False otherwise
        """
        if self.connection is None:
            return False
        try:
            return bool(self.connection.is_connected())
        except Exception:
            return False

    def create_collection(self, collection_name: str, schema: Dict[str, Any]) -> bool:
        """
        Create a MariaDB table (collection) with proper column types

        Args:
            collection_name: Name of the table to create
            schema: Schema definition with 'columns' and optionally 'indexes' keys

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()

            # Check if table exists
            cursor.execute(f"SHOW TABLES LIKE '{collection_name}'")
            if cursor.fetchone():
                cursor.close()
                return True  # Table already exists

            # Schema must have 'columns' defined - no fallback to JSON storage
            if 'columns' not in schema:
                print(f"ERROR: Schema for table '{collection_name}' must define 'columns'. "
                      "JSON-based storage is not supported.")
                cursor.close()
                return False

            # Use explicit column definitions
            columns_def = schema['columns']
            columns_sql = ', '.join([f"`{col}` {typedef}" for col, typedef in columns_def.items()])

            # Add indexes if specified
            indexes_sql = ""
            if 'indexes' in schema and schema['indexes']:
                indexes_sql = ", " + ", ".join(schema['indexes'])

            create_table_query = f"""
            CREATE TABLE `{collection_name}` (
                {columns_sql}{indexes_sql}
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """

            cursor.execute(create_table_query)
            cursor.close()
            print(f"Created MariaDB table: {collection_name}")
            return True

        except MySQLError as e:
            print(f"Error creating table {collection_name}: {e}")
            return False

    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a MariaDB table (collection) exists

        Args:
            collection_name: Name of the table

        Returns:
            bool: True if exists, False otherwise
        """
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SHOW TABLES LIKE '{collection_name}'")
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
        except Exception:
            return False

    def create_record(self, collection_name: str, record_id: str, record: Dict[str, Any]) -> bool:
        """
        Create a new row (record) in MariaDB (must not exist)

        Args:
            collection_name: Name of the table
            record_id: Unique identifier for the row
            record: Record data

        Returns:
            bool: True if successful, False if record already exists or error
        """
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()

            # Determine primary key column
            if collection_name == 'users':
                pk_col = 'username'
                record_with_id = record.copy()
            else:
                pk_col = 'record_id'
                record_with_id = record.copy()
                record_with_id[pk_col] = record_id

            cols = ', '.join([f"`{k}`" for k in record_with_id.keys()])
            placeholders = ', '.join(['%s' for _ in record_with_id])
            insert_query = f"INSERT INTO `{collection_name}` ({cols}) VALUES ({placeholders})"
            cursor.execute(insert_query, tuple(record_with_id.values()))

            cursor.close()
            return True

        except MySQLError as e:
            # Duplicate entry error (errno 1062) or other MySQL errors
            if hasattr(e, 'errno') and e.errno == 1062:
                return False
            print(f"ERROR: Failed to create record in {collection_name}: {e}")
            return False

    def insert_record(
        self, collection_name: str, record: Dict[str, Any]
    ) -> Optional[str]:
        """
        Insert a row (record) in MariaDB (create or update), with automatic embedding generation.

        The database service handles all embedding operations internally:
        - Generates a UUID for record_id automatically
        - Reads EMBEDDING_SOURCE_COLUMNS from config to determine source text columns
        - Generates embeddings from source columns in the record
        - Stores embeddings in separate tables (one per embedding column)

        Args:
            collection_name: Name of the table
            record: Record data (must contain all source columns from config)

        Returns:
            str: Record ID if successful, None otherwise

        Raises:
            RuntimeError: If embedding generation or insertion fails
        """
        if not self.connection:
            return None

        try:
            import uuid
            cursor = self.connection.cursor()

            # Generate UUID for new record
            record_id = str(uuid.uuid4())

            # Determine primary key column
            if collection_name == 'users':
                pk_col = 'username'
                record_with_id = record.copy()
            else:
                pk_col = 'record_id'
                record_with_id = record.copy()
                record_with_id[pk_col] = record_id

            cols = ', '.join([f"`{k}`" for k in record_with_id.keys()])
            placeholders = ', '.join(['%s' for _ in record_with_id])
            replace_query = f"REPLACE INTO `{collection_name}` ({cols}) VALUES ({placeholders})"
            cursor.execute(replace_query, tuple(record_with_id.values()))
            cursor.close()

            # Generate and store embeddings from source columns in the record
            # Read source columns from config - do NOT use any defaults
            self._insert_embeddings_from_record(collection_name, record_id, record)

            return record_id

        except RuntimeError:
            # Re-raise RuntimeError from embedding operations
            raise
        except MySQLError as e:
            print(f"ERROR: Failed to insert record in {collection_name}: {e}")
            return None

    def _insert_embeddings_from_record(
        self, collection_name: str, record_id: str, record: Dict[str, Any]
    ) -> None:
        """
        Generate embeddings from source columns in record and insert into separate tables.

        Reads EMBEDDING_SOURCE_COLUMNS from config to determine which columns
        in the record to use as embedding sources. Does NOT use any defaults.

        Args:
            collection_name: Name of the main table
            record_id: Record ID to link embeddings to
            record: The record containing source text columns

        Raises:
            RuntimeError: If embedding generation or insertion fails
        """
        from .schemas import get_embedding_source_mapping, get_embedding_table_name

        # Get source-to-embedding column mapping from config (no defaults!)
        source_to_embedding = get_embedding_source_mapping()

        # Generate embeddings and insert into separate tables
        for source_col, embedding_col in source_to_embedding.items():
            # Get source text from record - MUST exist, no defaults
            if source_col not in record:
                error_msg = (
                    f"Cannot generate embedding for column '{embedding_col}': "
                    f"source column '{source_col}' not found in record. "
                    f"Record must contain all columns defined in EMBEDDING_SOURCE_COLUMNS config."
                )
                print(f"ERROR: {error_msg}")
                raise RuntimeError(error_msg)

            source_text = record[source_col]
            if not source_text:
                error_msg = (
                    f"Cannot generate embedding for column '{embedding_col}': "
                    f"source column '{source_col}' is empty. "
                    f"All source columns must have non-empty values."
                )
                print(f"ERROR: {error_msg}")
                raise RuntimeError(error_msg)

            # Generate embedding using centralized function - MUST succeed
            try:
                embedding = generate_embedding(source_text)
            except RuntimeError as e:
                print(f"ERROR: {e}")
                raise

            # Get the embedding table name
            embedding_table = get_embedding_table_name(collection_name, embedding_col)

            # Insert embedding into separate table - MUST succeed
            if self.connection is None:
                raise RuntimeError("Database connection is not available")
            try:
                cursor = self.connection.cursor()
                cols = "`record_id`, `embedding`"
                replace_query = f"REPLACE INTO `{embedding_table}` ({cols}) VALUES (%s, %s)"
                # Convert embedding list to MariaDB VECTOR format
                embedding_str = str(embedding)
                cursor.execute(replace_query, (record_id, embedding_str))
                cursor.close()
            except MySQLError as e:
                error_msg = f"Failed to insert embedding into {embedding_table}: {e}"
                print(f"ERROR: {error_msg}")
                raise RuntimeError(error_msg) from e

    def get_record(self, collection_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a row (record) from MariaDB by ID

        Args:
            collection_name: Name of the table
            record_id: Record ID

        Returns:
            dict: Record data if found, None otherwise
        """
        if not self.connection:
            return None

        try:
            cursor = self.connection.cursor()

            # Determine primary key column
            if collection_name == 'users':
                pk_col = 'username'
            else:
                pk_col = 'record_id'

            select_query = f"SELECT * FROM `{collection_name}` WHERE `{pk_col}` = %s"
            cursor.execute(select_query, (record_id,))

            # Get column names
            column_names = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            cursor.close()

            if row:
                # Convert to dict, excluding the primary key from the result
                result: Dict[str, Any] = {}
                for idx, col_name in enumerate(column_names):
                    if col_name == pk_col and col_name == 'record_id':
                        continue  # Skip record_id in result
                    result[col_name] = row[idx]
                return result
            return None

        except MySQLError as e:
            print(f"ERROR: Failed to get record from {collection_name}: {e}")
            return None

    def _build_where_clause(self, filters: Optional[Dict[str, Any]]) -> tuple[str, List[Any]]:
        """Build WHERE clause from filters."""
        if not filters:
            return "", []
        where_clauses: List[str] = []
        params: List[Any] = []
        for field, value in filters.items():
            where_clauses.append(f"`{field}` = %s")
            params.append(value)
        return f"WHERE {' AND '.join(where_clauses)}", params

    def _build_order_clause(self, sort: Optional[List[Dict[str, Any]]]) -> str:
        """Build ORDER BY clause from sort specifications."""
        if not sort:
            return ""
        sort_parts = []
        for sort_spec in sort:
            for field, order in sort_spec.items():
                direction = "DESC" if order == "desc" else "ASC"
                sort_parts.append(f"`{field}` {direction}")
        return f"ORDER BY {', '.join(sort_parts)}" if sort_parts else ""

    def _convert_row_to_record(
        self, row: tuple, column_names: List[str], pk_col: str
    ) -> Dict[str, Any]:
        """Convert a database row to a record dict with _id and _source."""
        record: Dict[str, Any] = {}
        record_id = None
        for idx, col_name in enumerate(column_names):
            if col_name == pk_col:
                record_id = row[idx]
                if pk_col == 'username':
                    record[col_name] = row[idx]
            else:
                record[col_name] = row[idx]
        return {'_id': record_id, '_source': record}

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
        Search for rows (records) in MariaDB

        Args:
            collection_name: Name of the table
            query: Search query (for column-based tables)
            filters: Filter conditions
            sort: Sort specifications
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            list: List of matching records with id and data
        """
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor()
            where_sql, params = self._build_where_clause(filters)
            order_sql = self._build_order_clause(sort)

            select_query = f"""
            SELECT * FROM `{collection_name}`
            {where_sql}
            {order_sql}
            LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])

            cursor.execute(select_query, params)
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            cursor.close()

            pk_col = 'username' if collection_name == 'users' else 'record_id'
            return [self._convert_row_to_record(row, column_names, pk_col) for row in rows]

        except MySQLError as e:
            print(f"ERROR: Failed to search records in {collection_name}: {e}")
            return []

    def update_record(self, collection_name: str, record_id: str, partial_record: Dict[str, Any]) -> bool:
        """
        Update a row (record) partially in MariaDB

        Args:
            collection_name: Name of the table
            record_id: Record ID
            partial_record: Fields to update

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()

            # Determine primary key column
            if collection_name == 'users':
                pk_col = 'username'
            else:
                pk_col = 'record_id'

            # Build UPDATE SET clause
            set_clauses = []
            params: List[Any] = []
            for field, value in partial_record.items():
                if field != pk_col:  # Don't update primary key
                    set_clauses.append(f"`{field}` = %s")
                    params.append(value)

            if not set_clauses:
                cursor.close()
                return True  # Nothing to update

            params.append(record_id)
            update_query = f"""
            UPDATE `{collection_name}`
            SET {', '.join(set_clauses)}
            WHERE `{pk_col}` = %s
            """
            cursor.execute(update_query, params)

            cursor.close()
            return True

        except MySQLError as e:
            print(f"ERROR: Failed to update record in {collection_name}: {e}")
            return False

    def delete_record(self, collection_name: str, record_id: str) -> bool:
        """
        Delete a row (record) from MariaDB

        Args:
            collection_name: Name of the table
            record_id: Record ID

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()

            # Determine primary key column
            if collection_name == 'users':
                pk_col = 'username'
            else:
                pk_col = 'record_id'
            delete_query = f"DELETE FROM `{collection_name}` WHERE `{pk_col}` = %s"

            cursor.execute(delete_query, (record_id,))
            affected = cursor.rowcount
            cursor.close()
            return bool(affected > 0)

        except MySQLError as e:
            print(f"ERROR: Failed to delete record from {collection_name}: {e}")
            return False

    def count_records(
        self, collection_name: str, query: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count rows (records) matching a query in MariaDB

        Args:
            collection_name: Name of the table
            query: Search query (filters take precedence)
            filters: Simple filters (key-value pairs for WHERE clause)

        Returns:
            int: Number of matching records
        """
        if not self.connection:
            return 0

        try:
            cursor = self.connection.cursor()

            where_sql = ""
            params: List[Any] = []

            # Use filters if provided (preferred)
            if filters:
                where_clauses = []
                for field, value in filters.items():
                    where_clauses.append(f"`{field}` = %s")
                    params.append(value)
                where_sql = f"WHERE {' AND '.join(where_clauses)}"
            elif query:
                # Fall back to query if no filters
                where_clauses = []
                for field, value in query.items():
                    where_clauses.append(f"`{field}` = %s")
                    params.append(value)
                where_sql = f"WHERE {' AND '.join(where_clauses)}"

            count_query = f"SELECT COUNT(*) as count FROM `{collection_name}` {where_sql}"
            cursor.execute(count_query, params)
            result = cursor.fetchone()
            cursor.close()

            return result[0] if result else 0

        except MySQLError as e:
            print(f"ERROR: Failed to count records in {collection_name}: {e}")
            return 0

    def create_quiz_history_collection(
        self, collection_name: str, include_embeddings: bool = True
    ) -> bool:
        """
        Create the quiz history collection with embedding support for MariaDB.

        For MariaDB, this creates:
        1. The main quiz_history table
        2. Separate embedding tables (one per embedding column) because
           MariaDB doesn't support multiple VECTOR indexes on the same table.

        Args:
            collection_name: Name of the collection (e.g., 'quiz_history')
            include_embeddings: Whether to include embedding columns (default: True)

        Returns:
            bool: True if all tables created successfully, False otherwise
        """
        from .schemas import (
            get_answer_history_schema_for_backend,
            get_embedding_config,
            get_embedding_table_schemas_mariadb
        )

        # Create main table
        schema = get_answer_history_schema_for_backend('mariadb', include_embeddings)
        if not self.create_collection(collection_name, schema):
            return False

        # Create separate embedding tables
        if include_embeddings:
            embedding_config = get_embedding_config()
            embedding_tables = get_embedding_table_schemas_mariadb(
                collection_name,
                embedding_config
            )
            for table_name, table_schema in embedding_tables.items():
                if not self.create_collection(table_name, table_schema):
                    print(f"Warning: Failed to create embedding table {table_name}")

        return True
