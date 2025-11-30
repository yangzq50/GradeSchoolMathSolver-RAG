# AI Model Service

The AI Model Service provides natural language generation and embedding capabilities using an OpenAI-compatible API (Docker Model Runner, Ollama, or other compatible services).

## Quick Setup

### Docker Model Runner (Recommended)

1. **Enable Docker Model Runner**: Docker Desktop → Settings → Features in development → Enable "Docker AI Model Runner"
2. **Download Models**: AI Models section → Pull `llama3.2:1B-Q4_0` and `embeddinggemma:300M-Q8_0`
3. **Verify**: Test endpoints at `localhost:12434`

```bash
# Test generation API
curl http://localhost:12434/engines/llama.cpp/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "ai/llama3.2:1B-Q4_0", "messages": [{"role": "user", "content": "What is 2+2?"}]}'

# Test embeddings API
curl http://localhost:12434/engines/llama.cpp/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "ai/embeddinggemma:300M-Q8_0", "input": ["What is 2+2?"]}'
```

### Alternative: Ollama

```bash
ollama serve
ollama pull llama3.2
```

## Configuration

Set in `.env`:

```bash
# Generation Service
GENERATION_SERVICE_URL=http://localhost:12434/engines/llama.cpp/v1/chat/completions
GENERATION_MODEL_NAME=ai/llama3.2:1B-Q4_0

# Embedding Service
EMBEDDING_SERVICE_URL=http://localhost:12434/engines/llama.cpp/v1/embeddings
EMBEDDING_MODEL_NAME=ai/embeddinggemma:300M-Q8_0
```

## Using the Model Access Module

All AI interactions are centralized in the `model_access` module:

```python
from gradeschoolmathsolver import model_access

# Text generation
messages = [
    {"role": "system", "content": "You are a math teacher."},
    {"role": "user", "content": "What is 5 + 3?"}
]
response = model_access.generate_text_completion(messages)

# Single embedding
embedding = model_access.generate_embedding("What is 5 + 3?")

# Batch embeddings
embeddings = model_access.generate_embeddings_batch(["Question 1", "Question 2"])

# Check availability
if model_access.is_generation_service_available():
    print("Generation service ready")
```

## System Integration

The AI model is used by these services:
- **QA Generation**: Converts equations to natural language questions
- **Agent Service**: Solves math problems with reasoning
- **Teacher Service**: Provides educational feedback for wrong answers
- **Classification Service**: Optional AI-based question categorization
- **Embedding Service**: Vector embeddings for RAG functionality

## Graceful Degradation

The system continues working if AI is unavailable:
- **QA Generation**: Falls back to template-based questions
- **Classification**: Uses rule-based classification
- **Agent**: Returns direct calculation results

## Resource Requirements

| Level | CPU | RAM | Notes |
|-------|-----|-----|-------|
| Minimum | 4 cores | 8GB | Basic functionality |
| Recommended | 8 cores | 16GB | Smoother operation |
| Production | GPU | 16GB+ | Best performance |

## Troubleshooting

### AI Not Responding
1. Check Docker Model Runner: `curl http://localhost:12434/engines/llama.cpp/v1/models`
2. Verify models are downloaded in Docker Desktop
3. Check `.env` configuration

### Slow Responses
- Use smaller models (e.g., `1B-Q4_0` instead of `7B`)
- Enable GPU acceleration in Docker Desktop
- Increase timeout: `model_access.generate_text_completion(messages, timeout=60)`
