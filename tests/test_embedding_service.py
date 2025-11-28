"""
Unit tests for the Embedding Service

Tests embedding generation functionality with mocked API responses.
"""
from typing import Any, Dict
import pytest
from unittest.mock import Mock, patch, MagicMock
from gradeschoolmathsolver.services.embedding import EmbeddingService


@pytest.fixture
def embedding_service() -> EmbeddingService:
    """Create an EmbeddingService instance for testing"""
    return EmbeddingService(max_retries=3, timeout=30)


@pytest.fixture
def mock_embedding_response() -> Dict[str, Any]:
    """Create a mock successful embedding response"""
    return {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                "index": 0
            }
        ],
        "model": "ai/embeddinggemma:300M-Q8_0",
        "usage": {
            "prompt_tokens": 5,
            "total_tokens": 5
        }
    }


@pytest.fixture
def mock_batch_embedding_response() -> Dict[str, Any]:
    """Create a mock successful batch embedding response"""
    return {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                "index": 0
            },
            {
                "object": "embedding",
                "embedding": [0.6, 0.7, 0.8, 0.9, 1.0],
                "index": 1
            },
            {
                "object": "embedding",
                "embedding": [1.1, 1.2, 1.3, 1.4, 1.5],
                "index": 2
            }
        ],
        "model": "ai/embeddinggemma:300M-Q8_0",
        "usage": {
            "prompt_tokens": 15,
            "total_tokens": 15
        }
    }


