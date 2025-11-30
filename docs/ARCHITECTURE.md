# System Architecture

GradeSchoolMathSolver is a modular AI-powered math learning system with RAG (Retrieval-Augmented Generation) capabilities.

## Component Overview

```
┌───────────────────────────────────────────────────────────────┐
│                      Web UI (Flask)                           │
│                   Port 5000 - User Interface                  │
└────────────────────────────┬──────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│                       Core Services                           │
├───────────────────────────────────────────────────────────────┤
│ QA Generation │ Exam Service │ Agent Service │ Teacher Service│
│ Classification│ Quiz History │ Account       │ Mistake Review │
└────────────────────────────┬──────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│                    External Services                          │
├───────────────────────────────────────────────────────────────┤
│  AI Model (Docker Model Runner)  │  Database (MariaDB/ES)    │
│  Port 12434 - LLaMA + Embeddings │  User data & Quiz History │
└───────────────────────────────────────────────────────────────┘
```

## Key Services

| Service | Purpose |
|---------|---------|
| **QA Generation** | Creates math problems at easy/medium/hard levels |
| **Classification** | Categorizes questions (addition, subtraction, etc.) |
| **Account** | User management and statistics tracking |
| **Quiz History** | RAG storage for personalized learning |
| **Exam** | Coordinates question generation and answer evaluation |
| **Immersive Exam** | Synchronized multi-participant exams |
| **Agent** | RAG bots that solve problems with reasoning |
| **Teacher** | Educational feedback for wrong answers |
| **Mistake Review** | Review and retry past incorrect answers |
| **Embedding** | Vector embeddings for semantic similarity search |

## Data Flow

### Human Exam
```
User → Web UI → Exam Service → QA Generation → Questions
                     ↓
              User submits answers
                     ↓
         Account Service → Statistics
                     ↓
         Quiz History → RAG Storage
```

### Agent Exam
```
Request → Exam Service → Questions → Agent Service
                                          ↓
                                   Classification (optional)
                                          ↓
                                   RAG Search (optional)
                                          ↓
                                   AI Model → Answer
```

## Configuration

All services are configured via `.env`:

```bash
# AI Model
GENERATION_SERVICE_URL=http://localhost:12434/engines/llama.cpp/v1/chat/completions
GENERATION_MODEL_NAME=ai/llama3.2:1B-Q4_0

# Database
DATABASE_BACKEND=mariadb
MARIADB_HOST=localhost

# Features
TEACHER_SERVICE_ENABLED=True
```

## Default RAG Bots

- **basic_agent**: Simple AI, no classification or RAG
- **classifier_agent**: Uses classification only
- **rag_agent**: Full classification + RAG
- **rag_correct_only**: RAG with correct answers only
