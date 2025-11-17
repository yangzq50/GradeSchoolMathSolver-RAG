"""
Configuration settings for the GradeSchoolMathSolver-RAG system

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
        AI_MODEL_URL: URL of the AI model service endpoint
        AI_MODEL_NAME: Name/identifier of the AI model to use
        LLM_ENGINE: LLM engine type (e.g., 'llama.cpp')

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

    Web UI Settings:
        FLASK_HOST: Flask server bind address
        FLASK_PORT: Flask server port
        FLASK_DEBUG: Enable Flask debug mode

    Question Settings:
        QUESTION_CATEGORIES: List of valid question categories
        DIFFICULTY_LEVELS: List of valid difficulty levels

    Service Toggles:
        TEACHER_SERVICE_ENABLED: Enable/disable teacher feedback feature
    """

    # AI Model Service Configuration
    AI_MODEL_URL = os.getenv('AI_MODEL_URL', 'http://localhost:12434')
    AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'ai/llama3.2:1B-Q4_0')
    LLM_ENGINE = os.getenv('LLM_ENGINE', 'llama.cpp')

    # Database Backend Selection
    DATABASE_BACKEND = os.getenv('DATABASE_BACKEND', 'elasticsearch')  # 'elasticsearch' or 'mariadb'

    # Elasticsearch Configuration
    ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'localhost')
    ELASTICSEARCH_PORT = int(os.getenv('ELASTICSEARCH_PORT', '9200'))
    ELASTICSEARCH_INDEX = os.getenv('ELASTICSEARCH_INDEX', 'quiz_history')

    # MariaDB Configuration
    MARIADB_HOST = os.getenv('MARIADB_HOST', 'localhost')
    MARIADB_PORT = int(os.getenv('MARIADB_PORT', '3306'))
    MARIADB_USER = os.getenv('MARIADB_USER', 'root')
    MARIADB_PASSWORD = os.getenv('MARIADB_PASSWORD', '')
    MARIADB_DATABASE = os.getenv('MARIADB_DATABASE', 'math_solver')

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
