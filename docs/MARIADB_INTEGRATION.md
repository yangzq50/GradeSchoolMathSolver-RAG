# MariaDB Integration Documentation

## Overview

MariaDB 11.8 LTS is the **default database backend** for the GradeSchoolMathSolver system. This document explains how MariaDB is integrated, configured, and used throughout the application.

## Why MariaDB?

MariaDB was chosen as the default database for several reasons:

- **Mature and Stable**: MariaDB 11.8 LTS provides long-term support and proven reliability
- **ACID Compliance**: Full transactional support ensures data integrity
- **Relational Structure**: Proper relational tables with typed columns for better performance
- **JSON Support**: Native JSON column type for flexible data storage when needed
- **Vector Search Ready**: MariaDB 11.8+ supports vector search for future RAG enhancements
- **Easy Setup**: Simple installation and configuration compared to Elasticsearch
- **Lower Resource Usage**: Less memory and disk space required

## Architecture

### Database Schema

MariaDB uses a well-structured relational schema with proper column types based on the unified schema definitions in `services/database/schemas.py`.

#### Users Table

**Table**: `users`

```sql
CREATE TABLE `users` (
    `username` VARCHAR(255) PRIMARY KEY,
    `created_at` TIMESTAMP NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

**Columns**:
- `username`: User identifier (primary key)
- `created_at`: ISO timestamp of account creation

**Example Row**:
```
username: "john_doe"
created_at: "2025-11-17T10:00:00.000000"
```

#### Quiz History Table (Answer History)

**Table**: `quiz_history` (configurable via `ELASTICSEARCH_INDEX` for compatibility)

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
    `question_embedding` BLOB,
    `equation_embedding` BLOB,
    INDEX idx_username (username),
    INDEX idx_timestamp (timestamp),
    INDEX idx_category (category),
    INDEX idx_reviewed (reviewed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

**Columns**:
- `record_id`: Unique record identifier (UUID, primary key)
- `username`: User identifier (indexed for fast filtering)
- `question`: Natural language question text
- `equation`: Mathematical equation (e.g., "5 + 3")
- `user_answer`: User's submitted answer (NULL if not answered)
- `correct_answer`: The correct answer
- `is_correct`: Boolean flag indicating correctness
- `category`: Question category (addition, subtraction, etc.)
- `timestamp`: When the answer was recorded
- `reviewed`: Whether this mistake has been reviewed
- `question_embedding`: Vector embedding of the question text (BLOB, for RAG features)
- `equation_embedding`: Vector embedding of the equation (BLOB, for RAG features)

**Indexes**:
- `idx_username`: Fast filtering by user
- `idx_timestamp`: Efficient sorting by time
- `idx_category`: Category-based queries
- `idx_reviewed`: Quick lookup of unreviewed mistakes

**Example Row**:
```
record_id: "550e8400-e29b-41d4-a716-446655440000"
username: "john_doe"
question: "What is 5 + 3?"
equation: "5 + 3"
user_answer: 8
correct_answer: 8
is_correct: TRUE
category: "addition"
timestamp: "2025-11-17T10:15:30.000000"
reviewed: FALSE
question_embedding: <binary vector data>
equation_embedding: <binary vector data>
```

## Configuration

### Environment Variables

Set the following in your `.env` file:

```bash
# Database Backend Selection
DATABASE_BACKEND=mariadb

# MariaDB Configuration
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=math_solver
MARIADB_PASSWORD=math_solver_password
MARIADB_DATABASE=math_solver

# Quiz history table name (for compatibility)
ELASTICSEARCH_INDEX=quiz_history

# Embedding Storage Configuration (for RAG features)
EMBEDDING_COLUMN_COUNT=2
EMBEDDING_DIMENSIONS=768
```

### Embedding Storage Configuration

The schema supports configurable embedding columns for RAG (Retrieval-Augmented Generation) features. Configuration options:

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_COLUMN_COUNT` | 2 | Number of embedding columns per record |
| `EMBEDDING_DIMENSIONS` | 768 | Dimension(s) for embedding vectors (comma-separated for different dimensions per column) |

**Default Embedding Columns**:
- `question_embedding`: Vector embedding of the question text
- `equation_embedding`: Vector embedding of the mathematical equation

**Multiple Dimensions**: If you need different dimensions for each column, use comma-separated values:
```bash
EMBEDDING_DIMENSIONS=768,512
```

### Database Setup

#### Option 1: Using Docker Compose (Recommended)

The easiest way to get started with MariaDB:

