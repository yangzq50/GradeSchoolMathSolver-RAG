"""
Embedding Service
Generates vector embeddings using the EmbeddingGemma model via Docker Model Runner

This service now wraps the centralized model_access module for consistency.
All actual HTTP calls to the embedding model are handled by model_access.
"""
from typing import List, Optional, Union
import logging
from gradeschoolmathsolver.config import Config
from gradeschoolmathsolver import model_access

# Configure logging
logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using Docker Model Runner

    This service interfaces with the EmbeddingGemma model (ai/embeddinggemma:300M-Q8_0)
    to generate vector embeddings for text inputs. These embeddings enable:
    - Semantic similarity search
    - Vector-based retrieval for RAG
    - Efficient question matching in quiz history

    The service is designed to work with Docker Desktop's Model Runner, which provides
    an OpenAI-compatible API at localhost:12434 by default.

    Note: This service now uses the centralized model_access module for all
    HTTP interactions with the embedding model.

    Attributes:
        config: Configuration object with embedding model settings
        max_retries: Maximum number of retry attempts for API calls
        timeout: Request timeout in seconds
    """

    def __init__(self, max_retries: int = 3, timeout: int = 30):
        """
        Initialize the embedding service

        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            timeout: Request timeout in seconds (default: 30)
        """
        self.config = Config()
        self.max_retries = max_retries
        self.timeout = timeout

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for a single text input with retry logic

        This method converts text into a dense vector representation that captures
        semantic meaning. The embedding can be used for similarity search and RAG.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector (list of floats), or None if generation fails after all retries

        Example:
            >>> service = EmbeddingService()
            >>> embedding = service.generate_embedding("What is 5 + 3?")
            >>> print(len(embedding))  # Typically 768 or similar dimension
            768
        """
        return model_access.generate_embedding(
            text,
            max_retries=self.max_retries,
            timeout=self.timeout
        )

    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in a single API call

        This is more efficient than calling generate_embedding() multiple times
        as it batches the requests to the embedding model.

        Note: Empty or invalid strings are preserved in the output as None values
        to maintain index correspondence with the input list.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each is a list of floats).
            Returns None for any text that is empty, invalid, or failed to embed.
            The output list length matches the input list length.

        Example:
            >>> service = EmbeddingService()
            >>> texts = ["What is 5 + 3?", "", "Calculate 10 - 4"]
            >>> embeddings = service.generate_embeddings_batch(texts)
            >>> print(len(embeddings))  # 3 - same as input
            3
            >>> print(embeddings[1] is None)  # Empty string -> None
            True
        """
        return model_access.generate_embeddings_batch(
            texts,
            max_retries=self.max_retries,
            timeout=self.timeout
        )

    def is_available(self) -> bool:
        """
        Check if the embedding service is available

        This makes a lightweight test call to verify the embedding model
        is accessible and responding.

        Returns:
            True if service is available, False otherwise

        Example:
            >>> service = EmbeddingService()
            >>> if service.is_available():
            ...     embedding = service.generate_embedding("test")
        """
        return model_access.is_embedding_service_available()


def main():
    """
    Test the embedding service

    This function demonstrates basic usage of the embedding service
    and can be used for manual testing.
    """
    print("Testing Embedding Service...")
    print("=" * 60)

    service = EmbeddingService()

    # Test 1: Check if service is available
    print("\n1. Checking if embedding service is available...")
    if service.is_available():
        print("✓ Embedding service is available")
    else:
        print("✗ Embedding service is NOT available")
        print("  Make sure Docker Model Runner is running with the embedding model")
        print("  Model: ai/embeddinggemma:300M-Q8_0")
        return

    # Test 2: Generate single embedding
    print("\n2. Generating embedding for a single question...")
    test_text = "What is 5 + 3?"
    embedding = service.generate_embedding(test_text)

    if embedding:
        print(f"✓ Generated embedding for: '{test_text}'")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
    else:
        print(f"✗ Failed to generate embedding for: '{test_text}'")

    # Test 3: Generate batch embeddings
    print("\n3. Generating embeddings for multiple questions...")
    test_texts = [
        "Calculate 10 - 4",
        "What is 7 * 6?",
        "Solve: 20 / 5"
    ]
    embeddings = service.generate_embeddings_batch(test_texts)

    if embeddings and all(e is not None for e in embeddings):
        print(f"✓ Generated {len(embeddings)} embeddings")
        for i, text in enumerate(test_texts):
            print(f"  {i+1}. '{text}' -> {len(embeddings[i])} dimensions")
    else:
        print("✗ Failed to generate batch embeddings")

    # Test 4: Test error handling
    print("\n4. Testing error handling...")
    invalid_embedding = service.generate_embedding("")
    if invalid_embedding is None:
        print("✓ Correctly handled empty string input")
    else:
        print("✗ Should have returned None for empty string")

    print("\n" + "=" * 60)
    print("Embedding service testing complete!")


if __name__ == "__main__":
    main()
