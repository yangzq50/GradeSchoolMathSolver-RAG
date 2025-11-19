"""
Tests for database connection retry logic
"""
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_mariadb_connection_retry_success_on_second_attempt():
    """Test MariaDB connection succeeds on second attempt"""
    from services.database.mariadb_backend import MariaDBDatabaseService
    from mysql.connector import Error as MySQLError

    with patch('services.database.mariadb_backend.mysql.connector.connect') as mock_connect:
        # First attempt fails, second succeeds
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.side_effect = [
            MySQLError("Connection refused"),
            mock_connection
        ]

        with patch('services.database.mariadb_backend.time.sleep'):  # Skip actual sleep
            service = MariaDBDatabaseService(max_retries=3, retry_delay=0.1)

        assert service.connection is not None
        assert mock_connect.call_count == 2
        print("✅ MariaDB retry logic: Success on second attempt")


def test_mariadb_connection_retry_exhausted():
    """Test MariaDB connection fails after exhausting retries"""
    from services.database.mariadb_backend import MariaDBDatabaseService
    from mysql.connector import Error as MySQLError

    with patch('services.database.mariadb_backend.mysql.connector.connect') as mock_connect:
        mock_connect.side_effect = MySQLError("Connection refused")

        with patch('services.database.mariadb_backend.time.sleep'):  # Skip actual sleep
            service = MariaDBDatabaseService(max_retries=3, retry_delay=0.1)

        assert service.connection is None
        assert mock_connect.call_count == 3
        print("✅ MariaDB retry logic: Properly exhausts retries")


def test_elasticsearch_connection_retry_success_on_second_attempt():
    """Test Elasticsearch connection succeeds on second attempt"""
    from services.database.elasticsearch_backend import ElasticsearchDatabaseService

    with patch('services.database.elasticsearch_backend.Elasticsearch') as mock_es_class:
        # First attempt fails, second succeeds
        mock_es_fail = Mock()
        mock_es_fail.ping.return_value = False

        mock_es_success = Mock()
        mock_es_success.ping.return_value = True

        mock_es_class.side_effect = [mock_es_fail, mock_es_success]

        with patch('services.database.elasticsearch_backend.time.sleep'):  # Skip actual sleep
            service = ElasticsearchDatabaseService(max_retries=3, retry_delay=0.1)

        assert service.es is not None
        assert mock_es_class.call_count == 2
        print("✅ Elasticsearch retry logic: Success on second attempt")


def test_elasticsearch_connection_retry_exhausted():
    """Test Elasticsearch connection fails after exhausting retries"""
    from services.database.elasticsearch_backend import ElasticsearchDatabaseService
    from elasticsearch import ConnectionError as ESConnectionError

    with patch('services.database.elasticsearch_backend.Elasticsearch') as mock_es_class:
        mock_es_class.side_effect = ESConnectionError("Connection refused")

        with patch('services.database.elasticsearch_backend.time.sleep'):  # Skip actual sleep
            service = ElasticsearchDatabaseService(max_retries=3, retry_delay=0.1)

        assert service.es is None
        assert mock_es_class.call_count == 3
        print("✅ Elasticsearch retry logic: Properly exhausts retries")


def test_exponential_backoff():
    """Test that retry delays follow exponential backoff pattern"""
    from services.database.mariadb_backend import MariaDBDatabaseService
    from mysql.connector import Error as MySQLError

    with patch('services.database.mariadb_backend.mysql.connector.connect') as mock_connect:
        mock_connect.side_effect = MySQLError("Connection refused")

        sleep_times = []
        with patch('services.database.mariadb_backend.time.sleep') as mock_sleep:
            def record_sleep(duration):
                sleep_times.append(duration)
            mock_sleep.side_effect = record_sleep

            # Service creation will fail, but we're just testing the sleep times
            _ = MariaDBDatabaseService(max_retries=4, retry_delay=1.0)

        # Verify exponential backoff: 1.0, 2.0, 4.0 seconds
        assert len(sleep_times) == 3
        assert sleep_times[0] == 1.0  # 1.0 * 2^0
        assert sleep_times[1] == 2.0  # 1.0 * 2^1
        assert sleep_times[2] == 4.0  # 1.0 * 2^2
        print("✅ Exponential backoff: Delays follow correct pattern")


def test_immediate_success_no_retry():
    """Test that no retry happens when connection succeeds immediately"""
    from services.database.mariadb_backend import MariaDBDatabaseService

    with patch('services.database.mariadb_backend.mysql.connector.connect') as mock_connect:
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        with patch('services.database.mariadb_backend.time.sleep') as mock_sleep:
            service = MariaDBDatabaseService(max_retries=3, retry_delay=0.1)

        assert service.connection is not None
        assert mock_connect.call_count == 1
        assert mock_sleep.call_count == 0
        print("✅ No retry on immediate success")


if __name__ == "__main__":
    print("\n🧪 Running Database Connection Retry Tests")
    print("=" * 50)

    tests = [
        test_immediate_success_no_retry,
        test_mariadb_connection_retry_success_on_second_attempt,
        test_mariadb_connection_retry_exhausted,
        test_elasticsearch_connection_retry_success_on_second_attempt,
        test_elasticsearch_connection_retry_exhausted,
        test_exponential_backoff,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")

    sys.exit(0 if failed == 0 else 1)