class TestEmbeddingService:
    """Test suite for EmbeddingService"""

    def test_initialization(self, embedding_service: EmbeddingService) -> None:
        """Test service initialization"""
        assert embedding_service.max_retries == 3
        assert embedding_service.timeout == 30
        assert embedding_service.config is not None

    def test_custom_initialization(self) -> None:
        """Test service initialization with custom parameters"""
        service = EmbeddingService(max_retries=5, timeout=60)
        assert service.max_retries == 5
        assert service.timeout == 60

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_generate_embedding_success(
        self, mock_post: MagicMock, embedding_service: EmbeddingService,
        mock_embedding_response: Dict[str, Any]
    ) -> None:
        """Test successful single embedding generation"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_embedding_response
        mock_post.return_value = mock_response

        # Test
        text = "What is 5 + 3?"
        embedding = embedding_service.generate_embedding(text)

        # Assertions
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 5
        assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_post.assert_called_once()

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_generate_embedding_api_failure(self, mock_post: MagicMock, embedding_service: EmbeddingService) -> None:
        """Test embedding generation with API failure"""
        # Setup mock to fail
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Test
        text = "What is 5 + 3?"
        embedding = embedding_service.generate_embedding(text)

        # Assertions
        assert embedding is None
        # Should retry 3 times
        assert mock_post.call_count == 3

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_generate_embedding_timeout(self, mock_post, embedding_service) -> None:
        """Test embedding generation with timeout"""
        # Setup mock to timeout
        mock_post.side_effect = Exception("Timeout")

        # Test
        text = "What is 5 + 3?"
        embedding = embedding_service.generate_embedding(text)

        # Assertions
        assert embedding is None
        assert mock_post.call_count == 3

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_generate_embedding_retry_success(self, mock_post, embedding_service, mock_embedding_response) -> None:
        """Test embedding generation succeeds after retry"""
        # Setup mock to fail first, then succeed
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = mock_embedding_response

        mock_post.side_effect = [mock_response_fail, mock_response_success]

        # Test
        text = "What is 5 + 3?"
        embedding = embedding_service.generate_embedding(text)

        # Assertions
        assert embedding is not None
        assert len(embedding) == 5
        assert mock_post.call_count == 2

    def test_generate_embedding_empty_string(self, embedding_service) -> None:
        """Test embedding generation with empty string"""
        embedding = embedding_service.generate_embedding("")
        assert embedding is None

    def test_generate_embedding_none_input(self, embedding_service) -> None:
        """Test embedding generation with None input"""
        embedding = embedding_service.generate_embedding(None)
        assert embedding is None

    def test_generate_embedding_invalid_type(self, embedding_service) -> None:
        """Test embedding generation with invalid input type"""
        embedding = embedding_service.generate_embedding(123)
        assert embedding is None

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_generate_embeddings_batch_success(
        self, mock_post: MagicMock, embedding_service: EmbeddingService,
        mock_batch_embedding_response: Dict[str, Any]
    ) -> None:
        """Test successful batch embedding generation"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_batch_embedding_response
        mock_post.return_value = mock_response

        # Test
        texts = ["What is 5 + 3?", "Calculate 10 - 4", "Solve: 20 / 5"]
        embeddings = embedding_service.generate_embeddings_batch(texts)

        # Assertions
        assert embeddings is not None
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(isinstance(e, list) for e in embeddings)
        assert embeddings[0] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert embeddings[1] == [0.6, 0.7, 0.8, 0.9, 1.0]
        assert embeddings[2] == [1.1, 1.2, 1.3, 1.4, 1.5]
        mock_post.assert_called_once()

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_generate_embeddings_batch_failure(self, mock_post, embedding_service) -> None:
        """Test batch embedding generation with API failure

        Note: On failure, the batch method returns a list of None values
        to maintain index correspondence with the input list.
        """
        # Setup mock to fail
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Test
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = embedding_service.generate_embeddings_batch(texts)

        # Assertions
        assert embeddings is not None
        assert len(embeddings) == 3
        # All embeddings should be None due to API failure
        assert all(e is None for e in embeddings)
        assert mock_post.call_count == 3

    def test_generate_embeddings_batch_empty_list(self, embedding_service) -> None:
        """Test batch embedding generation with empty list"""
        embeddings = embedding_service.generate_embeddings_batch([])
        assert embeddings == []

    def test_generate_embeddings_batch_none_input(self, embedding_service) -> None:
        """Test batch embedding generation with None input"""
        embeddings = embedding_service.generate_embeddings_batch(None)
        assert embeddings == []

    def test_generate_embeddings_batch_invalid_type(self, embedding_service) -> None:
        """Test batch embedding generation with invalid input type"""
        embeddings = embedding_service.generate_embeddings_batch("not a list")
        assert embeddings == []

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_generate_embeddings_batch_with_empty_strings(
            self, mock_post, embedding_service, mock_batch_embedding_response):
        """Test batch embedding with empty strings - should preserve None at empty positions"""
        # Setup mock - only returns embeddings for valid texts
        mock_response = Mock()
        mock_response.status_code = 200
        # API returns embeddings only for the 2 valid texts
        valid_response = {
            "object": "list",
            "data": [
                {"object": "embedding", "embedding": [0.1, 0.2, 0.3, 0.4, 0.5], "index": 0},
                {"object": "embedding", "embedding": [0.6, 0.7, 0.8, 0.9, 1.0], "index": 1}
            ],
            "model": "ai/embeddinggemma:300M-Q8_0",
            "usage": {"prompt_tokens": 10, "total_tokens": 10}
        }
        mock_response.json.return_value = valid_response
        mock_post.return_value = mock_response

        # Test with empty string in the middle
        texts = ["Valid text 1", "", "Valid text 2"]
        embeddings = embedding_service.generate_embeddings_batch(texts)

        # Assertions - output length should match input length
        assert embeddings is not None
        assert len(embeddings) == 3  # Same length as input
        # First position should have embedding
        assert embeddings[0] is not None
        assert len(embeddings[0]) == 5
        # Second position (empty string) should be None
        assert embeddings[1] is None
        # Third position should have embedding
        assert embeddings[2] is not None
        assert len(embeddings[2]) == 5

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_is_available_true(self, mock_post, embedding_service, mock_embedding_response) -> None:
        """Test is_available returns True when service is up"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_embedding_response
        mock_post.return_value = mock_response

        # Test
        available = embedding_service.is_available()

        # Assertions
        assert available is True
        mock_post.assert_called_once()

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_is_available_false(self, mock_post: MagicMock, embedding_service: EmbeddingService) -> None:
        """Test is_available returns False when service is down"""
        # Setup mock to fail
        mock_post.side_effect = Exception("Connection error")

        # Test
        available = embedding_service.is_available()

        # Assertions
        assert available is False

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_api_call_with_correct_endpoint(self, mock_post, embedding_service, mock_embedding_response) -> None:
        """Test that API calls use correct endpoint format"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_embedding_response
        mock_post.return_value = mock_response

        # Test
        embedding_service.generate_embedding("test")

        # Assertions - check the URL called
        call_args = mock_post.call_args
        url = call_args[0][0] if call_args[0] else call_args[1].get('url', '')
        assert '/engines/' in url
        assert '/v1/embeddings' in url

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_api_call_with_correct_payload(self, mock_post, embedding_service, mock_embedding_response) -> None:
        """Test that API calls include correct payload format"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_embedding_response
        mock_post.return_value = mock_response

        # Test
        test_text = "What is 5 + 3?"
        embedding_service.generate_embedding(test_text)

        # Assertions - check the payload
        call_args = mock_post.call_args
        json_payload = call_args[1].get('json', {})
        assert 'model' in json_payload
        assert 'input' in json_payload
        assert json_payload['input'] == [test_text]

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_malformed_response_handling(self, mock_post: MagicMock, embedding_service: EmbeddingService) -> None:
        """Test handling of malformed API responses"""
        # Setup mock with malformed response (missing 'data' field)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "list"}  # Missing 'data'
        mock_post.return_value = mock_response

        # Test
        embedding = embedding_service.generate_embedding("test")

        # Assertions
        assert embedding is None

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_empty_data_in_response(self, mock_post, embedding_service) -> None:
        """Test handling of empty data array in response"""
        # Setup mock with empty data array
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "list", "data": []}
        mock_post.return_value = mock_response

        # Test
        embedding = embedding_service.generate_embedding("test")

        # Assertions
        assert embedding is None

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_missing_embedding_in_response(self, mock_post, embedding_service) -> None:
        """Test handling of missing embedding field in response"""
        # Setup mock with missing embedding field
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "object": "list",
            "data": [{"object": "embedding", "index": 0}]  # Missing 'embedding'
        }
        mock_post.return_value = mock_response

        # Test
        embedding = embedding_service.generate_embedding("test")

        # Assertions
        assert embedding is None


class TestEmbeddingServiceEdgeCases:
    """Test edge cases and boundary conditions"""

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_very_long_text(self, mock_post, embedding_service, mock_embedding_response) -> None:
        """Test embedding generation with very long text"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_embedding_response
        mock_post.return_value = mock_response

        # Test with long text
        long_text = "What is " + " + ".join([str(i) for i in range(100)])
        embedding = embedding_service.generate_embedding(long_text)

        # Assertions
        assert embedding is not None
        assert len(embedding) == 5

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_special_characters(self, mock_post, embedding_service, mock_embedding_response) -> None:
        """Test embedding generation with special characters"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_embedding_response
        mock_post.return_value = mock_response

        # Test with special characters
        text = "What is 5 + 3? !@#$%^&*()"
        embedding = embedding_service.generate_embedding(text)

        # Assertions
        assert embedding is not None

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_unicode_text(self, mock_post, embedding_service, mock_embedding_response) -> None:
        """Test embedding generation with unicode characters"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_embedding_response
        mock_post.return_value = mock_response

        # Test with unicode
        text = "What is 5 + 3? 你好 🎉"
        embedding = embedding_service.generate_embedding(text)

        # Assertions
        assert embedding is not None

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_whitespace_only(self, mock_post, embedding_service, mock_embedding_response) -> None:
        """Test embedding generation with whitespace-only text"""
        # Even though it's whitespace, the service should try to process it
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_embedding_response
        mock_post.return_value = mock_response

        # Test with whitespace
        text = "   "
        embedding = embedding_service.generate_embedding(text)

        # Service will process it
        assert embedding is not None

    @patch('gradeschoolmathsolver.model_access.requests.post')
    def test_large_batch(self, mock_post, embedding_service) -> None:
        """Test batch embedding with many texts"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        # Create response with 50 embeddings
        data = [
            {"object": "embedding", "embedding": [0.1 * i] * 5, "index": i}
            for i in range(50)
        ]
        mock_response.json.return_value = {
            "object": "list",
            "data": data,
            "model": "ai/embeddinggemma:300M-Q8_0"
        }
        mock_post.return_value = mock_response

        # Test with 50 texts
        texts = [f"Text {i}" for i in range(50)]
        embeddings = embedding_service.generate_embeddings_batch(texts)

        # Assertions
        assert len(embeddings) == 50
        assert all(e is not None for e in embeddings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
