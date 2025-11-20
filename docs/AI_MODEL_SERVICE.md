# AI Model Service Documentation

## Overview

The GradeSchoolMathSolver system uses an AI model (LLaMA 3.2 or similar) via an **OpenAI-compatible API** for:
- Generating natural language questions from equations
- Classifying math questions into categories
- Solving math problems with reasoning (Agent service)
- Providing educational feedback through the teacher service

## API Format

**Important**: This system uses the **OpenAI-compatible chat completions API format**, not the legacy Ollama generate API.

All services in the codebase use:
- Endpoint: `/engines/{LLM_ENGINE}/v1/chat/completions`
- Request format: Messages array with `role` and `content`
- Response format: OpenAI-style with `choices` array

## Deployment Options

### Option 1: Docker Desktop Model Runner (Recommended)

This project is designed to work with **Docker Model Runner**, Docker Desktop's built-in AI model hosting service.

**What is Docker Model Runner?**
- A feature of Docker Desktop that runs AI models locally with an OpenAI-compatible API
- Models run at `localhost:12434` by default
- Provides the same API format as OpenAI (chat completions)
- No need for separate Ollama or other LLM infrastructure
- Integrated directly into Docker Desktop

#### Setup Steps:

1. **Install/Update Docker Desktop**
   - Download from https://www.docker.com/products/docker-desktop
   - Ensure you have Docker Desktop version 4.32 or later

2. **Enable Docker Model Runner**
   - Open Docker Desktop
   - Navigate to **Settings** → **Features in development**
   - Enable **"Enable Docker AI Model Runner"** (or similar option)
   - Click **Apply & Restart**

3. **Download AI Models**
   - In Docker Desktop, navigate to the **AI Models** or **Models** section
   - Search for and download your desired model (e.g., `llama3.2:1B-Q4_0`)
   - Wait for the download to complete
   - The model becomes available immediately after download

4. **Verify Installation**
   ```bash
   # Test the models API
   curl http://localhost:12434/engines/llama.cpp/v1/models
   
   # Test the OpenAI-compatible chat completions API
   curl http://localhost:12434/engines/llama.cpp/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "ai/llama3.2:1B-Q4_0",
       "messages": [
         {"role": "system", "content": "You are a helpful assistant."},
         {"role": "user", "content": "What is 2+2?"}
       ]
     }'
   ```

4. **Expected Response Format**
   ```json
   {
     "id": "chatcmpl-123",
     "object": "chat.completion",
     "created": 1234567890,
     "model": "ai/llama3.2:1B-Q4_0",
     "choices": [
       {
         "index": 0,
         "message": {
           "role": "assistant",
           "content": "2+2 equals 4."
         },
         "finish_reason": "stop"
       }
     ]
   }'
   ```

### Option 2: Alternative OpenAI-Compatible Services

The system works with any service providing an OpenAI-compatible chat completions API:

#### Local Ollama with OpenAI Compatibility

1. **Install Ollama**
   ```bash
   # Linux
   curl https://ollama.ai/install.sh | sh
   
   # macOS
   brew install ollama
   ```

2. **Pull Model**
   ```bash
   ollama pull llama3.2
   ```

3. **Start Ollama**
   ```bash
   ollama serve
   ```

4. **Update Configuration**
   ```bash
   AI_MODEL_URL=http://localhost:11434
   AI_MODEL_NAME=llama3.2
   LLM_ENGINE=ollama
   ```

#### Other Compatible Services

- **LM Studio**: Local LLM server with OpenAI API
- **vLLM**: High-performance inference server
- **text-generation-webui**: Local web UI with API support
- **OpenAI API**: Direct OpenAI API (with API key)

All services must support the `/v1/chat/completions` endpoint format.

## Configuration

Set these environment variables in `.env`:

```bash
# AI Model Service (Docker Desktop default)
AI_MODEL_URL=http://localhost:12434
AI_MODEL_NAME=ai/llama3.2:1B-Q4_0
LLM_ENGINE=llama.cpp
```

**Configuration Parameters:**
- `AI_MODEL_URL`: Base URL of the AI model service
- `AI_MODEL_NAME`: Model identifier (varies by service)
- `LLM_ENGINE`: Engine name used in the API path (e.g., `llama.cpp`, `ollama`)

## API Endpoint

**The system uses the OpenAI-compatible chat completions API:**

### Chat Completion (Used by All Services)
```bash
POST {AI_MODEL_URL}/engines/{LLM_ENGINE}/v1/chat/completions
Content-Type: application/json

{
  "model": "ai/llama3.2:1B-Q4_0",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Your question here"
    }
  ]
}
```

