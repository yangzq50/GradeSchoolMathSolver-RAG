"""
Configuration settings for the GradeSchoolMathSolver-RAG system
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # AI Model Service
    AI_MODEL_URL = os.getenv('AI_MODEL_URL', 'http://localhost:11434')
    AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'llama3.2')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/math_solver.db')
    
    # Elasticsearch
    ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'localhost')
    ELASTICSEARCH_PORT = int(os.getenv('ELASTICSEARCH_PORT', '9200'))
    ELASTICSEARCH_INDEX = os.getenv('ELASTICSEARCH_INDEX', 'quiz_history')
    
    # Web UI
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Question categories
    QUESTION_CATEGORIES = [
        'addition',
        'subtraction',
        'multiplication',
        'division',
        'mixed_operations',
        'parentheses',
        'fractions'
    ]
    
    # Difficulty levels
    DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']
