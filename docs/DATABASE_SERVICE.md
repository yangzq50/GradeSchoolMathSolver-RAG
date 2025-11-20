# Database Service Architecture

## Overview

The Database Service provides a unified abstraction layer for all database operations in the GradeSchoolMathSolver-RAG project. This architecture allows the application to easily switch between different database backends (MariaDB or Elasticsearch) without modifying business logic.

**Default Backend**: MariaDB 11.8 LTS is the default database backend, providing reliable relational storage with JSON support.

## Architecture

```
┌─────────────────────────────────────────────────┐
│          Application Services                   │
│  (AccountService, QuizHistoryService, etc.)     │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│          DatabaseService (Abstract)             │
│  - Unified Interface for CRUD Operations        │
│  - Database-agnostic API                        │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│        Backend Implementations                  │
│  ┌──────────────────────────────────────────┐  │
│  │  ElasticsearchDatabaseService            │  │
│  │  (Full-text search, JSON documents)      │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │  MariaDBDatabaseService                  │  │
│  │  (Relational, JSON support, vectors)     │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Directory Structure

```
services/database/
├── __init__.py                   # Module exports
├── service.py                    # Abstract DatabaseService interface
├── elasticsearch_backend.py     # Elasticsearch 9.x implementation
└── mariadb_backend.py           # MariaDB 11.8 LTS implementation
```

## Core Components

### 1. DatabaseService (Abstract Interface)

The `DatabaseService` class defines a standard interface that all database backend implementations must follow. This uses database-agnostic terminology:

**Key Methods:**
- `connect()`: Establish database connection
- `is_connected()`: Check connection status
- `create_collection(name, schema)`: Create collection/table/index
- `collection_exists(name)`: Check if collection exists
- `create_record(collection, id, data)`: Create new record (fail if exists)
- `insert_record(collection, data, id)`: Create or update record
- `get_record(collection, id)`: Retrieve record by ID
- `search_records(collection, query, filters, sort, limit, offset)`: Search with query and filters
- `update_record(collection, id, partial_data)`: Partial record update
- `delete_record(collection, id)`: Delete record
- `count_records(collection, query)`: Count matching records

### 2. ElasticsearchDatabaseService

Elasticsearch 9.x implementation optimized for full-text search and document storage.

**Features:**
- URL-based connection initialization
- Automatic index creation with mappings
- Full-text search capabilities
- JSON document storage
- Conflict detection for unique constraints
- Real-time search and analytics

**Best For:**
- Full-text search requirements (RAG functionality)
- Document-oriented data
- Real-time analytics
- Semantic search and similarity matching
- Flexible schema needs

### 3. MariaDBDatabaseService

MariaDB 11.8 LTS implementation using relational storage with typed columns (default backend).

**Features:**
- MySQL connector for reliable connections
- Proper relational tables with typed columns based on schema definitions
- Native indexes for fast queries
- Transaction support and ACID compliance
- Vector search capabilities (for future RAG enhancements)
- Mature, stable database engine
- Lower resource usage compared to Elasticsearch

**Best For:**
- User account management and statistics
- Answer history tracking
- Relational data models
- Transaction requirements
- Data integrity constraints
- Production deployments with lower resource requirements

### 4. Global Service Instance

The `get_database_service()` function provides a singleton database service instance based on configuration:

```python
from services.database import get_database_service

db = get_database_service()  # Returns configured database service
```

## Configuration

### Backend Selection

Set the database backend via environment variable in `.env`:

```bash
# Use MariaDB (default, recommended)
DATABASE_BACKEND=mariadb

# Or use Elasticsearch (for RAG full-text search features)
DATABASE_BACKEND=elasticsearch
```

### Elasticsearch Configuration

```bash
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=quiz_history
```

### MariaDB Configuration

```bash
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=root
MARIADB_PASSWORD=your_password
MARIADB_DATABASE=math_solver
```

## Usage Examples

### Basic CRUD Operations

```python
from services.database import get_database_service

