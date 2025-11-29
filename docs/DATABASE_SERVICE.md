# Database Service

The Database Service provides a unified abstraction layer for all database operations, allowing the application to switch between MariaDB (default) and Elasticsearch without modifying business logic.

## Configuration

### Backend Selection

Set the database backend in `.env`:

```bash
# Use MariaDB (default, recommended)
DATABASE_BACKEND=mariadb

# Or use Elasticsearch (for advanced RAG features)
DATABASE_BACKEND=elasticsearch
```

### MariaDB Configuration (Default)

```bash
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=math_solver
MARIADB_PASSWORD=math_solver_password
MARIADB_DATABASE=math_solver
```

### Elasticsearch Configuration

```bash
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=quiz_history
```

## Quick Start

```bash
# Start MariaDB with Docker
docker-compose up -d mariadb

# Start web application
docker-compose up -d
```

For Elasticsearch:
```bash
DATABASE_BACKEND=elasticsearch docker-compose up -d elasticsearch
docker-compose up -d
```

## Backend Comparison

| Feature | MariaDB (Default) | Elasticsearch |
|---------|-------------------|---------------|
| Best for | User management, statistics, ACID compliance | Full-text search, RAG, analytics |
| Resource usage | Lower | Higher (8GB+ RAM) |
| Setup | Simpler | More complex |
| Vector search | Supported | Native support |

## Basic Usage

```python
from gradeschoolmathsolver.services.database import get_database_service

db = get_database_service()

# Create a record
db.create_record("users", "john_doe", {"username": "john_doe", "created_at": "2025-01-15T10:00:00Z"})

# Get a record
user = db.get_record("users", "john_doe")

# Search records
results = db.search_records("users", filters={"username": "john_doe"}, limit=10)

# Update a record
db.update_record("users", "john_doe", {"last_login": "2025-01-16T09:00:00Z"})

# Delete a record
db.delete_record("users", "john_doe")
```

## Data Models

Schemas are defined in `services/database/schemas.py`. Key tables:

- **users**: User accounts (username, created_at)
- **quiz_history**: Answer history with question, equation, answers, category, timestamp

## Troubleshooting

### Connection Issues
- Check if database is running: `docker ps`
- Verify `.env` configuration
- Review logs: `docker logs math-solver-mariadb`

### Performance Issues
- Add indexes for frequently queried columns
- Use pagination for large result sets
- Consider MariaDB for transactional workloads, Elasticsearch for search-heavy workloads

## Additional Resources

- [Elasticsearch 9.x Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/9.0/index.html)
- [MariaDB 11.8 Documentation](https://mariadb.com/kb/en/what-is-mariadb-118/)
