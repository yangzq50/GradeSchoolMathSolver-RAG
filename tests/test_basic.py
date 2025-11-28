"""
Basic tests for the GradeSchoolMathSolver system
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_qa_generation():
    """Test QA generation service"""
    from gradeschoolmathsolver.services.qa_generation import QAGenerationService

    service = QAGenerationService()

    # Test easy question
    question = service.generate_question('easy')
    assert question.difficulty == 'easy'
    assert question.equation
    assert question.answer is not None
    print("✅ QA Generation: Easy question generated")

    # Test medium question
    question = service.generate_question('medium')
    assert question.difficulty == 'medium'
    print("✅ QA Generation: Medium question generated")

    # Test hard question
    question = service.generate_question('hard')
    assert question.difficulty == 'hard'
    print("✅ QA Generation: Hard question generated")


def test_classification():
    """Test classification service"""
    from gradeschoolmathsolver.services.classification import ClassificationService

    service = ClassificationService()

    # Test different equation types
    assert service.classify_question("5 + 3") == "addition"
    assert service.classify_question("10 - 4") == "subtraction"
    assert service.classify_question("6 * 7") == "multiplication"
    assert service.classify_question("12 / 4") == "division"
    assert service.classify_question("5 + 3 - 2") == "mixed_operations"
    assert service.classify_question("(4 + 5) * 2") == "parentheses"

    print("✅ Classification: All equation types classified correctly")


def test_account_service():
    """Test account service"""
    from gradeschoolmathsolver.services.account import AccountService
    import pytest
    import random

    service = AccountService()

    # Skip if database is not available
    if not service._is_connected():
        pytest.skip("Database not available")

    # Create test user with unique name
    username = f"test_user_pytest_{random.randint(1000, 9999)}"
    service.create_user(username)

    # Record answers with refresh for testing
    service.record_answer(username, "Test Q1", "2 + 2", 4, 4, "addition", refresh=True)
    service.record_answer(username, "Test Q2", "5 - 3", 2, 2, "subtraction", refresh=True)
    service.record_answer(username, "Test Q3", "3 * 4", 11, 12, "multiplication", refresh=True)

    # Get stats
    stats = service.get_user_stats(username)
    assert stats is not None
    assert stats.total_questions == 3
    assert stats.correct_answers == 2

    print("✅ Account Service: User created and stats calculated")


def test_agent_management():
    """Test agent management service"""
    from gradeschoolmathsolver.services.agent_management import AgentManagementService

    service = AgentManagementService()

    # Create default agents
    service.create_default_agents()

    # List agents
    agents = service.list_agents()
    assert len(agents) > 0

    # Get agent
    agent = service.get_agent("basic_agent")
    assert agent is not None
    assert agent.name == "basic_agent"

    print("✅ Agent Management: Agents created and retrieved")


def test_models():
    """Test data models"""
    from gradeschoolmathsolver.models import Question, AgentConfig, UserStats

    # Test Question model
    q = Question(
        equation="2 + 2",
        question_text="What is 2 + 2?",
        answer=4,
        difficulty="easy"
    )
    assert q.equation == "2 + 2"

    # Test AgentConfig model
    agent = AgentConfig(
        name="test_agent",
        use_classification=True,
        use_rag=False
    )
    assert agent.name == "test_agent"

    # Test UserStats model
    stats = UserStats(
        username="test",
        total_questions=10,
        correct_answers=8,
        overall_correctness=80.0,
        recent_100_score=85.0
    )
    assert stats.username == "test"

    print("✅ Models: All models validated")


def test_config():
    """Test configuration"""
    from gradeschoolmathsolver.config import Config

    config = Config()
    assert config.AI_MODEL_NAME
    assert config.DIFFICULTY_LEVELS == ['easy', 'medium', 'hard']
    assert len(config.QUESTION_CATEGORIES) > 0

    print("✅ Config: Configuration loaded successfully")


def run_all_tests():
    """Run all tests"""
    print("\n🧪 Running GradeSchoolMathSolver Tests")
    print("=" * 50)

    tests = [
        test_config,
        test_models,
        test_qa_generation,
        test_classification,
        test_account_service,
        test_agent_management,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {str(e)}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
