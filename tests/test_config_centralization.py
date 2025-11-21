"""
Tests for config centralization - ensuring all env vars are accessed through config.py
"""
import sys
import os
from unittest.mock import patch
import importlib

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_config_default_values():
    """Test that Config class has sensible defaults"""
    from gradeschoolmathsolver.config import Config
    
    config = Config()
    
    # AI Model defaults
    assert config.AI_MODEL_URL == 'http://localhost:12434'
    assert config.AI_MODEL_NAME == 'ai/llama3.2:1B-Q4_0'
    assert config.LLM_ENGINE == 'llama.cpp'
    
    # Database backend defaults
    assert config.DATABASE_BACKEND == 'mariadb'
    
    # Database retry defaults
    # Check if running in CI environment (which sets DB_MAX_RETRIES=2)
    if os.getenv('DB_MAX_RETRIES'):
        # CI environment - use CI values
        assert config.DB_MAX_RETRIES == int(os.getenv('DB_MAX_RETRIES', '2'))
        assert config.DB_RETRY_DELAY == float(os.getenv('DB_RETRY_DELAY', '0.5'))
    else:
        # Normal environment - use production defaults
        assert config.DB_MAX_RETRIES == 12
        assert config.DB_RETRY_DELAY == 5.0
    
    # MariaDB defaults
    assert config.MARIADB_HOST == 'localhost'
    assert config.MARIADB_PORT == 3306
    assert config.MARIADB_USER == 'math_solver'
    assert config.MARIADB_PASSWORD == 'math_solver_password'
    assert config.MARIADB_DATABASE == 'math_solver'
    
    # Elasticsearch defaults
    assert config.ELASTICSEARCH_HOST == 'localhost'
    assert config.ELASTICSEARCH_PORT == 9200
    assert config.ELASTICSEARCH_INDEX == 'quiz_history'
    
    # Flask defaults
    assert config.FLASK_HOST == '0.0.0.0'
    assert config.FLASK_PORT == 5000
    assert config.FLASK_DEBUG is False
    
    # Teacher service defaults
    assert config.TEACHER_SERVICE_ENABLED is True
    
    print("✅ Config default values are correct")


def test_config_environment_variable_override():
    """Test that environment variables properly override defaults"""
    # Set environment variables
    env_vars = {
        'AI_MODEL_URL': 'http://custom-host:8080',
        'DATABASE_BACKEND': 'elasticsearch',
        'DB_MAX_RETRIES': '20',
        'DB_RETRY_DELAY': '10.5',
        'MARIADB_HOST': 'custom-db-host',
        'MARIADB_PORT': '3307',
        'TEACHER_SERVICE_ENABLED': 'False',
        'FLASK_PORT': '8000',
        'FLASK_DEBUG': 'True'
    }
    
    with patch.dict(os.environ, env_vars, clear=False):
        # Reload config module to pick up new environment variables
        import gradeschoolmathsolver.config as config_module
        importlib.reload(config_module)
        from gradeschoolmathsolver.config import Config
        
        config = Config()
        
        # Verify overrides
        assert config.AI_MODEL_URL == 'http://custom-host:8080'
        assert config.DATABASE_BACKEND == 'elasticsearch'
        assert config.DB_MAX_RETRIES == 20
        assert config.DB_RETRY_DELAY == 10.5
        assert config.MARIADB_HOST == 'custom-db-host'
        assert config.MARIADB_PORT == 3307
        assert config.TEACHER_SERVICE_ENABLED is False
        assert config.FLASK_PORT == 8000
        assert config.FLASK_DEBUG is True
        
        print("✅ Config environment variable overrides work correctly")


def test_teacher_service_enabled_default_true():
    """Test that TEACHER_SERVICE_ENABLED defaults to True when env var not set"""
    # Ensure env var is not set
    with patch.dict(os.environ, {}, clear=True):
        # Reload config to pick up the environment change
        import gradeschoolmathsolver.config as config_module
        importlib.reload(config_module)
        from gradeschoolmathsolver.config import Config
        
        config = Config()
        
        # Verify default is True
        assert config.TEACHER_SERVICE_ENABLED is True
        
        print("✅ TEACHER_SERVICE_ENABLED defaults to True")


