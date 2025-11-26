"""
Database Schema Definitions

Defines the data structures used across all database backends.
Each schema class represents one record (row/document) in a collection (table/index).

These schemas are backend-agnostic and can be used for:
- Elasticsearch: Convert to JSON documents
- MariaDB: Map to table columns with proper types
- Other backends: Easy to extend

When adding new fields:
1. Add the field to the appropriate schema class
2. Fresh deployments will automatically use the new schema
3. For existing deployments, add migration logic if needed

Embedding Storage:
The schema supports configurable embedding columns for RAG features.
Configuration is read from config.py:
- EMBEDDING_COLUMN_COUNT: Number of embedding columns (default: 2)
- EMBEDDING_DIMENSIONS: Dimension for each column (default: 768)
- EMBEDDING_COLUMN_NAMES: Names for each column (default: question_embedding,equation_embedding)
- EMBEDDING_SOURCE_COLUMNS: Source text columns for embedding generation (default: question,equation)
- ELASTICSEARCH_VECTOR_SIMILARITY: Similarity metric (default: cosine)
"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, asdict


@dataclass
class UserRecord:
    """
    User account record

    Stores basic user information and account creation timestamp.

    Fields:
        username: Unique username (primary key)
        created_at: ISO timestamp of account creation
    """
    username: str
    created_at: str  # ISO format datetime string

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserRecord':
        """Create from dictionary (database retrieval)"""
        return cls(
            username=data['username'],
            created_at=data['created_at']
        )

    @classmethod
    def create_new(cls, username: str) -> 'UserRecord':
        """Create a new user record with current timestamp"""
        return cls(
            username=username,
            created_at=datetime.utcnow().isoformat()
        )


@dataclass
class AnswerHistoryRecord:
    """
    Answer history record (quiz_history collection)

    Stores each answer a user submits during exams.
    Unified schema combining answer history and quiz history.

    Fields:
        username: Username who answered the question
        question: Full text of the math problem
        equation: Mathematical equation to solve
        user_answer: User's submitted answer (None if skipped)
        correct_answer: The correct answer
        is_correct: Whether user_answer == correct_answer
        category: Question category (e.g., 'addition', 'multiplication')
        timestamp: ISO timestamp when answer was recorded
        reviewed: Whether this mistake has been reviewed (for mistake tracking)
        record_id: Optional unique ID for the record (auto-generated if not provided)
    """
    username: str
    question: str
    equation: str
    user_answer: Optional[int]
    correct_answer: int
    is_correct: bool
    category: str
    timestamp: str  # ISO format datetime string
    reviewed: bool = False
    record_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        # Remove record_id from stored data (it's used as primary key)
        if 'record_id' in data:
            del data['record_id']
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], record_id: Optional[str] = None) -> 'AnswerHistoryRecord':
        """Create from dictionary (database retrieval)"""
        return cls(
            username=data['username'],
            question=data['question'],
            equation=data['equation'],
            user_answer=data.get('user_answer'),
            correct_answer=data['correct_answer'],
            is_correct=data['is_correct'],
            category=data['category'],
            timestamp=data['timestamp'],
            reviewed=data.get('reviewed', False),
            record_id=record_id
        )

    @classmethod
    def create_new(
        cls,
        username: str,
        question: str,
        equation: str,
        user_answer: Optional[int],
        correct_answer: int,
        category: str,
        reviewed: bool = False
    ) -> 'AnswerHistoryRecord':
        """Create a new answer history record with current timestamp"""
        is_correct = user_answer is not None and user_answer == correct_answer
        return cls(
            username=username,
            question=question,
            equation=equation,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            category=category,
            timestamp=datetime.utcnow().isoformat(),
            reviewed=reviewed,
            record_id=None  # Will be auto-generated
        )


# Schema type mappings for different backends

# Elasticsearch field type mapping
ELASTICSEARCH_TYPE_MAPPING = {
    'str': 'keyword',  # Use keyword for exact matching
    'text': 'text',    # Use text for full-text search
    'int': 'integer',
    'bool': 'boolean',
    'datetime': 'date',
    'Optional[int]': 'integer'
}

# MariaDB column type mapping
MARIADB_TYPE_MAPPING = {
    'str': 'VARCHAR(255)',
    'text': 'TEXT',
    'int': 'INT',
    'bool': 'BOOLEAN',
    'datetime': 'TIMESTAMP',
    'Optional[int]': 'INT'
}


# ============================================================================
# Answer History Schema Definition (common for all backends)
# ============================================================================
# This is the single source of truth for the answer_history schema columns.
# Each entry: (column_name, elasticsearch_type, mariadb_type, is_text_column)
# The is_text_column flag indicates if this column can be used as an embedding source.
ANSWER_HISTORY_SCHEMA_COLUMNS = [
    ('record_id', 'keyword', 'VARCHAR(255) PRIMARY KEY', False),
    ('username', 'keyword', 'VARCHAR(255) NOT NULL', False),
    ('question', 'text', 'TEXT NOT NULL', True),  # Text column - can be embedding source
    ('equation', 'text', 'VARCHAR(500) NOT NULL', True),  # Text column - can be embedding source
    ('user_answer', 'integer', 'INT', False),
    ('correct_answer', 'integer', 'INT NOT NULL', False),
    ('is_correct', 'boolean', 'BOOLEAN NOT NULL', False),
    ('category', 'keyword', 'VARCHAR(100) NOT NULL', False),
    ('timestamp', 'date', 'TIMESTAMP NOT NULL', False),
    ('reviewed', 'boolean', 'BOOLEAN DEFAULT FALSE', False),
]

# Standard indexes for answer_history (non-embedding indexes)
ANSWER_HISTORY_INDEXES = [
    'INDEX idx_username (username)',
    'INDEX idx_timestamp (timestamp)',
    'INDEX idx_category (category)',
    'INDEX idx_reviewed (reviewed)',
]


def get_answer_history_text_columns() -> List[str]:
    """
    Get list of text columns that can be used as embedding sources.

    Returns:
        List of column names that are text columns in the answer_history schema.
    """
    return [col[0] for col in ANSWER_HISTORY_SCHEMA_COLUMNS if col[3]]


def get_embedding_config() -> Dict[str, Any]:
    """
    Get embedding configuration from config.py

    Returns:
        Dict containing:
        - column_count: Number of embedding columns
        - dimensions: List of dimensions for each column
        - similarity: Elasticsearch vector similarity metric
        - column_names: List of embedding column names
        - source_columns: List of source text columns for embedding generation

    Raises:
        ValueError: If configuration validation fails (e.g., mismatched counts)
    """
    from gradeschoolmathsolver.config import Config
    config = Config()

    column_count = config.EMBEDDING_COLUMN_COUNT
    dimensions = config.EMBEDDING_DIMENSIONS
    similarity = config.ELASTICSEARCH_VECTOR_SIMILARITY
    column_names = config.EMBEDDING_COLUMN_NAMES
    source_columns = config.EMBEDDING_SOURCE_COLUMNS

    # Extend dimensions list if needed (apply last dimension to remaining columns)
    if len(dimensions) < column_count:
        last_dim = dimensions[-1]
        dimensions = dimensions + [last_dim] * (column_count - len(dimensions))

    # Extend column names list if needed (generate names for additional columns)
    if len(column_names) < column_count:
        for i in range(len(column_names), column_count):
            column_names = column_names + [f'embedding_{i}']

    # Extend source columns list if needed (generate names for additional columns)
    if len(source_columns) < column_count:
        for i in range(len(source_columns), column_count):
            source_columns = source_columns + [f'source_{i}']

    # Truncate lists to match column_count
    column_names = column_names[:column_count]
    dimensions = dimensions[:column_count]
    source_columns = source_columns[:column_count]

    return {
        'column_count': column_count,
        'dimensions': dimensions,
        'similarity': similarity,
        'column_names': column_names,
        'source_columns': source_columns
    }


def get_embedding_source_mapping() -> Dict[str, str]:
    """
    Get mapping from source text columns to embedding columns.

    This function provides a convenient way to determine which source column
    should be used to generate each embedding column. Services can use this
    to know where to get the text for embedding generation.

    Returns:
        Dict mapping source column name -> embedding column name
        Example: {'question': 'question_embedding', 'equation': 'equation_embedding'}
    """
    config = get_embedding_config()
    source_columns = config['source_columns']
    column_names = config['column_names']

    return {
        source: embedding
        for source, embedding in zip(source_columns, column_names)
    }


def validate_embedding_config(valid_source_columns: List[str]) -> bool:
    """
    Validate embedding configuration for consistency.

    Checks that:
    - EMBEDDING_COLUMN_COUNT matches the length of column names and source columns
    - All lists are properly aligned after extension/truncation
    - Source columns exist in the provided valid source columns list

    Args:
        valid_source_columns: List of valid source column names from the database schema.
                              All configured source columns must exist in this list.

    Returns:
        True if configuration is valid

    Raises:
        ValueError: If configuration is invalid with details about the issue
    """
    config = get_embedding_config()

    column_count = config['column_count']
    if len(config['column_names']) != column_count:
        raise ValueError(
            f"Column names count ({len(config['column_names'])}) "
            f"does not match EMBEDDING_COLUMN_COUNT ({column_count})"
        )

    if len(config['source_columns']) != column_count:
        raise ValueError(
            f"Source columns count ({len(config['source_columns'])}) "
            f"does not match EMBEDDING_COLUMN_COUNT ({column_count})"
        )

    if len(config['dimensions']) != column_count:
        raise ValueError(
            f"Dimensions count ({len(config['dimensions'])}) "
            f"does not match EMBEDDING_COLUMN_COUNT ({column_count})"
        )

    # Validate source columns exist in the database schema
    for source_col in config['source_columns']:
        if source_col not in valid_source_columns:
            raise ValueError(
                f"Source column '{source_col}' does not exist in database schema. "
                f"Valid source columns are: {valid_source_columns}"
            )

    return True


def get_embedding_fields_elasticsearch(
    column_names: List[str],
    dimensions: List[int],
    similarity: str = 'cosine'
) -> Dict[str, Any]:
    """
    Generate Elasticsearch mapping for embedding fields

    Uses dense_vector type with configurable dimensions and similarity.

    Args:
        column_names: List of embedding column names
        dimensions: List of dimensions for each column
        similarity: Similarity metric ('cosine', 'dot_product', 'l2_norm')

    Returns:
        Dict of field mappings for Elasticsearch

    Raises:
        ValueError: If dimensions list is empty
    """
    if not dimensions:
        raise ValueError("dimensions list cannot be empty")

    fields = {}
    for i, col_name in enumerate(column_names):
        if i < len(dimensions):
            dim = dimensions[i]
        else:
            dim = dimensions[-1]
        fields[col_name] = {
            "type": "dense_vector",
            "dims": dim,
            "index": True,
            "similarity": similarity
        }
    return fields


def get_embedding_columns_mariadb(
    column_names: List[str],
    dimensions: List[int]
) -> Dict[str, str]:
    """
    Generate MariaDB column definitions for embedding fields

    Uses VECTOR(dim) type for native vector storage in MariaDB 11.8+.
    This enables efficient vector similarity search using vector indexes.

    Note: VECTOR columns must be NOT NULL for vector indexing to work in MariaDB.
    MariaDB requires all parts of a VECTOR index to be NOT NULL.

    Args:
        column_names: List of embedding column names
        dimensions: List of dimensions for each column

    Returns:
        Dict of column name to column definition

    Raises:
        ValueError: If dimensions list is empty
    """
    if not dimensions:
        raise ValueError("dimensions list cannot be empty")

    columns = {}
    for i, col_name in enumerate(column_names):
        if i < len(dimensions):
            dim = dimensions[i]
        else:
            dim = dimensions[-1]
        # Use VECTOR type with NOT NULL constraint for vector index compatibility
        # MariaDB requires NOT NULL for all parts of a VECTOR index
        columns[col_name] = f"VECTOR({dim}) NOT NULL"
    return columns


def get_embedding_indexes_mariadb(
    column_names: List[str]
) -> List[str]:
    """
    Generate MariaDB vector index definitions for embedding fields

    Note: MariaDB doesn't support multiple VECTOR indexes on the same table.
    Embeddings are now stored in separate tables (one per embedding column),
    so this function returns an empty list since indexes are created per-table.

    Args:
        column_names: List of embedding column names

    Returns:
        Empty list (indexes are created in separate embedding tables)
    """
    # MariaDB doesn't support multiple VECTOR indexes on same table
    # Each embedding column gets its own table with its own index
    return []


def get_embedding_table_schemas_mariadb(
    base_table_name: str,
    embedding_config: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Generate separate table schemas for each embedding column in MariaDB.

    MariaDB doesn't support multiple VECTOR indexes on the same table.
    This function creates a separate table for each embedding column.
    Each table has:
    - record_id: PRIMARY KEY that references the main table
    - embedding: VECTOR column with a VECTOR INDEX

    Note: The record_id is limited to VARCHAR(64) because MariaDB vector indexes
    require primary keys to be max 256 bytes. VARCHAR(64) with UTF-8 is safe.

    Args:
        base_table_name: Name of the main table (e.g., 'quiz_history')
        embedding_config: Embedding configuration from get_embedding_config()

    Returns:
        Dict mapping table_name -> schema dict with 'columns' and 'indexes'
        Example: {
            'quiz_history_question_embedding': {
                'columns': {...},
                'indexes': [...]
            },
            ...
        }
    """
    column_names = embedding_config['column_names']
    dimensions = embedding_config['dimensions']

    tables = {}
    for i, col_name in enumerate(column_names):
        dim = dimensions[i] if i < len(dimensions) else dimensions[-1]
        table_name = f"{base_table_name}_{col_name}"

        tables[table_name] = {
            "columns": {
                # Use VARCHAR(64) for record_id because MariaDB vector indexes
                # require primary key to be max 256 bytes
                "record_id": "VARCHAR(64) PRIMARY KEY",
                "embedding": f"VECTOR({dim}) NOT NULL"
            },
            "indexes": [
                "VECTOR INDEX idx_embedding (embedding)"
            ]
        }

    return tables


