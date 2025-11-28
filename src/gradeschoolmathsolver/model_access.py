"""
Model Access Module

This module provides a centralized interface for all AI model interactions.
It consolidates HTTP calls to both embedding and text generation services,
providing a single point of configuration and maintenance.

All business logic should call into this module rather than directly
accessing model endpoints.

Configuration:
    Model endpoints and names are configured via environment variables:
    - EMBEDDING_SERVICE_URL: Full URL for embedding endpoint
    - EMBEDDING_MODEL_NAME: Name of the embedding model
    - GENERATION_SERVICE_URL: Full URL for text generation endpoint
    - GENERATION_MODEL_NAME: Name of the generation model

Example Usage:
    # Generate text completion
    response = generate_text_completion(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ]
    )

    # Generate embeddings
    embedding = generate_embedding("What is 5 + 3?")

    # Generate batch embeddings
    embeddings = generate_embeddings_batch(["Question 1", "Question 2"])
"""
from typing import List, Optional, Dict, Any
import logging
import requests
from requests.exceptions import RequestException, Timeout
from gradeschoolmathsolver.config import Config

# Configure logging
logger = logging.getLogger(__name__)

# HTTP status codes
HTTP_OK = 200


def generate_text_completion(
    messages: List[Dict[str, str]],
    max_retries: int = 3,
    timeout: int = 30,
    **kwargs: Any
) -> Optional[str]:
    """
    Generate text completion using the configured LLM service.

    This is the single entry point for all text generation requests in the system.
    It handles retries, error handling, and provides a consistent interface.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
                 following OpenAI chat format
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 30)
        **kwargs: Additional parameters to pass to the model API

    Returns:
        Generated text content, or None if generation fails after all retries

    Example:
        >>> messages = [
        ...     {"role": "system", "content": "You are a math teacher."},
        ...     {"role": "user", "content": "What is 5 + 3?"}
        ... ]
        >>> response = generate_text_completion(messages)
        >>> print(response)
        "5 + 3 equals 8"
    """
    config = Config()

    if not messages or not isinstance(messages, list):
        logger.warning("Invalid input: messages must be a non-empty list")
        return None

    # Prepare request payload
    payload = {
        "model": config.GENERATION_MODEL_NAME,
        "messages": messages,
        **kwargs
    }

    # Try with retries
    for attempt in range(max_retries):
        try:
            response = requests.post(
                config.GENERATION_SERVICE_URL,
                json=payload,
                timeout=timeout
            )

            if response.status_code == HTTP_OK:
                result = response.json()
                choices = result.get('choices', [])
                if choices:
                    content = choices[0].get('message', {}).get('content', '').strip()
                    if content:
                        return str(content)
            else:
                logger.warning(
                    f"Text generation request failed with status {response.status_code}: {response.text}"
                )

        except (Timeout, RequestException) as e:
            logger.warning(f"Text generation attempt {attempt + 1}/{max_retries} failed: {e}")

        except Exception as e:
            logger.error(f"Unexpected error in text generation: {e}")

        if attempt < max_retries - 1:
            logger.info(f"Retrying text generation ({attempt + 1}/{max_retries})...")

    logger.warning(f"Failed to generate text completion after {max_retries} attempts")
    return None


def generate_embedding(
    text: str,
    max_retries: int = 3,
    timeout: int = 30
) -> Optional[List[float]]:
    """
    Generate embedding vector for a single text input.

    This is the single entry point for single text embedding requests.
    It converts text into a dense vector representation that captures semantic meaning.

    Args:
        text: Text string to embed
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Embedding vector (list of floats), or None if generation fails after all retries

    Example:
        >>> embedding = generate_embedding("What is 5 + 3?")
        >>> print(len(embedding))
        768
    """
    if not text or not isinstance(text, str):
        logger.warning("Invalid input: text must be a non-empty string")
        return None

    # Use batch function for single text (intentional - provides consistent API
    # and reuses the same retry/error handling logic without code duplication)
    embeddings = generate_embeddings_batch([text], max_retries=max_retries, timeout=timeout)

    if embeddings and len(embeddings) > 0 and embeddings[0] is not None:
        return embeddings[0]

    return None


def _filter_valid_texts(texts: List[str]) -> tuple:
    """
    Filter valid texts and create index mapping.

    Args:
        texts: List of text strings

    Returns:
        Tuple of (valid_indices, valid_texts)
    """
    valid_indices = []
    valid_texts = []
    for i, text in enumerate(texts):
        if text and isinstance(text, str):
            valid_indices.append(i)
            valid_texts.append(text)
    return valid_indices, valid_texts


def _make_embedding_request(config: Config, valid_texts: List[str], timeout: int) -> Optional[List[List[float]]]:
    """
    Make a single embedding API request.

    Args:
        config: Config object with service URLs
        valid_texts: List of valid text strings to embed
        timeout: Request timeout in seconds

    Returns:
        List of embeddings if successful, None otherwise
    """
    response = requests.post(
        config.EMBEDDING_SERVICE_URL,
        json={
            "model": config.EMBEDDING_MODEL_NAME,
            "input": valid_texts
        },
        timeout=timeout
    )

    if response.status_code != HTTP_OK:
        logger.warning(f"Embedding request failed with status {response.status_code}: {response.text}")
        return None

    result = response.json()
    data = result.get('data', [])
    if not data:
        return None

    embeddings = [item.get('embedding', []) for item in data]
    if embeddings and all(len(e) > 0 for e in embeddings):
        return embeddings
    return None