**Response Format:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "ai/llama3.2:1B-Q4_0",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The assistant's response"
      },
      "finish_reason": "stop"
    }
  ]
}
```

**Note**: The legacy `/api/generate` endpoint is **NOT** used by this system. All services use the OpenAI-compatible format.

## System Integration

The AI model is used by these services (all using OpenAI-compatible API):

1. **QA Generation Service** (`services/qa_generation/service.py`)
   - Endpoint: `/engines/{LLM_ENGINE}/v1/chat/completions`
   - System role: "You are a helpful math teacher creating grade school word problems."
   - Converts equations to natural language questions
   - Falls back to template-based generation if AI is unavailable

2. **Classification Service** (`services/classification/service.py`)
   - Endpoint: `/engines/{LLM_ENGINE}/v1/chat/completions`
   - System role: "You are a helpful math classification assistant."
   - Classifies questions into categories
   - Uses rule-based classification as fallback

3. **Agent Service** (`services/agent/service.py`)
   - Endpoint: `/engines/{LLM_ENGINE}/v1/chat/completions`
   - System role: "You are a helpful math tutor assistant."
   - Solves math problems with reasoning
   - Can use RAG context for better answers

4. **Teacher Service** (`services/teacher/service.py`)
   - Endpoint: `/engines/{LLM_ENGINE}/v1/chat/completions`
   - System role: "You are a patient and encouraging math teacher."
   - Provides educational feedback for incorrect answers
   - Falls back to template-based feedback if AI is unavailable

**All services use the same API format for consistency and maintainability.**

## Troubleshooting

### Connection Issues

If you get connection errors:

1. **Check if the AI model service is running:**
   ```bash
   # For Docker Desktop models (default port 12434)
   curl http://localhost:12434/engines/llama.cpp/v1/models
   
   # For Ollama (default port 11434)
   curl http://localhost:11434/api/version
   ```

2. **Test the chat completions endpoint:**
   ```bash
   curl http://localhost:12434/engines/llama.cpp/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "ai/llama3.2:1B-Q4_0",
       "messages": [{"role": "user", "content": "test"}]
     }'
   ```

3. **Check Docker Desktop status:**
   - Open Docker Desktop
   - Navigate to Settings → AI
   - Verify models are downloaded and running
   - Check resource allocation (CPU/Memory)

4. **Verify port availability:**
   ```bash
   # Check if port 12434 is in use
   netstat -tulpn | grep 12434
   # or
   lsof -i :12434
   ```

5. **Review application logs:**
   ```bash
   # Check for AI service connection errors
   grep "AI" app.log
   grep "timeout" app.log
   ```

### Performance Optimization

For better performance:

1. **Use GPU acceleration** (Docker Desktop):
   - Enable GPU support in Docker Desktop settings
   - Allocate sufficient VRAM to Docker
   - Monitor GPU usage in Docker Desktop dashboard

2. **Adjust model parameters** (optional in request):
   ```json
   {
     "model": "ai/llama3.2:1B-Q4_0",
     "messages": [...],
     "temperature": 0.7,
     "max_tokens": 256,
     "top_p": 0.9
   }
   ```

3. **Use smaller/quantized models** for faster responses:
   - `ai/llama3.2:1B-Q4_0` - Smallest, fastest (default)
   - `ai/llama3.2:3B-Q4_0` - Balanced quality/speed
   - `ai/llama3.2:7B` - Best quality, slower

4. **Connection pooling**: Services automatically reuse connections

5. **Retry logic**: Built-in 3-attempt retry with timeouts (30s default)

## Graceful Degradation

The system is designed to work even if the AI model is unavailable:

- **QA Generation**: Falls back to template-based questions
- **Classification**: Uses rule-based classification
- **Agent**: Returns direct calculation results

This ensures the system remains functional even during AI service downtime.

## Resource Requirements

### Minimum Requirements:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 10 GB (for model storage)

### Recommended Requirements:
- CPU: 8 cores (or GPU)
- RAM: 16 GB
- Disk: 20 GB
- GPU: NVIDIA GPU with 8GB+ VRAM (optional, for better performance)

## Security Considerations

1. **Network Access**: The AI model service should only be accessible from the application
2. **Rate Limiting**: Consider implementing rate limiting for API calls
3. **Input Validation**: All prompts should be validated before sending to the model
4. **Monitoring**: Monitor API usage and response times

## Next Steps

After setting up the AI model service:

1. Test the connection with the provided verification commands
2. Update the `.env` file with the correct configuration
3. Run the test scripts in each service to verify integration
4. Start the web UI and test the full system

For more information, see the main README.md file.
