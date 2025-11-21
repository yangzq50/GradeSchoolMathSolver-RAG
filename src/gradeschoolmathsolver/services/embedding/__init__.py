"""
Embedding Service Module

This module provides embedding generation capabilities using Docker Model Runner.
It supports the EmbeddingGemma model for generating vector embeddings of text inputs,
which are essential for RAG (Retrieval-Augmented Generation) functionality.
"""
from .service import EmbeddingService

__all__ = ['EmbeddingService']
