"""
Tests for the enhancements:
1. Integer-only equation generation
2. Number formatting utilities
3. Visibility and display improvements
"""
import pytest
from services.qa_generation.service import QAGenerationService


def test_integer_only_equations():
    """Test that all equation generation produces integer results"""
    service = QAGenerationService()

    # Test each difficulty level
    for difficulty in ['easy', 'medium', 'hard']:
        # Generate 30 equations per difficulty
        for _ in range(30):
            equation, answer = service.generate_equation(difficulty)

            # Verify answer is an integer
            assert answer == int(answer), (
                f"Non-integer result for {difficulty} difficulty: "
                f"{equation} = {answer}"
            )

            # Verify no decimal point in the answer when formatted
            if answer == int(answer):
                formatted = str(int(answer))
                assert '.' not in formatted, (
                    f"Decimal point found in integer: {formatted}"
                )


def test_easy_equations_integer():
    """Test easy equations produce integer results"""
    service = QAGenerationService()

    for _ in range(50):
        equation, answer = service._generate_easy_equation()
        assert answer == int(answer), f"Easy equation {equation} = {answer} is not integer"


def test_medium_equations_integer():
    """Test medium equations produce integer results"""
    service = QAGenerationService()

    for _ in range(50):
        equation, answer = service._generate_medium_equation()
        assert answer == int(answer), f"Medium equation {equation} = {answer} is not integer"


def test_hard_equations_integer():
    """Test hard equations produce integer results"""
    service = QAGenerationService()

    for _ in range(50):
        equation, answer = service._generate_hard_equation()
        assert answer == int(answer), f"Hard equation {equation} = {answer} is not integer"


def test_hard_division_equations():
    """Test that hard difficulty division equations always produce integers"""
    service = QAGenerationService()

    # Test multiple times to ensure consistency
    division_count = 0
    for _ in range(100):
        equation, answer = service._generate_hard_equation()

        # Check if this is a division equation
        if '/' in equation:
            division_count += 1
            # Verify the result is an integer
            assert answer == int(answer), (
                f"Division equation {equation} = {answer} is not integer"
            )
            # Verify we can evaluate it and get an integer
            result = eval(equation)
            assert result == int(result), (
                f"Division equation {equation} evaluates to non-integer: {result}"
            )

    # Make sure we tested at least some division equations
    assert division_count > 0, "No division equations generated"
    print(f"\nTested {division_count} division equations, all produced integer results")


def test_question_generation():
    """Test complete question generation produces integer answers"""
    service = QAGenerationService()

    for difficulty in ['easy', 'medium', 'hard']:
        question = service.generate_question(difficulty)

        # Verify answer is stored as integer value
        assert isinstance(question.answer, int), "Answer should be stored as int"


def test_format_number_utility():
    """Test the format_number utility function"""
    from services.qa_generation.service import format_number

    # Test integers
    assert format_number(5.0) == "5"
    assert format_number(10.0) == "10"
    assert format_number(100.0) == "100"

    # Test whole numbers stored as floats
    assert format_number(42.0) == "42"

    # Test actual integers
    assert format_number(7) == "7"

    # Test non-integer (edge case, shouldn't happen in our equations)
    assert format_number(3.5) == "3.5"
    assert format_number(2.75) == "2.75"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
