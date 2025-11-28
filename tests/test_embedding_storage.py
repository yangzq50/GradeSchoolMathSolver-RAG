"""
Tests for embedding storage configuration and schema generation

Tests the new embedding storage functionality added to support RAG features:
- Embedding configuration settings in config.py
- Schema generation for MariaDB and Elasticsearch with embedding columns
- Config-driven embedding dimensions and column counts
"""
import os
import importlib
from unittest.mock import patch
import pytest


class TestEmbeddingConfigDefaults:
    """Test default embedding configuration values"""

    def test_embedding_column_count_default(self) -> None:
        """Test that EMBEDDING_COLUMN_COUNT defaults to 2"""
        from gradeschoolmathsolver.config import Config
        config = Config()
        assert config.EMBEDDING_COLUMN_COUNT == 2

    def test_embedding_dimensions_default(self) -> None:
        """Test that EMBEDDING_DIMENSIONS defaults to [768]"""
        from gradeschoolmathsolver.config import Config
        config = Config()
        assert config.EMBEDDING_DIMENSIONS == [768]

    def test_elasticsearch_vector_similarity_default(self) -> None:
        """Test that ELASTICSEARCH_VECTOR_SIMILARITY defaults to 'cosine'"""
        from gradeschoolmathsolver.config import Config
        config = Config()
        assert config.ELASTICSEARCH_VECTOR_SIMILARITY == 'cosine'

    def test_embedding_column_names_default(self) -> None:
        """Test that EMBEDDING_COLUMN_NAMES defaults to ['question_embedding', 'equation_embedding']"""
        from gradeschoolmathsolver.config import Config
        config = Config()
        assert config.EMBEDDING_COLUMN_NAMES == ['question_embedding', 'equation_embedding']

    def test_embedding_source_columns_default(self) -> None:
        """Test that EMBEDDING_SOURCE_COLUMNS defaults to ['question', 'equation']"""
        from gradeschoolmathsolver.config import Config
        config = Config()
        assert config.EMBEDDING_SOURCE_COLUMNS == ['question', 'equation']


class TestEmbeddingConfigOverrides:
    """Test environment variable overrides for embedding configuration"""

    def test_embedding_column_count_override(self) -> None:
        """Test that EMBEDDING_COLUMN_COUNT can be overridden via env var"""
        env_vars = {'EMBEDDING_COLUMN_COUNT': '3'}

        with patch.dict(os.environ, env_vars, clear=False):
            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.config import Config

            config = Config()
            assert config.EMBEDDING_COLUMN_COUNT == 3

    def test_embedding_dimensions_single_override(self) -> None:
        """Test that EMBEDDING_DIMENSIONS can be overridden with single value"""
        env_vars = {'EMBEDDING_DIMENSIONS': '1024'}

        with patch.dict(os.environ, env_vars, clear=False):
            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.config import Config

            config = Config()
            assert config.EMBEDDING_DIMENSIONS == [1024]

    def test_embedding_dimensions_multiple_override(self) -> None:
        """Test that EMBEDDING_DIMENSIONS can be overridden with multiple values"""
        env_vars = {'EMBEDDING_DIMENSIONS': '768, 512, 256'}

        with patch.dict(os.environ, env_vars, clear=False):
            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.config import Config

            config = Config()
            assert config.EMBEDDING_DIMENSIONS == [768, 512, 256]

    def test_elasticsearch_vector_similarity_override(self) -> None:
        """Test that ELASTICSEARCH_VECTOR_SIMILARITY can be overridden"""
        env_vars = {'ELASTICSEARCH_VECTOR_SIMILARITY': 'dot_product'}

        with patch.dict(os.environ, env_vars, clear=False):
            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.config import Config

            config = Config()
            assert config.ELASTICSEARCH_VECTOR_SIMILARITY == 'dot_product'

    def test_embedding_column_names_override(self) -> None:
        """Test that EMBEDDING_COLUMN_NAMES can be overridden via env var"""
        env_vars = {'EMBEDDING_COLUMN_NAMES': 'custom_emb_1, custom_emb_2, custom_emb_3'}

        with patch.dict(os.environ, env_vars, clear=False):
            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.config import Config

            config = Config()
            assert config.EMBEDDING_COLUMN_NAMES == ['custom_emb_1', 'custom_emb_2', 'custom_emb_3']

    def test_embedding_source_columns_override(self) -> None:
        """Test that EMBEDDING_SOURCE_COLUMNS can be overridden via env var"""
        env_vars = {'EMBEDDING_SOURCE_COLUMNS': 'title, description, content'}

        with patch.dict(os.environ, env_vars, clear=False):
            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.config import Config

            config = Config()
            assert config.EMBEDDING_SOURCE_COLUMNS == ['title', 'description', 'content']


