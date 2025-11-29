# Quick Start Guide

Get GradeSchoolMathSolver running in 5 minutes.

## Prerequisites

- Python 3.11+
- Docker Desktop (4.32+) with Model Runner enabled
- 8GB+ RAM

## Setup

### 1. Enable Docker Model Runner

1. Open Docker Desktop → Settings → Features in development
2. Enable "Enable Docker AI Model Runner"
3. Apply & Restart

### 2. Download AI Models

In Docker Desktop's AI Models section:
- Download `llama3.2:1B-Q4_0`
- Download `embeddinggemma:300M-Q8_0` (optional, for RAG)

### 3. Start the Application

```bash
git clone https://github.com/yangzq50/GradeSchoolMathSolver.git
cd GradeSchoolMathSolver
cp .env.example .env
docker-compose up -d
```

### 4. Open the Application

Navigate to http://localhost:5000

## First Steps

1. **Create a User**: Go to "Users" → Add your username
2. **Take an Exam**: Select difficulty and question count
3. **Test RAG Bots**: Try different agents in "Agents" page

## Alternative Setup: Ollama

```bash
# Install and start Ollama
ollama serve
ollama pull llama3.2

# Update .env
AI_MODEL_URL=http://localhost:11434
LLM_ENGINE=ollama

# Start application
docker-compose up -d mariadb
pip install -e .
gradeschoolmathsolver
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| AI not responding | Check Docker Model Runner is enabled and models are downloaded |
| Slow responses | Use smaller model (`1B-Q4_0`), enable GPU in Docker Desktop |
| Port conflicts | Change ports in `.env` or stop conflicting services |

## Verify Installation

```bash
pytest tests/ -v
```

## Next Steps

- Read [Architecture](ARCHITECTURE.md) to understand the system
- Configure [AI Models](AI_MODEL_SERVICE.md) for advanced setup
- See [README](../README.md) for complete documentation
