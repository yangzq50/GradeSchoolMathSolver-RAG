"""
Mistake Review Service
Manages reviewing past mistakes for users
"""
import sys
import os
from typing import Optional, List
from datetime import datetime

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
        if not self.account_service._is_connected():
            return None

        try:
            # Query for oldest unreviewed incorrect answer
            query = {
                "bool": {
                    "must": [
                        {"term": {"username": username}},
                        {"term": {"is_correct": False}},
                        {"term": {"reviewed": False}}
                    ]
                }
            }
            sort = [{"timestamp": {"order": "asc"}}]

            hits = self.account_service.db.search_records(
                index_name=self.account_service.answers_index,
                query=query,
                sort=sort,
                size=1
            )

            if not hits:
                return None

            hit = hits[0]
            source = hit['_source']

            return MistakeReview(
                mistake_id=hit['_id'],
                username=source['username'],
                question=source['question'],
                equation=source['equation'],
                user_answer=source.get('user_answer'),
                correct_answer=source['correct_answer'],
                category=source['category'],
                timestamp=datetime.fromisoformat(source['timestamp']),
                reviewed=source.get('reviewed', False)
            )
        except Exception as e:
            print(f"Error getting next mistake: {e}")
            return None

    def mark_as_reviewed(self, username: str, mistake_id: str, refresh: bool = False) -> bool:
        """
        Mark a mistake as reviewed

        Args:
            username: Username
            mistake_id: ID of the mistake to mark as reviewed
            refresh: Whether to refresh the index immediately (for testing)

        Returns:
            True if successful, False otherwise
        """
        if not self.account_service._is_connected():
            return False

        try:
            # Get the document first to verify username matches
            doc = self.account_service.db.get_record(
                self.account_service.answers_index,
                mistake_id
            )

            if not doc or doc['username'] != username:
                return False

            # Update the document
            success = self.account_service.db.update_record(
                self.account_service.answers_index,
                mistake_id,
                {"reviewed": True}
            )

            # Refresh index if requested (useful for testing)
            if refresh and success:
                from services.database.elasticsearch_backend import ElasticsearchDatabaseService
                if isinstance(self.account_service.db, ElasticsearchDatabaseService):
                    self.account_service.db.refresh_index(self.account_service.answers_index)

            return success
        except Exception as e:
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
        if not self.account_service._is_connected():
            return 0

        try:
            query = {
                "bool": {
                    "must": [
                        {"term": {"username": username}},
                        {"term": {"is_correct": False}},
                        {"term": {"reviewed": False}}
                    ]
                }
            }

            return self.account_service.db.count_records(
                self.account_service.answers_index,
                query
            )
        except Exception as e:
            print(f"Error getting unreviewed count: {e}")
            return 0

    def get_all_unreviewed_mistakes(self, username: str, limit: int = 100) -> List[MistakeReview]:
        """
        Get all unreviewed mistakes for a user in FIFO order

        Args:
            username: Username
            limit: Maximum number of mistakes to return

        Returns:
            List of MistakeReview objects
        """
        if not self.account_service.es:
            return []

        try:
            query = {
                "size": limit,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"username": username}},
                            {"term": {"is_correct": False}},
                            {"term": {"reviewed": False}}
                        ]
                    }
                },
                "sort": [{"timestamp": {"order": "asc"}}]
            }

            response = self.account_service.es.search(
                index=self.account_service.answers_index,
                body=query
            )

            mistakes = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                mistakes.append(MistakeReview(
                    mistake_id=hit['_id'],
                    username=source['username'],
                    question=source['question'],
                    equation=source['equation'],
                    user_answer=source.get('user_answer'),
                    correct_answer=source['correct_answer'],
                    category=source['category'],
                    timestamp=datetime.fromisoformat(source['timestamp']),
                    reviewed=source.get('reviewed', False)
                ))

            return mistakes
        except Exception as e:
            print(f"Error getting all unreviewed mistakes: {e}")
            return []


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
