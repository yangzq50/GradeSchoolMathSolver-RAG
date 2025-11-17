"""
MariaDB Database Backend

Implementation of DatabaseService interface using MariaDB 11.8 LTS.
Uses mysql-connector-python for database access.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import mysql.connector
from mysql.connector import Error as MySQLError
from config import Config
from .service import DatabaseService


class MariaDBDatabaseService(DatabaseService):
    """
    MariaDB implementation of DatabaseService

    Provides database operations using MariaDB as the backend.
    Maps generic database operations to SQL operations (tables, rows, etc.).
    """

    def __init__(self):
        """Initialize MariaDB database service"""
        self.config = Config()
        self.connection = None
        self.connect()

    def connect(self) -> bool:
        """
        Establish connection to MariaDB

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.connection = mysql.connector.connect(
                host=getattr(self.config, 'MARIADB_HOST', 'localhost'),
                port=getattr(self.config, 'MARIADB_PORT', 3306),
                user=getattr(self.config, 'MARIADB_USER', 'root'),
                password=getattr(self.config, 'MARIADB_PASSWORD', ''),
                database=getattr(self.config, 'MARIADB_DATABASE', 'math_solver'),
                autocommit=True
            )

            if self.connection.is_connected():
                print("MariaDB connected successfully")
                return True
            else:
                print("Warning: MariaDB connection failed")
                self.connection = None
                return False

        except MySQLError as e:
            print(f"Warning: Could not connect to MariaDB: {e}")
            print("Database service will operate in limited mode")
            self.connection = None
            return False
        except Exception as e:
            print(f"Warning: Unexpected error connecting to MariaDB: {e}")
            print("Database service will operate in limited mode")
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
            return self.connection.is_connected()
        except:
            return False

    def create_collection(self, collection_name: str, schema: Dict[str, Any]) -> bool:
        """
        Create a MariaDB table (collection)

        Args:
            collection_name: Name of the table to create
            schema: Schema definition (simplified - columns and types)

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

            # Create table with generic schema
            # Default schema: id (VARCHAR PRIMARY KEY), data (JSON), created_at (TIMESTAMP)
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
        except:
            return False

    def create_record(self, collection_name: str, record_id: str, record: Dict[str, Any]) -> bool:
        """
        Create a new row (record) in MariaDB (must not exist)

        Args:
            collection_name: Name of the table
            record_id: Unique identifier for the row
            record: Record data (stored as JSON)

        Returns:
            bool: True if successful, False if record already exists or error
        """
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()

            # Try to insert - will fail if ID exists
            insert_query = f"""
            INSERT INTO `{collection_name}` (id, data)
            VALUES (%s, %s)
            """
            cursor.execute(insert_query, (record_id, json.dumps(record)))
            cursor.close()
            return True

        except MySQLError as e:
            # Duplicate entry error
            if e.errno == 1062:
                return False
            print(f"Error creating record: {e}")
            return False

    def insert_record(self, collection_name: str, record: Dict[str, Any], record_id: Optional[str] = None) -> Optional[str]:
        """
        Insert a row (record) in MariaDB (create or update)

        Args:
            collection_name: Name of the table
            record: Record data (stored as JSON)
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

            # Use REPLACE to insert or update
            replace_query = f"""
            REPLACE INTO `{collection_name}` (id, data)
            VALUES (%s, %s)
            """
            cursor.execute(replace_query, (record_id, json.dumps(record)))
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
            cursor = self.connection.cursor(dictionary=True)
            select_query = f"SELECT data FROM `{collection_name}` WHERE id = %s"
            cursor.execute(select_query, (record_id,))
            row = cursor.fetchone()
            cursor.close()

            if row and 'data' in row:
                return json.loads(row['data'])
            return None

        except MySQLError as e:
            print(f"Error getting record: {e}")
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
        Search for rows (records) in MariaDB

        Args:
            collection_name: Name of the table
            query: Search query (JSON path queries for MariaDB)
            filters: Filter conditions (JSON path filters)
            sort: Sort specifications
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            list: List of matching records with id and data
        """
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)

            # Build WHERE clause for filters
            where_clauses = []
            params = []

            if filters:
                for field, value in filters.items():
                    # Use JSON_EXTRACT for filtering
                    where_clauses.append(f"JSON_EXTRACT(data, '$.{field}') = %s")
                    params.append(json.dumps(value) if not isinstance(value, str) else value)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            # Build ORDER BY clause
            order_sql = ""
            if sort:
                # Simplified sort - assumes sort is list of {field: order}
                sort_parts = []
                for sort_spec in sort:
                    for field, order in sort_spec.items():
                        direction = "DESC" if order == "desc" else "ASC"
                        sort_parts.append(f"JSON_EXTRACT(data, '$.{field}') {direction}")
                if sort_parts:
                    order_sql = f"ORDER BY {', '.join(sort_parts)}"

            # Build final query
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

            # Format results similar to Elasticsearch format
            results = []
            for row in rows:
                results.append({
                    '_id': row['id'],
                    '_source': json.loads(row['data'])
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
            delete_query = f"DELETE FROM `{collection_name}` WHERE id = %s"
            cursor.execute(delete_query, (record_id,))
            affected = cursor.rowcount
            cursor.close()
            return affected > 0

        except MySQLError as e:
            print(f"Error deleting record: {e}")
            return False

    def count_records(self, collection_name: str, query: Optional[Dict[str, Any]] = None) -> int:
        """
        Count rows (records) matching a query in MariaDB

        Args:
            collection_name: Name of the table
            query: Search query (JSON path queries)

        Returns:
            int: Number of matching records
        """
        if not self.connection:
            return 0

        try:
            cursor = self.connection.cursor()

            # Build WHERE clause if query provided
            where_sql = ""
            params = []
            if query:
                # Simplified - assumes query is field: value pairs
                where_clauses = []
                for field, value in query.items():
                    where_clauses.append(f"JSON_EXTRACT(data, '$.{field}') = %s")
                    params.append(json.dumps(value) if not isinstance(value, str) else value)
                where_sql = f"WHERE {' AND '.join(where_clauses)}"

            count_query = f"SELECT COUNT(*) as count FROM `{collection_name}` {where_sql}"
            cursor.execute(count_query, params)
            result = cursor.fetchone()
            cursor.close()

            return result[0] if result else 0

        except MySQLError as e:
            print(f"Error counting records: {e}")
            return 0
