# Embedding Service Documentation

## Overview

The Embedding Service provides vector embedding generation capabilities using the EmbeddingGemma model (`ai/embeddinggemma:300M-Q8_0`) via Docker Model Runner. This service is a foundational component for enabling Retrieval-Augmented Generation (RAG) in the GradeSchoolMathSolver system.

## Purpose

Vector embeddings convert text into numerical representations that capture semantic meaning. This enables:

- **Semantic Similarity Search**: Find similar questions based on meaning, not just keywords
- **Vector-Based Retrieval**: Efficiently retrieve relevant historical questions for RAG
- **Enhanced Question Matching**: Better matching of user questions to quiz history
- **Personalized Learning**: Provide contextually relevant examples based on semantic similarity

## Architecture

The Embedding Service follows the same design patterns as other AI services in the system:

```
User Request → Embedding Service → Docker Model Runner → EmbeddingGemma Model
                     ↓
              Vector Embeddings
                     ↓
          Quiz History / RAG System
```

### Key Features

- **OpenAI-Compatible API**: Uses standard embeddings endpoint format
- **Batch Processing**: Generate embeddings for multiple texts in a single API call
- **Retry Logic**: Automatic retry with configurable attempts (default: 3)
- **Graceful Degradation**: Returns None on failure, allowing system to continue
- **Error Handling**: Comprehensive error handling for network issues and API failures
- **Service Health Check**: Built-in availability testing

## Docker Model Runner Setup

### Prerequisites

- Docker Desktop version 4.32 or later
- 8GB+ RAM recommended (16GB+ for better performance)
- 5GB disk space for the embedding model

### Enable Docker Model Runner

1. **Open Docker Desktop**
   - Launch Docker Desktop application

2. **Enable Model Runner**
   - Navigate to **Settings** → **Features in development**
   - Enable **"Enable Docker AI Model Runner"**
   - Click **Apply & Restart**

3. **Download the Embedding Model**
   - In Docker Desktop, go to the **AI Models** or **Models** section
   - Search for: `ai/embeddinggemma:300M-Q8_0`
   - Click **Pull** or **Download**
   - Wait for the download to complete (approximately 300MB quantized)

4. **Verify Model is Running**
   ```bash
   # Check if models API is accessible
   curl http://localhost:12434/engines/llama.cpp/v1/models
   ```

### Model Information

**Model**: `ai/embeddinggemma:300M-Q8_0`
- **Type**: EmbeddingGemma (text embedding model)
- **Size**: ~300M parameters (Q8_0 quantization)
- **Quantization**: 8-bit quantization for efficient inference
- **Output**: 768-dimensional embedding vectors (typically)
- **Use Case**: Text similarity, semantic search, RAG

**Why EmbeddingGemma?**
- Optimized specifically for embedding generation
- Smaller and faster than general-purpose LLMs
- High-quality semantic representations
- Efficient resource usage
- Good balance of quality and performance

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Embedding Service Configuration
EMBEDDING_MODEL_URL=http://localhost:12434
EMBEDDING_MODEL_NAME=ai/embeddinggemma:300M-Q8_0
LLM_ENGINE=llama.cpp
```

### Configuration Details

- **EMBEDDING_MODEL_URL**: Docker Model Runner endpoint (default: http://localhost:12434)
- **EMBEDDING_MODEL_NAME**: Model identifier for embeddings
- **LLM_ENGINE**: Engine type for API path construction (default: llama.cpp)

### Docker Compose

The embedding service uses the same Docker Model Runner endpoint as the main AI service. No additional Docker configuration is needed beyond ensuring Docker Model Runner is enabled.

When running in Docker:
```yaml
services:
  web:
    environment:
      - EMBEDDING_MODEL_URL=http://host.docker.internal:12434
      - EMBEDDING_MODEL_NAME=ai/embeddinggemma:300M-Q8_0
```

## Usage

### Basic Usage

```python
from gradeschoolmathsolver.services.embedding import EmbeddingService

# Initialize service
service = EmbeddingService()

# Check if service is available
if service.is_available():
    # Generate embedding for a single text
    embedding = service.generate_embedding("What is 5 + 3?")
    print(f"Embedding dimension: {len(embedding)}")
    
    # Generate embeddings for multiple texts
    texts = [
        "Calculate 10 - 4",
        "What is 7 * 6?",
        "Solve: 20 / 5"
    ]
    embeddings = service.generate_embeddings_batch(texts)
    print(f"Generated {len(embeddings)} embeddings")
else:
    print("Embedding service not available")
```

### Single Text Embedding

```python
service = EmbeddingService()

# Generate embedding
text = "What is the sum of 15 and 27?"
embedding = service.generate_embedding(text)

