"""
Tests for database connection status page feature
"""
import sys
import os
import threading
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_get_connection_status_not_started() -> None:
    """Test get_connection_status returns 'not_started' initially"""
    from gradeschoolmathsolver.services.database import service

    # Reset globals
    service._db_service = None
    service._connection_status = "not_started"
    service._connection_thread = None

    status = service.get_connection_status()
    assert status == "not_started"
    print("✅ get_connection_status returns 'not_started' initially")


def test_get_connection_status_connecting() -> None:
    """Test get_connection_status returns 'connecting' when in progress"""
    from gradeschoolmathsolver.services.database import service

    # Reset globals
    service._db_service = None
    service._connection_status = "connecting"
    service._connection_thread = None

    status = service.get_connection_status()
    assert status == "connecting"
    print("✅ get_connection_status returns 'connecting' when set")


def test_get_connection_status_updates_when_connected() -> None:
    """Test get_connection_status updates to 'connected' when db is ready"""
    from gradeschoolmathsolver.services.database import service

    # Create a mock db_service that reports connected
    mock_service = Mock()
    mock_service.is_connected.return_value = True

    # Set globals to simulate "connecting" state with connected service
    service._db_service = mock_service
    service._connection_status = "connecting"
    service._connection_thread = None

    status = service.get_connection_status()
    assert status == "connected"
    print("✅ get_connection_status updates to 'connected' when db is ready")


def test_is_database_ready_returns_false_when_not_connected() -> None:
    """Test is_database_ready returns False when db service is not connected"""
    from gradeschoolmathsolver.services.database import service

    # Reset globals
    service._db_service = None
    service._connection_status = "not_started"
    service._connection_thread = None

    assert service.is_database_ready() is False
    print("✅ is_database_ready returns False when db_service is None")


def test_is_database_ready_returns_true_when_connected() -> None:
    """Test is_database_ready returns True when db service is connected"""
    from gradeschoolmathsolver.services.database import service

    # Create a mock db_service that reports connected
    mock_service = Mock()
    mock_service.is_connected.return_value = True

    # Set globals
    service._db_service = mock_service
    service._connection_status = "connected"
    service._connection_thread = None

    assert service.is_database_ready() is True
    print("✅ is_database_ready returns True when db is connected")


def test_set_database_service_updates_status() -> None:
    """Test set_database_service updates connection status"""
    from gradeschoolmathsolver.services.database import service

    # Create a mock db_service that reports connected
    mock_service = Mock()
    mock_service.is_connected.return_value = True

    # Reset status
    service._connection_status = "not_started"

    service.set_database_service(mock_service)

    assert service._connection_status == "connected"
    assert service._db_service == mock_service
    print("✅ set_database_service updates connection status")


def test_non_blocking_get_database_service() -> None:
    """Test non-blocking get_database_service sets connecting status"""
    from gradeschoolmathsolver.services.database import service

    # Reset globals
    service._db_service = None
    service._connection_status = "not_started"
    service._connection_thread = None

    # We need to test that the non-blocking mode:
    # 1. Sets status to "connecting"
    # 2. Starts a background thread
    # 3. Returns a placeholder service

    # Use an event to block the background thread until we've verified status
    connection_blocker = threading.Event()

    def blocking_connect_side_effect(*args: object, **kwargs: object) -> None:
        # Wait for the test to signal it's done checking status
        connection_blocker.wait(timeout=5)
        raise ConnectionRefusedError("Connection refused")

    # Patch the MariaDB connection to block until we've verified status
    with patch('gradeschoolmathsolver.services.database.mariadb_backend.mysql.connector.connect') as mock_connect:
        mock_connect.side_effect = blocking_connect_side_effect

        # Also patch time.sleep to speed up the test after we unblock
        with patch('gradeschoolmathsolver.services.database.mariadb_backend.time.sleep'):
            # Call with blocking=False
            result = service.get_database_service(blocking=False)

            # Should return immediately with a placeholder
            assert result is not None
            assert service._connection_status == "connecting"
            assert service._connection_thread is not None
            # The thread should have been started
            assert isinstance(service._connection_thread, threading.Thread)

            # Now allow the background thread to proceed
            connection_blocker.set()

            print("✅ Non-blocking get_database_service sets connecting status")


def test_api_db_status_endpoint() -> None:
    """Test /api/db/status endpoint returns correct status"""
    from gradeschoolmathsolver.services.database import service

    # Reset globals for clean state
    service._db_service = None
    service._connection_status = "connecting"
    service._connection_thread = None

    # Import app after resetting service state
    from gradeschoolmathsolver.web_ui.app import app

    with app.test_client() as client:
        response = client.get('/api/db/status')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert 'ready' in data
        print("✅ /api/db/status endpoint returns correct format")


def test_db_status_page_redirects_when_connected() -> None:
    """Test /db-status page redirects when database is connected"""
    from gradeschoolmathsolver.services.database import service

    # Create a mock db_service that reports connected
    mock_service = Mock()
    mock_service.is_connected.return_value = True
    service._db_service = mock_service
    service._connection_status = "connected"

    from gradeschoolmathsolver.web_ui.app import app

    with app.test_client() as client:
        response = client.get('/db-status', follow_redirects=False)
        # Should redirect to home
        assert response.status_code == 302
        assert response.location == '/'
        print("✅ /db-status redirects to home when connected")


def test_home_shows_db_status_when_not_connected() -> None:
    """Test home page shows db status when database is not connected"""
    from gradeschoolmathsolver.services.database import service

    # Reset globals
    service._db_service = None
    service._connection_status = "connecting"
    service._connection_thread = None

    from gradeschoolmathsolver.web_ui.app import app

    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        # Should show db status page content
        assert b'Connecting to database' in response.data
        print("✅ Home page shows db status when not connected")


if __name__ == "__main__":
    print("\n🧪 Running Database Connection Status Tests")
    print("=" * 50)

    tests = [
        test_get_connection_status_not_started,
        test_get_connection_status_connecting,
        test_get_connection_status_updates_when_connected,
        test_is_database_ready_returns_false_when_not_connected,
        test_is_database_ready_returns_true_when_connected,
        test_set_database_service_updates_status,
        test_non_blocking_get_database_service,
        test_api_db_status_endpoint,
        test_db_status_page_redirects_when_connected,
        test_home_shows_db_status_when_not_connected,
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