def get_embedding_table_name(base_table_name: str, embedding_col_name: str) -> str:
    """
    Get the table name for a specific embedding column.

    Args:
        base_table_name: Name of the main table (e.g., 'quiz_history')
        embedding_col_name: Name of the embedding column

    Returns:
        Table name for the embedding (e.g., 'quiz_history_question_embedding')
    """
    return f"{base_table_name}_{embedding_col_name}"


def get_user_schema_for_backend(backend: str) -> Dict[str, Any]:
    """
    Get users collection schema for specific database backend

    Args:
        backend: 'elasticsearch' or 'mariadb'

    Returns:
        Schema definition dict appropriate for the backend
    """
    if backend == 'elasticsearch':
        return {
            "mappings": {
                "properties": {
                    "username": {"type": "keyword"},
                    "created_at": {"type": "date"}
                }
            }
        }
    elif backend == 'mariadb':
        return {
            "columns": {
                "username": "VARCHAR(255) PRIMARY KEY",
                "created_at": "TIMESTAMP NOT NULL"
            },
            "indexes": []
        }
    else:
        raise ValueError(f"Unknown backend: {backend}")


def get_answer_history_schema_for_backend(
    backend: str,
    include_embeddings: bool = True
) -> Dict[str, Any]:
    """
    Get answer history (quiz_history) collection schema for specific database backend

    Uses ANSWER_HISTORY_SCHEMA_COLUMNS as the single source of truth for column definitions.
    Validates embedding configuration using the actual schema columns.

    For MariaDB: Embeddings are stored in separate tables (one per embedding column)
    because MariaDB doesn't support multiple VECTOR indexes on the same table.
    Use get_embedding_table_schemas_mariadb() to get the embedding table schemas.

    Args:
        backend: 'elasticsearch' or 'mariadb'
        include_embeddings: Whether to include embedding columns (default: True)
                           For MariaDB, this only validates config - embeddings go in separate tables

    Returns:
        Schema definition dict appropriate for the backend

    Raises:
        ValueError: If embedding configuration is invalid (when include_embeddings is True)
    """
    # Get embedding configuration
    embedding_config = get_embedding_config()

    # Get valid source columns from the real schema definition
    valid_source_columns = get_answer_history_text_columns()

    # Validate embedding configuration if embeddings are enabled
    if include_embeddings:
        validate_embedding_config(valid_source_columns)

    if backend == 'elasticsearch':
        # Build properties from the common schema definition
        properties: Dict[str, Any] = {}
        for col_name, es_type, _, _ in ANSWER_HISTORY_SCHEMA_COLUMNS:
            # Skip record_id for Elasticsearch (it uses _id)
            if col_name == 'record_id':
                continue
            properties[col_name] = {"type": es_type}

        # Add embedding fields if enabled (Elasticsearch supports multiple vector fields)
        if include_embeddings:
            embedding_fields = get_embedding_fields_elasticsearch(
                embedding_config['column_names'],
                embedding_config['dimensions'],
                embedding_config['similarity']
            )
            properties.update(embedding_fields)

        return {
            "mappings": {
                "properties": properties
            }
        }
    elif backend == 'mariadb':
        # Build columns from the common schema definition
        # Note: Embedding columns are NOT included here for MariaDB
        # They are stored in separate tables (see get_embedding_table_schemas_mariadb)
        columns: Dict[str, str] = {}
        for col_name, _, maria_type, _ in ANSWER_HISTORY_SCHEMA_COLUMNS:
            columns[col_name] = maria_type

        # Use the predefined indexes (no vector indexes here)
        indexes = list(ANSWER_HISTORY_INDEXES)

        return {
            "columns": columns,
            "indexes": indexes
        }
    else:
        raise ValueError(f"Unknown backend: {backend}")
