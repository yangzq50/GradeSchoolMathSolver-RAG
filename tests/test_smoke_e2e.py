"""
End-to-end smoke test with external services mocked
Tests the full flow from question generation to result processing with mocked dependencies
"""
import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@patch.dict(os.environ, {'DATABASE_BACKEND': 'elasticsearch'})
@patch('gradeschoolmathsolver.services.database.elasticsearch_backend.Elasticsearch')
@patch('gradeschoolmathsolver.model_access.requests.post')
def test_full_exam_flow_with_mocked_external_services(mock_requests_post, mock_elasticsearch):  # noqa: C901
    """
    End-to-end smoke test: Generate questions, take exam, process results
    with Database and AI Model service mocked
    """
    # Reload config to pick up environment variable changes
    import importlib
    import gradeschoolmathsolver.config as config_module
    importlib.reload(config_module)
    
    # Reset database service to pick up elasticsearch backend
    from gradeschoolmathsolver.services.database.service import set_database_service
    set_database_service(None)
    
    from gradeschoolmathsolver.services.exam import ExamService
    from gradeschoolmathsolver.models import ExamRequest
    from elasticsearch import NotFoundError

    # Track created users
    created_users = set()

    # Mock Elasticsearch to avoid connection errors
    mock_es_instance = MagicMock()
    mock_es_instance.ping.return_value = True
    mock_es_instance.indices.exists.return_value = True
    mock_es_instance.index.return_value = {"result": "created", "_id": "test_id"}

    def mock_create(index, id, document, **kwargs):
        if index == "users":
            created_users.add(id)
        return {"result": "created"}

    mock_es_instance.create.side_effect = mock_create

    # Mock get to raise NotFoundError for non-existent users, return user if created
    def mock_get(index, id, **kwargs):
        if index == "users":
            if id not in created_users:
                raise NotFoundError("User not found", {"error": "not_found"}, {})
            return {"_source": {"username": id, "created_at": "2025-01-01T00:00:00"}}
        return {"_source": {"username": id}}

    mock_es_instance.get.side_effect = mock_get

    # Mock search to return created records after they're indexed
    indexed_records = []

    def mock_index(index, document, **kwargs):
        doc_with_id = document.copy()
        if index == "quiz_history":
            indexed_records.append(doc_with_id)
        return {"result": "created", "_id": f"doc_{len(indexed_records)}"}

    mock_es_instance.index.side_effect = mock_index

    def mock_search(index, body, **kwargs):
        if index == "quiz_history" and indexed_records:
            # Return the indexed records
            return {
                "hits": {
                    "hits": [
                        {
                            "_id": str(i),
                            "_source": rec
                        }
                        for i, rec in enumerate(indexed_records)
                    ]
                }
            }
        return {"hits": {"hits": []}}

    mock_es_instance.search.side_effect = mock_search

    # Mock count to return number of indexed records
    def mock_count(index, body, **kwargs):
        return {"count": len(indexed_records)}

    mock_es_instance.count.side_effect = mock_count

    # Mock indices.refresh for testing
    mock_es_instance.indices.refresh = MagicMock()
    mock_es_instance.indices.create = MagicMock()

    mock_elasticsearch.return_value = mock_es_instance

    # Reset global database service to ensure fresh initialization
    from gradeschoolmathsolver.services.database import service as db_service_module
    db_service_module._db_service = None

    # Mock AI model API to return a simple question text
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": "What is 5 plus 3?"
    }
    mock_response.raise_for_status.return_value = None
    mock_requests_post.return_value = mock_response

    # Create exam service
    service = ExamService()

    # Step 1: Create exam
    request = ExamRequest(
        username="smoke_test_user",
        difficulty="easy",
        question_count=3
    )

    questions = service.create_exam(request)

    # Verify questions were created
    assert len(questions) == 3, "Should create 3 questions"
    assert all(q.equation for q in questions), "All questions should have equations"
    assert all(q.answer is not None for q in questions), "All questions should have answers"
    assert all(q.category for q in questions), "All questions should be classified"

    # Step 2: Simulate user answering questions
    # Answer first correctly, second incorrectly, third correctly
    user_answers = [
        questions[0].answer,  # Correct
        questions[1].answer + 100,  # Incorrect
        questions[2].answer,  # Correct
    ]

    # Step 3: Process exam results
    results = service.process_human_exam(request, questions, user_answers)

    # Verify results
    assert results is not None, "Results should be returned"
    assert results["total_questions"] == 3, "Should have 3 questions"
    assert results["correct_answers"] == 2, "Should have 2 correct answers"
    assert results["score"] == pytest.approx(66.67, rel=0.1), "Score should be ~66.67%"
    assert len(results["results"]) == 3, "Should have 3 individual results"

    # Verify individual results
    assert results["results"][0]["is_correct"] is True, "First answer should be correct"
    assert results["results"][1]["is_correct"] is False, "Second answer should be incorrect"
    assert results["results"][2]["is_correct"] is True, "Third answer should be correct"

    # Refresh the index to make documents searchable (for testing)
    if service.account_service._is_connected():
        from gradeschoolmathsolver.services.database.elasticsearch_backend import ElasticsearchDatabaseService
        if isinstance(service.account_service.db, ElasticsearchDatabaseService):
            service.account_service.db.refresh_index(service.account_service.answers_index)

    # Step 4: Verify user stats were updated
    user_stats = service.account_service.get_user_stats("smoke_test_user")
    assert user_stats is not None, "User stats should exist"
    assert user_stats.total_questions >= 3, "Should have at least 3 questions recorded"

    print("✅ End-to-end smoke test: Full exam flow works with mocked services")


