# AI Model Service Documentation

## Overview

The GradeSchoolMathSolver-RAG system uses an AI model (LLaMA 3.2 or similar) for:
- Generating natural language questions from equations
- Classifying math questions into categories
- Solving math problems with reasoning (Agent service)

## Deployment Options

### Option 1: Docker Model Runner (Recommended)

This project is designed to work with Ollama running LLaMA 3.2 in a Docker container.

#### Setup Steps:

1. **Install Docker**
   ```bash
   # Install Docker on your system
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. **Pull and Run Ollama**
   ```bash
   # Pull Ollama Docker image
   docker pull ollama/ollama
   
   # Run Ollama container
   docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
   ```

3. **Pull LLaMA 3.2 Model**
   ```bash
   # Pull the model
   docker exec -it ollama ollama pull llama3.2
   ```

4. **Verify Installation**
   ```bash
   # Test the model
   curl http://localhost:11434/api/generate -d '{
     "model": "llama3.2",
     "prompt": "What is 2+2?",
     "stream": false
   }'
   ```

#### Docker Compose Setup:

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama:/root/.ollama
    restart: unless-stopped

volumes:
  ollama:
```

Run with:
```bash
docker-compose up -d
docker exec -it <container_id> ollama pull llama3.2
```

### Option 2: Local Ollama Installation

If you prefer not to use Docker:

1. **Install Ollama**
   ```bash
   # Linux
   curl https://ollama.ai/install.sh | sh
   
   # macOS
   brew install ollama
   
   # Windows
   # Download from https://ollama.ai/download
   ```

2. **Pull Model**
   ```bash
   ollama pull llama3.2
   ```

3. **Start Ollama**
   ```bash
   ollama serve
   ```

### Option 3: Alternative Models

The system can work with other models that provide an OpenAI-compatible API:

- **LLaMA 3.1**: `ollama pull llama3.1`
- **Mistral**: `ollama pull mistral`
- **Gemma**: `ollama pull gemma`

Update the configuration in `.env`:
```
AI_MODEL_NAME=mistral
```

## Configuration

Set these environment variables in `.env`:

```bash
# AI Model Service
AI_MODEL_URL=http://localhost:11434
AI_MODEL_NAME=llama3.2
```

## API Endpoints

The Ollama API provides these endpoints:

### Generate Text
```bash
POST http://localhost:11434/api/generate
Content-Type: application/json

{
  "model": "llama3.2",
  "prompt": "Your prompt here",
  "stream": false
}
```

### Chat Completion (Alternative)
```bash
POST http://localhost:11434/api/chat
Content-Type: application/json

{
  "model": "llama3.2",
  "messages": [
    {"role": "user", "content": "Your message here"}
  ],
  "stream": false
}
```

## System Integration

The AI model is used by these services:

1. **QA Generation Service** (`services/qa_generation/service.py`)
   - Converts equations to natural language questions
   - Falls back to template-based generation if AI is unavailable

2. **Classification Service** (`services/classification/service.py`)
   - Classifies questions into categories
   - Uses rule-based classification as fallback

3. **Agent Service** (`services/agent/service.py`)
   - Solves math problems with reasoning
   - Can use RAG context for better answers

## Troubleshooting

### Connection Issues

If you get connection errors:

1. Check if Ollama is running:
   ```bash
   curl http://localhost:11434/api/version
   ```

2. Check Docker container status:
   ```bash
   docker ps | grep ollama
   docker logs ollama
   ```

3. Verify port availability:
   ```bash
   netstat -tulpn | grep 11434
   ```

### Performance Optimization

For better performance:

1. **Use GPU acceleration** (if available):
   ```bash
   docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
   ```

2. **Adjust model parameters**:
   ```json
   {
     "model": "llama3.2",
     "prompt": "...",
     "options": {
       "temperature": 0.7,
       "top_p": 0.9,
       "num_predict": 128
     }
   }
   ```

3. **Use smaller models** for faster responses:
   - `llama3.2:1b` - Smallest, fastest
   - `llama3.2:3b` - Balanced
   - `llama3.2` - Best quality (default)

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
