# Database Service Architecture

## Overview

The Database Service provides a unified abstraction layer for all database operations in the GradeSchoolMathSolver-RAG project. This architecture allows the application to easily switch between different database backends (Elasticsearch, MongoDB, PostgreSQL, etc.) without modifying business logic.

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
│  │  ElasticsearchDatabaseService (Current)  │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │  MongoDBDatabaseService (Future)         │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │  PostgreSQLDatabaseService (Future)      │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Directory Structure

```
services/database/
├── __init__.py                   # Module exports
├── service.py                    # Abstract DatabaseService interface
└── elasticsearch_backend.py     # Elasticsearch implementation
```

## Core Components

### 1. DatabaseService (Abstract Interface)

The `DatabaseService` class defines a standard interface that all database backend implementations must follow:

**Key Methods:**
- `connect()`: Establish database connection
- `is_connected()`: Check connection status
- `create_index()`: Create index/collection/table
- `index_exists()`: Check if index exists
- `create_document()`: Create new document (fail if exists)
- `index_document()`: Create or update document
- `get_document()`: Retrieve document by ID
- `search_documents()`: Search with query and filters
- `update_document()`: Partial document update
- `delete_document()`: Delete document
- `count_documents()`: Count matching documents

### 2. ElasticsearchDatabaseService

Current implementation using Elasticsearch 9.x:

**Features:**
- URL-based connection initialization
- Automatic index creation with mappings
- Proper error handling and graceful degradation
- Support for complex queries and full-text search
- Conflict detection for unique constraints

### 3. Global Service Instance

The `get_database_service()` function provides a singleton database service instance:

```python
from services.database import get_database_service

db = get_database_service()  # Returns configured database service
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

# Create index
mapping = {
    "mappings": {
        "properties": {
            "username": {"type": "keyword"},
            "email": {"type": "keyword"},
            "created_at": {"type": "date"}
        }
    }
}
db.create_index("users", mapping)

# Create document (unique)
user = {
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2025-01-01T00:00:00"
}
success = db.create_document("users", "john_doe", user)

# Index document (create or update)
user["email"] = "john.doe@example.com"
doc_id = db.index_document("users", user, doc_id="john_doe")

# Get document
user_data = db.get_document("users", "john_doe")

# Search documents
query = {"term": {"username": "john_doe"}}
results = db.search_documents("users", query=query, size=10)

# Update document
db.update_document("users", "john_doe", {"email": "newemail@example.com"})

# Delete document
db.delete_document("users", "john_doe")

# Count documents
count = db.count_documents("users", query=query)
```

### Integration with Services

```python
from services.database import get_database_service

class MyService:
    def __init__(self):
        self.db = get_database_service()
        self.index_name = "my_data"
        self._create_index()
    
    def _create_index(self):
        mapping = {...}
        self.db.create_index(self.index_name, mapping)
    
    def add_record(self, data):
        if not self.db.is_connected():
            return False
        
        doc_id = self.db.index_document(self.index_name, data)
        return doc_id is not None
    
    def search_records(self, filters):
        if not self.db.is_connected():
            return []
        
        query = {"bool": {"must": [...]}}
        return self.db.search_documents(self.index_name, query=query)
```

## Switching Database Backends

### Option 1: Implement New Backend

1. Create new backend file (e.g., `mongodb_backend.py`)
2. Implement `DatabaseService` interface
3. Update `service.py` to use new backend

```python
# services/database/mongodb_backend.py
from .service import DatabaseService
from pymongo import MongoClient

class MongoDBDatabaseService(DatabaseService):
    def __init__(self):
        self.client = MongoClient(...)
        
    def connect(self) -> bool:
        # MongoDB connection logic
        pass
    
    def create_document(self, index_name, doc_id, document):
        # MongoDB insert logic
        collection = self.client[index_name]
        collection.insert_one({"_id": doc_id, **document})
        return True
    
    # Implement other methods...
```

2. Update `service.py`:

```python
def get_database_service() -> DatabaseService:
    global _db_service
    if _db_service is None:
        # Switch to MongoDB
        from .mongodb_backend import MongoDBDatabaseService
        _db_service = MongoDBDatabaseService()
    return _db_service
```

### Option 2: Configuration-Based Selection

Add configuration for database type:

