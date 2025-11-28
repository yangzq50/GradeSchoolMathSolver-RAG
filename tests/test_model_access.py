"""
Tests for the model_access module
"""
import sys
import os
from unittest.mock import patch, Mock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gradeschoolmathsolver import model_access  # noqa: E402


def test_generate_text_completion_success() -> None:
    """Test successful text completion generation"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'choices': [
            {'message': {'content': 'Test response'}}
        ]
    }

    with patch('requests.post', return_value=mock_response) as mock_post:
        messages = [
            {"role": "system", "content": "You are a helper."},
            {"role": "user", "content": "Test question"}
        ]
        result = model_access.generate_text_completion(messages, max_retries=1)

        assert result == 'Test response'
        assert mock_post.called

        # Verify the call was made with correct parameters
        call_args = mock_post.call_args
        assert 'json' in call_args.kwargs
        assert call_args.kwargs['json']['messages'] == messages


def test_generate_text_completion_failure() -> None:
    """Test text completion generation failure"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Server error"

    with patch('requests.post', return_value=mock_response):
        messages = [{"role": "user", "content": "Test"}]
        result = model_access.generate_text_completion(messages, max_retries=1)

        assert result is None


def test_generate_text_completion_empty_messages() -> None:
    """Test text completion with empty messages"""
    result = model_access.generate_text_completion([], max_retries=1)
    assert result is None

    result = model_access.generate_text_completion(None, max_retries=1)  # type: ignore[arg-type]
    assert result is None


def test_generate_embedding_success() -> None:
    """Test successful embedding generation"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'data': [
            {'embedding': [0.1, 0.2, 0.3]}
        ]
    }

    with patch('requests.post', return_value=mock_response) as mock_post:
        result = model_access.generate_embedding("Test text", max_retries=1)

        assert result == [0.1, 0.2, 0.3]
        assert mock_post.called


def test_generate_embedding_failure() -> None:
    """Test embedding generation failure"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Server error"

    with patch('requests.post', return_value=mock_response):
        result = model_access.generate_embedding("Test text", max_retries=1)

        assert result is None


def test_generate_embedding_empty_text() -> None:
    """Test embedding generation with empty text"""
    result = model_access.generate_embedding("", max_retries=1)
    assert result is None

    result = model_access.generate_embedding(None, max_retries=1)  # type: ignore[arg-type]
    assert result is None


def test_generate_embeddings_batch_success() -> None:
    """Test successful batch embedding generation"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'data': [
            {'embedding': [0.1, 0.2]},
            {'embedding': [0.3, 0.4]},
            {'embedding': [0.5, 0.6]}
        ]
    }

    with patch('requests.post', return_value=mock_response) as mock_post:
        texts = ["Text 1", "Text 2", "Text 3"]
        result = model_access.generate_embeddings_batch(texts, max_retries=1)

        assert len(result) == 3
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]
        assert result[2] == [0.5, 0.6]
        assert mock_post.called


def test_generate_embeddings_batch_with_empty_texts() -> None:
    """Test batch embedding with some empty texts"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'data': [
            {'embedding': [0.1, 0.2]},
            {'embedding': [0.5, 0.6]}
        ]
    }

    with patch('requests.post', return_value=mock_response):
        texts = ["Text 1", "", "Text 3"]
        result = model_access.generate_embeddings_batch(texts, max_retries=1)

        assert len(result) == 3
        assert result[0] == [0.1, 0.2]
        assert result[1] is None  # Empty text -> None
        assert result[2] == [0.5, 0.6]


def test_generate_embeddings_batch_all_empty() -> None:
    """Test batch embedding with all empty texts"""
    texts = ["", "", ""]
    result = model_access.generate_embeddings_batch(texts, max_retries=1)

    assert len(result) == 3
    assert all(r is None for r in result)


def test_generate_embeddings_batch_empty_list() -> None:
    """Test batch embedding with empty list"""
    result = model_access.generate_embeddings_batch([], max_retries=1)
    assert result == []

    result = model_access.generate_embeddings_batch(None, max_retries=1)  # type: ignore[arg-type]
    assert result == []