class TestEmbeddingSchemaHelpers:
    """Test embedding schema helper functions"""

    def test_get_embedding_config_default(self) -> None:
        """Test get_embedding_config returns correct default values"""
        # Reset environment to ensure defaults are used
        env_vars_to_clear = [
            'EMBEDDING_COLUMN_COUNT', 'EMBEDDING_DIMENSIONS',
            'ELASTICSEARCH_VECTOR_SIMILARITY', 'EMBEDDING_COLUMN_NAMES'
        ]
        original_values = {k: os.environ.get(k) for k in env_vars_to_clear}

        try:
            for key in env_vars_to_clear:
                if key in os.environ:
                    del os.environ[key]

            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)

            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import get_embedding_config

            config = get_embedding_config()

            assert config['column_count'] == 2
            assert len(config['dimensions']) == 2
            assert config['dimensions'][0] == 768
            assert config['dimensions'][1] == 768
            assert config['similarity'] == 'cosine'
            assert config['column_names'] == ['question_embedding', 'equation_embedding']
        finally:
            # Restore original values
            for key, value in original_values.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

    def test_get_embedding_config_extends_dimensions(self) -> None:
        """Test that get_embedding_config extends dimensions list when needed"""
        env_vars = {
            'EMBEDDING_COLUMN_COUNT': '4',
            'EMBEDDING_DIMENSIONS': '768, 512'
        }

        with patch.dict(os.environ, env_vars, clear=False):
            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)

            # Also reload schemas to pick up new config
            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import get_embedding_config

            config = get_embedding_config()

            assert config['column_count'] == 4
            assert len(config['dimensions']) == 4
            # First two should be as specified
            assert config['dimensions'][0] == 768
            assert config['dimensions'][1] == 512
            # Remaining should use last specified value
            assert config['dimensions'][2] == 512
            assert config['dimensions'][3] == 512

    def test_get_embedding_config_generates_column_names(self) -> None:
        """Test that get_embedding_config generates column names for extra columns"""
        env_vars = {'EMBEDDING_COLUMN_COUNT': '4'}

        with patch.dict(os.environ, env_vars, clear=False):
            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)

            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import get_embedding_config

            config = get_embedding_config()

            assert len(config['column_names']) == 4
            assert config['column_names'][0] == 'question_embedding'
            assert config['column_names'][1] == 'equation_embedding'
            assert config['column_names'][2] == 'embedding_2'
            assert config['column_names'][3] == 'embedding_3'

    def test_get_embedding_config_includes_source_columns(self) -> None:
        """Test that get_embedding_config includes source_columns"""
        # Clean up environment to ensure defaults
        env_vars_to_clear = [
            'EMBEDDING_COLUMN_COUNT', 'EMBEDDING_DIMENSIONS',
            'ELASTICSEARCH_VECTOR_SIMILARITY', 'EMBEDDING_COLUMN_NAMES',
            'EMBEDDING_SOURCE_COLUMNS'
        ]
        original_values = {k: os.environ.get(k) for k in env_vars_to_clear}

        try:
            for key in env_vars_to_clear:
                if key in os.environ:
                    del os.environ[key]

            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import get_embedding_config

            config = get_embedding_config()

            assert 'source_columns' in config
            assert config['source_columns'] == ['question', 'equation']
        finally:
            # Restore original values
            for key, value in original_values.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

    def test_get_embedding_config_extends_source_columns(self) -> None:
        """Test that get_embedding_config extends source columns when needed"""
        env_vars = {'EMBEDDING_COLUMN_COUNT': '4'}

        with patch.dict(os.environ, env_vars, clear=False):
            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)

            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import get_embedding_config

            config = get_embedding_config()

            assert len(config['source_columns']) == 4
            assert config['source_columns'][0] == 'question'
            assert config['source_columns'][1] == 'equation'
            assert config['source_columns'][2] == 'source_2'
            assert config['source_columns'][3] == 'source_3'


