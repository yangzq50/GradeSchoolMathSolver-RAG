"""Configuration settings for GradeSchoolMathSolver-RAG"""

import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./math_solver.db")

# LLaMA model configuration
LLAMA_MODEL_NAME = os.getenv("LLAMA_MODEL_NAME", "meta-llama/Llama-3.2-1B")

# RAG configuration
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# API configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Problem generation settings
PROBLEM_TYPES = ["addition", "subtraction", "multiplication", "division"]
MIN_NUMBER = 1
MAX_NUMBER = 100