def _build_output_with_embeddings(
    texts_len: int,
    valid_indices: List[int],
    embeddings_result: Optional[List[List[float]]]
) -> List[Optional[List[float]]]:
    """
    Build output list with embeddings mapped to original positions.

    Args:
        texts_len: Length of original texts list
        valid_indices: Indices of valid texts in original list
        embeddings_result: List of embeddings (or None if failed)

    Returns:
        Output list with embeddings at correct positions, None elsewhere
    """
    output: List[Optional[List[float]]] = [None] * texts_len

    if embeddings_result:
        for valid_idx, embedding in zip(valid_indices, embeddings_result):
            output[valid_idx] = embedding

    return output


def generate_embeddings_batch(
    texts: List[str],
    max_retries: int = 3,
    timeout: int = 30
) -> List[Optional[List[float]]]:
    """
    Generate embeddings for multiple texts in a single API call.

    This is the single entry point for batch embedding requests.
    It's more efficient than calling generate_embedding() multiple times.

    Note: Empty or invalid strings are preserved in the output as None values
    to maintain index correspondence with the input list.

    Args:
        texts: List of text strings to embed
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 30)

    Returns:
        List of embedding vectors (each is a list of floats).
        Returns None for any text that is empty, invalid, or failed to embed.
        The output list length matches the input list length.

    Example:
        >>> texts = ["What is 5 + 3?", "", "Calculate 10 - 4"]
        >>> embeddings = generate_embeddings_batch(texts)
        >>> print(len(embeddings))  # 3 - same as input
        3
        >>> print(embeddings[1] is None)  # Empty string -> None
        True
    """
    config = Config()

    if not texts or not isinstance(texts, list):
        logger.warning("Invalid input: texts must be a non-empty list")
        return []

    valid_indices, valid_texts = _filter_valid_texts(texts)

    if not valid_texts:
        logger.warning("No valid texts to embed")
        return [None] * len(texts)

    # Try with retries
    embeddings_result = None
    for attempt in range(max_retries):
        try:
            embeddings_result = _make_embedding_request(config, valid_texts, timeout)
            if embeddings_result:
                break
        except (Timeout, RequestException) as e:
            logger.warning(f"Embedding attempt {attempt + 1}/{max_retries} failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in embedding generation: {e}")

        if attempt < max_retries - 1:
            logger.info(f"Retrying embedding generation ({attempt + 1}/{max_retries})...")

    if not embeddings_result:
        logger.warning(f"Failed to generate batch embeddings after {max_retries} attempts")

    return _build_output_with_embeddings(len(texts), valid_indices, embeddings_result)


def is_embedding_service_available() -> bool:
    """
    Check if the embedding service is available.

    This makes a lightweight test call to verify the embedding model
    is accessible and responding.

    Returns:
        True if service is available, False otherwise

    Example:
        >>> if is_embedding_service_available():
        ...     embedding = generate_embedding("test")
    """
    try:
        result = generate_embedding("test", max_retries=1, timeout=5)
        return result is not None
    except Exception:
        return False


def is_generation_service_available() -> bool:
    """
    Check if the text generation service is available.

    This makes a lightweight test call to verify the generation model
    is accessible and responding.

    Returns:
        True if service is available, False otherwise

    Example:
        >>> if is_generation_service_available():
        ...     response = generate_text_completion(messages)
    """
    try:
        messages = [{"role": "user", "content": "test"}]
        result = generate_text_completion(messages, max_retries=1, timeout=5)
        return result is not None
    except Exception:
        return False


def main() -> None:
    """
    Test the model access module.

    This function demonstrates basic usage and can be used for manual testing.
    """
    print("Testing Model Access Module...")
    print("=" * 60)

    # Test 1: Check generation service availability
    print("\n1. Checking if text generation service is available...")
    if is_generation_service_available():
        print("✓ Text generation service is available")
    else:
        print("✗ Text generation service is NOT available")
        print("  Make sure the model service is running")

    # Test 2: Check embedding service availability
    print("\n2. Checking if embedding service is available...")
    if is_embedding_service_available():
        print("✓ Embedding service is available")
    else:
        print("✗ Embedding service is NOT available")
        print("  Make sure the embedding model is running")

    # Test 3: Generate text completion
    print("\n3. Testing text completion generation...")
    messages = [
        {"role": "system", "content": "You are a helpful math teacher."},
        {"role": "user", "content": "What is 5 + 3? Respond in one sentence."}
    ]
    response = generate_text_completion(messages)
    if response:
        print(f"✓ Generated response: {response[:100]}...")
    else:
        print("✗ Failed to generate text completion")

    # Test 4: Generate single embedding
    print("\n4. Testing single embedding generation...")
    test_text = "What is 5 + 3?"
    embedding = generate_embedding(test_text)
    if embedding:
        print(f"✓ Generated embedding for: '{test_text}'")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
    else:
        print(f"✗ Failed to generate embedding for: '{test_text}'")

    # Test 5: Generate batch embeddings
    print("\n5. Testing batch embedding generation...")
    test_texts = [
        "Calculate 10 - 4",
        "What is 7 * 6?",
        "Solve: 20 / 5"
    ]
    embeddings = generate_embeddings_batch(test_texts)
    if embeddings and all(e is not None for e in embeddings):
        print(f"✓ Generated {len(embeddings)} embeddings")
        for i, text in enumerate(test_texts):
            emb = embeddings[i]
            if emb is not None:
                print(f"  {i+1}. '{text}' -> {len(emb)} dimensions")
    else:
        print("✗ Failed to generate batch embeddings")

    # Test 6: Test error handling
    print("\n6. Testing error handling...")
    invalid_embedding = generate_embedding("")
    if invalid_embedding is None:
        print("✓ Correctly handled empty string input")
    else:
        print("✗ Should have returned None for empty string")

    print("\n" + "=" * 60)
    print("Model access module testing complete!")


if __name__ == "__main__":
    main()
