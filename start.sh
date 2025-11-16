#!/bin/bash
# Startup script for GradeSchoolMathSolver-RAG

echo "🚀 Starting GradeSchoolMathSolver-RAG System"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start Docker services
echo "🐳 Starting Docker services (Ollama and Elasticsearch)..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check Ollama
echo "🤖 Checking Ollama service..."
if curl -s http://localhost:11434/api/version > /dev/null; then
    echo "✅ Ollama is running"
    
    # Check if model is pulled
    echo "📦 Checking if llama3.2 model is installed..."
    if ! docker exec math-solver-ollama ollama list | grep -q "llama3.2"; then
        echo "📥 Pulling llama3.2 model (this may take a while)..."
        docker exec math-solver-ollama ollama pull llama3.2
    else
        echo "✅ llama3.2 model is already installed"
    fi
else
    echo "⚠️  Ollama is not responding yet. It may still be starting up."
fi

# Check Elasticsearch
echo "🔍 Checking Elasticsearch..."
if curl -s http://localhost:9200 > /dev/null; then
    echo "✅ Elasticsearch is running"
else
    echo "⚠️  Elasticsearch is not responding yet. It may still be starting up."
fi

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data

# Install Python dependencies if needed
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

# Create default agents
echo "🤖 Initializing default agents..."
python -c "
from services.agent_management import AgentManagementService
mgmt = AgentManagementService()
mgmt.create_default_agents()
print('✅ Default agents created')
" 2>/dev/null || echo "⚠️  Could not create default agents (will be created on first run)"

echo ""
echo "=========================================="
echo "✨ System is ready!"
echo "=========================================="
echo ""
echo "To start the web application:"
echo "  source venv/bin/activate"
echo "  python -m web_ui.app"
echo ""
echo "Or set PYTHONPATH and run:"
echo "  export PYTHONPATH=\$(pwd)"
echo "  python web_ui/app.py"
echo ""
echo "Then open your browser to:"
echo "  http://localhost:5000"
echo ""
echo "To stop Docker services:"
echo "  docker-compose down"
echo ""