def test_mariadb_backend_uses_config():
    """Test that MariaDB backend uses Config for retry parameters"""
    import importlib
    from mysql.connector import Error as MySQLError
    
    # Reload config module to pick up current environment variables
    import gradeschoolmathsolver.config as config_module
    importlib.reload(config_module)
    from gradeschoolmathsolver.config import Config
    from gradeschoolmathsolver.services.database.mariadb_backend import MariaDBDatabaseService
    
    # Get expected values from Config (respects environment)
    config = Config()
    expected_retries = config.DB_MAX_RETRIES
    expected_delay = config.DB_RETRY_DELAY
    
    with patch('gradeschoolmathsolver.services.database.mariadb_backend.mysql.connector.connect') as mock_connect:
        mock_connect.side_effect = MySQLError("Connection refused")
        
        with patch('gradeschoolmathsolver.services.database.mariadb_backend.time.sleep'):
            # Create service without explicit retry params (should use Config)
            service = MariaDBDatabaseService()
            
            # Should use config values (respects CI environment if set)
            assert service.max_retries == expected_retries
            assert service.retry_delay == expected_delay
            
            print("✅ MariaDB backend correctly uses Config defaults")


def test_elasticsearch_backend_uses_config():
    """Test that Elasticsearch backend uses Config for retry parameters"""
    import importlib
    from elasticsearch import ConnectionError as ESConnectionError
    
    # Reload config module to pick up current environment variables
    import gradeschoolmathsolver.config as config_module
    importlib.reload(config_module)
    from gradeschoolmathsolver.config import Config
    from gradeschoolmathsolver.services.database.elasticsearch_backend import ElasticsearchDatabaseService
    
    # Get expected values from Config (respects environment)
    config = Config()
    expected_retries = config.DB_MAX_RETRIES
    expected_delay = config.DB_RETRY_DELAY
    
    with patch('gradeschoolmathsolver.services.database.elasticsearch_backend.Elasticsearch') as mock_es_class:
        mock_es = mock_es_class.return_value
        mock_es.ping.side_effect = ESConnectionError("Connection refused")
        
        with patch('gradeschoolmathsolver.services.database.elasticsearch_backend.time.sleep'):
            # Create service without explicit retry params (should use Config)
            service = ElasticsearchDatabaseService()
            
            # Should use config values (respects CI environment if set)
            assert service.max_retries == expected_retries
            assert service.retry_delay == expected_delay
            
            print("✅ Elasticsearch backend correctly uses Config defaults")


def test_database_service_uses_config():
    """Test that database service selection uses Config"""
    from gradeschoolmathsolver.services.database.service import get_database_service, set_database_service
    
    # Reset the global service
    set_database_service(None)
    
    with patch.dict(os.environ, {'DATABASE_BACKEND': 'mariadb'}, clear=False):
        # Reload config module
        import gradeschoolmathsolver.config as config_module
        importlib.reload(config_module)
        
        with patch('gradeschoolmathsolver.services.database.mariadb_backend.mysql.connector.connect') as mock_connect:
            from mysql.connector import Error as MySQLError
            mock_connect.side_effect = MySQLError("Connection refused")
            
            with patch('gradeschoolmathsolver.services.database.mariadb_backend.time.sleep'):
                # Reset again to force re-initialization
                set_database_service(None)
                service = get_database_service()
                
                # Should be MariaDB service
                from gradeschoolmathsolver.services.database.mariadb_backend import MariaDBDatabaseService
                assert isinstance(service, MariaDBDatabaseService)
                
                print("✅ Database service selection correctly uses Config")


def test_no_direct_os_getenv_outside_config():
    """Test that no direct os.getenv calls exist outside config.py"""
    import ast
    import os
    from pathlib import Path
    
    # Get the source directory (relative to test file location)
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    src_dir = project_root / 'src' / 'gradeschoolmathsolver'
    
    # Ensure the source directory exists
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")
    
    # Track violations
    violations = []
    
    def check_file(filepath):
        """Check a Python file for direct os.getenv calls"""
        # Skip config.py itself
        if filepath.name == 'config.py':
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(filepath))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for os.getenv calls
                    if (isinstance(node.func, ast.Attribute) and 
                        node.func.attr == 'getenv' and
                        isinstance(node.func.value, ast.Name) and
                        node.func.value.id == 'os'):
                        violations.append(f"{filepath}:{node.lineno}")
        except Exception as e:
            print(f"Warning: Could not parse {filepath}: {e}")
    
    # Walk through all Python files
    for py_file in src_dir.rglob('*.py'):
        check_file(py_file)
    
    if violations:
        print(f"❌ Found os.getenv calls outside config.py:")
        for violation in violations:
            print(f"  - {violation}")
        assert False, f"Found {len(violations)} direct os.getenv calls outside config.py"
    else:
        print("✅ No direct os.getenv calls found outside config.py")


if __name__ == '__main__':
    test_config_default_values()
    test_config_environment_variable_override()
    test_teacher_service_enabled_default_true()
    test_mariadb_backend_uses_config()
    test_elasticsearch_backend_uses_config()
    test_database_service_uses_config()
    test_no_direct_os_getenv_outside_config()
    
    print("\n✅ All config centralization tests passed!")