if embedding:
    print(f"Success! Dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
else:
    print("Failed to generate embedding")
```

### Batch Embedding Generation

```python
service = EmbeddingService()

# Prepare multiple texts
questions = [
    "What is 5 + 3?",
    "Calculate 12 * 4",
    "Solve 100 / 25",
    "What is 45 - 18?"
]

# Generate all embeddings at once (more efficient)
embeddings = service.generate_embeddings_batch(questions)

for i, (question, embedding) in enumerate(zip(questions, embeddings)):
    if embedding:
        print(f"{i+1}. '{question}' -> {len(embedding)} dimensions")
    else:
        print(f"{i+1}. '{question}' -> FAILED")
```

### Error Handling

```python
service = EmbeddingService(max_retries=3, timeout=30)

try:
    embedding = service.generate_embedding(text)
    
    if embedding is None:
        # Service unavailable or all retries failed
        print("Falling back to keyword-based search")
        # Implement fallback logic
    else:
        # Use embedding for similarity search
        similar_items = search_by_embedding(embedding)
        
except Exception as e:
    print(f"Unexpected error: {e}")
    # Graceful degradation
```

### Integration with RAG

Here's how the embedding service integrates with the RAG workflow:

```python
from gradeschoolmathsolver.services.embedding import EmbeddingService
from gradeschoolmathsolver.services.quiz_history import QuizHistoryService

embedding_service = EmbeddingService()
quiz_history = QuizHistoryService()

# When user asks a question
user_question = "What is 15 + 27?"

# Generate embedding for the question
question_embedding = embedding_service.generate_embedding(user_question)

if question_embedding:
    # Use embedding for semantic similarity search
    # (This would require updating quiz_history to support vector search)
    similar_questions = quiz_history.search_by_embedding(
        username="john_doe",
        embedding=question_embedding,
        top_k=5
    )
    
    # Use similar questions as context for RAG
    # ...
else:
    # Fallback to text-based search
    similar_questions = quiz_history.search_relevant_history(
        username="john_doe",
        question=user_question,
        top_k=5
    )
```

## API Reference

### EmbeddingService Class

#### `__init__(max_retries: int = 3, timeout: int = 30)`

Initialize the embedding service.

**Parameters:**
- `max_retries`: Maximum number of retry attempts (default: 3)
- `timeout`: Request timeout in seconds (default: 30)

#### `generate_embedding(text: str) -> Optional[List[float]]`

Generate embedding vector for a single text input.

**Parameters:**
- `text`: Text string to embed

**Returns:**
- List of floats representing the embedding vector, or None if generation fails

**Example:**
```python
embedding = service.generate_embedding("What is 5 + 3?")
```

#### `generate_embeddings_batch(texts: List[str]) -> List[Optional[List[float]]]`

Generate embeddings for multiple texts in a single API call.

**Parameters:**
- `texts`: List of text strings to embed

**Returns:**
- List of embedding vectors (each is a list of floats). Returns None for any text that failed.

**Example:**
```python
embeddings = service.generate_embeddings_batch(["Text 1", "Text 2", "Text 3"])
```

#### `is_available() -> bool`

Check if the embedding service is available and responding.

**Returns:**
- True if service is available, False otherwise

**Example:**
```python
if service.is_available():
    # Proceed with embedding generation
    pass
```

## Testing

### Manual Testing

Run the built-in test suite:

```bash
# Test the embedding service directly
python -m gradeschoolmathsolver.services.embedding.service

# Or as a module
cd /path/to/GradeSchoolMathSolver
python -m gradeschoolmathsolver.services.embedding.service
```

Expected output:
```
Testing Embedding Service...
============================================================

1. Checking if embedding service is available...
✓ Embedding service is available

2. Generating embedding for a single question...
✓ Generated embedding for: 'What is 5 + 3?'
  Embedding dimension: 768
  First 5 values: [0.123, -0.456, 0.789, ...]

3. Generating embeddings for multiple questions...
✓ Generated 3 embeddings
  1. 'Calculate 10 - 4' -> 768 dimensions
  2. 'What is 7 * 6?' -> 768 dimensions
  3. 'Solve: 20 / 5' -> 768 dimensions

4. Testing error handling...
✓ Correctly handled empty string input

============================================================
Embedding service testing complete!
```

### Unit Testing

```bash
# Run embedding service tests
pytest tests/test_embedding_service.py -v

# Run all tests
pytest tests/ -v
```

### API Testing with curl

Test the Docker Model Runner embeddings endpoint directly:

```bash
# Test embeddings API
curl http://localhost:12434/engines/llama.cpp/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ai/embeddinggemma:300M-Q8_0",
    "input": ["What is 5 + 3?", "Calculate 10 - 4"]
  }'
```

Expected response format:
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.123, -0.456, 0.789, ...],
      "index": 0
    },
    {
      "object": "embedding",
      "embedding": [0.234, -0.567, 0.890, ...],
      "index": 1
    }
  ],
  "model": "ai/embeddinggemma:300M-Q8_0",
  "usage": {
    "prompt_tokens": 10,
    "total_tokens": 10
  }
}
```

## Troubleshooting

### Embedding Service Not Available

**Problem**: `service.is_available()` returns False

**Solutions**:

1. **Check Docker Model Runner is running:**
   ```bash
   curl http://localhost:12434/engines/llama.cpp/v1/models
   ```

2. **Verify embedding model is downloaded:**
   - Open Docker Desktop
   - Go to AI Models section
   - Check if `ai/embeddinggemma:300M-Q8_0` is listed and active

