# Elasticsearch Storage Documentation

## Overview

This document describes the Elasticsearch storage implementation for the GradeSchoolMathSolver-RAG system. Elasticsearch 9.2.1 is available as an **optional backend** for advanced full-text search and RAG (Retrieval-Augmented Generation) features.

**Note**: MariaDB is the default database backend. Elasticsearch is recommended when you need advanced full-text search and semantic similarity features for RAG functionality.

## When to Use Elasticsearch

Consider using Elasticsearch instead of the default MariaDB backend when you need:

- **Advanced full-text search**: Semantic matching and text analysis
- **RAG similarity search**: Finding similar historical questions for context
- **Real-time analytics**: Aggregations and statistics across large datasets
- **Flexible schema**: Document-oriented storage without predefined structure

For basic user management, answer history, and statistics, the default MariaDB backend is recommended for better performance and lower resource usage.

## Configuration

To use Elasticsearch as your database backend, set the following in your `.env` file:

```bash
# Switch to Elasticsearch backend
DATABASE_BACKEND=elasticsearch

# Elasticsearch Configuration
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=quiz_history
```

## Architecture

### Storage Services

The system uses two complementary services for data operations:

1. **AccountService** (`services/account/service.py`)
   - Manages user accounts and answer history
   - Handles user statistics calculations
   - Primary interface for storing quiz answers
   - Works with both Elasticsearch and MariaDB backends

2. **QuizHistoryService** (`services/quiz_history/service.py`)
   - Provides RAG (Retrieval-Augmented Generation) functionality
   - Enables similarity-based search of historical questions
   - Used for personalized learning recommendations
   - Optimized for Elasticsearch's full-text search capabilities

### Unified Storage Design

Both services share the same database indices/tables to prevent data duplication:
- **users** index/table: User account information
- **quiz_history** index/table: All answer history with unified schema

⚠️ **Important**: Data should be recorded **once** through `AccountService.record_answer()` to prevent duplicates.

## Elasticsearch Schema

### Users Index

**Index**: `users`

**Mapping**:
```json
{
  "mappings": {
    "properties": {
      "username": {"type": "keyword"},
      "created_at": {"type": "date"}
    }
  }
}
```

**Example Document**:
```json
{
  "_id": "john_doe",
  "_source": {
    "username": "john_doe",
    "created_at": "2025-11-17T05:00:00.000000"
  }
}
```

**Key Points**:
- Document ID is the username (ensures uniqueness)
- Uses `es.create()` to prevent overwriting existing users
- Timestamps stored as ISO 8601 format

### Quiz History Index (Unified Schema)

**Index**: `quiz_history` (configurable via `ELASTICSEARCH_INDEX`)

**Mapping**:
```json
{
  "mappings": {
    "properties": {
      "username": {"type": "keyword"},
      "question": {"type": "text"},
      "equation": {"type": "text"},
      "user_equation": {"type": "text"},
      "user_answer": {"type": "integer"},
      "correct_answer": {"type": "integer"},
      "is_correct": {"type": "boolean"},
      "category": {"type": "keyword"},
      "timestamp": {"type": "date"},
      "reviewed": {"type": "boolean"}
    }
  }
}
```

**Example Document**:
```json
{
  "_id": "auto-generated",
  "_source": {
    "username": "john_doe",
    "question": "What is 5 + 3?",
    "equation": "5 + 3",
    "user_equation": "5 + 3",
    "user_answer": 8,
    "correct_answer": 8,
    "is_correct": true,
    "category": "addition",
    "timestamp": "2025-11-17T05:00:00.000000",
    "reviewed": false
  }
}
```

**Field Descriptions**:
- `username`: User identifier (keyword for exact matching)
- `question`: Natural language question (text for full-text search)
- `equation`: Mathematical equation (text for search)
- `user_equation`: Backward compatibility alias for equation
- `user_answer`: User's answer (null if not answered)
- `correct_answer`: The correct answer
- `is_correct`: Whether answer was correct
- `category`: Question category (addition, subtraction, etc.)
- `timestamp`: When recorded (ISO 8601 format)
- `reviewed`: Whether mistake has been reviewed

## CRUD Operations

### Create User

```python
from services.account import AccountService

account_service = AccountService()
success = account_service.create_user("username")
```

**Behavior**:
- Uses `es.create()` which raises `ConflictError` if user exists
- Returns `True` on success, `False` on failure
- Validates username format (alphanumeric, underscore, hyphen, max 100 chars)

### Record Answer

```python
account_service.record_answer(
    username="john_doe",
    question="What is 5 + 3?",
    equation="5 + 3",
    user_answer=8,
    correct_answer=8,
    category="addition",
    refresh=False  # Use True only in tests
)
```

