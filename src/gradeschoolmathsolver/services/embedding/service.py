"""
Embedding Service
Generates vector embeddings using the EmbeddingGemma model via Docker Model Runner
"""
from typing import List, Optional, Union
import logging
import requests
from requests.exceptions import RequestException, Timeout
from gradeschoolmathsolver.config import Config

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

    def _call_embedding_api(self, text: Union[str, List[str]]) -> Optional[List[List[float]]]:
        """
        Make API call to generate embeddings

        Note: This uses LLM_ENGINE from config for endpoint construction.
        Docker Model Runner uses the same engine path for both LLM and embedding models.

        Args:
            text: Single text string or list of text strings

        Returns:
            List of embedding vectors (list of floats), or None if API call fails
        """
        # Normalize input to list
        if isinstance(text, str):
            texts = [text]
        else:
            texts = text

        try:
            # Docker Model Runner uses OpenAI-compatible embeddings endpoint
            # The endpoint format: /engines/{engine}/v1/embeddings
            response = requests.post(
                f"{self.config.EMBEDDING_MODEL_URL}/engines/{self.config.LLM_ENGINE}/v1/embeddings",
                json={
                    "model": self.config.EMBEDDING_MODEL_NAME,
                    "input": texts
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                # OpenAI embeddings API format: {"data": [{"embedding": [...]}], ...}
                data = result.get('data', [])
                if data:
                    embeddings = [item.get('embedding', []) for item in data]
                    # Return None if any embedding is empty or missing
                    if embeddings and all(len(e) > 0 for e in embeddings):
                        return embeddings

            return None

        except (Timeout, RequestException) as e:
            logger.warning(f"Embedding API call failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in embedding API call: {e}")
            return None

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
        if not text or not isinstance(text, str):
            logger.warning("Invalid input: text must be a non-empty string")
            return None

        # Try with retries
        for attempt in range(self.max_retries):
            embeddings = self._call_embedding_api(text)

            if embeddings and len(embeddings) > 0:
                return embeddings[0]

            if attempt < self.max_retries - 1:
                logger.info(f"Embedding generation attempt {attempt + 1}/{self.max_retries} failed, retrying...")

        logger.warning(f"Failed to generate embedding after {self.max_retries} attempts")
        return None

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
        if not texts or not isinstance(texts, list):
            logger.warning("Invalid input: texts must be a non-empty list")
            return []

        # Create index mapping and filter valid texts
        valid_indices = []
        valid_texts = []
        for i, text in enumerate(texts):
            if text and isinstance(text, str):
                valid_indices.append(i)
                valid_texts.append(text)

        if not valid_texts:
            logger.warning("No valid texts to embed")
            # Return list of None matching input length
            return [None] * len(texts)

        # Try with retries
        embeddings_result = None
        for attempt in range(self.max_retries):
            embeddings_result = self._call_embedding_api(valid_texts)

            if embeddings_result:
                break

            if attempt < self.max_retries - 1:
                logger.info(f"Batch embedding generation attempt {attempt + 1}/{self.max_retries} failed, retrying...")

        # Create output list matching input size, with None for invalid/empty texts
        output: List[Optional[List[float]]] = [None] * len(texts)

        if embeddings_result:
            # Map valid embeddings back to their original positions
            for valid_idx, embedding in zip(valid_indices, embeddings_result):
                output[valid_idx] = embedding
        else:
            logger.warning(f"Failed to generate batch embeddings after {self.max_retries} attempts")

        return output

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
        try:
            # Try a simple embedding with minimal text
            result = self._call_embedding_api("test")
            return result is not None and len(result) > 0
        except Exception:
            return False


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