class TestEmbeddingSourceMapping:
    """Test embedding source to column mapping functions"""

    def test_get_embedding_source_mapping_default(self) -> None:
        """Test that get_embedding_source_mapping returns correct default mapping"""
        # Clean up environment to ensure defaults
        env_vars_to_clear = [
            'EMBEDDING_COLUMN_COUNT', 'EMBEDDING_DIMENSIONS',
            'ELASTICSEARCH_VECTOR_SIMILARITY', 'EMBEDDING_COLUMN_NAMES',
            'EMBEDDING_SOURCE_COLUMNS'
        ]
        original_values = {k: os.environ.get(k) for k in env_vars_to_clear}

        try:
            for key in env_vars_to_clear:
                if key in os.environ:
                    del os.environ[key]

            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import get_embedding_source_mapping

            mapping = get_embedding_source_mapping()

            assert mapping == {
                'question': 'question_embedding',
                'equation': 'equation_embedding'
            }
        finally:
            # Restore original values
            for key, value in original_values.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

    def test_get_embedding_source_mapping_custom(self) -> None:
        """Test that get_embedding_source_mapping respects custom config"""
        env_vars = {
            'EMBEDDING_SOURCE_COLUMNS': 'title,body',
            'EMBEDDING_COLUMN_NAMES': 'title_embedding,body_embedding'
        }

        with patch.dict(os.environ, env_vars, clear=False):
            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)

            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import get_embedding_source_mapping

            mapping = get_embedding_source_mapping()

            assert mapping == {
                'title': 'title_embedding',
                'body': 'body_embedding'
            }

    def test_validate_embedding_config_valid(self) -> None:
        """Test that validate_embedding_config returns True for valid config"""
        # Clean up environment to ensure defaults
        env_vars_to_clear = [
            'EMBEDDING_COLUMN_COUNT', 'EMBEDDING_DIMENSIONS',
            'ELASTICSEARCH_VECTOR_SIMILARITY', 'EMBEDDING_COLUMN_NAMES',
            'EMBEDDING_SOURCE_COLUMNS'
        ]
        original_values = {k: os.environ.get(k) for k in env_vars_to_clear}

        try:
            for key in env_vars_to_clear:
                if key in os.environ:
                    del os.environ[key]

            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import (
                validate_embedding_config,
                get_answer_history_text_columns
            )

            # Use the real schema columns
            valid_columns = get_answer_history_text_columns()
            assert validate_embedding_config(valid_columns) is True
        finally:
            # Restore original values
            for key, value in original_values.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

    def test_validate_embedding_config_invalid_source_column(self) -> None:
        """Test that validate_embedding_config raises ValueError for invalid source columns"""
        env_vars = {'EMBEDDING_SOURCE_COLUMNS': 'invalid_column,equation'}

        with patch.dict(os.environ, env_vars, clear=False):
            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import (
                validate_embedding_config,
                get_answer_history_text_columns
            )

            # Use the real schema columns
            valid_columns = get_answer_history_text_columns()
            with pytest.raises(ValueError, match="does not exist in database schema"):
                validate_embedding_config(valid_columns)

    def test_validate_embedding_config_custom_valid_columns(self) -> None:
        """Test that validate_embedding_config accepts custom valid source columns"""
        # Clean up environment to ensure defaults
        env_vars_to_clear = [
            'EMBEDDING_COLUMN_COUNT', 'EMBEDDING_DIMENSIONS',
            'ELASTICSEARCH_VECTOR_SIMILARITY', 'EMBEDDING_COLUMN_NAMES',
            'EMBEDDING_SOURCE_COLUMNS'
        ]
        original_values = {k: os.environ.get(k) for k in env_vars_to_clear}

        try:
            for key in env_vars_to_clear:
                if key in os.environ:
                    del os.environ[key]

            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import validate_embedding_config

            # Should accept custom valid_source_columns
            assert validate_embedding_config(['question', 'equation', 'custom']) is True
        finally:
            # Restore original values
            for key, value in original_values.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

    def test_get_answer_history_text_columns(self) -> None:
        """Test that get_answer_history_text_columns returns text columns from schema"""
        from gradeschoolmathsolver.services.database.schemas import get_answer_history_text_columns

        text_columns = get_answer_history_text_columns()

        # Should include only text columns from the schema
        assert 'question' in text_columns
        assert 'equation' in text_columns
        # Should not include non-text columns
        assert 'username' not in text_columns
        assert 'record_id' not in text_columns


