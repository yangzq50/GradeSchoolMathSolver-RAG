# GradeSchoolMathSolver-RAG

An AI-powered Grade School Math Solver with RAG (Retrieval-Augmented Generation). Automatically generates arithmetic problems, tracks correct and incorrect answers, and provides personalized practice and exams. Ideal for learning, testing, and building adaptive math tutoring agents.

## 🎯 Features

- **AI-Generated Questions**: Automatically generate math problems at easy, medium, and hard difficulty levels
- **Question Classification**: Categorize questions by type (addition, subtraction, multiplication, etc.)
- **User Management**: Track user progress, answer history, and performance statistics
- **Quiz History with RAG**: Store and retrieve similar questions using Elasticsearch for personalized learning
- **Intelligent AI Agents**: Configurable agents that can use classification and RAG for better problem-solving
- **Web Interface**: User-friendly Flask-based web UI for taking exams and viewing statistics
- **Agent Management**: Create and test different AI agent configurations
- **Performance Tracking**: Monitor correctness rates, recent performance, and trends
- **🆕 Immersive Exams**: Synchronized exams where all participants answer the same questions with optional answer reveal strategies

## 🏗️ Architecture

The system consists of 10 main components:

### 0. AI Model Service
- Deployed using Docker with Ollama running LLaMA 3.2
- Provides natural language generation for questions and reasoning
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

### 4. Quiz History Service
- Elasticsearch integration for RAG capabilities
- Stores question, answer, and context for retrieval
- Enables similarity search for personalized learning

### 5. Exam Service
- Coordinates question generation and answer evaluation
- Supports both human and AI agent exams
- Updates user statistics and quiz history

### 6. Immersive Exam Service (NEW)
- Synchronized exam management for multiple participants
- Pre-generates shared questions for all participants
- Ordered participant registration (humans and AI agents)
- Configurable reveal strategies for cheating experiments
- Server-controlled question progression
- Real-time status updates and results

### 7. Web UI Service
- Flask-based web interface
- User dashboard with statistics and trends
- Interactive exam interface
- Immersive exam creation and participation
- Agent testing and management

### 8. AI Agent Service
- Configurable problem-solving agents
- Optional question classification
- Optional RAG from quiz history
- Provides reasoning for answers

### 9. Agent Management Service
- Create, update, and delete agent configurations
- Pre-configured default agents
- Test agents with different settings

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (for AI model and Elasticsearch)
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
   ```

4. **Start infrastructure with Docker Compose**
   ```bash
   docker-compose up -d
   ```

5. **Pull the AI model**
   ```bash
   docker exec -it math-solver-ollama ollama pull llama3.2
   ```

6. **Run the web application**
   ```bash
   python web_ui/app.py
   ```

7. **Open your browser**
   ```
   http://localhost:5000
   ```

### Alternative: Local Setup (Without Docker)

If you prefer to run everything locally:

1. **Install Ollama** (see [AI Model Service docs](docs/AI_MODEL_SERVICE.md))
2. **Install and run Elasticsearch**
3. **Update .env** with local URLs
4. **Run the web application**

## 📖 Usage

### Taking an Exam (Human)

1. Navigate to the "Take Exam" page
2. Enter your username
3. Select difficulty level (easy, medium, hard)
4. Choose number of questions (1-20)
5. Answer the generated questions
6. Submit to see your results and statistics

### Creating an Immersive Exam (NEW)

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
   - Add AI agents from the dropdown
7. Click "Start Exam" when all participants are registered
8. Participants join using their username/agent name
9. Answer questions in synchronized order
10. View final results with leaderboard

### Testing an AI Agent

1. Navigate to the "Agents" page
2. Select an agent configuration
3. Set test parameters (difficulty, question count)
4. Run the test
5. Review agent performance and reasoning

### Creating a Custom Agent

```python
from models import AgentConfig
from services.agent_management import AgentManagementService

# Create agent management service
agent_mgmt = AgentManagementService()

# Define custom agent
custom_agent = AgentConfig(
    name="my_custom_agent",
    use_classification=True,
    use_rag=True,
    rag_top_k=3,
    include_incorrect_history=True
)

# Create agent
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

# Test Immersive Exam Service (NEW)
python services/immersive_exam/service.py

# Run all basic tests
python tests/test_basic.py

# Run immersive exam tests (NEW)
python tests/test_immersive_exam.py
```

## 🔧 Configuration

### Default Agents

The system creates these default agents:

1. **basic_agent**: Simple AI without classification or RAG
2. **classifier_agent**: Uses classification but no RAG
3. **rag_agent**: Uses both classification and RAG
4. **rag_correct_only**: RAG with only correct answers from history

### Environment Variables

See `.env.example` for all available configuration options.

Key settings:
- `AI_MODEL_URL`: URL of the AI model service
- `AI_MODEL_NAME`: Name of the model to use (e.g., llama3.2)
- `ELASTICSEARCH_HOST`: Elasticsearch hostname
- `DATABASE_PATH`: Path to SQLite database

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
├── models.py                 # Data models (including immersive exam models)
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
│   ├── immersive_exam/   # Immersive exam management (NEW)
│   ├── agent/            # AI agent logic
│   └── agent_management/ # Agent configuration
├── web_ui/               # Flask web interface
│   ├── app.py           # Web application
│   └── templates/       # HTML templates
│       ├── immersive_exam_create.html  # (NEW)
│       ├── immersive_exam_live.html    # (NEW)
│       └── immersive_exam_results.html # (NEW)
├── docs/                # Documentation
└── tests/              # Test files
    ├── test_basic.py
    └── test_immersive_exam.py  # (NEW)
```

### Adding New Features

1. **New Question Type**: Modify `services/qa_generation/service.py`
2. **New Category**: Add to `config.py` QUESTION_CATEGORIES
3. **New Agent Strategy**: Extend `services/agent/service.py`
4. **New UI Page**: Add template to `web_ui/templates/`

## 🐛 Troubleshooting

### AI Model Not Responding

1. Check if Ollama is running: `docker ps | grep ollama`
2. Test the API: `curl http://localhost:11434/api/version`
3. Check logs: `docker logs math-solver-ollama`

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
