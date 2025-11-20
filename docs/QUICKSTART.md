# Quick Start Guide

Get GradeSchoolMathSolver-RAG up and running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.11 or higher
- ✅ Docker Desktop with **Docker Model Runner** enabled
- ✅ 8GB+ RAM available
- ✅ 10GB+ free disk space

Quick check:
```bash
python3 --version  # Should be 3.11+
docker --version   # Should be installed
```

## Option 1: Docker Model Runner (Recommended)

### Step 1: Set Up Docker Model Runner

**Docker Model Runner** is Docker Desktop's built-in AI model hosting service.

1. **Install Docker Desktop** from https://www.docker.com/products/docker-desktop (version 4.32+)
2. **Enable Docker Model Runner**: 
   - Open Docker Desktop → Settings → Features in development
   - Enable "Enable Docker AI Model Runner"
   - Click Apply & Restart
3. **Download Model**: 
   - Navigate to the AI Models or Models section in Docker Desktop
   - Search for and download `llama3.2:1B-Q4_0` (recommended for speed)
4. **Verify**: Models should be accessible at `localhost:12434`

Test the AI service:
```bash
curl http://localhost:12434/engines/llama.cpp/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ai/llama3.2:1B-Q4_0",
    "messages": [{"role": "user", "content": "test"}]
  }'
```

### Step 2: Clone and Setup
```bash
git clone https://github.com/yangzq50/GradeSchoolMathSolver-RAG.git
cd GradeSchoolMathSolver-RAG
```

### Step 3: Configure Environment
```bash
cp .env.example .env
# Default .env values are configured for Docker Model Runner:
# AI_MODEL_URL=http://localhost:12434
# AI_MODEL_NAME=ai/llama3.2:1B-Q4_0
# LLM_ENGINE=llama.cpp
```

### Step 4: Start Services with Docker Compose

You have two options:

**Option A: Start Everything (Recommended)**
```bash
docker-compose up -d
```
This starts both Elasticsearch and the web application. Open http://localhost:5000 when ready.

**Option B: Start Elasticsearch Only (for local development)**
```bash
docker-compose up -d elasticsearch
```

Wait 30 seconds for Elasticsearch to start.

### Step 5: Install Python Dependencies (if using Option B)
```bash
pip install -e .
```

### Step 6: Start Web Application (if using Option B)
```bash
python -m web_ui.app
```

### Step 7: Access the Application
Open http://localhost:5000 in your browser.

🎉 **You're done!** Start exploring the application.

## Option 2: Alternative AI Services

### Using Local Ollama

If you prefer Ollama over Docker Desktop AI:

### Step 1: Install Ollama
```bash
# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai/download
```

### Step 2: Start Ollama and Download Model
```bash
ollama serve  # In one terminal

# In another terminal:
ollama pull llama3.2
```

### Step 3: Update Configuration
Edit `.env`:
```bash
AI_MODEL_URL=http://localhost:11434
AI_MODEL_NAME=llama3.2
LLM_ENGINE=ollama
```

### Step 4: Start Elasticsearch and Application
```bash
# Option 1: Start everything with docker-compose
docker-compose up -d

# Option 2: Start only Elasticsearch, then run web app locally
docker-compose up -d elasticsearch
pip install -e .
python -m web_ui.app
```

**Note**: Without Elasticsearch, RAG features will be limited but the system will still work.

## Option 3: Minimal Setup (No Docker)

If you can't use Docker at all, you can run with limited functionality:

### Step 1: Install AI Service Locally
Set up Docker Desktop AI or Ollama as described above.

### Step 2: Install Python Dependencies
```bash
pip install -e .
```

### Step 3: Configure for No-Docker Mode
```bash
cp .env.example .env
# Ensure AI_MODEL_URL points to your local AI service
```

### Step 4: Run Application
```bash
python -m web_ui.app
```

**Note**: Without Elasticsearch, RAG features will be disabled.

## First Steps After Setup

### 1. Create a User
- Go to "Users" page
- Click "Add New User"
- Enter a username (e.g., "student1")

### 2. Take Your First Exam
- Click "Take Exam"
- Enter your username
- Select difficulty: "easy"
- Set question count: 5
- Answer the questions
- View your results!