class TestElasticsearchEmbeddingSchema:
    """Test Elasticsearch schema generation with embeddings"""

    def test_elasticsearch_embedding_fields_generation(self) -> None:
        """Test that embedding fields are generated correctly for Elasticsearch"""
        from gradeschoolmathsolver.services.database.schemas import get_embedding_fields_elasticsearch

        fields = get_embedding_fields_elasticsearch(
            column_names=['question_embedding', 'equation_embedding'],
            dimensions=[768, 512],
            similarity='cosine'
        )

        assert 'question_embedding' in fields
        assert 'equation_embedding' in fields

        assert fields['question_embedding']['type'] == 'dense_vector'
        assert fields['question_embedding']['dims'] == 768
        assert fields['question_embedding']['index'] is True
        assert fields['question_embedding']['similarity'] == 'cosine'

        assert fields['equation_embedding']['type'] == 'dense_vector'
        assert fields['equation_embedding']['dims'] == 512
        assert fields['equation_embedding']['similarity'] == 'cosine'

    def test_elasticsearch_embedding_fields_empty_dimensions(self) -> None:
        """Test that embedding fields raise ValueError when dimensions list is empty"""
        from gradeschoolmathsolver.services.database.schemas import get_embedding_fields_elasticsearch
        import pytest

        with pytest.raises(ValueError, match="dimensions list cannot be empty"):
            get_embedding_fields_elasticsearch(
                column_names=['test_embedding'],
                dimensions=[],
                similarity='cosine'
            )

    def test_elasticsearch_schema_includes_embeddings(self) -> None:
        """Test that answer history schema includes embedding fields for Elasticsearch"""
        # Clean up environment to ensure defaults
        env_vars_to_clear = [
            'EMBEDDING_COLUMN_COUNT', 'EMBEDDING_DIMENSIONS',
            'ELASTICSEARCH_VECTOR_SIMILARITY', 'EMBEDDING_COLUMN_NAMES',
            'EMBEDDING_SOURCE_COLUMNS'
        ]
        original_values = {k: os.environ.get(k) for k in env_vars_to_clear}

        try:
            for key in env_vars_to_clear:
                if key in os.environ:
                    del os.environ[key]

            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import get_answer_history_schema_for_backend

            schema = get_answer_history_schema_for_backend('elasticsearch', include_embeddings=True)

            properties = schema['mappings']['properties']

            # Check standard fields are present
            assert 'username' in properties
            assert 'question' in properties
            assert 'is_correct' in properties

            # Check embedding fields are present
            assert 'question_embedding' in properties
            assert properties['question_embedding']['type'] == 'dense_vector'
            assert properties['question_embedding']['dims'] == 768

            assert 'equation_embedding' in properties
            assert properties['equation_embedding']['type'] == 'dense_vector'
        finally:
            # Restore original values
            for key, value in original_values.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

    def test_elasticsearch_schema_without_embeddings(self) -> None:
        """Test that embeddings can be excluded from Elasticsearch schema"""
        from gradeschoolmathsolver.services.database.schemas import get_answer_history_schema_for_backend

        schema = get_answer_history_schema_for_backend('elasticsearch', include_embeddings=False)

        properties = schema['mappings']['properties']

        # Check standard fields are present
        assert 'username' in properties
        assert 'question' in properties

        # Check embedding fields are NOT present
        assert 'question_embedding' not in properties
        assert 'equation_embedding' not in properties


