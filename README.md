# GradeSchoolMathSolver-RAG

[![CI](https://github.com/yangzq50/GradeSchoolMathSolver-RAG/actions/workflows/ci.yml/badge.svg)](https://github.com/yangzq50/GradeSchoolMathSolver-RAG/actions/workflows/ci.yml)

An AI-powered Grade School Math Solver with RAG (Retrieval-Augmented Generation). Automatically generates arithmetic problems, tracks correct and incorrect answers, and provides personalized practice and exams. Ideal for learning, testing, and building adaptive math tutoring agents.

## 🎯 Features

- **AI-Generated Questions**: Automatically generate math problems at easy, medium, and hard difficulty levels
- **Question Classification**: Categorize questions by type (addition, subtraction, multiplication, etc.)
- **User Management**: Track user progress, answer history, and performance statistics
- **Quiz History with RAG**: Store and retrieve similar questions using Elasticsearch for personalized learning
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
- SQLite database for user management
- Tracks answer correctness history with timestamps
- Calculates overall correctness and recent 100 questions score
- Tracks reviewed status for mistake review feature

### 4. Quiz History Service
- Elasticsearch integration for RAG capabilities
- Stores question, answer, and context for retrieval
- Enables similarity search for personalized learning

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

### 8. Mistake Review Service (NEW)
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
- Docker (for Elasticsearch)
- Docker Desktop with AI models (for LLM service via localhost:12434)
- 8GB+ RAM recommended

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yangzq50/GradeSchoolMathSolver-RAG.git
   cd GradeSchoolMathSolver-RAG
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   # AI_MODEL_URL should point to your Docker Desktop models endpoint (e.g., http://localhost:12434)
   # AI_MODEL_NAME should be your model name (e.g., ai/llama3.2:1B-Q4_0)
   # LLM_ENGINE should be your engine (e.g., llama.cpp)
   ```

4. **Set up Docker Desktop AI Models**
   - Ensure Docker Desktop is running with AI models enabled
   - The models should be accessible at localhost:12434 (or your configured port)
   - Example model: `ai/llama3.2:1B-Q4_0`

5. **Start infrastructure with Docker Compose**
   ```bash
   docker-compose up -d
   ```
   
   Note: This only starts Elasticsearch. The LLM service runs via Docker Desktop models on your localhost.

6. **Run the web application**
   
   From the project root directory, run:
   ```bash
   python -m web_ui.app
   ```
   
   **Note:** Make sure you run this command from the project root directory (`GradeSchoolMathSolver-RAG/`), not from inside the `web_ui/` folder.

7. **Open your browser**
   ```
   http://localhost:5000
   ```

### Alternative: Local Setup (Without Docker)

If you prefer to run everything locally:

1. **Set up LLM service** - Use any OpenAI-compatible API endpoint
2. **Install and run Elasticsearch**
3. **Update .env** with your LLM endpoint and Elasticsearch URLs
4. **Run the web application**

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
from models import AgentConfig
from services.agent_management import AgentManagementService

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
- `ELASTICSEARCH_HOST`: Elasticsearch hostname
- `DATABASE_PATH`: Path to SQLite database
- `TEACHER_SERVICE_ENABLED`: Enable/disable teacher feedback (default: True)

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
├── config.py                 # Configuration settings
├── models.py                 # Data models (including mistake review)
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker setup
├── Dockerfile               # Web app container
├── .env.example             # Environment template
├── services/                # Core services
│   ├── qa_generation/      # Question generation
│   ├── classification/     # Question classification
│   ├── account/           # User management
│   ├── quiz_history/      # RAG history storage
│   ├── exam/             # Exam management
│   ├── immersive_exam/   # Immersive exam management
│   ├── teacher/          # Teacher feedback service
│   ├── mistake_review/   # Mistake review service (NEW)
│   ├── agent/            # RAG bot logic
│   └── agent_management/ # Agent configuration
├── web_ui/               # Flask web interface
│   ├── app.py           # Web application
│   └── templates/       # HTML templates
│       ├── immersive_exam_create.html
│       ├── immersive_exam_live.html
│       ├── immersive_exam_results.html
│       └── mistake_review.html            # (NEW)
├── docs/                # Documentation
└── tests/              # Test files
    ├── test_basic.py
    ├── test_teacher_service.py
    ├── test_immersive_exam.py
    └── test_mistake_review.py            # (NEW)
```

### Adding New Features

1. **New Question Type**: Modify `services/qa_generation/service.py`
2. **New Category**: Add to `config.py` QUESTION_CATEGORIES
3. **New Agent Strategy**: Extend `services/agent/service.py`
4. **New UI Page**: Add template to `web_ui/templates/`

## 🐛 Troubleshooting

### Module Import Errors

If you get errors like `ModuleNotFoundError: No module named 'config'`, `'models'`, or `'services'`:

1. **Make sure you're running from the project root directory**
   ```bash
   cd GradeSchoolMathSolver-RAG
   python -m web_ui.app
   ```

2. **Alternative: Set PYTHONPATH**
   ```bash
   export PYTHONPATH=/path/to/GradeSchoolMathSolver-RAG
   python web_ui/app.py
   ```

3. **Make sure dependencies are installed**
   ```bash
   pip install -r requirements.txt
   ```

### AI Model Not Responding

1. Check if Docker Desktop models are running and accessible
2. Test the API: `curl http://localhost:12434/engines/llama.cpp/v1/models`
3. Verify your AI_MODEL_URL, AI_MODEL_NAME, and LLM_ENGINE environment variables are correct
4. Check that the model is available in Docker Desktop

### Elasticsearch Connection Issues

1. Check if ES is running: `docker ps | grep elasticsearch`
2. Test connection: `curl http://localhost:9200`
3. The system will work in limited mode without ES

### Database Errors

1. Check permissions on data directory
2. Delete and recreate: `rm data/math_solver.db`
3. Restart application to recreate tables

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- Ollama for easy AI model deployment
- LLaMA 3.2 for language generation
- Elasticsearch for RAG capabilities
- Flask for web framework
