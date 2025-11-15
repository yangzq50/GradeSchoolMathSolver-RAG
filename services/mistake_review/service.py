"""
Mistake Review Service
Manages reviewing past mistakes for users
"""
import sys
import os
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.account import AccountService  # noqa: E402
from models import MistakeReview  # noqa: E402


class MistakeReviewService:
    """Service for reviewing past mistakes"""

    def __init__(self):
        self.account_service = AccountService()

    def get_next_mistake(self, username: str) -> Optional[MistakeReview]:
        """
        Get the next unreviewed mistake for a user (FIFO order)

        Args:
            username: Username

        Returns:
            MistakeReview object or None if no unreviewed mistakes exist
        """
        # Get the oldest unreviewed incorrect answer
        from services.account.service import AnswerHistory

        mistake = self.account_service.session.query(AnswerHistory)\
            .filter_by(username=username, is_correct=False, reviewed=False)\
            .order_by(AnswerHistory.timestamp.asc())\
            .first()

        if not mistake:
            return None

        return MistakeReview(
            mistake_id=mistake.id,
            username=mistake.username,
            question=mistake.question,
            equation=mistake.equation,
            user_answer=mistake.user_answer,
            correct_answer=mistake.correct_answer,
            category=mistake.category,
            timestamp=mistake.timestamp,
            reviewed=mistake.reviewed
        )

    def mark_as_reviewed(self, username: str, mistake_id: int) -> bool:
        """
        Mark a mistake as reviewed

        Args:
            username: Username
            mistake_id: ID of the mistake to mark as reviewed

        Returns:
            True if successful, False otherwise
        """
        try:
            from services.account.service import AnswerHistory

            mistake = self.account_service.session.query(AnswerHistory)\
                .filter_by(id=mistake_id, username=username)\
                .first()

            if not mistake:
                return False

            mistake.reviewed = True
            self.account_service.session.commit()
            return True
        except Exception as e:
            self.account_service.session.rollback()
            print(f"Error marking mistake as reviewed: {e}")
            return False

    def get_unreviewed_count(self, username: str) -> int:
        """
        Get count of unreviewed mistakes for a user

        Args:
            username: Username

        Returns:
            Count of unreviewed mistakes
        """
        from services.account.service import AnswerHistory

        return self.account_service.session.query(AnswerHistory)\
            .filter_by(username=username, is_correct=False, reviewed=False)\
            .count()

    def get_all_unreviewed_mistakes(self, username: str, limit: int = 100) -> List[MistakeReview]:
        """
        Get all unreviewed mistakes for a user in FIFO order

        Args:
            username: Username
            limit: Maximum number of mistakes to return

        Returns:
            List of MistakeReview objects
        """
        from services.account.service import AnswerHistory

        mistakes = self.account_service.session.query(AnswerHistory)\
            .filter_by(username=username, is_correct=False, reviewed=False)\
            .order_by(AnswerHistory.timestamp.asc())\
            .limit(limit)\
            .all()

        return [
            MistakeReview(
                mistake_id=m.id,
                username=m.username,
                question=m.question,
                equation=m.equation,
                user_answer=m.user_answer,
                correct_answer=m.correct_answer,
                category=m.category,
                timestamp=m.timestamp,
                reviewed=m.reviewed
            )
            for m in mistakes
        ]


if __name__ == "__main__":
    # Test the service
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    from services.account import AccountService  # noqa: E402, F811

    # Create test data
    account_service = AccountService()
    username = "test_mistake_user"
    account_service.create_user(username)

    # Record some wrong answers
    account_service.record_answer(username, "What is 5 + 3?", "5 + 3", 7, 8, "addition")
    account_service.record_answer(username, "What is 10 - 4?", "10 - 4", 5, 6, "subtraction")
    account_service.record_answer(username, "What is 3 * 4?", "3 * 4", 11, 12, "multiplication")

    # Test mistake review service
    service = MistakeReviewService()

    print(f"\nUnreviewed mistakes: {service.get_unreviewed_count(username)}")

    # Get next mistake
    mistake = service.get_next_mistake(username)
    if mistake:
        print("\nNext mistake to review:")
        print(f"  Question: {mistake.question}")
        print(f"  Your answer: {mistake.user_answer}")
        print(f"  Correct answer: {mistake.correct_answer}")
        print(f"  Category: {mistake.category}")

        # Mark as reviewed
        success = service.mark_as_reviewed(username, mistake.mistake_id)
        print(f"\nMarked as reviewed: {success}")
        print(f"Unreviewed mistakes remaining: {service.get_unreviewed_count(username)}")
    else:
        print("\nNo mistakes to review!")