class TestMariaDBEmbeddingSchema:
    """Test MariaDB schema generation with embeddings"""

    def test_mariadb_embedding_columns_generation(self) -> None:
        """Test that embedding columns are generated correctly for MariaDB"""
        from gradeschoolmathsolver.services.database.schemas import get_embedding_columns_mariadb

        columns = get_embedding_columns_mariadb(
            column_names=['question_embedding', 'equation_embedding'],
            dimensions=[768, 512]
        )

        assert 'question_embedding' in columns
        assert 'equation_embedding' in columns

        # Both should use VECTOR type with NOT NULL for vector index compatibility
        assert columns['question_embedding'] == 'VECTOR(768) NOT NULL'
        assert columns['equation_embedding'] == 'VECTOR(512) NOT NULL'

    def test_mariadb_embedding_columns_empty_dimensions(self) -> None:
        """Test that embedding columns raise ValueError when dimensions list is empty"""
        from gradeschoolmathsolver.services.database.schemas import get_embedding_columns_mariadb
        import pytest

        with pytest.raises(ValueError, match="dimensions list cannot be empty"):
            get_embedding_columns_mariadb(
                column_names=['test_embedding'],
                dimensions=[]
            )

    def test_mariadb_embedding_indexes_generation(self) -> None:
        """Test that vector indexes return empty list (indexes are in separate tables)"""
        from gradeschoolmathsolver.services.database.schemas import get_embedding_indexes_mariadb

        indexes = get_embedding_indexes_mariadb(
            column_names=['question_embedding', 'equation_embedding']
        )

        # MariaDB doesn't support multiple VECTOR indexes on same table
        # Each embedding column gets its own table with its own index
        assert len(indexes) == 0

    def test_mariadb_embedding_table_schemas(self) -> None:
        """Test that separate embedding tables are generated for MariaDB"""
        from gradeschoolmathsolver.services.database.schemas import get_embedding_table_schemas_mariadb

        embedding_config = {
            'column_names': ['question_embedding', 'equation_embedding'],
            'dimensions': [768, 768]
        }

        tables = get_embedding_table_schemas_mariadb('quiz_history', embedding_config)

        # Should have two separate tables
        assert len(tables) == 2
        assert 'quiz_history_question_embedding' in tables
        assert 'quiz_history_equation_embedding' in tables

        # Each table should have record_id and embedding columns
        for table_name, table_schema in tables.items():
            columns = table_schema['columns']
            assert 'record_id' in columns
            # CHAR(36) is used because MariaDB vector indexes require primary key max 256 bytes
            assert columns['record_id'] == 'CHAR(36) CHARACTER SET ascii PRIMARY KEY'
            assert 'embedding' in columns
            assert columns['embedding'] == 'VECTOR(768) NOT NULL'

            indexes = table_schema['indexes']
            assert len(indexes) == 1
            assert 'VECTOR INDEX idx_embedding (embedding)' in indexes

    def test_mariadb_schema_excludes_embeddings_in_main_table(self) -> None:
        """Test that answer history schema excludes embedding columns for MariaDB"""
        # Clean up environment to ensure defaults
        env_vars_to_clear = [
            'EMBEDDING_COLUMN_COUNT', 'EMBEDDING_DIMENSIONS',
            'ELASTICSEARCH_VECTOR_SIMILARITY', 'EMBEDDING_COLUMN_NAMES',
            'EMBEDDING_SOURCE_COLUMNS'
        ]
        original_values = {k: os.environ.get(k) for k in env_vars_to_clear}

        try:
            for key in env_vars_to_clear:
                if key in os.environ:
                    del os.environ[key]

            import gradeschoolmathsolver.config as config_module
            importlib.reload(config_module)
            from gradeschoolmathsolver.services.database import schemas
            importlib.reload(schemas)
            from gradeschoolmathsolver.services.database.schemas import get_answer_history_schema_for_backend

            schema = get_answer_history_schema_for_backend('mariadb', include_embeddings=True)

            columns = schema['columns']

            # Check standard columns are present
            assert 'record_id' in columns
            assert 'username' in columns
            assert 'is_correct' in columns

            # Embedding columns should NOT be in main table for MariaDB
            # They are stored in separate tables
            assert 'question_embedding' not in columns
            assert 'equation_embedding' not in columns

            # No vector indexes in main table
            indexes = schema['indexes']
            assert 'VECTOR INDEX' not in ' '.join(indexes)
        finally:
            # Restore original values
            for key, value in original_values.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

    def test_mariadb_schema_without_embeddings(self) -> None:
        """Test that embeddings can be excluded from MariaDB schema"""
        from gradeschoolmathsolver.services.database.schemas import get_answer_history_schema_for_backend

        schema = get_answer_history_schema_for_backend('mariadb', include_embeddings=False)

        columns = schema['columns']
        indexes = schema['indexes']

        # Check standard columns are present
        assert 'record_id' in columns
        assert 'username' in columns

        # Check embedding columns are NOT present
        assert 'question_embedding' not in columns
        assert 'equation_embedding' not in columns

        # Check vector indexes are NOT present
        assert 'VECTOR INDEX idx_question_embedding (question_embedding)' not in indexes
        assert 'VECTOR INDEX idx_equation_embedding (equation_embedding)' not in indexes


