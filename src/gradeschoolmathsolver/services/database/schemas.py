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

# Default embedding column names for consistency across backends
DEFAULT_EMBEDDING_COLUMN_NAMES = ['question_embedding', 'equation_embedding']


def get_embedding_config() -> Dict[str, Any]:
    """
    Get embedding configuration from config.py

    Returns:
        Dict containing:
        - column_count: Number of embedding columns
        - dimensions: List of dimensions for each column
        - similarity: Elasticsearch vector similarity metric
        - column_names: List of embedding column names
    """
    from gradeschoolmathsolver.config import Config
    config = Config()

    column_count = config.EMBEDDING_COLUMN_COUNT
    dimensions = config.EMBEDDING_DIMENSIONS
    similarity = config.ELASTICSEARCH_VECTOR_SIMILARITY

    # Extend dimensions list if needed (apply last dimension to remaining columns)
    if len(dimensions) < column_count:
        last_dim = dimensions[-1] if dimensions else 768
        dimensions = dimensions + [last_dim] * (column_count - len(dimensions))

    # Generate column names (use defaults or generate based on count)
    if column_count <= len(DEFAULT_EMBEDDING_COLUMN_NAMES):
        column_names = DEFAULT_EMBEDDING_COLUMN_NAMES[:column_count]
    else:
        column_names = DEFAULT_EMBEDDING_COLUMN_NAMES.copy()
        for i in range(len(DEFAULT_EMBEDDING_COLUMN_NAMES), column_count):
            column_names.append(f'embedding_{i}')

    return {
        'column_count': column_count,
        'dimensions': dimensions,
        'similarity': similarity,
        'column_names': column_names
    }


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
    """
    fields = {}
    default_dim = 768  # Default dimension if dimensions list is empty
    for i, col_name in enumerate(column_names):
        if not dimensions:
            dim = default_dim
        elif i < len(dimensions):
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

    Args:
        column_names: List of embedding column names
        dimensions: List of dimensions for each column

    Returns:
        Dict of column name to column definition
    """
    columns = {}
    default_dim = 768  # Default dimension if dimensions list is empty
    for i, col_name in enumerate(column_names):
        if not dimensions:
            dim = default_dim
        elif i < len(dimensions):
            dim = dimensions[i]
        else:
            dim = dimensions[-1]
        # Use VECTOR type with specified dimension for native vector storage
        columns[col_name] = f"VECTOR({dim})"
    return columns


def get_embedding_indexes_mariadb(
    column_names: List[str]
) -> List[str]:
    """
    Generate MariaDB vector index definitions for embedding fields

    Creates vector indexes for efficient similarity search on embedding columns.
    MariaDB 11.8+ supports VECTOR INDEX for approximate nearest neighbor search.

    Args:
        column_names: List of embedding column names

    Returns:
        List of index definition strings
    """
    indexes = []
    for col_name in column_names:
        # Create vector index for each embedding column
        indexes.append(f"VECTOR INDEX idx_{col_name} ({col_name})")
    return indexes


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

    Args:
        backend: 'elasticsearch' or 'mariadb'
        include_embeddings: Whether to include embedding columns (default: True)

    Returns:
        Schema definition dict appropriate for the backend
    """
    # Get embedding configuration
    embedding_config = get_embedding_config()

    if backend == 'elasticsearch':
        properties: Dict[str, Any] = {
            "username": {"type": "keyword"},
            "question": {"type": "text"},
            "equation": {"type": "text"},
            "user_answer": {"type": "integer"},
            "correct_answer": {"type": "integer"},
            "is_correct": {"type": "boolean"},
            "category": {"type": "keyword"},
            "timestamp": {"type": "date"},
            "reviewed": {"type": "boolean"}
        }

        # Add embedding fields if enabled
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
        columns: Dict[str, str] = {
            "record_id": "VARCHAR(255) PRIMARY KEY",
            "username": "VARCHAR(255) NOT NULL",
            "question": "TEXT NOT NULL",
            "equation": "VARCHAR(500) NOT NULL",
            "user_answer": "INT",
            "correct_answer": "INT NOT NULL",
            "is_correct": "BOOLEAN NOT NULL",
            "category": "VARCHAR(100) NOT NULL",
            "timestamp": "TIMESTAMP NOT NULL",
            "reviewed": "BOOLEAN DEFAULT FALSE"
        }

        # Base indexes for standard columns
        indexes = [
            "INDEX idx_username (username)",
            "INDEX idx_timestamp (timestamp)",
            "INDEX idx_category (category)",
            "INDEX idx_reviewed (reviewed)"
        ]

        # Add embedding columns and vector indexes if enabled
        if include_embeddings:
            embedding_columns = get_embedding_columns_mariadb(
                embedding_config['column_names'],
                embedding_config['dimensions']
            )
            columns.update(embedding_columns)

            # Add vector indexes for embedding columns
            vector_indexes = get_embedding_indexes_mariadb(
                embedding_config['column_names']
            )
            indexes.extend(vector_indexes)

        return {
            "columns": columns,
            "indexes": indexes
        }
    else:
        raise ValueError(f"Unknown backend: {backend}")
