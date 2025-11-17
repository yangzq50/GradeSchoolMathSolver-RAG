# Elasticsearch Storage Documentation

## Overview

This document describes the Elasticsearch storage implementation for the GradeSchoolMathSolver-RAG system. As of the SQLite to Elasticsearch migration, all data persistence is handled exclusively through Elasticsearch 9.2.1.

## Architecture

### Storage Services

The system uses two primary services for data operations:

1. **AccountService** (`services/account/service.py`)
   - Manages user accounts and answer history
   - Handles user statistics calculations
   - Primary interface for account-related CRUD operations

2. **QuizHistoryService** (`services/quiz_history/service.py`)
   - Provides RAG (Retrieval-Augmented Generation) functionality
   - Enables similarity-based search of historical questions
   - Used for personalized learning recommendations

### Unified Storage Design

Both services share the same Elasticsearch indices to avoid data duplication:
- **users** index: Stores user account information
- **quiz_history** index: Stores all answer history (unified from previous separate implementations)

⚠️ **Important**: Since both services write to the same `quiz_history` index, data should only be recorded **once** through AccountService to prevent duplicates.

## Elasticsearch Schema

### Users Index

**Index Name**: `users`

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

**Document Structure**:
```json
{
  "_id": "username",  // Username is used as document ID
  "_source": {
    "username": "john_doe",
    "created_at": "2025-11-17T05:00:00.000000"
  }
}
```

**Key Points**:
- Document ID is the username itself (ensures uniqueness)
- Uses `es.create()` for insertion to prevent overwriting existing users
- `created_at` stored as ISO 8601 format string

### Quiz History Index (Unified Schema)

**Index Name**: `quiz_history` (configurable via `ELASTICSEARCH_INDEX` environment variable)

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

**Document Structure**:
```json
{
  "_id": "auto-generated-by-elasticsearch",
  "_source": {
    "username": "john_doe",
    "question": "What is 5 + 3?",
    "equation": "5 + 3",
    "user_equation": "5 + 3",  // Backward compatibility field
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
- `question`: Natural language question text (text for full-text search)
- `equation`: Mathematical equation (text for full-text search)
- `user_equation`: Alias for equation (maintained for backward compatibility with QuizHistoryService)
- `user_answer`: User's submitted answer (null if not answered or LLM failed)
- `correct_answer`: The correct answer
- `is_correct`: Boolean flag indicating if user_answer == correct_answer
- `category`: Question category (addition, subtraction, etc.)
- `timestamp`: When the answer was recorded (ISO 8601 format)
- `reviewed`: Whether this mistake has been reviewed (for mistake review feature)

## CRUD Operations

### Create Operations

#### Create User
```python
from services.account import AccountService