class TestBackwardsCompatibility:
    """Test backwards compatibility with existing Q&A features"""

    def test_user_schema_unchanged(self) -> None:
        """Test that user schema is not affected by embedding changes"""
        from gradeschoolmathsolver.services.database.schemas import get_user_schema_for_backend

        # Elasticsearch
        es_schema = get_user_schema_for_backend('elasticsearch')
        assert 'mappings' in es_schema
        assert 'username' in es_schema['mappings']['properties']
        assert 'created_at' in es_schema['mappings']['properties']
        assert 'question_embedding' not in es_schema['mappings']['properties']

        # MariaDB
        maria_schema = get_user_schema_for_backend('mariadb')
        assert 'columns' in maria_schema
        assert 'username' in maria_schema['columns']
        assert 'created_at' in maria_schema['columns']
        assert 'question_embedding' not in maria_schema['columns']

    def test_answer_history_core_fields_preserved(self) -> None:
        """Test that core answer history fields are preserved"""
        from gradeschoolmathsolver.services.database.schemas import get_answer_history_schema_for_backend

        # Test both backends
        for backend in ['elasticsearch', 'mariadb']:
            schema = get_answer_history_schema_for_backend(backend, include_embeddings=True)

            if backend == 'elasticsearch':
                props = schema['mappings']['properties']
                assert 'username' in props
                assert 'question' in props
                assert 'equation' in props
                assert 'user_answer' in props
                assert 'correct_answer' in props
                assert 'is_correct' in props
                assert 'category' in props
                assert 'timestamp' in props
                assert 'reviewed' in props
            else:
                cols = schema['columns']
                assert 'record_id' in cols
                assert 'username' in cols
                assert 'question' in cols
                assert 'equation' in cols
                assert 'user_answer' in cols
                assert 'correct_answer' in cols
                assert 'is_correct' in cols
                assert 'category' in cols
                assert 'timestamp' in cols
                assert 'reviewed' in cols

    def test_answer_history_indexes_preserved(self) -> None:
        """Test that MariaDB indexes are preserved"""
        from gradeschoolmathsolver.services.database.schemas import get_answer_history_schema_for_backend

        schema = get_answer_history_schema_for_backend('mariadb', include_embeddings=True)

        indexes = schema['indexes']
        assert 'INDEX idx_username (username)' in indexes
        assert 'INDEX idx_timestamp (timestamp)' in indexes
        assert 'INDEX idx_category (category)' in indexes
        assert 'INDEX idx_reviewed (reviewed)' in indexes


class TestVectorSimilarityOptions:
    """Test different vector similarity options for Elasticsearch"""

    @pytest.mark.parametrize("similarity", ['cosine', 'dot_product', 'l2_norm'])
    def test_elasticsearch_similarity_options(self, similarity) -> None:
        """Test that all Elasticsearch similarity options work"""
        from gradeschoolmathsolver.services.database.schemas import get_embedding_fields_elasticsearch

        fields = get_embedding_fields_elasticsearch(
            column_names=['test_embedding'],
            dimensions=[768],
            similarity=similarity
        )

        assert fields['test_embedding']['similarity'] == similarity


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
