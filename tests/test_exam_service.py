"""
Unit tests for the ExamService - core solver functionality
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.exam import ExamService  # noqa: E402
from models import ExamRequest, Question  # noqa: E402


def test_create_exam_basic():
    """Test basic exam creation with specified parameters"""
    service = ExamService()

    # Create exam request
    request = ExamRequest(
        username="test_user",
        difficulty="easy",
        question_count=3
    )

    # Generate exam
    questions = service.create_exam(request)

    # Verify results
    assert len(questions) == 3
    assert all(isinstance(q, Question) for q in questions)
    assert all(q.difficulty == "easy" for q in questions)
    assert all(q.category is not None for q in questions)
    assert all(q.answer is not None for q in questions)
    print("✅ ExamService: Basic exam creation works correctly")


def test_create_exam_different_difficulties():
    """Test exam creation with different difficulty levels"""
    service = ExamService()

    difficulties = ["easy", "medium", "hard"]

    for difficulty in difficulties:
        request = ExamRequest(
            username="test_user",
            difficulty=difficulty,
            question_count=2
        )

        questions = service.create_exam(request)

        assert len(questions) == 2
        assert all(q.difficulty == difficulty for q in questions)
        assert all(q.equation for q in questions)
        assert all(isinstance(q.answer, int) for q in questions)

    print("✅ ExamService: All difficulty levels work correctly")


def test_create_exam_question_variety():
    """Test that exam creates different questions"""
    service = ExamService()

    request = ExamRequest(
        username="test_user",
        difficulty="medium",
        question_count=5
    )

    questions = service.create_exam(request)

    # Check that we have variety in equations (not all the same)
    equations = [q.equation for q in questions]
    unique_equations = set(equations)

    # At least some variety expected (not all identical)
    assert len(unique_equations) >= 3, "Should generate varied questions"

    print("✅ ExamService: Questions show variety")


def test_process_human_exam_correct_answers():
    """Test processing exam with correct answers"""
    service = ExamService()

    # Create exam
    request = ExamRequest(
        username="test_human_correct",
        difficulty="easy",
        question_count=3
    )

    questions = service.create_exam(request)

    # Submit all correct answers
    answers = [q.answer for q in questions]

    results = service.process_human_exam(request, questions, answers)

    # Verify results
    assert results["correct_answers"] == 3
    assert results["total_questions"] == 3
    assert results["score"] == 100.0
    assert len(results["results"]) == 3

    print("✅ ExamService: Correct answer processing works")


def test_process_human_exam_mixed_answers():
    """Test processing exam with mixed correct/incorrect answers"""
    service = ExamService()

    # Create exam
    request = ExamRequest(
        username="test_human_mixed",
        difficulty="easy",
        question_count=4
    )

    questions = service.create_exam(request)

    # Submit mixed answers (2 correct, 2 wrong)
    answers = [
        questions[0].answer,  # correct
        questions[1].answer + 999,  # wrong
        questions[2].answer,  # correct
        questions[3].answer - 100  # wrong
    ]

    results = service.process_human_exam(request, questions, answers)

    # Verify results
    assert results["correct_answers"] == 2
    assert results["total_questions"] == 4
    assert results["score"] == 50.0
    assert len(results["results"]) == 4

    # Check individual results
    assert results["results"][0]["is_correct"] is True
    assert results["results"][1]["is_correct"] is False
    assert results["results"][2]["is_correct"] is True
    assert results["results"][3]["is_correct"] is False

    print("✅ ExamService: Mixed answer processing works")


def test_exam_service_creates_user_if_not_exists():
    """Test that exam service creates user if they don't exist"""
    service = ExamService()

    import random
    username = f"new_user_{random.randint(10000, 99999)}"

    request = ExamRequest(
        username=username,
        difficulty="easy",
        question_count=2
    )

    questions = service.create_exam(request)
    answers = [q.answer for q in questions]

    # This should create the user automatically
    results = service.process_human_exam(request, questions, answers)

    # Verify user was created and results are correct
    assert results is not None
    assert results["correct_answers"] == 2

    # Verify user exists now
    user = service.account_service.get_user(username)
    assert user is not None

    print("✅ ExamService: Auto-creates users correctly")


if __name__ == "__main__":
    # Run tests
    print("\n🧪 Running ExamService Unit Tests")
    print("=" * 60)

    tests = [
        test_create_exam_basic,
        test_create_exam_different_difficulties,
        test_create_exam_question_variety,
        test_process_human_exam_correct_answers,
        test_process_human_exam_mixed_answers,
        test_exam_service_creates_user_if_not_exists,
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

    print("\n" + "=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")

    sys.exit(0 if failed == 0 else 1)
