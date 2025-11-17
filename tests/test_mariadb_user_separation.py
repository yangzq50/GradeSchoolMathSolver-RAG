"""
Test MariaDB user history separation and query parsing

This test validates that MariaDB correctly parses Elasticsearch-style queries
to ensure proper user isolation when filtering records.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_mariadb_query_parsing():
    """Test that MariaDB backend correctly parses Elasticsearch-style queries"""
    from services.database.mariadb_backend import MariaDBDatabaseService
    from unittest.mock import Mock, MagicMock, patch
    import mysql.connector
    
    # Create a mock MariaDB service
    db = MariaDBDatabaseService()
    
    # Mock the connection
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    mock_connection.is_connected.return_value = True
    db.connection = mock_connection
    
    # Test data
    test_user = "test_user_123"
    
    # Mock describe table to return column-based storage
    mock_cursor.fetchall.side_effect = [
        # First call: DESCRIBE query
        [('record_id', 'VARCHAR(255)', 'NO', 'PRI', None, ''),
         ('username', 'VARCHAR(255)', 'NO', '', None, ''),
         ('question', 'TEXT', 'NO', '', None, '')],
        # Second call: SELECT query results
        []
    ]
    mock_cursor.description = [
        ('record_id',), ('username',), ('question',)
    ]
    
    print("\n=== Testing MariaDB Query Parsing ===\n")
    
    # Test 1: Simple term query (Elasticsearch-style)
    print("Test 1: Parsing {'term': {'username': 'user'}} query...")
    query1 = {"term": {"username": test_user}}
    
    # Reset mock
    mock_cursor.reset_mock()
    mock_cursor.fetchall.side_effect = [
        # DESCRIBE query
        [('record_id', 'VARCHAR(255)', 'NO', 'PRI', None, ''),
         ('username', 'VARCHAR(255)', 'NO', '', None, '')],
        # SELECT query results
        []
    ]
    mock_cursor.description = [('record_id',), ('username',)]
    
    results = db.search_records(
        collection_name="quiz_history",
        query=query1,
        limit=10
    )
    
    # Verify the SQL query was called with proper WHERE clause
    calls = mock_cursor.execute.call_args_list
    sql_query = calls[-1][0][0]  # Get the SQL query from the last execute call
    params = calls[-1][0][1]      # Get the parameters
    
    assert "WHERE" in sql_query, "Query should include WHERE clause"
    assert "`username` = %s" in sql_query, "Query should filter by username"
    assert test_user in params, "Parameters should include the username"
    print("✅ Term query correctly parsed into SQL WHERE clause")
    
    # Test 2: Match query
    print("\nTest 2: Parsing {'match': {'username': 'user'}} query...")
    query2 = {"match": {"username": test_user}}
    
    # Reset mock
    mock_cursor.reset_mock()
    mock_cursor.fetchall.side_effect = [
        [('record_id', 'VARCHAR(255)', 'NO', 'PRI', None, ''),
         ('username', 'VARCHAR(255)', 'NO', '', None, '')],
        []
    ]
    mock_cursor.description = [('record_id',), ('username',)]
    
    results = db.search_records(
        collection_name="quiz_history",
        query=query2,
        limit=10
    )
    
    calls = mock_cursor.execute.call_args_list
    sql_query = calls[-1][0][0]
    params = calls[-1][0][1]
    
    assert "WHERE" in sql_query, "Match query should include WHERE clause"
    assert "`username` = %s" in sql_query, "Match query should filter by username"
    assert test_user in params, "Parameters should include the username"
    print("✅ Match query correctly parsed into SQL WHERE clause")
    
    # Test 3: Bool query with must clause
    print("\nTest 3: Parsing bool query with must clauses...")
    query3 = {
        "bool": {
            "must": [
                {"term": {"username": test_user}},
                {"term": {"category": "addition"}}
            ]
        }
    }
    
    # Reset mock
    mock_cursor.reset_mock()
    mock_cursor.fetchall.side_effect = [
        [('record_id', 'VARCHAR(255)', 'NO', 'PRI', None, ''),
         ('username', 'VARCHAR(255)', 'NO', '', None, ''),
         ('category', 'VARCHAR(100)', 'NO', '', None, '')],
        []
    ]
    mock_cursor.description = [('record_id',), ('username',), ('category',)]
    
    results = db.search_records(
        collection_name="quiz_history",
        query=query3,
        limit=10
    )
    
    calls = mock_cursor.execute.call_args_list
    sql_query = calls[-1][0][0]
    params = calls[-1][0][1]
    
    assert "WHERE" in sql_query, "Bool query should include WHERE clause"
    assert "`username` = %s" in sql_query, "Bool query should filter by username"
    assert "`category` = %s" in sql_query, "Bool query should filter by category"
    assert test_user in params, "Parameters should include the username"
    assert "addition" in params, "Parameters should include the category"
    assert "AND" in sql_query, "Bool query should use AND for multiple conditions"
    print("✅ Bool query with must clauses correctly parsed into SQL WHERE clause with AND")
    
    # Test 4: Count records with term query
    print("\nTest 4: Testing count_records with term query...")
    query4 = {"term": {"username": test_user}}
    
    # Reset mock
    mock_cursor.reset_mock()
    mock_cursor.fetchall.side_effect = [
        [('username', 'VARCHAR(255)', 'NO', '', None, '')]  # DESCRIBE
    ]
    mock_cursor.fetchone.return_value = (5,)  # COUNT result
    
    count = db.count_records(
        collection_name="quiz_history",
        query=query4
    )
    
    calls = mock_cursor.execute.call_args_list
    sql_query = calls[-1][0][0]
    params = calls[-1][0][1]
    
    assert "COUNT(*)" in sql_query, "Count query should use COUNT(*)"
    assert "WHERE" in sql_query, "Count query should include WHERE clause"
    assert "`username` = %s" in sql_query, "Count query should filter by username"
    assert test_user in params, "Parameters should include the username"
    print("✅ Count query correctly parsed with WHERE clause")
    
    print("\n=== All MariaDB Query Parsing Tests Passed ===\n")
    print("✅ User history separation is properly implemented")
    print("✅ Elasticsearch-style queries are correctly translated to SQL")
    print("✅ Multiple users' data will be properly isolated")


def test_user_isolation_scenario():
    """Test a realistic scenario of multiple users with separate histories"""
    from services.database.mariadb_backend import MariaDBDatabaseService
    from unittest.mock import MagicMock
    
    db = MariaDBDatabaseService()
    
    # Mock connection
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    mock_connection.is_connected.return_value = True
    db.connection = mock_connection
    
    print("\n=== Testing User Isolation Scenario ===\n")
    
    # Simulate two users with different answer histories
    users = ["alice", "bob"]
    
    for user in users:
        print(f"Simulating query for user: {user}")
        
        # Reset mock
        mock_cursor.reset_mock()
        mock_cursor.fetchall.side_effect = [
            # DESCRIBE table
            [('record_id', 'VARCHAR(255)', 'NO', 'PRI', None, ''),
             ('username', 'VARCHAR(255)', 'NO', '', None, ''),
             ('question', 'TEXT', 'NO', '', None, '')],
            # SELECT results (would be filtered by username in real DB)
            []
        ]
        mock_cursor.description = [('record_id',), ('username',), ('question',)]
        
        # Query for user's history
        query = {"term": {"username": user}}
        results = db.search_records(
            collection_name="quiz_history",
            query=query,
            limit=100
        )
        
        # Verify the query was properly constructed
        calls = mock_cursor.execute.call_args_list
        sql_query = calls[-1][0][0]
        params = calls[-1][0][1]
        
        # Check that username filter is present
        assert "`username` = %s" in sql_query, f"Query for {user} should filter by username"
        assert user in params, f"Query parameters should include {user}"
        
        print(f"✅ Query for {user} correctly includes WHERE username = '{user}'")
    
    print("\n=== User Isolation Test Passed ===")
    print("✅ Each user's query is properly filtered by their username")
    print("✅ Users' histories will not mix in MariaDB")


if __name__ == "__main__":
    print("Running MariaDB User History Separation Tests...\n")
    
    try:
        test_mariadb_query_parsing()
        test_user_isolation_scenario()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED! ✅")
        print("="*60)
        print("\nMariaDB user history separation is working correctly.")
        print("Different users' data will be properly isolated.")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