```bash
# Start MariaDB with docker-compose
docker-compose up -d mariadb

# Verify MariaDB is running
docker ps | grep mariadb

# Check logs
docker logs math-solver-mariadb
```

The Docker Compose configuration automatically:
- Creates the `math_solver` database
- Sets up user credentials
- Persists data in `./data/mariadb`
- Exposes port 3306 for local access

#### Option 2: Local MariaDB Installation

1. **Install MariaDB 11.8+**:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install mariadb-server
   
   # macOS
   brew install mariadb
   
   # Start service
   sudo systemctl start mariadb  # Linux
   brew services start mariadb   # macOS
   ```

2. **Secure Installation**:
   ```bash
   sudo mysql_secure_installation
   ```

3. **Create Database and User**:
   ```sql
   CREATE DATABASE math_solver CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'math_solver'@'localhost' IDENTIFIED BY 'math_solver_password';
   GRANT ALL PRIVILEGES ON math_solver.* TO 'math_solver'@'localhost';
   FLUSH PRIVILEGES;
   ```

4. **Update .env**:
   ```bash
   DATABASE_BACKEND=mariadb
   MARIADB_HOST=localhost
   MARIADB_PORT=3306
   MARIADB_USER=math_solver
   MARIADB_PASSWORD=math_solver_password
   MARIADB_DATABASE=math_solver
   ```

## Usage

### Automatic Schema Creation

The application automatically creates tables when started:

```python
from services.account import AccountService

# Tables are created automatically on first use
account_service = AccountService()
```

The `AccountService` uses the centralized schema definitions from `services/database/schemas.py` to create tables with proper column types.

### CRUD Operations

#### Create a User

```python
from services.account import AccountService

account_service = AccountService()
success = account_service.create_user("john_doe")
```

**SQL Executed**:
```sql
INSERT INTO users (username, created_at) 
VALUES ('john_doe', '2025-11-17T10:00:00.000000');
```

#### Record an Answer

```python
account_service.record_answer(
    username="john_doe",
    question="What is 5 + 3?",
    equation="5 + 3",
    user_answer=8,
    correct_answer=8,
    category="addition"
)
```

**SQL Executed**:
```sql
REPLACE INTO quiz_history 
(record_id, username, question, equation, user_answer, correct_answer, is_correct, category, timestamp, reviewed)
VALUES 
('uuid-here', 'john_doe', 'What is 5 + 3?', '5 + 3', 8, 8, TRUE, 'addition', '2025-11-17T10:15:30.000000', FALSE);
```

#### Get User Statistics

```python
stats = account_service.get_user_stats("john_doe")
print(f"Total: {stats.total_questions}")
print(f"Correct: {stats.correct_answers}")
print(f"Overall: {stats.overall_correctness}%")
print(f"Recent 100: {stats.recent_100_score}%")
```

**SQL Executed**:
```sql
SELECT * FROM quiz_history 
WHERE username = 'john_doe'
ORDER BY timestamp DESC
LIMIT 10000;
```

#### Get Answer History

```python
history = account_service.get_answer_history("john_doe", limit=50)
for answer in history:
    print(f"{answer['question']}: {answer['is_correct']}")
```

**SQL Executed**:
```sql
SELECT * FROM quiz_history 
WHERE username = 'john_doe'
ORDER BY timestamp DESC
LIMIT 50;
```

### User History Separation

**Important**: With MariaDB, each user's history is properly isolated using indexed `username` filters. This ensures:

- Fast queries filtered by username
- No mixing of user data
- Efficient statistics calculation per user
- Proper isolation for mistake review

The fix ensures that all queries use proper filtering:
```python
# Correct approach (works with both Elasticsearch and MariaDB)
filters = {"username": username}
results = db.search_records(
    collection_name="quiz_history",
    filters=filters,
    sort=[{"timestamp": {"order": "desc"}}],
    limit=100
)
```

## Performance Optimization

### Indexes

The schema includes strategic indexes for common queries:

```sql
INDEX idx_username (username)      -- User filtering
INDEX idx_timestamp (timestamp)    -- Time-based sorting
INDEX idx_category (category)      -- Category filtering
INDEX idx_reviewed (reviewed)      -- Mistake review queries
```

### Query Optimization Tips

1. **Always use indexed columns** in WHERE clauses
2. **Limit result sets** appropriately (default: 100, max: 1000)
3. **Use prepared statements** (handled automatically by mysql-connector-python)
4. **Leverage covering indexes** for frequently accessed data

### Typical Query Performance

- User creation: < 10ms
- Answer recording: < 20ms
- Get user stats: 50-200ms (depends on history size)
- Get answer history (50 records): 10-50ms
- Mistake review query: 10-30ms

## Backup and Maintenance

### Backup Database

```bash
# Full database backup
mysqldump -u math_solver -p math_solver > backup.sql