3. **Check Docker Desktop settings:**
   - Ensure "Enable Docker AI Model Runner" is enabled
   - Check resource allocation (RAM, CPU)
   - Restart Docker Desktop if needed

4. **Test endpoint directly:**
   ```bash
   curl http://localhost:12434/engines/llama.cpp/v1/embeddings \
     -H "Content-Type: application/json" \
     -d '{"model": "ai/embeddinggemma:300M-Q8_0", "input": ["test"]}'
   ```

### Connection Timeout

**Problem**: API calls timeout

**Solutions**:

1. Increase timeout value:
   ```python
   service = EmbeddingService(timeout=60)  # 60 seconds
   ```

2. Check system resources:
   - Docker Desktop resource allocation
   - Available RAM and CPU
   - Other running processes

3. Try smaller batch sizes:
   ```python
   # Instead of 100 texts at once
   for chunk in chunks(texts, 10):
       embeddings.extend(service.generate_embeddings_batch(chunk))
   ```

### Embedding Dimension Mismatch

**Problem**: Generated embeddings have unexpected dimensions

**Solution**: Different embedding models produce different dimensions:
- EmbeddingGemma typically produces 768-dimensional vectors
- Store embedding dimension in your database schema
- Validate dimension consistency across your dataset

### Rate Limiting or Performance Issues

**Problem**: Slow embedding generation or rate limiting

**Solutions**:

1. **Use batch processing:**
   ```python
   # More efficient than individual calls
   embeddings = service.generate_embeddings_batch(texts)
   ```

2. **Implement caching:**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=1000)
   def get_cached_embedding(text: str):
       return service.generate_embedding(text)
   ```

3. **Pre-generate embeddings:**
   - Generate embeddings during off-peak hours
   - Store in database for quick retrieval
   - Regenerate only when content changes

## Performance Considerations

### Resource Usage

- **Memory**: ~500MB-1GB for model loading
- **CPU**: 2-4 cores for reasonable performance
- **GPU**: Optional but significantly faster (if available)

### Optimization Tips

1. **Batch Processing**: Always prefer batch generation over individual calls
2. **Caching**: Cache embeddings for frequently used texts
3. **Pre-computation**: Generate embeddings during data ingestion
4. **Dimension Reduction**: Consider PCA or other techniques for large datasets
5. **GPU Acceleration**: Enable GPU support in Docker Desktop for faster inference

### Expected Performance

- **Single embedding**: ~100-500ms (CPU)
- **Batch (10 items)**: ~500-2000ms (CPU)
- **Model loading**: ~2-5 seconds (first call)

## Integration Roadmap

### Current Implementation (Phase 1)

- ✅ Embedding service with Docker Model Runner
- ✅ Single and batch embedding generation
- ✅ Error handling and retry logic
- ✅ Service availability checking
- ✅ Configuration and documentation

### Future Enhancements (Phase 2)

- [ ] Vector database integration (e.g., Milvus, Qdrant, or Elasticsearch with vectors)
- [ ] Update quiz history to store embeddings
- [ ] Implement vector-based similarity search
- [ ] Add embedding-based question deduplication
- [ ] Semantic clustering of question categories

### RAG Integration (Phase 3)

- [ ] Update RAG agent to use embedding-based retrieval
- [ ] Implement hybrid search (text + embeddings)
- [ ] Add embedding-based question recommendation
- [ ] Performance comparison: keyword vs. embedding search

## Security Considerations

1. **Input Validation**: Always validate text inputs before embedding
2. **Rate Limiting**: Consider implementing rate limits for production use
3. **Resource Monitoring**: Monitor Docker Model Runner resource usage
4. **API Security**: Ensure Docker Model Runner is not exposed publicly

## Best Practices

1. **Graceful Degradation**: Always have a fallback when embeddings fail
2. **Caching**: Cache embeddings for frequently accessed content
3. **Batch Processing**: Use batch generation for multiple texts
4. **Error Handling**: Log errors but continue operation
5. **Testing**: Test with various input sizes and edge cases
6. **Monitoring**: Monitor embedding generation success rate
7. **Documentation**: Document embedding dimension and model version

## References

- [Docker Model Runner Documentation](https://docs.docker.com/desktop/features/model-runner/)
- [OpenAI Embeddings API](https://platform.openai.com/docs/api-reference/embeddings)
- [EmbeddingGemma Model Information](https://github.com/google/gemma.cpp)
- [GradeSchoolMathSolver AI Model Service](AI_MODEL_SERVICE.md)

## Support

For issues or questions:
- Check the [troubleshooting section](#troubleshooting)
- Review Docker Desktop logs
- Open an issue on GitHub with:
  - Error messages
  - Docker Desktop version
  - Model information
  - Steps to reproduce

## Next Steps

After setting up the embedding service:

1. Test the service using the built-in test script
2. Verify Docker Model Runner is working correctly
3. Consider integrating with vector database for production use
4. Implement caching strategy for frequently used embeddings
5. Monitor performance and adjust resources as needed
6. Plan for RAG integration with vector-based retrieval

For complete system documentation, see the main [README.md](../README.md).
