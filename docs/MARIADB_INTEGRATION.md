# MariaDB Integration Documentation

## Overview

MariaDB 11.8 LTS is the **default database backend** for the GradeSchoolMathSolver-RAG system. It provides a reliable, ACID-compliant relational database with excellent performance for storing user accounts, answer history, and quiz data.

## Why MariaDB?

MariaDB offers several advantages as the default database backend:

- **Relational Integrity**: ACID-compliant transactions ensure data consistency
- **Mature & Stable**: MariaDB 11.8 is an LTS (Long Term Support) release with proven reliability
- **High Performance**: Optimized for both read and write operations
- **Easy Setup**: Simple Docker deployment with minimal configuration
- **Proper User Isolation**: Each user's history is properly separated with indexed queries
- **JSON Support**: Flexible JSON column type for schema evolution
- **Future-Ready**: Vector search capabilities for enhanced RAG features (planned)

## Architecture

### Database Schema

MariaDB uses a structured schema with proper column types for optimal performance:

#### Users Table

```sql
CREATE TABLE `users` (
    `username` VARCHAR(255) PRIMARY KEY,
    `created_at` TIMESTAMP NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Fields:**
- `username`: Unique identifier for each user (primary key)
- `created_at`: Account creation timestamp

#### Quiz History Table

```sql
CREATE TABLE `quiz_history` (
    `record_id` VARCHAR(255) PRIMARY KEY,
    `username` VARCHAR(255) NOT NULL,
    `question` TEXT NOT NULL,
    `equation` VARCHAR(500) NOT NULL,
    `user_answer` INT,
    `correct_answer` INT NOT NULL,
    `is_correct` BOOLEAN NOT NULL,
    `category` VARCHAR(100) NOT NULL,
    `timestamp` TIMESTAMP NOT NULL,
    `reviewed` BOOLEAN DEFAULT FALSE,
    INDEX idx_username (username),
    INDEX idx_timestamp (timestamp),
    INDEX idx_category (category),
    INDEX idx_reviewed (reviewed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Fields:**
- `record_id`: Unique identifier for each answer record (UUID)
- `username`: User who submitted the answer (indexed for fast lookups)
- `question`: Natural language question text
- `equation`: Mathematical equation
- `user_answer`: User's submitted answer (NULL if skipped)
- `correct_answer`: The correct answer
- `is_correct`: Boolean flag for correctness
- `category`: Question category (addition, subtraction, etc.)
- `timestamp`: When the answer was recorded (indexed)
- `reviewed`: Whether this mistake has been reviewed

**Indexes:**
- Primary key on `record_id` for unique identification
- Index on `username` for fast user-specific queries
- Index on `timestamp` for chronological sorting
- Index on `category` for category-based filtering
- Index on `reviewed` for mistake review feature

### User History Separation

MariaDB ensures proper user history separation through:

1. **Indexed Username Column**: Fast filtering of records by username
2. **Query Translation**: Elasticsearch-style queries are automatically converted to SQL WHERE clauses
3. **Proper WHERE Clauses**: All user-specific queries include `WHERE username = ?`

Example query translation:
```python
# Application code (Elasticsearch-style)
query = {"term": {"username": "john_doe"}}

# MariaDB backend converts to SQL
SELECT * FROM quiz_history WHERE username = 'john_doe'
```

## Configuration

### Environment Variables

Set these in your `.env` file:

```bash
# Database Backend Selection (default: mariadb)
DATABASE_BACKEND=mariadb

# MariaDB Connection Settings
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=math_solver
MARIADB_PASSWORD=math_solver_password
MARIADB_DATABASE=math_solver
```

### Docker Deployment

#### Start MariaDB with Docker Compose

```bash
# Start MariaDB service
docker-compose --profile mariadb up -d mariadb

# Verify MariaDB is running
docker ps | grep mariadb
```

#### Start Full Application with MariaDB

```bash
# Set database backend
export DATABASE_BACKEND=mariadb

# Start all services
docker-compose --profile mariadb up -d

# Check logs
docker logs math-solver-mariadb
```

### Local Development Setup

If running MariaDB locally without Docker:

1. **Install MariaDB 11.8 LTS**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mariadb-server-11.8
   
   # macOS
   brew install mariadb@11.8
   ```

2. **Create Database and User**
   ```sql
   CREATE DATABASE math_solver;
   CREATE USER 'math_solver'@'localhost' IDENTIFIED BY 'math_solver_password';
   GRANT ALL PRIVILEGES ON math_solver.* TO 'math_solver'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Configure Application**
   ```bash
   # .env file
   DATABASE_BACKEND=mariadb
   MARIADB_HOST=localhost
   MARIADB_PORT=3306
   MARIADB_USER=math_solver
   MARIADB_PASSWORD=math_solver_password
   MARIADB_DATABASE=math_solver
   ```

4. **Run Application**
   ```bash
   python -m web_ui.app
   ```

## Usage

### Database Service API

The application uses a unified database service that abstracts MariaDB operations:

```python
from services.database import get_database_service

# Get database service (automatically uses MariaDB based on config)
db = get_database_service()

# Check connection
if db.is_connected():
    print("Connected to MariaDB")

# Create a user
user_data = {
    "username": "john_doe",
    "created_at": "2025-01-15T10:00:00Z"
}
db.create_record("users", "john_doe", user_data)

# Search user's answer history
query = {"term": {"username": "john_doe"}}
results = db.search_records(
    collection_name="quiz_history",
    query=query,
    sort=[{"timestamp": {"order": "desc"}}],
    limit=100
)
```

### Query Translation

The MariaDB backend automatically translates Elasticsearch-style queries:

#### Simple Term Query
```python
# Elasticsearch-style
query = {"term": {"username": "alice"}}

# Translates to SQL
WHERE `username` = 'alice'
```

#### Match Query
```python
# Elasticsearch-style
query = {"match": {"category": "addition"}}

# Translates to SQL
WHERE `category` = 'addition'
```

#### Boolean Query with Multiple Conditions
```python
# Elasticsearch-style
query = {
    "bool": {
        "must": [
            {"term": {"username": "bob"}},
            {"term": {"category": "multiplication"}}
        ]
    }
}

# Translates to SQL
WHERE `username` = 'bob' AND `category` = 'multiplication'
```

## Performance

### Typical Response Times

- **User lookup**: < 10ms
- **Insert answer record**: < 20ms
- **Get user history (100 records)**: < 50ms
- **Count user statistics**: < 30ms
- **Search with filters**: < 40ms

### Optimization Tips

1. **Use Indexes**: The default schema includes indexes on frequently queried columns
2. **Limit Results**: Use appropriate `limit` values to reduce data transfer
3. **Connection Pooling**: MariaDB connector uses connection pooling automatically
4. **Batch Operations**: For bulk imports, consider using batch inserts

### Scaling Recommendations

For production deployments with high traffic:

- **Read Replicas**: Add read-only replicas for query distribution
- **Connection Pooling**: Configure connection pool size based on concurrent users
- **Caching Layer**: Add Redis for frequently accessed data
- **Database Tuning**: Adjust `innodb_buffer_pool_size` and other parameters

## Monitoring

### Health Checks

```bash
# Check if MariaDB is accessible
mysql -h localhost -u math_solver -p -e "SELECT 1"

# Check database size
mysql -h localhost -u math_solver -p -e "
  SELECT 
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
  FROM information_schema.tables
  WHERE table_schema = 'math_solver'
  GROUP BY table_schema;
"

# Check table row counts
mysql -h localhost -u math_solver -p math_solver -e "
  SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
  UNION ALL
  SELECT 'quiz_history', COUNT(*) FROM quiz_history;
"
```

### Performance Monitoring

```sql
-- Show slow queries (if enabled)
SHOW VARIABLES LIKE 'slow_query_log';

-- Check index usage
SHOW INDEX FROM quiz_history;

-- Analyze query performance
EXPLAIN SELECT * FROM quiz_history WHERE username = 'test_user' ORDER BY timestamp DESC LIMIT 100;
```

## Backup and Restore

### Backup Database

```bash
# Backup all data
docker exec math-solver-mariadb mysqldump \
  -u math_solver -pmath_solver_password \
  math_solver > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup structure only
docker exec math-solver-mariadb mysqldump \
  -u math_solver -pmath_solver_password \
  --no-data math_solver > schema.sql
```

### Restore Database

```bash
# Restore from backup
docker exec -i math-solver-mariadb mysql \
  -u math_solver -pmath_solver_password \
  math_solver < backup_20250115_120000.sql
```

## Migration from Elasticsearch

If you're migrating from Elasticsearch to MariaDB:

1. **Export data from Elasticsearch**
   ```python
   from services.database.elasticsearch_backend import ElasticsearchDatabaseService
   
   es_db = ElasticsearchDatabaseService()
   users = es_db.search_records("users", limit=10000)
   history = es_db.search_records("quiz_history", limit=100000)
   ```

2. **Change database backend**
   ```bash
   # Update .env
   DATABASE_BACKEND=mariadb
   ```

3. **Import data to MariaDB**
   ```python
   from services.database.mariadb_backend import MariaDBDatabaseService
   
   mariadb = MariaDBDatabaseService()
   
   # Import users
   for user in users:
       mariadb.create_record("users", user['_id'], user['_source'])
   
   # Import history
   for record in history:
       mariadb.insert_record("quiz_history", record['_source'])
   ```

## Troubleshooting

### Connection Refused

**Problem**: Cannot connect to MariaDB

**Solutions**:
```bash
# Check if MariaDB is running
docker ps | grep mariadb

# Check MariaDB logs
docker logs math-solver-mariadb

# Verify port is accessible
nc -zv localhost 3306

# Restart MariaDB
docker-compose restart mariadb
```

### Authentication Errors

**Problem**: Access denied for user

**Solutions**:
```bash
# Verify credentials in .env file
cat .env | grep MARIADB

# Reset user password
docker exec -it math-solver-mariadb mysql -u root -p
# Then in MySQL prompt:
ALTER USER 'math_solver'@'%' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
```

### Slow Queries

**Problem**: Queries taking too long

**Solutions**:
```sql
-- Check if indexes exist
SHOW INDEX FROM quiz_history;

-- Add missing indexes if needed
CREATE INDEX idx_username_timestamp ON quiz_history(username, timestamp);

-- Analyze table for optimization
ANALYZE TABLE quiz_history;

-- Check query execution plan
EXPLAIN SELECT * FROM quiz_history WHERE username = 'test' ORDER BY timestamp DESC;
```

### Database Size Growing Too Large

**Problem**: Database taking up too much space

**Solutions**:
```sql
-- Archive old records (older than 1 year)
CREATE TABLE quiz_history_archive LIKE quiz_history;
INSERT INTO quiz_history_archive 
  SELECT * FROM quiz_history 
  WHERE timestamp < DATE_SUB(NOW(), INTERVAL 1 YEAR);

DELETE FROM quiz_history 
  WHERE timestamp < DATE_SUB(NOW(), INTERVAL 1 YEAR);

-- Optimize table to reclaim space
OPTIMIZE TABLE quiz_history;
```

## Advantages Over Elasticsearch

While Elasticsearch is excellent for full-text search, MariaDB offers benefits for this application:

| Feature | MariaDB | Elasticsearch |
|---------|---------|---------------|
| **Setup Complexity** | Simple | Moderate |
| **Memory Usage** | Low (512MB) | High (2GB+) |
| **ACID Compliance** | Yes | No |
| **Transaction Support** | Yes | Limited |
| **Data Integrity** | Strong | Eventual consistency |
| **Query Speed** | Very Fast | Fast |
| **Full-Text Search** | Basic | Advanced |
| **Aggregations** | SQL-based | Advanced |
| **User Isolation** | Native (indexed) | Query-based |
| **Backup/Restore** | Standard tools | Complex |

## Future Enhancements

MariaDB 11.8 supports features we may use in the future:

- **Vector Search**: For semantic similarity in RAG (Retrieval-Augmented Generation)
- **Window Functions**: For advanced analytics
- **JSON Functions**: For flexible schema evolution
- **Replication**: For high availability
- **Partitioning**: For large-scale data management

## Additional Resources

- [MariaDB 11.8 Documentation](https://mariadb.com/kb/en/what-is-mariadb-118/)
- [MariaDB Best Practices](https://mariadb.com/kb/en/optimization-and-tuning/)
- [Database Service Architecture](./DATABASE_SERVICE.md)
- [Project Overview](./PROJECT_OVERVIEW.txt)

## Summary

MariaDB 11.8 LTS provides a robust, reliable, and efficient database backend for the GradeSchoolMathSolver-RAG system. Its proper indexing ensures excellent performance for user-specific queries, and the structured schema guarantees data integrity. The automatic query translation layer allows the application to use Elasticsearch-style queries while benefiting from MariaDB's relational capabilities.