def test_is_embedding_service_available_success() -> None:
    """Test embedding service availability check when service is available"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'data': [{'embedding': [0.1, 0.2]}]
    }

    with patch('requests.post', return_value=mock_response):
        result = model_access.is_embedding_service_available()
        assert result is True


def test_is_embedding_service_available_failure() -> None:
    """Test embedding service availability check when service is unavailable"""
    with patch('requests.post', side_effect=Exception("Connection error")):
        result = model_access.is_embedding_service_available()
        assert result is False


def test_is_generation_service_available_success() -> None:
    """Test generation service availability check when service is available"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'test'}}]
    }

    with patch('requests.post', return_value=mock_response):
        result = model_access.is_generation_service_available()
        assert result is True


def test_is_generation_service_available_failure() -> None:
    """Test generation service availability check when service is unavailable"""
    with patch('requests.post', side_effect=Exception("Connection error")):
        result = model_access.is_generation_service_available()
        assert result is False


def test_retry_logic() -> None:
    """Test that retry logic works correctly"""
    # Mock a failing then succeeding scenario
    mock_responses = [
        Mock(status_code=500, text="Error 1"),
        Mock(status_code=500, text="Error 2"),
        Mock(status_code=200, json=lambda: {'choices': [{'message': {'content': 'Success'}}]})
    ]

    with patch('requests.post', side_effect=mock_responses) as mock_post:
        messages = [{"role": "user", "content": "Test"}]
        result = model_access.generate_text_completion(messages, max_retries=3)

        assert result == 'Success'
        assert mock_post.call_count == 3  # Called 3 times before success


def test_config_integration() -> None:
    """Test that model_access uses Config correctly"""
    from gradeschoolmathsolver.config import Config

    # Test that config values are accessible
    config = Config()
    assert hasattr(config, 'GENERATION_SERVICE_URL')
    assert hasattr(config, 'GENERATION_MODEL_NAME')
    assert hasattr(config, 'EMBEDDING_SERVICE_URL')
    assert hasattr(config, 'EMBEDDING_MODEL_NAME')

    # Verify defaults
    assert config.GENERATION_MODEL_NAME is not None
    assert config.EMBEDDING_MODEL_NAME is not None


def test_model_access_with_custom_config() -> None:
    """Test model_access with custom configuration

    Note: This test uses importlib.reload() to pick up environment changes.
    This pattern is consistent with existing config tests in test_config_centralization.py
    and is necessary to test environment variable overrides.
    """
    custom_env = {
        'GENERATION_SERVICE_URL': 'http://custom:8080/v1/completions',
        'GENERATION_MODEL_NAME': 'custom-model',
        'EMBEDDING_SERVICE_URL': 'http://custom:8080/v1/embeddings',
        'EMBEDDING_MODEL_NAME': 'custom-embedding'
    }

    with patch.dict(os.environ, custom_env, clear=False):
        # Reload config to pick up environment changes
        import importlib
        import gradeschoolmathsolver.config as config_module
        importlib.reload(config_module)
        from gradeschoolmathsolver.config import Config

        config = Config()
        assert config.GENERATION_SERVICE_URL == 'http://custom:8080/v1/completions'
        assert config.GENERATION_MODEL_NAME == 'custom-model'
        assert config.EMBEDDING_SERVICE_URL == 'http://custom:8080/v1/embeddings'
        assert config.EMBEDDING_MODEL_NAME == 'custom-embedding'


if __name__ == '__main__':
    # Run basic tests
    test_generate_text_completion_success()
    test_generate_text_completion_failure()
    test_generate_text_completion_empty_messages()
    test_generate_embedding_success()
    test_generate_embedding_failure()
    test_generate_embedding_empty_text()
    test_generate_embeddings_batch_success()
    test_generate_embeddings_batch_with_empty_texts()
    test_generate_embeddings_batch_all_empty()
    test_generate_embeddings_batch_empty_list()
    test_is_embedding_service_available_success()
    test_is_embedding_service_available_failure()
    test_is_generation_service_available_success()
    test_is_generation_service_available_failure()
    test_retry_logic()
    test_config_integration()
    test_model_access_with_custom_config()

    print("✅ All model_access tests passed!")
