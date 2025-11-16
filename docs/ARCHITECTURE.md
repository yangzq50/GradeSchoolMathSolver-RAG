# System Architecture

## Overview

GradeSchoolMathSolver-RAG is a modular AI-powered math learning system with 9 core components working together to provide personalized math education.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web UI (Flask)                           │
│                     Port 5000 - User Interface                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ HTTP REST API
             │
┌────────────▼────────────────────────────────────────────────────┐
│                        Exam Service                              │
│          Coordinates question generation & evaluation             │
└──┬────┬─────┬───────┬──────────────┬──────────────┬────────────┘
   │    │     │       │              │              │
   │    │     │       │              │              │
┌──▼────▼─────▼───────▼──────────────▼──────────────▼────────────┐
│                      Core Services Layer                         │
├──────────────────────────────────────────────────────────────────┤
│  QA Generation │ Classification │ Account │ Quiz History │Agent  │
│  Service       │ Service        │ Service │ Service      │Service│
└──┬────────┬────┴────────┬───────┴────┬────┴──────┬──────┴───┬───┘
   │        │             │            │           │          │
   │        │             │            │           │          │
┌──▼────────▼─────────────▼────────────▼───────────▼──────────▼───┐
│                    External Services Layer                       │
├──────────────────────────────────────────────────────────────────┤
│ AI Model (Docker Desktop) │  SQLite Database  │  Elasticsearch    │
│ Port 12434                 │  data/solver.db   │  Port 9200        │
│ - LLaMA 3.2 (quantized)    │  - Users          │  - Quiz History   │
│ - OpenAI API Format        │  - Answer History │  - RAG Search     │
│ - Chat Completions         │  - Statistics     │  - Similarity     │
└────────────────────────────┴───────────────────┴───────────────────┘
```

## Service Details

### 1. Web UI Service
- **Technology**: Flask + Jinja2
- **Port**: 5000
- **Responsibilities**:
  - User interface for taking exams
  - Display user statistics and history
  - Agent management interface
  - REST API endpoints

### 2. Exam Service
- **Purpose**: Central coordinator for exams
- **Functions**:
  - Generate exam questions
  - Evaluate answers
  - Update user statistics
  - Store quiz history
  - Support both human and agent exams

### 3. QA Generation Service
- **Purpose**: Generate math questions
- **Difficulty Levels**:
  - Easy: Single operation (1-20)
  - Medium: Multiple operations (1-50)
  - Hard: Parentheses, division
- **Features**:
  - Equation generation
  - Natural language conversion (AI-powered)
  - Fallback templates

### 4. Classification Service
- **Purpose**: Categorize questions
- **Categories**:
  - addition
  - subtraction
  - multiplication
  - division
  - mixed_operations
  - parentheses
  - fractions
- **Methods**:
  - Rule-based (primary)
  - AI-based (optional)

### 5. Account Service
- **Purpose**: User management
- **Database**: SQLite
- **Tables**:
  - users: User accounts
  - answer_history: All answers with timestamps
- **Statistics**:
  - Total questions answered
  - Correct answer count
  - Overall correctness percentage
  - Recent 100 questions score

### 6. Quiz History Service
- **Purpose**: RAG storage and retrieval
- **Database**: Elasticsearch
- **Features**:
  - Full-text search
  - Similarity matching
  - Category filtering
  - Top-K retrieval
- **Use Case**: Provide context to RAG bots

### 7. RAG Bot Service
- **Purpose**: Solve math problems
- **Configuration Options**:
  - use_classification: Enable question categorization
  - use_rag: Enable history retrieval
  - rag_top_k: Number of history items to retrieve
  - include_incorrect_history: Include wrong answers in RAG
- **Process**:
  1. Classify question (optional)
  2. Retrieve relevant history (optional)
  3. Generate answer with AI model
  4. Provide reasoning

### 8. Agent Management Service
- **Purpose**: Manage agent configurations
- **Storage**: JSON files in data/agents/
- **Default Agents**:
  - basic_agent: No classification, no RAG
  - classifier_agent: Classification only
  - rag_agent: Full features
  - rag_correct_only: RAG with correct answers only

### 9. AI Model Service
- **Technology**: Docker Model Runner (or Ollama/other compatible service)
- **Port**: 12434 (default for Docker Model Runner)
- **API**: OpenAI-compatible chat completions format
- **Endpoint**: `/engines/{LLM_ENGINE}/v1/chat/completions`
- **Uses**:
  - Generate natural language questions
  - Classify questions (optional, with fallback)
  - Solve problems with reasoning
  - Provide educational feedback (teacher service)
- **Models**: LLaMA 3.2 (quantized: 1B-Q4_0, 3B-Q4_0, 7B) or similar

## Data Flow

### Human Exam Flow
```
1. User → Web UI: Request exam (username, difficulty, count)
2. Web UI → Exam Service: Generate questions
3. Exam Service → QA Generation: Create questions
4. QA Generation → AI Model: Convert to natural language
5. QA Generation → Classification: Categorize questions
6. Questions → Web UI → User: Display exam
7. User → Web UI: Submit answers
8. Web UI → Exam Service: Process answers
9. Exam Service → Account Service: Update statistics
10. Exam Service → Quiz History: Store for RAG
11. Results → Web UI → User: Show score
```

### Agent Exam Flow
```
1. User → Web UI: Request agent test
2. Web UI → Agent Management: Load agent config
3. Web UI → Exam Service: Generate questions
4. Exam Service → QA Generation: Create questions
5. Questions → Agent Service: Solve each question
6. Agent Service → Classification: Categorize (if enabled)
7. Agent Service → Quiz History: RAG search (if enabled)
8. Agent Service → AI Model: Generate answer
9. Agent Service → Exam Service: Return answers
10. Exam Service → Quiz History: Store results
11. Results → Web UI → User: Show performance
```

## Database Schemas

### SQLite (Account Service)

**users table:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**answer_history table:**
```sql
CREATE TABLE answer_history (
    id INTEGER PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    question VARCHAR(500) NOT NULL,
    equation VARCHAR(200) NOT NULL,
    user_answer FLOAT NOT NULL,
    correct_answer FLOAT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    category VARCHAR(50) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Elasticsearch (Quiz History Service)

**quiz_history index:**
```json
{
  "mappings": {
    "properties": {
      "username": {"type": "keyword"},
      "question": {"type": "text"},
      "user_equation": {"type": "text"},
      "user_answer": {"type": "float"},
      "correct_answer": {"type": "float"},
      "is_correct": {"type": "boolean"},
      "category": {"type": "keyword"},
      "timestamp": {"type": "date"}
    }
  }
}
```

## Configuration

### Environment Variables

All services are configured via environment variables in `.env`:

```bash
# AI Model
AI_MODEL_URL=http://localhost:12434
AI_MODEL_NAME=ai/llama3.2:1B-Q4_0
LLM_ENGINE=llama.cpp

# Database
DATABASE_PATH=data/math_solver.db

# Elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=quiz_history

# Web UI
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

## Deployment Options

### Local Development
- Run services individually for development
- Use Docker Model Runner or local Ollama installation
- SQLite for persistence

### Docker Compose (Recommended)
- Elasticsearch and Web UI in containers
- Docker Model Runner running on host
- Persistent volumes for data
- Easy scaling

### Production
- Separate AI model service (Docker Model Runner, Ollama, or cloud API)
- Dedicated Elasticsearch cluster
- Load balanced web servers
- PostgreSQL instead of SQLite (for scaling)

## Scaling Considerations

### Vertical Scaling
- Increase AI model resources (GPU)
- More RAM for Elasticsearch
- Larger SQLite → PostgreSQL

### Horizontal Scaling
- Multiple web UI instances (stateless)
- Elasticsearch cluster with replicas
- Shared database connection pooling
- Load balancer in front of web UI

### Performance Optimization
- Cache frequently used questions
- Pre-compute user statistics
- Batch RAG retrieval
- Async AI model calls
- Connection pooling

## Security

### Authentication (To Be Added)
- User authentication for web UI
- API key for agent access
- JWT tokens for session management

### Data Protection
- Input validation on all endpoints
- SQL injection prevention (parameterized queries)
- XSS protection in web UI
- Rate limiting on API calls
- Secure credential storage

### Network Security
- Internal network for services
- HTTPS for web UI
- Firewall rules
- VPC/private network for databases

## Monitoring

### Metrics to Track
- Question generation success rate
- AI model response time
- Exam completion rate
- User correctness trends
- Agent performance comparison
- API response times
- Error rates

### Logging
- Application logs to files
- Structured logging (JSON)
- Log rotation
- Error tracking (Sentry)
- Performance monitoring (APM)

## Future Enhancements

### Planned Features
1. Real-time multiplayer exams
2. Adaptive difficulty based on performance
3. Visual equation editor
4. Mobile app (React Native)
5. Teacher dashboard for classroom management
6. Parent progress reports
7. Gamification (badges, leaderboards)
8. Multi-language support

### Technical Improvements
1. GraphQL API
2. WebSocket for real-time updates
3. Redis caching layer
4. Message queue (Celery) for async tasks
5. Microservices architecture
6. Kubernetes deployment
7. CI/CD pipeline
8. Automated testing suite

## Troubleshooting

### Common Issues

1. **AI Model Not Responding**
   - Check Docker Model Runner or Ollama status
   - Verify model is downloaded
   - Test API endpoint (localhost:12434 or localhost:11434)
   - Services fall back to templates

2. **Elasticsearch Connection Failed**
   - Check ES is running
   - Verify port 9200 accessible
   - System works without ES (limited RAG)

3. **Database Lock Errors**
   - SQLite concurrency limitation
   - Consider PostgreSQL for production
   - Reduce concurrent writes

4. **Slow Question Generation**
   - AI model resource constraints
   - Use smaller model variant
   - Enable GPU acceleration
   - Cache generated questions

## Development Workflow

1. **Setup**: Run `./start.sh` to initialize system
2. **Test**: Run `python tests/test_basic.py`
3. **Develop**: Modify services as needed
4. **Test Again**: Verify changes don't break tests
5. **Document**: Update relevant documentation
6. **Deploy**: Use Docker Compose for production

## API Reference

See `web_ui/app.py` for complete API documentation. Key endpoints:

- `GET /api/users` - List all users
- `POST /api/users` - Create user
- `POST /api/exam/human` - Generate exam
- `POST /api/exam/agent` - Test agent
- `GET /api/agents` - List agents
- `POST /api/agents` - Create agent

## Support

For issues or questions:
1. Check this documentation
2. Review service-specific README files
3. Check logs in Docker containers
4. Open issue on GitHub