# Get database service
db = get_database_service()

# Check connection
if db.is_connected():
    print("Database connected!")

# Create collection
schema = {
    "mappings": {  # For Elasticsearch
        "properties": {
            "username": {"type": "keyword"},
            "created_at": {"type": "date"}
        }
    }
}
db.create_collection("users", schema)

# Create a record
user_data = {
    "username": "john_doe",
    "created_at": "2025-01-15T10:00:00Z"
}
success = db.create_record("users", "john_doe", user_data)

# Get a record
user = db.get_record("users", "john_doe")
print(user)

# Update a record
db.update_record("users", "john_doe", {"last_login": "2025-01-16T09:00:00Z"})

# Search records
results = db.search_records(
    "users",
    filters={"username": "john_doe"},
    limit=10
)

# Count records
count = db.count_records("users", query={"match_all": {}})

# Delete a record
db.delete_record("users", "john_doe")
```

### Using in Application Services

```python
class AccountService:
    def __init__(self):
        self.db = get_database_service()
        self.users_collection = "users"
        self._create_collections()
    
    def _create_collections(self):
        schema = {...}
        self.db.create_collection(self.users_collection, schema)
    
    def create_user(self, username: str) -> bool:
        user_data = {
            "username": username,
            "created_at": datetime.utcnow().isoformat()
        }
        return self.db.create_record(self.users_collection, username, user_data)
```

## Docker Setup

### Using MariaDB (Default)

```bash
# Start MariaDB
docker-compose up -d mariadb

# Start web application with MariaDB
docker-compose up -d
```

### Using Elasticsearch

```bash
# Set environment variable
DATABASE_BACKEND=elasticsearch

# Start Elasticsearch
docker-compose up -d elasticsearch

# Start web application with Elasticsearch
docker-compose up -d
```

### Using Both (Development)

```bash
docker-compose --profile mariadb --profile elasticsearch up
```

## Data Models

### Schema Definitions

All database schemas are centrally defined in `services/database/schemas.py`:

#### UserRecord Schema

```python
@dataclass
class UserRecord:
    username: str              # Unique username (primary key)
    created_at: str           # ISO timestamp of account creation
```

#### AnswerHistoryRecord Schema

```python
@dataclass
class AnswerHistoryRecord:
    username: str              # User identifier
    question: str             # Full text of the math problem
    equation: str             # Mathematical equation
    user_answer: Optional[int] # User's submitted answer
    correct_answer: int       # The correct answer
    is_correct: bool          # Whether answer was correct
    category: str             # Question category
    timestamp: str            # ISO timestamp
    reviewed: bool            # Whether mistake has been reviewed
    record_id: Optional[str]  # Unique ID (auto-generated)
```

### Elasticsearch Mapping

Collections in Elasticsearch use index mappings:

```python
users_schema = {
    "mappings": {
        "properties": {
            "username": {"type": "keyword"},
            "created_at": {"type": "date"}
        }
    }
}