account_service = AccountService()
success = account_service.create_user("username")
```

**Elasticsearch Operation**:
```python
es.create(index="users", id="username", document={
    "username": "username",
    "created_at": datetime.utcnow().isoformat()
})
```

**Behavior**:
- Uses `es.create()` which raises `ConflictError` if user already exists
- Returns `True` on success, `False` on failure
- Validates username format before creation

#### Record Answer
```python
account_service.record_answer(
    username="john_doe",
    question="What is 5 + 3?",
    equation="5 + 3",
    user_answer=8,
    correct_answer=8,
    category="addition",
    refresh=False  # Set to True in tests for immediate visibility
)
```

**Elasticsearch Operation**:
```python
es.index(index="quiz_history", document={
    "username": username,
    "question": question,
    "equation": equation,
    "user_answer": user_answer,
    "correct_answer": correct_answer,
    "is_correct": user_answer == correct_answer,
    "category": category,
    "timestamp": datetime.utcnow().isoformat(),
    "reviewed": False
})
```

**Behavior**:
- Auto-generates document ID
- Calculates `is_correct` automatically
- Creates user if doesn't exist
- Optional `refresh` parameter for testing

### Read Operations

#### Get User
```python
user = account_service.get_user("username")
# Returns: {"username": "...", "created_at": "..."} or None
```

**Elasticsearch Operation**:
```python
es.get(index="users", id="username")
```

**Behavior**:
- Returns `None` if user not found (catches `NotFoundError`)
- Returns user document as dictionary

#### List All Users
```python
usernames = account_service.list_users()
# Returns: ["user1", "user2", ...]
```

**Elasticsearch Operation**:
```python
es.search(index="users", body={
    "size": 1000,
    "query": {"match_all": {}},
    "_source": ["username"]
})
```

#### Get User Statistics
```python
stats = account_service.get_user_stats("username")
# Returns: UserStats object with total_questions, correct_answers, etc.
```

**Elasticsearch Operation**:
```python
# Fetches all answers for the user
es.search(index="quiz_history", body={
    "size": 10000,
    "query": {"term": {"username": username}},
    "sort": [{"timestamp": {"order": "desc"}}]
})
```

**Calculations**:
- `total_questions`: Count of all documents
- `correct_answers`: Count where `is_correct == True`
- `overall_correctness`: (correct_answers / total_questions) * 100
- `recent_100_score`: Score for most recent 100 questions

#### Get Answer History
```python
history = account_service.get_answer_history("username", limit=50)
# Returns: List of dictionaries with answer details
```

**Elasticsearch Operation**:
```python
es.search(index="quiz_history", body={
    "size": limit,
    "query": {"term": {"username": username}},
    "sort": [{"timestamp": {"order": "desc"}}]
})
```

**Special Handling**:
- Timestamps are converted from ISO string to `datetime` objects for template compatibility
- Document ID is included as `id` field in results

#### Search Relevant History (RAG)
```python
from services.quiz_history import QuizHistoryService

quiz_service = QuizHistoryService()
results = quiz_service.search_relevant_history(
    username="john_doe",
    question="What is 6 + 2?",
    category="addition",  # Optional filter
    top_k=5
)
```

**Elasticsearch Operation**:
```python
es.search(index="quiz_history", body={
    "size": top_k,
    "query": {
        "bool": {
            "must": [
                {"match": {"username": username}}
            ],
            "should": [
                {"match": {"question": {"query": question, "boost": 2}}},
                {"match": {"user_equation": question}}
            ]
        }
    },
    "sort": [
        {"_score": {"order": "desc"}},
        {"timestamp": {"order": "desc"}}
    ]
})
```

**Behavior**:
- Uses text similarity matching on question and equation
- Optionally filters by category
- Returns results sorted by relevance score, then by recency

### Update Operations

#### Mark Mistake as Reviewed
```python
from services.mistake_review import MistakeReviewService

mistake_service = MistakeReviewService()
success = mistake_service.mark_as_reviewed("username", "mistake_doc_id")
```

**Elasticsearch Operation**:
```python
# First verify ownership
es.get(index="quiz_history", id=mistake_id)

# Then update
es.update(index="quiz_history", id=mistake_id, body={
    "doc": {"reviewed": True}
})
```

**Behavior**:
- Verifies username matches before updating
- Sets `reviewed` field to `True`
- Returns `True` on success, `False` on failure

### Delete Operations

Currently, there are **no delete operations** implemented in the system. All data is retained for historical analysis and learning purposes.

## Connection Management

### Initialization (Elasticsearch 9.x)

```python
es_url = f"http://{host}:{port}"
es = Elasticsearch(
    [es_url],
    request_timeout=10,
    max_retries=3,
    retry_on_timeout=True
)
```

**Key Points**:
- ES 9.x uses URL-based initialization (not dictionary-based)
- Connection failure is graceful - services operate in "limited mode"
- Indices are created automatically on first connection if they don't exist

### Configuration

Set via environment variables:
```bash
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=quiz_history
```

## Data Flow

### Taking an Exam (Human User)

```
User submits answer
    ↓
ExamService.process_human_exam()
    ↓
AccountService.record_answer() ← ONLY ONE INSERTION
    ↓
Elasticsearch quiz_history index
    ↓
QuizHistoryService can read the same data for RAG
```

⚠️ **Critical**: Data is recorded **only once** through `AccountService.record_answer()`. Previous implementations recorded twice (once in AccountService, once in QuizHistoryService) which caused duplicates.

### Taking an Exam (Agent/Bot)

```
Agent generates answer
    ↓