```python
# config.py
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "elasticsearch")

# service.py
def get_database_service() -> DatabaseService:
    global _db_service
    if _db_service is None:
        db_type = Config().DATABASE_TYPE
        
        if db_type == "elasticsearch":
            from .elasticsearch_backend import ElasticsearchDatabaseService
            _db_service = ElasticsearchDatabaseService()
        elif db_type == "mongodb":
            from .mongodb_backend import MongoDBDatabaseService
            _db_service = MongoDBDatabaseService()
        elif db_type == "postgresql":
            from .postgresql_backend import PostgreSQLDatabaseService
            _db_service = PostgreSQLDatabaseService()
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    return _db_service
```

## Benefits

### 1. **Abstraction**
- Business logic independent of database implementation
- Clean separation of concerns
- Easier to understand and maintain

### 2. **Flexibility**
- Switch databases without changing application code
- Test with different backends
- Gradual migration strategies

### 3. **Testability**
- Easy to mock database operations
- Unit tests don't require real database
- Consistent testing interface

### 4. **Maintainability**
- Centralized database logic
- Single point of change for database operations
- Clear API contract

### 5. **Scalability**
- Can use different databases for different use cases
- Easy to add caching layers
- Support for read replicas or sharding

## Migration Guide

### From Direct Elasticsearch to Database Service

**Before:**
```python
from elasticsearch import Elasticsearch, NotFoundError

class MyService:
    def __init__(self):
        self.es = Elasticsearch([...])
    
    def get_item(self, item_id):
        try:
            result = self.es.get(index="items", id=item_id)
            return result['_source']
        except NotFoundError:
            return None
```

**After:**
```python
from services.database import get_database_service

class MyService:
    def __init__(self):
        self.db = get_database_service()
    
    def get_item(self, item_id):
        return self.db.get_document("items", item_id)
```

## Best Practices

1. **Always check connection status** before operations
2. **Use create_document()** for unique constraints
3. **Use index_document()** for create-or-update semantics
4. **Handle None returns** from get/search operations
5. **Use appropriate index sizes** for search operations
6. **Leverage filters** for efficient queries
7. **Consider pagination** for large result sets

## Performance Considerations

- **Index creation**: Done once at service initialization
- **Connection pooling**: Handled by backend implementation
- **Query optimization**: Use filters over full queries when possible
- **Caching**: Can be added at service layer
- **Batch operations**: Consider adding bulk operations for large datasets

## Future Enhancements

1. **Transaction support**: Add transactional operations
2. **Bulk operations**: Batch insert/update/delete
3. **Aggregations**: Add aggregation query support
4. **Schema validation**: Validate documents before storage
5. **Migration tools**: Database migration utilities
6. **Performance monitoring**: Built-in metrics and logging
7. **Connection pooling**: Advanced connection management
8. **Backup/restore**: Database backup utilities

## Testing

### Unit Tests with Mocks

```python
from unittest.mock import MagicMock
from services.database import set_database_service

def test_my_service():
    # Create mock database
    mock_db = MagicMock()
    mock_db.is_connected.return_value = True
    mock_db.get_document.return_value = {"id": "1", "name": "test"}
    
    # Inject mock
    set_database_service(mock_db)
    
    # Test service
    service = MyService()
    result = service.get_item("1")
    assert result["name"] == "test"
```

### Integration Tests

```python
def test_with_real_elasticsearch():
    # Use real Elasticsearch for integration tests
    service = MyService()
    
    if not service.db.is_connected():
        pytest.skip("Elasticsearch not available")
    
    # Run integration tests
    ...
```

## Troubleshooting

### Connection Issues

```python
db = get_database_service()
if not db.is_connected():
    print("Database not connected - check:")
    print("1. Database server is running")
    print("2. Connection settings in config")
    print("3. Network connectivity")
    print("4. Credentials are correct")
```

### Query Performance

- Use appropriate indices
- Limit result set sizes
- Use filters instead of queries where possible
- Consider caching frequently accessed data

### Error Handling

All methods handle errors gracefully:
- Return `None` or empty list on error
- Print error messages for debugging
- No exceptions propagated to caller
- Services degrade gracefully when database unavailable

## Conclusion

The Database Service architecture provides a solid foundation for flexible, maintainable data access in the GradeSchoolMathSolver-RAG project. It allows the application to adapt to changing requirements and easily integrate new database technologies as needed.