**Behavior**:
- Auto-calculates `is_correct` field
- Creates user if doesn't exist
- Optional `refresh` parameter for immediate search visibility (testing only)

### Get User

```python
user = account_service.get_user("username")
# Returns: {"username": "...", "created_at": "..."} or None
```

### List Users

```python
usernames = account_service.list_users()
# Returns: ["user1", "user2", ...]
```

### Get User Statistics

```python
stats = account_service.get_user_stats("username")
# Returns: UserStats with total_questions, correct_answers, percentages
```

**Calculations**:
- `total_questions`: Count of all answers
- `correct_answers`: Count where `is_correct == True`
- `overall_correctness`: (correct / total) × 100
- `recent_100_score`: Score for most recent 100 questions

### Get Answer History

```python
history = account_service.get_answer_history("username", limit=50)
# Returns: List of dicts with answer details
```

**Note**: Timestamps automatically converted to `datetime` objects for template compatibility.

### Search Relevant History (RAG)

```python
from services.quiz_history import QuizHistoryService

quiz_service = QuizHistoryService()
results = quiz_service.search_relevant_history(
    username="john_doe",
    question="What is 6 + 2?",
    category="addition",  # Optional
    top_k=5
)
```

**Search Strategy**:
- Text similarity matching on question and equation
- Optional category filtering
- Results sorted by relevance, then recency

### Mark Mistake as Reviewed

```python
from services.mistake_review import MistakeReviewService

mistake_service = MistakeReviewService()
success = mistake_service.mark_as_reviewed("username", "doc_id")
```

## Connection Management

### Elasticsearch 9.x Initialization

```python
es_url = f"http://{host}:{port}"
es = Elasticsearch(
    [es_url],
    request_timeout=10,
    max_retries=3,
    retry_on_timeout=True
)
```

### Configuration

Environment variables:
```bash
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=quiz_history
```

### Graceful Degradation

Services operate in "limited mode" if Elasticsearch is unavailable:
```python
if not account_service.es:
    # Operations will fail safely
    print("Elasticsearch not connected")
```

## Data Flow

### Taking an Exam

```
User submits answer
    ↓
ExamService.process_human_exam()
    ↓
AccountService.record_answer() ← Single point of entry
    ↓
Elasticsearch quiz_history index
    ↓
Available to both AccountService and QuizHistoryService
```

⚠️ **Critical**: Record data **once** through `AccountService.record_answer()`. Do not call both `AccountService.record_answer()` and `QuizHistoryService.add_history()`.

## Best Practices

### 1. Single Point of Data Entry
Always use `AccountService.record_answer()` to store quiz data.

### 2. Testing with Refresh
Use `refresh=True` in tests for immediate visibility:
```python
account_service.record_answer(..., refresh=True)
```

In production, omit this parameter for better performance.

### 3. Timestamp Handling
- Store as ISO 8601 strings: `datetime.utcnow().isoformat()`
- `get_answer_history()` auto-converts to `datetime` objects

### 4. Username Validation
Usernames: alphanumeric with underscores/hyphens, max 100 chars.

### 5. Error Handling
All operations gracefully handle Elasticsearch failures.

## Performance Optimization

### Query Optimization
- Use `term` queries for exact matches (username, category)
- Use `match` queries for full-text search (question, equation)
- Set appropriate limits (default: 100, max: 1000)

### Indexing Performance
- Avoid `refresh=True` in production
- Default refresh interval: 1 second
- Use bulk API for multiple operations

### Scaling Recommendations
Current setup handles hundreds of users. For larger scale:
- Multi-node Elasticsearch cluster
- Index sharding strategy
- Connection pooling
- Redis caching layer

## Troubleshooting

### "User already exists" on new users
Fixed by using `es.create()` instead of `es.index()`.

### Duplicate history records
Ensure data recorded only through `AccountService.record_answer()`.

### Template error: "str has no attribute strftime"
Fixed by auto-converting timestamps in `get_answer_history()`.

### Elasticsearch not connecting
1. Verify Elasticsearch is running: `curl http://localhost:9200`
2. Check URL-based initialization (ES 9.x requirement)
3. Verify environment variables

## Additional Resources

- [Database Service Architecture Documentation](DATABASE_SERVICE.md)
- [MariaDB Integration Documentation](MARIADB_INTEGRATION.md)
- [Elasticsearch 9.x Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/9.0/index.html)
- Detailed inline documentation available in:
  - `services/account/service.py` - AccountService
  - `services/quiz_history/service.py` - QuizHistoryService
  - `services/mistake_review/service.py` - MistakeReviewService
  - `services/database/elasticsearch_backend.py` - Elasticsearch backend implementation