### 3. Test a RAG Bot
- Go to "Agents" page
- Select "basic_agent"
- Click "Test Agent"
- Choose difficulty and question count
- Watch the agent solve problems!

### 4. Compare Agent Performance
Try testing different agents:
- **basic_agent**: Simple AI, no extras
- **classifier_agent**: Uses question categorization
- **rag_agent**: Uses RAG to learn from history
- **rag_correct_only**: Only learns from correct answers

## Verify Installation

Run the test suite:
```bash
python tests/test_basic.py
```

You should see:
```
✅ Passed: 6
❌ Failed: 0
📊 Total: 6
```

## Troubleshooting

### AI Service Not Responding

Check if AI service is running:
```bash
# For Docker Model Runner (port 12434)
curl http://localhost:12434/engines/llama.cpp/v1/models

# For Ollama (port 11434)
curl http://localhost:11434/api/version
```

If Docker Model Runner is not responding:
1. Check Docker Desktop is running
2. Verify Docker Model Runner is enabled in Settings → Features in development
3. Check that models are downloaded in the Models section
4. Restart Docker Desktop if needed

### Docker Services Won't Start

Check if ports are already in use:
```bash
# Check port 12434 (Docker Model Runner)
lsof -i :12434

# Check port 9200 (Elasticsearch)
lsof -i :9200

# Check port 5000 (Web UI)
lsof -i :5000
```

Stop conflicting services or change ports in configuration.

### AI Model Responses Are Slow

This is normal on first run. The AI model needs to warm up. Subsequent questions will be faster.

To speed up:
1. Use Docker Model Runner with GPU support enabled in Docker Desktop
2. Use a smaller/quantized model: `ai/llama3.2:1B-Q4_0`
3. Reduce question complexity
4. Ensure adequate system resources (CPU/RAM)

## Configuration Tips

### Use GPU Acceleration (Docker Model Runner)

Enable GPU in Docker Desktop settings:
1. Open Docker Desktop → Settings → Resources
2. Enable "Use GPU" if available
3. Allocate sufficient GPU memory
4. Restart Docker Desktop

### Customize Question Difficulty

Edit `services/qa_generation/service.py` to adjust number ranges:
```python
# Make easy questions easier
def _generate_easy_equation(self):
    num1 = random.randint(1, 10)  # Was 1-20
    num2 = random.randint(1, 10)
    ...
```

### Change Web UI Port

In `.env`:
```bash
FLASK_PORT=8080  # Change from 5000
```

## Next Steps

Now that you're set up, explore:

1. **Create custom agents** - Configure your own RAG bot strategies
2. **Track progress** - Monitor user improvements over time
3. **Compare agents** - See which strategies work best
4. **Experiment** - Try different question types and difficulty levels

## Getting Help

- 📚 Read the [Architecture Documentation](docs/ARCHITECTURE.md)
- 🤖 Check [AI Model Service Guide](docs/AI_MODEL_SERVICE.md)
- 📖 Review the [README](README.md)
- 🐛 Report issues on GitHub
- 💡 Suggest features via GitHub Issues

## Updating the System

To update to the latest version:

```bash
git pull
pip install -e . --upgrade
docker-compose pull
docker-compose up -d
```

## Stopping the System

To stop Docker services:
```bash
docker-compose down
```

To completely remove all data:
```bash
docker-compose down -v
rm -rf data/
```

## Performance Benchmarks

Typical performance on modern hardware:

| Operation | Time | Notes |
|-----------|------|-------|
| Generate 1 question | 1-3s | First request slower |
| Classify question | <0.1s | Rule-based |
| Agent solve (no RAG) | 2-5s | Depends on model |
| Agent solve (with RAG) | 3-7s | Includes search |
| Exam (5 questions) | 5-15s | For agent |
| Database query | <0.1s | SQLite local |
| RAG search | 0.1-0.5s | Elasticsearch |

## System Requirements

### Minimum
- CPU: 4 cores
- RAM: 8GB
- Disk: 10GB
- OS: Linux, macOS, Windows

### Recommended
- CPU: 8 cores or GPU
- RAM: 16GB
- Disk: 20GB SSD
- OS: Linux or macOS

### Production
- CPU: 16+ cores or GPU
- RAM: 32GB+
- Disk: 100GB+ SSD
- Network: 1Gbps+

Happy Learning! 🎓📊🤖
