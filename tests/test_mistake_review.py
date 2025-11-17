"""
Test for Mistake Review Service
"""
import sys
import os
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_mistake_review_service():
    """Test mistake review service"""
    from services.mistake_review import MistakeReviewService
    from services.account import AccountService
    import pytest

    # Create services
    account_service = AccountService()
    mistake_service = MistakeReviewService()

    # Skip if Elasticsearch is not available
    if not account_service.es:
        pytest.skip("Elasticsearch not available")

    # Create test user with unique name
    username = f"test_mistake_{random.randint(1000, 9999)}"
    account_service.create_user(username)

    # Record some answers (2 wrong, 1 correct) with refresh for testing
    account_service.record_answer(username, "What is 5 + 3?", "5 + 3", 7, 8, "addition", refresh=True)  # Wrong
    account_service.record_answer(username, "What is 10 - 4?", "10 - 4", 6, 6, "subtraction", refresh=True)  # Correct
    account_service.record_answer(username, "What is 3 * 4?", "3 * 4", 11, 12, "multiplication", refresh=True)  # Wrong

    # Test get unreviewed count
    count = mistake_service.get_unreviewed_count(username)
    assert count == 2, f"Expected 2 unreviewed mistakes, got {count}"
    print(f"✅ Unreviewed count: {count}")

    # Test get next mistake (should be FIFO - first wrong answer)
    mistake = mistake_service.get_next_mistake(username)
    assert mistake is not None, "Expected a mistake to review"
    assert mistake.question == "What is 5 + 3?", "Expected first wrong answer"
    assert mistake.user_answer == 7, "Expected user answer to be 7"
    assert mistake.correct_answer == 8, "Expected correct answer to be 8"
    print(f"✅ Got next mistake: {mistake.question}")

    # Test mark as reviewed
    success = mistake_service.mark_as_reviewed(username, mistake.mistake_id, refresh=True)
    assert success, "Failed to mark mistake as reviewed"
    print("✅ Marked mistake as reviewed")

    # Test count decreased
    count_after = mistake_service.get_unreviewed_count(username)
    assert count_after == 1, f"Expected 1 unreviewed mistake after review, got {count_after}"
    print(f"✅ Unreviewed count after review: {count_after}")

    # Test get next mistake again (should be second wrong answer)
    mistake2 = mistake_service.get_next_mistake(username)
    assert mistake2 is not None, "Expected a second mistake to review"
    assert mistake2.question == "What is 3 * 4?", "Expected second wrong answer"
    print(f"✅ Got next mistake: {mistake2.question}")

    # Test get all unreviewed mistakes
    all_mistakes = mistake_service.get_all_unreviewed_mistakes(username)
    assert len(all_mistakes) == 1, f"Expected 1 unreviewed mistake, got {len(all_mistakes)}"
    print(f"✅ Got all unreviewed mistakes: {len(all_mistakes)}")

    # Mark second mistake as reviewed
    success2 = mistake_service.mark_as_reviewed(username, mistake2.mistake_id, refresh=True)
    assert success2, "Failed to mark second mistake as reviewed"

    # Test no more mistakes
    count_final = mistake_service.get_unreviewed_count(username)
    assert count_final == 0, f"Expected 0 unreviewed mistakes, got {count_final}"
    print(f"✅ No more unreviewed mistakes: {count_final}")

    # Test get next when no mistakes
    no_mistake = mistake_service.get_next_mistake(username)
    assert no_mistake is None, "Expected no mistake when all reviewed"
    print("✅ No mistake returned when all reviewed")

    print("✅ Mistake Review Service: All tests passed")


if __name__ == "__main__":
    test_mistake_review_service()
