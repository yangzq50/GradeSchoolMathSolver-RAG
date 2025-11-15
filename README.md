# GradeSchoolMathSolver-RAG

An AI-powered Grade School Math Solver with RAG (Retrieval-Augmented Generation). Automatically generates arithmetic problems, tracks correct and incorrect answers, and provides personalized practice and exams. Ideal for learning, testing, and building adaptive math tutoring agents.

## Features

- **Problem Generator**: Creates grade school arithmetic problems (addition, subtraction, multiplication, division)
- **Answer Tracker**: Tracks correct and incorrect answers with performance analytics
- **Local Database**: SQLite database for storing problems and student performance
- **LLaMA-1B Interface**: Optional LLM integration for hints and explanations
- **RAG Retrieval**: Adaptive problem selection based on student performance
- **FastAPI API**: RESTful API for testing and scoring

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yangzq50/GradeSchoolMathSolver-RAG.git
cd GradeSchoolMathSolver-RAG
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Start the API Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Generate a Problem
```bash
POST /api/problem/generate
{
  "problem_type": "addition",  # optional: addition, subtraction, multiplication, division
  "difficulty": 1               # 1-5
}
```

### Submit an Answer
```bash
POST /api/answer/submit
{
  "problem_id": 1,
  "user_answer": 42,
  "time_taken": 5.5  # optional, in seconds
}
```

### Get a Hint
```bash
POST /api/problem/hint
{
  "problem_id": 1
}
```

### Get Statistics
```bash
GET /api/stats?days=7
```

### Get Weak Areas
```bash
GET /api/stats/weak-areas
```

### Get Adaptive Problems
```bash
GET /api/problem/adaptive?limit=10
```

## Modules

### problem_generator.py
Generates arithmetic problems with configurable difficulty levels.

### answer_tracker.py
Tracks student answers and provides performance analytics.

### database.py
Database models and connection management using SQLAlchemy.

### llama_interface.py
Interface for LLaMA-1B model to provide hints and explanations.
Note: Works in fallback mode if LLaMA model is not available.

### rag_retrieval.py
RAG system for adaptive problem selection based on performance.

### main.py
FastAPI application with all API endpoints.

## Configuration

Edit `config.py` to customize:
- Database URL
- LLaMA model name
- RAG settings
- API host and port
- Problem generation parameters

## Example Usage

```python
import requests

# Start by generating a problem
response = requests.post("http://localhost:8000/api/problem/generate", json={
    "problem_type": "addition",
    "difficulty": 1
})
problem = response.json()
print(f"Problem: {problem['problem_text']}")

# Submit an answer
response = requests.post("http://localhost:8000/api/answer/submit", json={
    "problem_id": problem['problem_id'],
    "user_answer": 10,
    "time_taken": 3.5
})
result = response.json()
print(f"Result: {result['feedback']}")

# Get statistics
response = requests.get("http://localhost:8000/api/stats")
stats = response.json()
print(f"Accuracy: {stats['accuracy']:.2f}%")
```

## Development

The system is designed to work with minimal dependencies. The LLaMA and RAG features are optional and the system will work in fallback mode if these components cannot be initialized.

## License

See LICENSE file for details.
