"""
MariaDB Database Backend

Implementation of DatabaseService interface using MariaDB 11.8 LTS.
Uses MySQL Connector/Python for database access (MariaDB is MySQL-compatible).

This backend creates proper relational tables with typed columns
based on schema definitions, providing better performance and
type safety compared to generic JSON storage.
"""
from typing import List, Optional, Dict, Any
import json
import time
import mysql.connector
from mysql.connector import Error as MySQLError
from gradeschoolmathsolver.config import Config
from .service import DatabaseService


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
                    host=getattr(self.config, 'MARIADB_HOST', 'localhost'),
                    port=getattr(self.config, 'MARIADB_PORT', 3306),
                    user=getattr(self.config, 'MARIADB_USER', 'root'),
                    password=getattr(self.config, 'MARIADB_PASSWORD', ''),
                    database=getattr(self.config, 'MARIADB_DATABASE', 'math_solver'),
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
            schema: Schema definition with columns and indexes

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

            # Extract schema information
            # For MariaDB, schema should have 'columns' and 'indexes' keys
            if 'columns' in schema:
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
            else:
                # Fallback to generic JSON schema (for backward compatibility)
                create_table_query = f"""
                CREATE TABLE `{collection_name}` (
                    id VARCHAR(255) PRIMARY KEY,
                    data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_created (created_at)
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

            # Check if table uses explicit columns or JSON storage
            cursor.execute(f"DESCRIBE `{collection_name}`")
            columns = {row[0] for row in cursor.fetchall()}

            if 'data' in columns:
                # JSON-based storage
                insert_query = f"""
                INSERT INTO `{collection_name}` (id, data)
                VALUES (%s, %s)
                """
                cursor.execute(insert_query, (record_id, json.dumps(record)))
            else:
                # Column-based storage
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
            print(f"Error creating record: {e}")
            return False

    def insert_record(
        self, collection_name: str, record: Dict[str, Any],
        record_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Insert a row (record) in MariaDB (create or update)

        Args:
            collection_name: Name of the table
            record: Record data
            record_id: Optional record ID

        Returns:
            str: Record ID if successful, None otherwise
        """
        if not self.connection:
            return None

        try:
            cursor = self.connection.cursor()

            if record_id is None:
                # Generate UUID for new record
                import uuid
                record_id = str(uuid.uuid4())

            # Check if table uses explicit columns or JSON storage
            cursor.execute(f"DESCRIBE `{collection_name}`")
            columns = {row[0] for row in cursor.fetchall()}

            if 'data' in columns:
                # JSON-based storage
                replace_query = f"""
                REPLACE INTO `{collection_name}` (id, data)
                VALUES (%s, %s)
                """
                cursor.execute(replace_query, (record_id, json.dumps(record)))
            else:
                # Column-based storage
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
            return record_id

        except MySQLError as e:
            print(f"Error inserting record: {e}")
            return None

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

            # Check if table uses explicit columns or JSON storage
            cursor.execute(f"DESCRIBE `{collection_name}`")
            columns = {row[0] for row in cursor.fetchall()}

            if 'data' in columns:
                # JSON-based storage
                select_query = f"SELECT data FROM `{collection_name}` WHERE id = %s"
                cursor.execute(select_query, (record_id,))
                row = cursor.fetchone()
                cursor.close()

                if row and row[0]:
                    result: Dict[str, Any] = json.loads(row[0])
                    return result
                return None
            else:
                # Column-based storage
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
                    result = {}
                    for idx, col_name in enumerate(column_names):
                        if col_name == pk_col and col_name == 'record_id':
                            continue  # Skip record_id in result
                        result[col_name] = row[idx]
                    return result
                return None

        except MySQLError as e:
            print(f"Error getting record: {e}")
            return None

    def search_records(  # noqa: C901
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

            # Check if table uses explicit columns or JSON storage
            cursor.execute(f"DESCRIBE `{collection_name}`")
            columns_info = cursor.fetchall()
            columns = {row[0] for row in columns_info}

            if 'data' in columns:
                # JSON-based storage
                where_clauses = []
                params: List[Any] = []

                if filters:
                    for field, value in filters.items():
                        where_clauses.append(f"JSON_EXTRACT(data, '$.{field}') = %s")
                        params.append(json.dumps(value) if not isinstance(value, str) else value)

                where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

                order_sql = ""
                if sort:
                    sort_parts = []
                    for sort_spec in sort:
                        for field, order in sort_spec.items():
                            direction = "DESC" if order == "desc" else "ASC"
                            sort_parts.append(f"JSON_EXTRACT(data, '$.{field}') {direction}")
                    if sort_parts:
                        order_sql = f"ORDER BY {', '.join(sort_parts)}"

                select_query = f"""
                SELECT id, data FROM `{collection_name}`
                {where_sql}
                {order_sql}
                LIMIT %s OFFSET %s
                """
                params.extend([limit, offset])

                cursor.execute(select_query, params)
                rows = cursor.fetchall()
                cursor.close()

                results = []
                for row in rows:
                    results.append({
                        '_id': row[0],
                        '_source': json.loads(row[1])
                    })

                return results
            else:
                # Column-based storage
                where_clauses = []
                params = []

                if filters:
                    for field, value in filters.items():
                        where_clauses.append(f"`{field}` = %s")
                        params.append(value)

                where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

                order_sql = ""
                if sort:
                    sort_parts = []
                    for sort_spec in sort:
                        for field, order in sort_spec.items():
                            direction = "DESC" if order == "desc" else "ASC"
                            sort_parts.append(f"`{field}` {direction}")
                    if sort_parts:
                        order_sql = f"ORDER BY {', '.join(sort_parts)}"

                select_query = f"""
                SELECT * FROM `{collection_name}`
                {where_sql}
                {order_sql}
                LIMIT %s OFFSET %s
                """
                params.extend([limit, offset])

                cursor.execute(select_query, params)

                # Get column names
                column_names = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                cursor.close()

                # Determine primary key column
                if collection_name == 'users':
                    pk_col = 'username'
                else:
                    pk_col = 'record_id'

                results = []
                for row in rows:
                    record = {}
                    record_id = None
                    for idx, col_name in enumerate(column_names):
                        if col_name == pk_col:
                            record_id = row[idx]
                            if pk_col == 'username':
                                # Include username in the record
                                record[col_name] = row[idx]
                        else:
                            record[col_name] = row[idx]

                    results.append({
                        '_id': record_id,
                        '_source': record
                    })

                return results

        except MySQLError as e:
            print(f"Error searching records: {e}")
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

            # Check if table uses explicit columns or JSON storage
            cursor.execute(f"DESCRIBE `{collection_name}`")
            columns = {row[0] for row in cursor.fetchall()}

            if 'data' in columns:
                # JSON-based storage
                # Get existing record
                existing = self.get_record(collection_name, record_id)
                if existing is None:
                    cursor.close()
                    return False

                # Merge with partial update
                existing.update(partial_record)

                # Update the record
                update_query = f"""
                UPDATE `{collection_name}`
                SET data = %s
                WHERE id = %s
                """
                cursor.execute(update_query, (json.dumps(existing), record_id))
            else:
                # Column-based storage
                # Determine primary key column
                if collection_name == 'users':
                    pk_col = 'username'
                else:
                    pk_col = 'record_id'

                # Build UPDATE SET clause
                set_clauses = []
                params = []
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
            print(f"Error updating record: {e}")
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

            # Check if table uses explicit columns or JSON storage
            cursor.execute(f"DESCRIBE `{collection_name}`")
            columns = {row[0] for row in cursor.fetchall()}

            if 'data' in columns:
                # JSON-based storage
                delete_query = f"DELETE FROM `{collection_name}` WHERE id = %s"
            else:
                # Column-based storage
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
            print(f"Error deleting record: {e}")
            return False

    def count_records(  # noqa: C901
        self, collection_name: str, query: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count rows (records) matching a query in MariaDB

        Args:
            collection_name: Name of the table
            query: Search query (ignored for MariaDB)
            filters: Simple filters (key-value pairs for WHERE clause)

        Returns:
            int: Number of matching records
        """
        if not self.connection:
            return 0

        try:
            cursor = self.connection.cursor()

            # Check if table uses explicit columns or JSON storage
            cursor.execute(f"DESCRIBE `{collection_name}`")
            columns = {row[0] for row in cursor.fetchall()}

            where_sql = ""
            params = []

            # Use filters if provided (preferred for MariaDB)
            if filters:
                # Column-based filtering
                if 'data' not in columns:
                    where_clauses = []
                    for field, value in filters.items():
                        where_clauses.append(f"`{field}` = %s")
                        params.append(value)
                    where_sql = f"WHERE {' AND '.join(where_clauses)}"
                else:
                    # JSON-based storage
                    where_clauses = []
                    for field, value in filters.items():
                        where_clauses.append(f"JSON_EXTRACT(data, '$.{field}') = %s")
                        params.append(json.dumps(value) if not isinstance(value, str) else value)
                    where_sql = f"WHERE {' AND '.join(where_clauses)}"
            elif query:
                # Fall back to query if no filters
                if 'data' in columns:
                    # JSON-based storage
                    where_clauses = []
                    for field, value in query.items():
                        where_clauses.append(f"JSON_EXTRACT(data, '$.{field}') = %s")
                        params.append(json.dumps(value) if not isinstance(value, str) else value)
                    where_sql = f"WHERE {' AND '.join(where_clauses)}"
                else:
                    # Column-based storage
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
            print(f"Error counting records: {e}")
            return 0