ExamService.process_agent_exam()
    ↓
AccountService.record_answer() ← ONLY ONE INSERTION
    ↓
Elasticsearch quiz_history index
```

### Immersive Exam

```
Participant submits answer
    ↓
ImmersiveExamService.submit_answer()
    ↓
AccountService.record_answer() ← ONLY ONE INSERTION
    ↓
Elasticsearch quiz_history index
```

## Best Practices

### 1. Single Point of Data Entry
Always use `AccountService.record_answer()` to record quiz data. Do not call both `AccountService.record_answer()` and `QuizHistoryService.add_history()` - this creates duplicates.

### 2. Refresh for Testing
When writing tests, use the `refresh=True` parameter to ensure data is immediately searchable:
```python
account_service.record_answer(..., refresh=True)
```

In production, omit this parameter to allow Elasticsearch's default refresh interval (better performance).

### 3. Timestamp Handling
- Store timestamps as ISO 8601 strings: `datetime.utcnow().isoformat()`
- `get_answer_history()` automatically converts timestamps to `datetime` objects for template compatibility

### 4. Username Validation
Usernames must be alphanumeric with underscores and hyphens, max 100 characters. Validation happens automatically in all operations.

### 5. Error Handling
Services gracefully handle Elasticsearch connection failures:
```python
if not account_service.es:
    # Service is in limited mode, operations will fail safely
    print("Elasticsearch not connected")
```

## Troubleshooting

### Issue: "User already exists" when creating new users
**Solution**: This was fixed by using `es.create()` instead of `es.index()`. The create method properly raises `ConflictError` for duplicates.

### Issue: Duplicate history records
**Solution**: Ensure data is recorded only once through `AccountService.record_answer()`. Remove any duplicate calls to `QuizHistoryService.add_history()`.

### Issue: Template error - "str object has no attribute 'strftime'"
**Solution**: `get_answer_history()` now converts ISO string timestamps to `datetime` objects automatically.

### Issue: Elasticsearch not connecting
**Solution**: 
1. Check Elasticsearch is running: `curl http://localhost:9200`
2. Verify ES 9.x URL-based initialization is used (not dictionary format)
3. Check environment variables are set correctly

## Migration Notes

### From SQLite to Elasticsearch

The migration involved:
1. Replacing SQLAlchemy ORM with direct Elasticsearch queries
2. Merging `users` table → `users` index
3. Merging `answer_history` table + `quiz_history` index → unified `quiz_history` index
4. Updating all CRUD operations to use Elasticsearch API
5. Converting timestamps from datetime objects to ISO strings (storage) and back (retrieval)
6. Changing document IDs from integers to strings (ES uses string IDs)

### Schema Differences

| SQLite (Old) | Elasticsearch (New) | Notes |
|-------------|-------------------|-------|
| Integer ID (auto-increment) | String ID (auto-generated) | ES document IDs |
| `answer_history.equation` | `quiz_history.equation` + `user_equation` | Both fields for compatibility |
| Direct datetime objects | ISO 8601 strings | Converted on read for templates |
| Transaction-based | Eventually consistent | Refresh parameter for tests |

## Performance Considerations

### Query Optimization
- Use `term` queries for exact matches on keyword fields (username, category)
- Use `match` queries for full-text search (question, equation)
- Limit result sizes appropriately (default: 100, max: 1000)

### Indexing Performance
- Avoid using `refresh=True` in production (synchronous refresh is expensive)
- Elasticsearch refreshes every 1 second by default (configurable)
- For bulk operations, consider using the bulk API

### Scaling
- Current configuration suitable for hundreds of users
- For thousands of users, consider:
  - Elasticsearch cluster with multiple nodes
  - Index sharding strategy
  - Connection pooling
  - Caching layer (Redis) for frequently accessed data

## API Reference

See inline documentation in:
- `services/account/service.py` - AccountService methods
- `services/quiz_history/service.py` - QuizHistoryService methods
- `services/mistake_review/service.py` - MistakeReviewService methods

## Version History

- **v2.0** (Current): Elasticsearch-only storage with unified schema
- **v1.0** (Deprecated): Dual storage (SQLite + Elasticsearch) with redundant data
