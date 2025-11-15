# API Documentation

## Base URL

When running locally: `http://localhost:8000`

## Authentication

Currently, no authentication is required. This can be added for production use.

## Endpoints

### 1. Root
**GET** `/`

Get API information and available endpoints.

**Response:**
```json
{
  "message": "Welcome to GradeSchoolMathSolver-RAG API",
  "version": "1.0.0",
  "endpoints": { ... }
}
```

---

### 2. Generate Problem
**POST** `/api/problem/generate`

Generate a new math problem.

**Request Body:**
```json
{
  "problem_type": "addition",  // optional: addition, subtraction, multiplication, division
  "difficulty": 1              // 1-5
}
```

**Response:**
```json
{
  "problem_id": 1,
  "problem_text": "5 + 3 = ?",
  "problem_type": "addition",
  "difficulty": 1
}
```

---

### 3. Submit Answer
**POST** `/api/answer/submit`

Submit an answer to a problem.

**Request Body:**
```json
{
  "problem_id": 1,
  "user_answer": 8,
  "time_taken": 3.5  // optional, in seconds
}
```

**Response:**
```json
{
  "answer_id": 1,
  "is_correct": true,
  "correct_answer": 8.0,
  "user_answer": 8.0,
  "problem_text": "5 + 3 = ?",
  "feedback": "Correct! Well done!"
}
```

---

### 4. Get Hint
**POST** `/api/problem/hint`

Get a hint for a problem.

**Request Body:**
```json
{
  "problem_id": 1
}
```

**Response:**
```json
{
  "hint": "Think about counting up from the first number."
}
```

---

### 5. Get Explanation
**GET** `/api/problem/{problem_id}/explanation`

Get a step-by-step explanation for a problem.

**Response:**
```json
{
  "explanation": "To solve 5 + 3 = ?, work through the addition step by step. The answer is 8."
}
```

---

### 6. Get Statistics
**GET** `/api/stats?days=7`

Get performance statistics for the last N days.

**Query Parameters:**
- `days` (optional, default: 7): Number of days to look back

**Response:**
```json
{
  "total_answers": 10,
  "correct_answers": 8,
  "incorrect_answers": 2,
  "accuracy": 80.0,
  "average_time": 4.2
}
```

---

### 7. Get Weak Areas
**GET** `/api/stats/weak-areas`

Identify problem types where more practice is needed.

**Response:**
```json
{
  "weak_areas": [
    {
      "problem_type": "division",
      "accuracy": 60.0,
      "total_attempts": 5,
      "correct_attempts": 3
    }
  ]
}
```

---

### 8. Get Adaptive Problems
**GET** `/api/problem/adaptive?limit=10`

Get personalized problem recommendations based on performance.

**Query Parameters:**
- `limit` (optional, default: 10): Maximum number of problems to return

**Response:**
```json
{
  "problems": [
    {
      "problem_id": 5,
      "problem_text": "12 ÷ 4 = ?",
      "problem_type": "division",
      "difficulty": 2,
      "reason": "Practice needed in division"
    }
  ]
}
```

---

### 9. Get Problem
**GET** `/api/problem/{problem_id}`

Get details of a specific problem.

**Response:**
```json
{
  "problem_id": 1,
  "problem_text": "5 + 3 = ?",
  "problem_type": "addition",
  "difficulty": 1
}
```

---

### 10. List Problems
**GET** `/api/problems?skip=0&limit=10&problem_type=addition`

List problems with optional filtering.

**Query Parameters:**
- `skip` (optional, default: 0): Number of problems to skip
- `limit` (optional, default: 10): Maximum number of problems to return
- `problem_type` (optional): Filter by problem type

**Response:**
```json
{
  "problems": [
    {
      "problem_id": 1,
      "problem_text": "5 + 3 = ?",
      "problem_type": "addition",
      "difficulty": 1
    }
  ]
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message description"
}
```

Common status codes:
- `404 Not Found`: Problem or resource not found
- `500 Internal Server Error`: Server error

---

## Example Workflow

1. **Generate a problem**:
```bash
curl -X POST http://localhost:8000/api/problem/generate \
  -H "Content-Type: application/json" \
  -d '{"problem_type": "addition", "difficulty": 1}'
```

2. **Submit an answer**:
```bash
curl -X POST http://localhost:8000/api/answer/submit \
  -H "Content-Type: application/json" \
  -d '{"problem_id": 1, "user_answer": 8, "time_taken": 3.5}'
```

3. **Get statistics**:
```bash
curl http://localhost:8000/api/stats?days=7
```

4. **Get adaptive problems**:
```bash
curl http://localhost:8000/api/problem/adaptive?limit=5
```
