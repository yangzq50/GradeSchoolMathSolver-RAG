"""
Test suite for Teacher Service
"""
import sys
sys.path.insert(0, '/home/runner/work/GradeSchoolMathSolver/GradeSchoolMathSolver')

from gradeschoolmathsolver.services.teacher import TeacherService  # noqa: E402
from gradeschoolmathsolver.config import Config  # noqa: E402


def test_teacher_service() -> None:
    """Test teacher service feedback generation"""
    service = TeacherService()

    # Test with wrong answer
    feedback = service.generate_feedback(
        equation="5 + 3",
        question="What is five plus three?",
        correct_answer=8,
        user_answer=7
    )

    if service.enabled:
        assert feedback is not None, "Feedback should be generated when service is enabled"
        assert feedback.equation == "5 + 3"
        assert feedback.correct_answer == 8
        assert feedback.user_answer == 7
        assert len(feedback.feedback) > 0, "Feedback text should not be empty"
        assert len(feedback.explanation) > 0, "Explanation should not be empty"
        print("✅ Teacher Service: Feedback generated successfully")
    else:
        assert feedback is None, "Feedback should be None when service is disabled"
        print("✅ Teacher Service: Service correctly disabled")


def test_teacher_service_different_operations() -> None:
    """Test teacher service with different operation types"""
    service = TeacherService()

    if not service.enabled:
        print("⏭️  Teacher Service: Skipping operation tests (service disabled)")
        return

    test_cases = [
        ("10 - 4", "What is ten minus four?", 6, 5),
        ("6 * 7", "What is six times seven?", 42, 40),
        ("20 / 4", "What is twenty divided by four?", 5, 4),
    ]

    for equation, question, correct, wrong in test_cases:
        feedback = service.generate_feedback(
            equation=equation,
            question=question,
            correct_answer=correct,
            user_answer=wrong
        )

        assert feedback is not None
        assert feedback.equation == equation
        assert len(feedback.explanation) > 0

    print("✅ Teacher Service: Different operations tested successfully")


def test_teacher_service_config() -> None:
    """Test teacher service configuration"""
    config = Config()
    service = TeacherService()

    assert hasattr(config, 'TEACHER_SERVICE_ENABLED'), "Config should have TEACHER_SERVICE_ENABLED"
    assert service.enabled == config.TEACHER_SERVICE_ENABLED
    print(f"✅ Teacher Service: Configuration test passed (enabled={service.enabled})")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Teacher Service Tests")
    print("=" * 60)

    try:
        test_teacher_service_config()
        test_teacher_service()
        test_teacher_service_different_operations()
        print("\n" + "=" * 60)
        print("✅ All Teacher Service Tests Passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