# Backup with docker
docker exec math-solver-mariadb mysqldump -u math_solver -p'math_solver_password' math_solver > backup.sql
```

### Restore Database

```bash
# Restore from backup
mysql -u math_solver -p math_solver < backup.sql

# Restore with docker
docker exec -i math-solver-mariadb mysql -u math_solver -p'math_solver_password' math_solver < backup.sql
```

### Database Maintenance

```sql
-- Check table status
SHOW TABLE STATUS FROM math_solver;

-- Optimize tables
OPTIMIZE TABLE users, quiz_history;

-- Check table sizes
SELECT 
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'math_solver'
ORDER BY (data_length + index_length) DESC;
```

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to MariaDB

**Solutions**:
1. Check if MariaDB is running:
   ```bash
   docker ps | grep mariadb
   # or
   sudo systemctl status mariadb
   ```

2. Verify credentials in `.env`:
   ```bash
   DATABASE_BACKEND=mariadb
   MARIADB_HOST=localhost
   MARIADB_PORT=3306
   MARIADB_USER=math_solver
   MARIADB_PASSWORD=math_solver_password
   MARIADB_DATABASE=math_solver
   ```

3. Test connection:
   ```bash
   mysql -h localhost -P 3306 -u math_solver -p
   ```

4. Check firewall settings (ensure port 3306 is accessible)

### Table Creation Errors

**Problem**: Tables not created automatically

**Solution**: Check database permissions:
```sql
SHOW GRANTS FOR 'math_solver'@'localhost';
-- Should include: GRANT ALL PRIVILEGES ON math_solver.*
```

### Performance Issues

**Problem**: Slow queries

**Solutions**:
1. Check if indexes exist:
   ```sql
   SHOW INDEX FROM quiz_history;
   ```

2. Analyze slow queries:
   ```sql
   SET GLOBAL slow_query_log = 'ON';
   SET GLOBAL long_query_time = 1;
   ```

3. Use EXPLAIN to analyze query plans:
   ```sql
   EXPLAIN SELECT * FROM quiz_history WHERE username = 'john_doe';
   ```

### Character Encoding Issues

**Problem**: Special characters not displaying correctly

**Solution**: Ensure UTF-8 encoding:
```sql
ALTER DATABASE math_solver CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE quiz_history CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## Migration from Elasticsearch

If you're migrating from Elasticsearch to MariaDB:

### Export Data from Elasticsearch

```python
from services.database.elasticsearch_backend import ElasticsearchDatabaseService

es_db = ElasticsearchDatabaseService()

# Export users
users = es_db.search_records("users", limit=10000)

# Export quiz history
history = es_db.search_records("quiz_history", limit=100000)
```

### Import into MariaDB

```python
from services.database.mariadb_backend import MariaDBDatabaseService
from services.database.schemas import UserRecord, AnswerHistoryRecord

mariadb = MariaDBDatabaseService()

# Import users
for user_doc in users:
    user_data = user_doc['_source']
    mariadb.create_record("users", user_data['username'], user_data)

# Import quiz history
for history_doc in history:
    history_data = history_doc['_source']
    record_id = history_doc['_id']
    mariadb.insert_record("quiz_history", history_data, record_id)
```

### Update Configuration

```bash
# Change from
DATABASE_BACKEND=elasticsearch

# To
DATABASE_BACKEND=mariadb
```

## Best Practices

1. **Use Connection Pooling**: The MariaDB backend uses autocommit mode for better performance

2. **Index Strategy**: The default indexes cover most use cases, but add custom indexes for specific query patterns

3. **Backup Regularly**: Set up automated backups using cron or systemd timers

4. **Monitor Performance**: Use MariaDB's performance schema and slow query log

5. **Security**:
   - Use strong passwords
   - Limit user privileges to only necessary operations
   - Use SSL/TLS for remote connections
   - Keep MariaDB updated to latest LTS version

6. **Scaling**:
   - For high traffic, consider read replicas
   - Use connection pooling for multiple application instances
   - Consider partitioning large tables by date

## Additional Resources

- [MariaDB 11.8 Documentation](https://mariadb.com/kb/en/what-is-mariadb-118/)
- [MySQL Connector/Python Documentation](https://dev.mysql.com/doc/connector-python/en/)
- [Database Service Source Code](../services/database/)
- [Schema Definitions](../services/database/schemas.py)
