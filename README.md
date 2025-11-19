# GradeSchoolMathSolver-RAG

[![CI](https://github.com/yangzq50/GradeSchoolMathSolver-RAG/actions/workflows/ci.yml/badge.svg)](https://github.com/yangzq50/GradeSchoolMathSolver-RAG/actions/workflows/ci.yml)
[![Release](https://github.com/yangzq50/GradeSchoolMathSolver-RAG/actions/workflows/release.yml/badge.svg)](https://github.com/yangzq50/GradeSchoolMathSolver-RAG/actions/workflows/release.yml)
[![Docker Publish](https://github.com/yangzq50/GradeSchoolMathSolver-RAG/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/yangzq50/GradeSchoolMathSolver-RAG/actions/workflows/docker-publish.yml)

An AI-powered Grade School Math Solver with RAG (Retrieval-Augmented Generation). Automatically generates arithmetic problems, tracks correct and incorrect answers, and provides personalized practice and exams. Ideal for learning, testing, and building adaptive math tutoring agents.

**📦 Docker Hub**: [yangzq50/gradeschoolmathsolver](https://hub.docker.com/r/yangzq50/gradeschoolmathsolver)

![Homepage](https://github.com/user-attachments/assets/7e8d6f0d-c8af-4170-be71-77402945fe14)

## 🎯 Features

- **AI-Generated Questions**: Automatically generate math problems at easy, medium, and hard difficulty levels
- **Question Classification**: Categorize questions by type (addition, subtraction, multiplication, etc.)
- **User Management**: Track user progress, answer history, and performance statistics
- **Quiz History with RAG**: Store and retrieve similar questions using vector search for personalized learning
- **Database Flexibility**: Choose between MariaDB (default) or Elasticsearch based on your needs
- **Intelligent RAG bots**: Configurable RAG bots that can use classification and RAG for better problem-solving
- **Web Interface**: User-friendly Flask-based web UI for taking exams and viewing statistics
- **RAG Bot Management**: Create and test different RAG bot configurations
- **Performance Tracking**: Monitor correctness rates, recent performance, and trends
- **🆕 Immersive Exams**: Synchronized exams where all participants answer the same questions with optional answer reveal strategies
- **🆕 Teacher Service**: Optional educational feedback for wrong answers to help users learn from mistakes
- **🆕 Mistake Review Service**: Review and re-attempt past incorrect answers in FIFO order to learn from mistakes

## 🏗️ Architecture

The system consists of 12 main components:

### 0. AI Model Service
- Uses Docker Desktop models via localhost endpoint (port 12434)
- Provides natural language generation for questions and reasoning
- OpenAI-compatible chat/completions API format
- See [AI Model Service Documentation](docs/AI_MODEL_SERVICE.md)

### 1. QA Generation Service
- Generates mathematical equations based on difficulty level
- Converts equations to natural language questions using AI
- Supports easy (single operation), medium (multiple operations), and hard (parentheses/division)

### 2. Question Classification Service
- Classifies questions into predefined categories
- Rule-based classification with optional AI enhancement
- Categories: addition, subtraction, multiplication, division, mixed_operations, parentheses, fractions

### 3. Account Service
- Unified database storage for user management (MariaDB by default)
- Tracks answer correctness history with timestamps
- Calculates overall correctness and recent 100 questions score
- Tracks reviewed status for mistake review feature
- See [Database Service Documentation](docs/DATABASE_SERVICE.md)
- See [MariaDB Integration](docs/MARIADB_INTEGRATION.md)

### 4. Quiz History Service
- Database storage for RAG capabilities (works with both MariaDB and Elasticsearch)
- Stores question, answer, and context for retrieval
- Enables similarity search for personalized learning (best with Elasticsearch)
- See [Database Service Documentation](docs/DATABASE_SERVICE.md)

### 5. Exam Service
- Coordinates question generation and answer evaluation
- Supports both human and RAG bot exams
- Updates user statistics and quiz history
- Integrates teacher service for human feedback

### 6. Immersive Exam Service
- Synchronized exam management for multiple participants
- Pre-generates shared questions for all participants
- Ordered participant registration (humans and RAG bots)
- Configurable reveal strategies for cheating experiments
- Server-controlled question progression
- Real-time status updates and results

### 7. Teacher Service
- Provides educational feedback for incorrect answers
- AI-based explanations with template fallback
- Step-by-step guidance for correct solutions
- Toggle-able via configuration
- Only active for human users (not RAG bots)

### 8. Mistake Review Service
- Allows users to review past incorrect answers
- FIFO (First-In, First-Out) ordering of mistakes
- Mark mistakes as reviewed to avoid repetition
- Interactive retry with instant feedback
- Real-time tracking of unreviewed mistake count

### 9. Web UI Service
- Flask-based web interface
- User dashboard with statistics and trends
- Interactive exam interface
- Immersive exam creation and participation
- RAG bot testing and management
- Teacher feedback display
- Mistake review interface

### 10. RAG Bot Service
- Configurable problem-solving RAG bots
- Optional question classification
- Optional RAG from quiz history
- Provides reasoning for answers

### 11. RAG Bot Management Service
- Create, update, and delete RAG bot configurations
- Pre-configured default RAG bots
- Test RAG bots with different settings

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker Desktop with **Docker Model Runner** enabled (for AI models)
  - **Docker Model Runner** is Docker Desktop's built-in AI model hosting service that runs LLMs locally
  - Provides an OpenAI-compatible API at localhost:12434
  - See setup instructions below
- MariaDB or Elasticsearch for database (MariaDB recommended, included in Docker setup)
- 8GB+ RAM recommended (16GB+ recommended for larger models)

### Installation

#### Option 1: Using Pre-built Docker Image (Recommended for Quick Start)

Pull and run the latest Docker image from Docker Hub:

```bash
# Pull the latest image
docker pull yangzq50/gradeschoolmathsolver:latest

# Or pull a specific version
docker pull yangzq50/gradeschoolmathsolver:1.0.0
```

Then use with `docker-compose.yml` by modifying the web service to use the pre-built image instead of building locally.

#### Option 2: Install from Source

1. **Clone the repository**
   ```bash
   git clone https://github.com/yangzq50/GradeSchoolMathSolver-RAG.git
   cd GradeSchoolMathSolver-RAG
   ```

2. **Install the package**
   
   The project is now structured as a proper Python package for better maintainability.
   
   **Option 1: Install as a package (recommended)**
   ```bash
   pip install .
   ```
   
   **Option 2: Install in development mode**
   ```bash
   pip install -e .
   ```
   
   This will install all dependencies automatically and make the `gradeschoolmathsolver` command available.

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration:
   # - AI_MODEL_URL: Docker Desktop models endpoint (e.g., http://localhost:12434)
   # - AI_MODEL_NAME: Model name (e.g., ai/llama3.2:1B-Q4_0)
   # - LLM_ENGINE: Engine type (e.g., llama.cpp)
   # - DATABASE_BACKEND: mariadb (default) or elasticsearch
   ```

4. **Set up Docker Model Runner (Docker Desktop's AI model service)**
   
   Docker Model Runner is Docker Desktop's built-in feature for running AI models locally with an OpenAI-compatible API.
   
   **How to enable Docker Model Runner:**
   
   a. **Install/Update Docker Desktop**
      - Download from https://www.docker.com/products/docker-desktop
      - Ensure you have Docker Desktop version 4.32 or later
   
   b. **Enable Docker Model Runner**
      - Open Docker Desktop
      - Navigate to **Settings** → **Features in development**
      - Enable **"Enable Docker AI Model Runner"** (or similar option depending on your version)
      - Apply & Restart Docker Desktop
   
   c. **Download AI Models**
      - In Docker Desktop, navigate to the **AI Models** section (or **Models** tab)
      - Search for and pull `llama3.2:1B-Q4_0` (or your preferred model)
      - Wait for the model to download and become ready
   
   d. **Verify Docker Model Runner is working**
      ```bash
      # Test if models API is accessible
      curl http://localhost:12434/engines/llama.cpp/v1/models
      
      # Test a simple chat completion
      curl http://localhost:12434/engines/llama.cpp/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{
          "model": "ai/llama3.2:1B-Q4_0",
          "messages": [{"role": "user", "content": "What is 2+2?"}]
        }'
      ```
   
   The models run at **localhost:12434** and provide an OpenAI-compatible API endpoint.
   Example model: `ai/llama3.2:1B-Q4_0`

5. **Start the Application**

   You have two options for running the application:

   **Option 1: Using Docker Compose (Recommended)**
   
   This starts MariaDB, the web application, and optionally Elasticsearch in containers:
   
   ```bash
   # Start with MariaDB (default, recommended)
   docker-compose up -d
   ```
   
   The web app will be available at `http://localhost:5000`
   
   **What this does:**
   - Starts MariaDB container on port 3306
   - Starts the web application container on port 5000
   - Web app connects to Docker Model Runner via `host.docker.internal:12434`
   - Data is persisted in `./data` directory
   
   **Optional: Start with Elasticsearch for RAG features**
   ```bash
   # Start all services including Elasticsearch
   docker-compose --profile elasticsearch up -d
   # Update .env: DATABASE_BACKEND=elasticsearch
   ```
   
   To stop all services:
   ```bash
   docker-compose down
   ```

   **Option 2: Database in Docker + Web App Locally**
   
   If you prefer to run the web app locally (useful for development):
   
   a. Start only the database:
   ```bash
   # MariaDB (default)
   docker-compose up -d mariadb
   
   # Or Elasticsearch (for RAG)
   docker-compose up -d elasticsearch
   ```
   
   b. Run the web application locally:
   ```bash
   # Using the installed package command
   gradeschoolmathsolver
   
   # Or using Python module (if installed in development mode)
   python -m gradeschoolmathsolver.web_ui.app
   ```
   
   The web app will be available at `http://localhost:5000`

6. **Open your browser**
   ```
   http://localhost:5000
   ```

### Alternative: Local Setup (Without Docker)

If you prefer to run everything locally without Docker:

1. **Set up LLM service** - Use any OpenAI-compatible API endpoint (see [AI Model Service Documentation](docs/AI_MODEL_SERVICE.md))
2. **Install and run MariaDB locally** (see [MariaDB Integration Documentation](docs/MARIADB_INTEGRATION.md))
   - Or install Elasticsearch for RAG features (see [Elasticsearch Storage Documentation](docs/ELASTICSEARCH_STORAGE.md))
3. **Update .env** with your LLM endpoint and database URLs
4. **Install the package** with `pip install .`
5. **Run the web application** with `gradeschoolmathsolver`

## 📖 Usage

### Taking an Exam (Human)

1. Navigate to the "Take Exam" page
2. Enter your username
3. Select difficulty level (easy, medium, hard)
4. Choose number of questions (1-20)
5. Answer the generated questions
6. Submit to see your results and statistics
7. **NEW**: For any incorrect answers, you'll receive personalized teacher feedback explaining:
   - Why your answer was wrong
   - Step-by-step guidance to the correct solution
   - Educational tips for that operation type

### Teacher Feedback Feature

When you submit a wrong answer, the teacher service automatically provides:
- **Clear explanation** of why the answer is incorrect
- **Step-by-step guidance** on how to solve the problem correctly
- **Educational tips** specific to the type of math operation
- **Encouraging tone** to support learning

This feature can be toggled on/off via the `TEACHER_SERVICE_ENABLED` configuration option.

### Reviewing Your Mistakes (NEW)

The mistake review feature allows you to learn from your past errors:

1. Navigate to the "Review Mistakes" page
2. Enter your username
3. Click "Start Reviewing"
4. See your unreviewed mistake count
5. For each mistake, you'll see:
   - The original question
   - Your incorrect answer
   - The correct answer
   - Question category and date
6. **Try Again**: Enter a new answer and click "Check Answer" to see if you got it right
7. Click "→ Next Mistake" to mark the current mistake as reviewed and move to the next one
8. Mistakes are shown in FIFO (First-In, First-Out) order - oldest mistakes first
9. Once reviewed, mistakes won't appear in future review sessions

**Benefits:**
- Focused practice on areas where you struggled
- Immediate feedback on retry attempts
- Track your improvement over time
- Never miss reviewing an important mistake

### Creating an Immersive Exam

1. Navigate to the "Immersive Exam" page
2. Set difficulty distribution (easy, medium, hard question counts)
3. Choose a reveal strategy:
   - **None**: No participant sees others' answers
   - **Reveal to Later Participants**: Participants see answers from those before them (for cheating experiments)
   - **Reveal All After Round**: Everyone sees all answers after each question completes
4. Optionally set time per question
5. Click "Create Exam"
6. Register participants:
   - Add human users by username
   - Add RAG bots from the dropdown
7. Click "Start Exam" when all participants are registered
8. Participants join using their username or RAG bot name
9. Answer questions in synchronized order
10. View final results with leaderboard

### Testing a RAG Bot

1. Navigate to the "RAG Bots" page
2. Select a RAG bot configuration
3. Set test parameters (difficulty, question count)
4. Run the test
5. Review RAG bot performance and reasoning

### Creating a Custom RAG Bot

```python
from gradeschoolmathsolver.models import AgentConfig
from gradeschoolmathsolver.services.agent_management import AgentManagementService

# Create agent management service
agent_mgmt = AgentManagementService()

# Define custom RAG bot
custom_agent = AgentConfig(
    name="my_custom_bot",
    use_classification=True,
    use_rag=True,
    rag_top_k=3,
    include_incorrect_history=True
)

# Create RAG bot
agent_mgmt.create_agent(custom_agent)
```

### API Usage

The system provides REST APIs for integration:

```bash
# Create a user
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe"}'

# Generate exam questions
curl -X POST http://localhost:5000/api/exam/human \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "difficulty": "medium",
    "question_count": 5
  }'

# Run agent exam
curl -X POST http://localhost:5000/api/exam/agent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "rag_agent",
    "username": "john_doe",
    "difficulty": "hard",
    "question_count": 3
  }'

# Create immersive exam (NEW)
curl -X POST http://localhost:5000/api/exam/immersive/create \
  -H "Content-Type: application/json" \
  -d '{
    "difficulty_distribution": {"easy": 3, "medium": 4, "hard": 3},
    "reveal_strategy": "reveal_to_later_participants",
    "time_per_question": 60
  }'

# Register participant for immersive exam
curl -X POST http://localhost:5000/api/exam/immersive/{exam_id}/register \
  -H "Content-Type: application/json" \
  -d '{
    "participant_id": "alice",
    "participant_type": "human"
  }'

# Get immersive exam status
curl http://localhost:5000/api/exam/immersive/{exam_id}/status?participant_id=alice

# Submit answer in immersive exam
curl -X POST http://localhost:5000/api/exam/immersive/{exam_id}/answer \
  -H "Content-Type: application/json" \
  -d '{
    "participant_id": "alice",
    "question_index": 0,
    "answer": 42
  }'

# Get next mistake to review (NEW)
curl http://localhost:5000/api/mistakes/next/john_doe

# Get count of unreviewed mistakes (NEW)
curl http://localhost:5000/api/mistakes/count/john_doe

# Mark a mistake as reviewed (NEW)
curl -X POST http://localhost:5000/api/mistakes/review \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "mistake_id": 123
  }'

# Get all unreviewed mistakes (NEW)
curl http://localhost:5000/api/mistakes/all/john_doe?limit=50
```

## 🧪 Testing

Test individual services:

```bash
# Test QA Generation
python services/qa_generation/service.py

# Test Classification
python services/classification/service.py

# Test Account Service
python services/account/service.py

# Test Quiz History
python services/quiz_history/service.py

# Test Agent
python services/agent/service.py

# Test Agent Management
python services/agent_management/service.py

# Test Exam Service
python services/exam/service.py

# Test Immersive Exam Service
python services/immersive_exam/service.py

# Test Teacher Service (NEW)
python services/teacher/service.py

# Test Mistake Review Service (NEW)
python services/mistake_review/service.py

# Run all basic tests
python tests/test_basic.py

# Run teacher service tests (NEW)
python tests/test_teacher_service.py

# Run immersive exam tests (NEW)
python tests/test_immersive_exam.py

# Run mistake review tests (NEW)
python tests/test_mistake_review.py
```

## 🔧 Configuration

### Default RAG Bots

The system creates these default RAG bots:

1. **basic_agent**: Simple AI without classification or RAG
2. **classifier_agent**: Uses classification but no RAG
3. **rag_agent**: Uses both classification and RAG
4. **rag_correct_only**: RAG with only correct answers from history

### Environment Variables

See `.env.example` for all available configuration options.

Key settings:
- `AI_MODEL_URL`: URL of the AI model service (e.g., http://localhost:12434)
- `AI_MODEL_NAME`: Name of the model to use (e.g., ai/llama3.2:1B-Q4_0)
- `LLM_ENGINE`: LLM engine to use (e.g., llama.cpp)
- `DATABASE_BACKEND`: Database backend (mariadb or elasticsearch, default: mariadb)
- `MARIADB_HOST`: MariaDB hostname (default: localhost)
- `MARIADB_PORT`: MariaDB port (default: 3306)
- `MARIADB_USER`: MariaDB username (default: math_solver)
- `MARIADB_PASSWORD`: MariaDB password
- `MARIADB_DATABASE`: MariaDB database name (default: math_solver)
- `ELASTICSEARCH_HOST`: Elasticsearch hostname (when using Elasticsearch)
- `ELASTICSEARCH_PORT`: Elasticsearch port (when using Elasticsearch)
- `ELASTICSEARCH_INDEX`: Index name for quiz history (default: quiz_history)
- `TEACHER_SERVICE_ENABLED`: Enable/disable teacher feedback (default: True)

### Database Configuration

The system supports two database backends:

**MariaDB (Default, Recommended)**
- Lightweight and fast
- Proper relational structure with typed columns
- Lower resource usage
- Easy setup with Docker
- See [MariaDB Integration Documentation](docs/MARIADB_INTEGRATION.md)

```bash
DATABASE_BACKEND=mariadb
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=math_solver
MARIADB_PASSWORD=math_solver_password
MARIADB_DATABASE=math_solver
```

**Elasticsearch (Optional, for RAG)**
- Advanced full-text search
- Semantic similarity matching
- Best for RAG features
- Requires more resources
- See [Elasticsearch Storage Documentation](docs/ELASTICSEARCH_STORAGE.md)

```bash
DATABASE_BACKEND=elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=quiz_history
```

### Teacher Service Configuration

The teacher service can be enabled or disabled via environment variable:

```bash
# Enable teacher feedback (default)
TEACHER_SERVICE_ENABLED=True

# Disable teacher feedback
TEACHER_SERVICE_ENABLED=False
```

When enabled, the service provides:
- AI-generated explanations when AI model is available
- Template-based fallback explanations when AI is unavailable
- Feedback only for human users (not RAG bots)
- No performance impact on correct answers

## 📊 System Flow

```
User/Agent Request → Exam Service → QA Generation Service → Questions
                           ↓
                  Classification Service → Categories
                           ↓
                     Agent Service (optional) → AI Model
                           ↓           ↓
                    Quiz History ← RAG Search
                           ↓
                   Account Service → Statistics
                           ↓
                     Database Storage
```

## 🛠️ Development

### Project Structure

```
GradeSchoolMathSolver-RAG/
├── setup.py                     # Package installation script
├── MANIFEST.in                  # Package manifest
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker setup
├── Dockerfile                   # Multi-stage web app container
├── .env.example                 # Environment template
├── config.py                    # Backward compatibility stub (deprecated)
├── models.py                    # Backward compatibility stub (deprecated)
├── gradeschoolmathsolver/       # Main package
│   ├── __init__.py             # Package initialization
│   ├── config.py               # Configuration settings
│   ├── models.py               # Data models (including mistake review)
│   ├── services/               # Core services
│   │   ├── qa_generation/     # Question generation
│   │   ├── classification/    # Question classification
│   │   ├── account/          # User management
│   │   ├── database/         # Database backends
│   │   ├── quiz_history/     # RAG history storage
│   │   ├── exam/            # Exam management
│   │   ├── immersive_exam/  # Immersive exam management
│   │   ├── teacher/         # Teacher feedback service
│   │   ├── mistake_review/  # Mistake review service (NEW)
│   │   ├── agent/           # RAG bot logic
│   │   └── agent_management/ # Agent configuration
│   └── web_ui/              # Flask web interface
│       ├── app.py          # Web application
│       └── templates/      # HTML templates
│           ├── immersive_exam_create.html
│           ├── immersive_exam_live.html
│           ├── immersive_exam_results.html
│           └── mistake_review.html      # (NEW)
├── docs/                   # Documentation
└── tests/                 # Test files
    ├── test_basic.py
    ├── test_teacher_service.py
    ├── test_immersive_exam.py
    └── test_mistake_review.py          # (NEW)
```

### Adding New Features

1. **New Question Type**: Modify `gradeschoolmathsolver/services/qa_generation/service.py`
2. **New Category**: Add to `gradeschoolmathsolver/config.py` QUESTION_CATEGORIES
3. **New Agent Strategy**: Extend `gradeschoolmathsolver/services/agent/service.py`
4. **New UI Page**: Add template to `gradeschoolmathsolver/web_ui/templates/`

## 🐛 Troubleshooting

### Module Import Errors

The project is now a proper Python package. If you encounter import errors:

1. **Make sure the package is installed**
   ```bash
   cd GradeSchoolMathSolver-RAG
   pip install -e .
   ```

2. **Run using the package command**
   ```bash
   gradeschoolmathsolver
   ```

3. **Or run as a module**
   ```bash
   python -m gradeschoolmathsolver.web_ui.app
   ```

### AI Model Not Responding

1. **Check if Docker Model Runner is running and accessible:**
   ```bash
   # Test models endpoint
   curl http://localhost:12434/engines/llama.cpp/v1/models
   
   # Test chat completions endpoint
   curl http://localhost:12434/engines/llama.cpp/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "ai/llama3.2:1B-Q4_0", "messages": [{"role": "user", "content": "test"}]}'
   ```

2. **Verify Docker Model Runner is enabled in Docker Desktop:**
   - Open Docker Desktop
   - Go to Settings → Features in development
   - Ensure "Enable Docker AI Model Runner" is checked
   - Check that models are downloaded in the AI Models/Models section

3. **Verify your environment variables are correct:**
   ```bash
   AI_MODEL_URL=http://localhost:12434
   AI_MODEL_NAME=ai/llama3.2:1B-Q4_0
   LLM_ENGINE=llama.cpp
   ```

4. **Check Docker Desktop status:**
   - Open Docker Desktop and check if it's running
   - Navigate to Settings → Resources
   - Verify resource allocation (CPU/Memory) - at least 8GB RAM recommended
   - Check the Models tab to ensure your model is downloaded and active

### Database Connection Issues

**MariaDB Issues**

1. Check if MariaDB is running:
   ```bash
   docker ps | grep mariadb
   # Or for local install
   sudo systemctl status mariadb
   ```

2. Test connection:
   ```bash
   mysql -h localhost -P 3306 -u math_solver -p
   ```

3. Verify credentials in `.env` match your setup

4. Check logs:
   ```bash
   docker logs math-solver-mariadb
   ```

For detailed troubleshooting, see [MariaDB Integration Documentation](docs/MARIADB_INTEGRATION.md)

**Elasticsearch Issues** (if using Elasticsearch for RAG)

1. Check if ES is running: `docker ps | grep elasticsearch`
2. Test connection: `curl http://localhost:9200`
3. The system will work in limited mode without ES (uses MariaDB)
4. See [Elasticsearch Storage Documentation](docs/ELASTICSEARCH_STORAGE.md)

### Data Directory Issues

1. Check permissions on data directory:
   ```bash
   ls -la data/
   ```

2. For MariaDB data issues:
   ```bash
   # Remove MariaDB data (WARNING: deletes all data!)
   rm -rf data/mariadb/
   docker-compose up -d mariadb
   ```

3. Restart application to recreate tables

## 📦 Releases and Docker Publishing

This project uses automated GitHub Actions workflows to create releases and publish Docker images.

### Creating a Release

To create a new release:

1. Ensure all changes are committed and pushed to the main branch
2. Create and push a semantic version tag:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

This will automatically:
- Create a GitHub release with auto-generated release notes
- Build and publish multi-platform Docker images to Docker Hub
- Tag the Docker image with version numbers (e.g., `1.0.0`, `1.0`, `1`, `latest`)

### Docker Hub Images

Pre-built Docker images are available at:
- **Repository**: [yangzq50/gradeschoolmathsolver](https://hub.docker.com/r/yangzq50/gradeschoolmathsolver)
- **Tags**: Each release creates multiple tags for flexibility
  - `1.0.0` - Specific version (recommended for production)
  - `1.0` - Latest patch version
  - `1` - Latest minor version
  - `latest` - Latest release

### For Maintainers

Detailed instructions for setting up and customizing the release workflows:
- [Release Workflow Documentation](docs/RELEASE_WORKFLOW.md) - Complete guide for GitHub releases and Docker Hub publishing

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- Docker Model Runner for local AI model hosting
- Ollama for alternative AI model deployment
- LLaMA 3.2 for language generation
- MariaDB for reliable database storage
- Elasticsearch for advanced RAG capabilities
- Flask for web framework
