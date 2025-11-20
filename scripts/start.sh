#!/bin/bash
# Startup script for GradeSchoolMathSolver
# This script helps set up the development environment

echo "🚀 Starting GradeSchoolMathSolver System"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please review and update .env with your configuration if needed"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"

# Check if Docker Model Runner is accessible
echo "🤖 Checking Docker Model Runner (Docker Desktop AI models)..."
if curl -s http://localhost:12434/engines/llama.cpp/v1/models > /dev/null 2>&1; then
    echo "✅ Docker Model Runner is accessible at localhost:12434"
    
    # Try to list available models
    echo "📋 Available models:"
    curl -s http://localhost:12434/engines/llama.cpp/v1/models 2>/dev/null | grep -o '"id":"[^"]*"' | cut -d'"' -f4 || echo "  (Could not retrieve model list)"
else
    echo "⚠️  Docker Model Runner is not accessible at localhost:12434"
    echo "    Please ensure:"
    echo "    1. Docker Desktop is running"
    echo "    2. Docker Model Runner is enabled in Settings → Features in development"
    echo "    3. AI models are downloaded in Docker Desktop's Models section"
    echo "    4. The model service is running on port 12434"
fi

# Start Docker services (Elasticsearch and optionally Web App)
echo ""
echo "🐳 Starting Docker services..."
echo "Choose an option:"
echo "  1. Start Elasticsearch only (run web app locally with 'python -m web_ui.app')"
echo "  2. Start Elasticsearch + Web App (recommended)"
echo ""
read -p "Enter your choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo "Starting Elasticsearch only..."
    docker-compose up -d elasticsearch
elif [ "$choice" = "2" ]; then
    echo "Starting Elasticsearch and Web App..."
    docker-compose up -d
else
    echo "Invalid choice. Starting Elasticsearch only..."
    docker-compose up -d elasticsearch
fi

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check Elasticsearch
echo "🔍 Checking Elasticsearch..."
if curl -s http://localhost:9200 > /dev/null; then
    echo "✅ Elasticsearch is running"
else
    echo "⚠️  Elasticsearch is not responding yet. It may still be starting up."
    echo "    You can check status with: docker-compose logs elasticsearch"
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
pip install -q -e .

# Create default agents
echo "🤖 Initializing default RAG agents..."
python -c "
from services.agent_management import AgentManagementService
mgmt = AgentManagementService()
mgmt.create_default_agents()
print('✅ Default RAG agents created')
" 2>/dev/null || echo "⚠️  Could not create default agents (will be created on first run)"

echo ""
echo "=========================================="
echo "✨ Setup complete!"
echo "=========================================="
echo ""

if [ "$choice" = "2" ]; then
    echo "Web application is running in Docker!"
    echo "Open your browser to: http://localhost:5000"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f web"
    echo ""
else
    echo "To start the web application locally:"
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
fi

echo "To stop Docker services:"
echo "  docker-compose down"
echo ""
echo "For troubleshooting, see README.md or docs/AI_MODEL_SERVICE.md"
echo ""