quiz_history_schema = {
    "mappings": {
        "properties": {
            "username": {"type": "keyword"},
            "question": {"type": "text"},
            "equation": {"type": "text"},
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

### MariaDB Schema

Collections in MariaDB use typed relational tables:

```sql
-- Users table
CREATE TABLE users (
    username VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Quiz history table
CREATE TABLE quiz_history (
    record_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    equation VARCHAR(500) NOT NULL,
    user_answer INT,
    correct_answer INT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    category VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    reviewed BOOLEAN DEFAULT FALSE,
    INDEX idx_username (username),
    INDEX idx_timestamp (timestamp),
    INDEX idx_category (category),
    INDEX idx_reviewed (reviewed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

Data is stored in properly typed columns for optimal performance and integrity.

## Adding New Database Backends

To add a new database backend:

1. **Create Backend Class**: Create a new file in `services/database/` (e.g., `redis_backend.py`)

2. **Implement Interface**: Implement all methods from `DatabaseService`:

```python
from .service import DatabaseService

class RedisDatabaseService(DatabaseService):
    def connect(self) -> bool:
        # Implementation
        pass
    
    def create_collection(self, name: str, schema: Dict) -> bool:
        # Implementation
        pass
    
    # ... implement all other methods
```

3. **Update Service Loader**: Add to `get_database_service()` in `service.py`:

```python
def get_database_service() -> DatabaseService:
    backend = os.getenv('DATABASE_BACKEND', 'elasticsearch').lower()
    
    if backend == 'redis':
        from .redis_backend import RedisDatabaseService
        return RedisDatabaseService()
    elif backend == 'mariadb':
        from .mariadb_backend import MariaDBDatabaseService
        return MariaDBDatabaseService()
    else:  # Default to elasticsearch
        from .elasticsearch_backend import ElasticsearchDatabaseService
        return ElasticsearchDatabaseService()
```

4. **Add Dependencies**: Update `pyproject.toml` with required packages

5. **Update Configuration**: Add configuration in `config.py` and `.env.example`

6. **Update Docker**: Add service to `docker-compose.yml` if applicable

## Testing

### Testing with Different Backends

```python
from services.database import set_database_service
from services.database.mariadb_backend import MariaDBDatabaseService

# For testing with MariaDB
db = MariaDBDatabaseService()
set_database_service(db)

# Your tests here
```

### Mocking Database Operations

```python
from unittest.mock import Mock
from services.database import set_database_service

# Create mock database
mock_db = Mock()
mock_db.is_connected.return_value = True
mock_db.get_record.return_value = {"username": "test_user"}

# Inject mock
set_database_service(mock_db)

# Your tests here
```

## Best Practices

1. **Use Generic Terminology**: Always use collection/record terminology in application code, not database-specific terms

2. **Handle Connection Failures**: Always check `is_connected()` before operations

3. **Schema Definition**: Define schemas that work across backends when possible

4. **Error Handling**: Wrap database operations in try-except blocks

5. **Testing**: Test with both backends to ensure compatibility

6. **Performance**: Choose backend based on your specific needs:
   - **MariaDB**: Better for user management, statistics, transactional consistency (default, recommended)
   - **Elasticsearch**: Better for full-text search, RAG similarity matching, analytics

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to database

**Solutions**:
- Check if database service is running: `docker ps`
- Verify configuration in `.env`
- Check network connectivity
- Review logs: `docker logs math-solver-elasticsearch` or `docker logs math-solver-mariadb`

### Schema Errors

**Problem**: Schema/mapping errors

**Solutions**:
- Verify schema format matches backend requirements
- Check data types are compatible
- Review backend-specific documentation

### Performance Issues

**Problem**: Slow queries or operations

**Solutions**:
- Add appropriate indexes (Elasticsearch) or database indexes (MariaDB)
- Optimize queries and filters
- Consider pagination for large result sets
- Monitor database resource usage

## Future Enhancements

The database service architecture is designed to support:

- **Vector Search**: MariaDB 11.8 supports vector search for RAG enhancements
- **Caching Layer**: Add Redis caching with minimal changes
- **Read Replicas**: Support multiple database instances for scaling
- **Bulk Operations**: Batch insert/update operations for performance
- **Schema Migrations**: Automated schema version management
- **Backup/Restore**: Automated backup strategies
- **Monitoring**: Database performance metrics and alerts

## Additional Resources

- [MariaDB Integration Documentation](MARIADB_INTEGRATION.md)
- [Elasticsearch Storage Documentation](ELASTICSEARCH_STORAGE.md)
- [Elasticsearch 9.x Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/9.0/index.html)
- [MariaDB 11.8 Documentation](https://mariadb.com/kb/en/what-is-mariadb-118/)
- [Database Service Source Code](../services/database/)
- [Schema Definitions](../services/database/schemas.py)
