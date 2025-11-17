# Database Service Architecture

## Overview

The Database Service provides a unified abstraction layer for all database operations in the GradeSchoolMathSolver-RAG project. This architecture allows the application to easily switch between different database backends (Elasticsearch or MariaDB) without modifying business logic.

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
- Full-text search requirements
- Document-oriented data
- Real-time analytics
- Flexible schema needs

### 3. MariaDBDatabaseService

MariaDB 11.8 LTS implementation using relational storage with JSON support.

**Features:**
- MySQL connector for reliable connections
- JSON column type for flexible data storage
- Transaction support
- ACID compliance
- Vector search capabilities (for future RAG enhancements)
- Mature, stable database engine

**Best For:**
- Relational data models
- Transaction requirements
- Data integrity constraints
- Vector search for RAG (future feature)
- Traditional RDBMS needs

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
# Use Elasticsearch (default)
DATABASE_BACKEND=elasticsearch

# Or use MariaDB
DATABASE_BACKEND=mariadb
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

### Using Elasticsearch (Default)

```bash
docker-compose up
```

### Using MariaDB

```bash
DATABASE_BACKEND=mariadb docker-compose --profile mariadb up
```

### Using Both (Development)

```bash
docker-compose --profile elasticsearch --profile mariadb up
```

## Data Models

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
```

### MariaDB Schema

Collections in MariaDB use tables with JSON columns:

```sql
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

Data is stored in the `data` JSON column for flexibility.

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

4. **Add Dependencies**: Update `requirements.txt` with required packages

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
   - Elasticsearch: Better for full-text search, analytics
   - MariaDB: Better for transactional consistency, relational data

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

- [Elasticsearch 9.x Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/9.0/index.html)
- [MariaDB 11.8 Documentation](https://mariadb.com/kb/en/what-is-mariadb-118/)
- [Database Service Source Code](../services/database/)