@patch.dict(os.environ, {'DATABASE_BACKEND': 'elasticsearch'})
@patch('gradeschoolmathsolver.services.database.elasticsearch_backend.Elasticsearch')
def test_exam_flow_without_ai_model(mock_elasticsearch):
    """
    Test that exam flow works even when AI model is unavailable
    (should fall back to using equation as question text)
    """
    # Reload config to pick up environment variable changes
    import importlib
    import gradeschoolmathsolver.config as config_module
    importlib.reload(config_module)
    
    # Reset database service to pick up elasticsearch backend
    from gradeschoolmathsolver.services.database.service import set_database_service
    set_database_service(None)
    
    from gradeschoolmathsolver.services.exam import ExamService
    from gradeschoolmathsolver.models import ExamRequest

    # Mock Elasticsearch
    mock_es_instance = MagicMock()
    mock_es_instance.ping.return_value = True
    mock_elasticsearch.return_value = mock_es_instance

    # Don't mock requests - let it potentially fail gracefully

    service = ExamService()

    request = ExamRequest(
        username="no_ai_user",
        difficulty="medium",
        question_count=2
    )

    # Should still work even if AI model is unavailable
    questions = service.create_exam(request)

    assert len(questions) == 2
    assert all(q.equation for q in questions)
    assert all(q.answer is not None for q in questions)

    # Process answers
    answers = [q.answer for q in questions]
    results = service.process_human_exam(request, questions, answers)

    assert results["correct_answers"] == 2
    assert results["score"] == 100.0

    print("✅ End-to-end smoke test: Works without AI model service")


@patch.dict(os.environ, {'DATABASE_BACKEND': 'elasticsearch'})
@patch('gradeschoolmathsolver.services.database.elasticsearch_backend.Elasticsearch')
def test_exam_flow_without_elasticsearch(mock_elasticsearch):
    """
    Test that exam flow works when Elasticsearch is unavailable
    (should gracefully degrade, skipping RAG features)
    """
    # Reload config to pick up environment variable changes
    import importlib
    import gradeschoolmathsolver.config as config_module
    importlib.reload(config_module)
    
    # Reset database service to pick up elasticsearch backend
    from gradeschoolmathsolver.services.database.service import set_database_service
    set_database_service(None)
    
    from gradeschoolmathsolver.services.exam import ExamService
    from gradeschoolmathsolver.models import ExamRequest

    # Mock Elasticsearch to simulate connection failure
    mock_elasticsearch.side_effect = Exception("Connection failed")

    service = ExamService()

    request = ExamRequest(
        username="no_es_user",
        difficulty="easy",
        question_count=2
    )

    # Should still work even if Elasticsearch is unavailable
    questions = service.create_exam(request)

    assert len(questions) == 2
    assert all(q.equation for q in questions)

    # Process answers
    answers = [q.answer for q in questions]
    results = service.process_human_exam(request, questions, answers)

    assert results["correct_answers"] == 2

    print("✅ End-to-end smoke test: Works without Elasticsearch")


@patch.dict(os.environ, {'DATABASE_BACKEND': 'elasticsearch'})
@patch('gradeschoolmathsolver.services.database.elasticsearch_backend.Elasticsearch')
@patch('gradeschoolmathsolver.model_access.requests.post')
def test_classification_integration(mock_requests_post, mock_elasticsearch):
    """
    Test that question classification works in the full flow
    """
    # Reload config to pick up environment variable changes
    import importlib
    import gradeschoolmathsolver.config as config_module
    importlib.reload(config_module)
    
    # Reset database service to pick up elasticsearch backend
    from gradeschoolmathsolver.services.database.service import set_database_service
    set_database_service(None)
    
    from gradeschoolmathsolver.services.exam import ExamService
    from gradeschoolmathsolver.models import ExamRequest

    # Setup mocks
    mock_es_instance = MagicMock()
    mock_elasticsearch.return_value = mock_es_instance

    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Test question"}
    mock_requests_post.return_value = mock_response

    service = ExamService()

    # Test with different difficulties to get different operation types
    for difficulty in ["easy", "medium", "hard"]:
        request = ExamRequest(
            username="classification_test",
            difficulty=difficulty,
            question_count=3
        )

        questions = service.create_exam(request)

        # Verify all questions are classified
        assert all(q.category is not None for q in questions), \
            f"All {difficulty} questions should have categories"

        # Verify categories are valid
        valid_categories = [
            "addition", "subtraction", "multiplication", "division",
            "mixed_operations", "parentheses", "fractions"
        ]
        for q in questions:
            assert q.category in valid_categories, \
                f"Category '{q.category}' should be valid"

    print("✅ End-to-end smoke test: Classification integration works")


if __name__ == "__main__":
    print("\n🧪 Running End-to-End Smoke Tests")
    print("=" * 60)

    tests = [
        test_full_exam_flow_with_mocked_external_services,
        test_exam_flow_without_ai_model,
        test_exam_flow_without_elasticsearch,
        test_classification_integration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            # Call with mock arguments
            if "with_mocked_external_services" in test.__name__:
                mock_es = MagicMock()
                mock_req = MagicMock()
                test(mock_req, mock_es)
            elif "without_ai_model" in test.__name__ or "without_elasticsearch" in test.__name__:
                mock_es = MagicMock()
                test(mock_es)
            elif "classification_integration" in test.__name__:
                mock_req = MagicMock()
                mock_es = MagicMock()
                test(mock_req, mock_es)
            else:
                test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")

    sys.exit(0 if failed == 0 else 1)
