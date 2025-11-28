"""
Configuration settings for the GradeSchoolMathSolver system

This module manages all application configuration settings loaded from environment
variables with sensible defaults. It provides centralized configuration for:
- AI model service endpoints and authentication
- Database connections (Elasticsearch and MariaDB)
- Web server settings
- Question generation parameters
- Service feature toggles

Environment variables can be set via .env file or system environment.
See .env.example for all available configuration options.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Application configuration class

    All settings are loaded from environment variables with fallback defaults.
    Configuration is immutable after initialization.

    AI Model Service:
        AI_MODEL_URL: URL of the AI model service endpoint (deprecated, use GENERATION_SERVICE_URL)
        AI_MODEL_NAME: Name/identifier of the AI model to use (deprecated, use GENERATION_MODEL_NAME)
        LLM_ENGINE: LLM engine type (e.g., 'llama.cpp')
        GENERATION_SERVICE_URL: Full URL for text generation endpoint
        GENERATION_MODEL_NAME: Name of the generation model

    Embedding Service:
        EMBEDDING_MODEL_URL: URL of the embedding service endpoint (deprecated, use EMBEDDING_SERVICE_URL)
        EMBEDDING_MODEL_NAME: Name/identifier of the embedding model to use
        EMBEDDING_SERVICE_URL: Full URL for embedding endpoint

    Database Settings:
        DATABASE_BACKEND: Database backend to use ('elasticsearch' or 'mariadb')
        ELASTICSEARCH_HOST: Elasticsearch server hostname
        ELASTICSEARCH_PORT: Elasticsearch server port
        ELASTICSEARCH_INDEX: Name of the Elasticsearch index
        MARIADB_HOST: MariaDB server hostname
        MARIADB_PORT: MariaDB server port
        MARIADB_USER: MariaDB username
        MARIADB_PASSWORD: MariaDB password
        MARIADB_DATABASE: MariaDB database name
        DB_MAX_RETRIES: Maximum number of database connection retry attempts
        DB_RETRY_DELAY: Initial delay between connection retries in seconds

    Web UI Settings:
        FLASK_HOST: Flask server bind address
        FLASK_PORT: Flask server port
        FLASK_DEBUG: Enable Flask debug mode

    Question Settings:
        QUESTION_CATEGORIES: List of valid question categories
        DIFFICULTY_LEVELS: List of valid difficulty levels

    Service Toggles:
        TEACHER_SERVICE_ENABLED: Enable/disable teacher feedback feature

    Embedding Storage Settings:
        EMBEDDING_COLUMN_COUNT: Number of embedding columns per record (default: 2)
        EMBEDDING_DIMENSIONS: Dimension(s) for each embedding column (default: 768)
        EMBEDDING_COLUMN_NAMES: Column names for embeddings (default: question_embedding,equation_embedding)
        EMBEDDING_SOURCE_COLUMNS: Source text columns for embedding generation (default: question,equation)
        ELASTICSEARCH_VECTOR_SIMILARITY: Similarity metric for vector search (default: cosine)
    """

    # AI Model Service Configuration
    AI_MODEL_URL = os.getenv('AI_MODEL_URL', 'http://localhost:12434')
    AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'ai/llama3.2:1B-Q4_0')
    LLM_ENGINE = os.getenv('LLM_ENGINE', 'llama.cpp')

    # New configurable service endpoints
    _default_base_url = os.getenv('AI_MODEL_URL', 'http://localhost:12434')
    _default_engine = os.getenv('LLM_ENGINE', 'llama.cpp')
    GENERATION_SERVICE_URL = os.getenv(
        'GENERATION_SERVICE_URL',
        f"{_default_base_url}/engines/{_default_engine}/v1/chat/completions"
    )
    GENERATION_MODEL_NAME = os.getenv(
        'GENERATION_MODEL_NAME',
        os.getenv('AI_MODEL_NAME', 'ai/llama3.2:1B-Q4_0')
    )

    # Embedding Service Configuration
    EMBEDDING_MODEL_URL = os.getenv('EMBEDDING_MODEL_URL', 'http://localhost:12434')
    EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'ai/embeddinggemma:300M-Q8_0')

    # New configurable embedding endpoint
    _default_embed_url = os.getenv('EMBEDDING_MODEL_URL', 'http://localhost:12434')
    EMBEDDING_SERVICE_URL = os.getenv(
        'EMBEDDING_SERVICE_URL',
        f"{_default_embed_url}/engines/{_default_engine}/v1/embeddings"
    )

    # Database Backend Selection
    DATABASE_BACKEND = os.getenv('DATABASE_BACKEND', 'mariadb')  # 'elasticsearch' or 'mariadb'

    # Elasticsearch Configuration
    ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'localhost')
    ELASTICSEARCH_PORT = int(os.getenv('ELASTICSEARCH_PORT', '9200'))
    ELASTICSEARCH_INDEX = os.getenv('ELASTICSEARCH_INDEX', 'quiz_history')

    # MariaDB Configuration
    MARIADB_HOST = os.getenv('MARIADB_HOST', 'localhost')
    MARIADB_PORT = int(os.getenv('MARIADB_PORT', '3306'))
    MARIADB_USER = os.getenv('MARIADB_USER', 'math_solver')
    MARIADB_PASSWORD = os.getenv('MARIADB_PASSWORD', 'math_solver_password')
    MARIADB_DATABASE = os.getenv('MARIADB_DATABASE', 'math_solver')

    # Database Connection Retry Configuration
    DB_MAX_RETRIES = int(os.getenv('DB_MAX_RETRIES', '12'))
    DB_RETRY_DELAY = float(os.getenv('DB_RETRY_DELAY', '5.0'))

    # Web UI Configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Question categories for classification
    QUESTION_CATEGORIES = [
        'addition',
        'subtraction',
        'multiplication',
        'division',
        'mixed_operations',
        'parentheses',
        'fractions'
    ]

    # Supported difficulty levels
    DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']

    # Teacher Service Configuration
    TEACHER_SERVICE_ENABLED = os.getenv('TEACHER_SERVICE_ENABLED', 'True').lower() == 'true'

    # Embedding Storage Configuration
    # Number of embedding columns to store per record (e.g., question_embedding, equation_embedding)
    EMBEDDING_COLUMN_COUNT = int(os.getenv('EMBEDDING_COLUMN_COUNT', '2'))

    # Dimension of each embedding column (typically 768 for EmbeddingGemma)
    # Can be a single value (applied to all columns) or comma-separated list for each column
    _embedding_dims_str = os.getenv('EMBEDDING_DIMENSIONS', '768')
    EMBEDDING_DIMENSIONS = [int(d.strip()) for d in _embedding_dims_str.split(',')]

    # Embedding column names (comma-separated list)
    # Default: question_embedding,equation_embedding
    _embedding_names_str = os.getenv('EMBEDDING_COLUMN_NAMES', 'question_embedding,equation_embedding')
    EMBEDDING_COLUMN_NAMES = [name.strip() for name in _embedding_names_str.split(',')]

    # Source text columns for embedding generation (comma-separated list)
    # Each source column corresponds to an embedding column at the same index.
    # For example, with EMBEDDING_COLUMN_NAMES='question_embedding,equation_embedding'
    # and EMBEDDING_SOURCE_COLUMNS='question,equation', the 'question' field generates
    # 'question_embedding' and 'equation' field generates 'equation_embedding'.
    # Default: question,equation (maps to question_embedding and equation_embedding)
    _embedding_source_str = os.getenv('EMBEDDING_SOURCE_COLUMNS', 'question,equation')
    EMBEDDING_SOURCE_COLUMNS = [name.strip() for name in _embedding_source_str.split(',')]

    # Elasticsearch-specific: similarity metric for vector search
    # Options: 'cosine', 'dot_product', 'l2_norm'
    ELASTICSEARCH_VECTOR_SIMILARITY = os.getenv('ELASTICSEARCH_VECTOR_SIMILARITY', 'cosine')
