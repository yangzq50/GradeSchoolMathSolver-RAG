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
"""

from datetime import datetime
from typing import Optional, Any, Dict
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


def get_answer_history_schema_for_backend(backend: str) -> Dict[str, Any]:
    """
    Get answer history (quiz_history) collection schema for specific database backend

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
                    "question": {"type": "text"},
                    "equation": {"type": "text"},
                    "user_answer": {"type": "integer"},
                    "correct_answer": {"type": "integer"},
                    "is_correct": {"type": "boolean"},
                    "category": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "reviewed": {"type": "boolean"}
                }
            }
        }
    elif backend == 'mariadb':
        return {
            "columns": {
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
            },
            "indexes": [
                "INDEX idx_username (username)",
                "INDEX idx_timestamp (timestamp)",
                "INDEX idx_category (category)",
                "INDEX idx_reviewed (reviewed)"
            ]
        }
    else:
        raise ValueError(f"Unknown backend: {backend}")
