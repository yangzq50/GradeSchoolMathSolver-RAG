"""
Immersive Exam Service
Manages synchronized immersive exams with ordered answering and optional reveal strategies
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from models import (
    ImmersiveExam, ImmersiveExamConfig, ImmersiveParticipant,
    ImmersiveExamAnswer, ImmersiveExamStatus,
    ParticipantType, RevealStrategy, QuizHistory
)
from services.qa_generation import QAGenerationService
from services.classification import ClassificationService
from services.account import AccountService
from services.quiz_history import QuizHistoryService
from services.agent_management import AgentManagementService


class ImmersiveExamService:
    """Service for conducting immersive exams with synchronized question flow"""

    def __init__(self):
        self.qa_service = QAGenerationService()
        self.classification_service = ClassificationService()
        self.account_service = AccountService()
        self.quiz_history_service = QuizHistoryService()
        self.agent_management = AgentManagementService()
        # In-memory storage for active exams (in production, use Redis or database)
        self.active_exams: Dict[str, ImmersiveExam] = {}

    def create_immersive_exam(self, config: ImmersiveExamConfig) -> ImmersiveExam:
        """
        Create an immersive exam with pre-generated questions

        Args:
            config: ImmersiveExamConfig with exam settings

        Returns:
            ImmersiveExam object
        """
        exam_id = str(uuid.uuid4())

        # Generate questions based on difficulty distribution
        questions = []
        for difficulty, count in config.difficulty_distribution.items():
            for _ in range(count):
                question = self.qa_service.generate_question(difficulty)
                # Classify the question
                category = self.classification_service.classify_question(question.equation)
                question.category = category
                questions.append(question)

        # Create exam
        exam = ImmersiveExam(
            exam_id=exam_id,
            config=config,
            questions=questions,
            participants=[],
            current_question_index=0,
            status="waiting",
            created_at=datetime.now()
        )

        # Store exam
        self.active_exams[exam_id] = exam

        return exam

    def register_participant(self, exam_id: str, participant_id: str,
                             participant_type: ParticipantType) -> bool:
        """
        Register a participant (human or agent) for an immersive exam

        Args:
            exam_id: ID of the exam
            participant_id: Username or agent name
            participant_type: Type of participant (human or agent)

        Returns:
            True if successful
        """
        exam = self.active_exams.get(exam_id)
        if not exam:
            return False

        if exam.status != "waiting":
            return False  # Can only register when exam is waiting

        # Check if participant already registered
        for p in exam.participants:
            if p.participant_id == participant_id:
                return False

        # Create participant with order
        order = len(exam.participants)
        participant = ImmersiveParticipant(
            participant_id=participant_id,
            participant_type=participant_type,
            order=order,
            answers=[None] * len(exam.questions),
            scores=[False] * len(exam.questions),
            total_score=0.0,
            has_answered_current=False
        )

        exam.participants.append(participant)

        # Ensure user exists in account service if human
        if participant_type == ParticipantType.HUMAN:
            if not self.account_service.get_user(participant_id):
                self.account_service.create_user(participant_id)

        return True

    def start_exam(self, exam_id: str) -> bool:
        """
        Start an immersive exam

        Args:
            exam_id: ID of the exam

        Returns:
            True if successful
        """
        exam = self.active_exams.get(exam_id)
        if not exam or exam.status != "waiting":
            return False

        if len(exam.participants) == 0:
            return False  # Need at least one participant

        exam.status = "in_progress"
        exam.started_at = datetime.now()
        return True

    def get_exam_status(self, exam_id: str, participant_id: str) -> Optional[ImmersiveExamStatus]:
        """
        Get current status of the exam for a specific participant

        Args:
            exam_id: ID of the exam
            participant_id: ID of the participant requesting status

        Returns:
            ImmersiveExamStatus object
        """
        exam = self.active_exams.get(exam_id)
        if not exam:
            return None

        # Find participant
        participant = None
        for p in exam.participants:
            if p.participant_id == participant_id:
                participant = p
                break

        if not participant:
            return None

        # Count participants who have answered current question
        participants_answered = sum(1 for p in exam.participants if p.has_answered_current)

        # Current question (if exam is in progress)
        current_question = None
        if exam.status == "in_progress" and exam.current_question_index < len(exam.questions):
            current_question = exam.questions[exam.current_question_index]

        # Determine if participant can see previous answers
        can_see_previous = False
        previous_answers = []

        if exam.config.reveal_strategy == RevealStrategy.REVEAL_TO_LATER_PARTICIPANTS:
            # Show answers from participants with lower order (who answered before)
            can_see_previous = True
            for p in sorted(exam.participants, key=lambda x: x.order):
                if p.order < participant.order and exam.current_question_index < len(p.answers):
                    answer = p.answers[exam.current_question_index]
                    if answer is not None:
                        previous_answers.append({
                            'participant_id': p.participant_id,
                            'participant_type': p.participant_type.value,
                            'answer': answer,
                            'is_correct': (
                                p.scores[exam.current_question_index]
                                if exam.current_question_index < len(p.scores)
                                else False
                            )
                        })

        elif exam.config.reveal_strategy == RevealStrategy.REVEAL_ALL_AFTER_ROUND:
            # Show all answers after everyone has answered current question
            if participants_answered == len(exam.participants):
                can_see_previous = True
                for p in exam.participants:
                    if p.participant_id != participant_id and exam.current_question_index < len(p.answers):
                        answer = p.answers[exam.current_question_index]
                        if answer is not None:
                            previous_answers.append({
                                'participant_id': p.participant_id,
                                'participant_type': p.participant_type.value,
                                'answer': answer,
                                'is_correct': (
                                    p.scores[exam.current_question_index]
                                    if exam.current_question_index < len(p.scores)
                                    else False
                                )
                            })

        return ImmersiveExamStatus(
            exam_id=exam_id,
            status=exam.status,
            current_question_index=exam.current_question_index,
            total_questions=len(exam.questions),
            current_question=current_question,
            time_remaining=None,  # TODO: Implement time tracking
            participants_answered=participants_answered,
            total_participants=len(exam.participants),
            can_see_previous_answers=can_see_previous,
            previous_answers=previous_answers
        )

    def submit_answer(self, answer_submission: ImmersiveExamAnswer) -> bool:
        """
        Submit an answer for the current question

        Args:
            answer_submission: ImmersiveExamAnswer object

        Returns:
            True if successful
        """
        exam = self.active_exams.get(answer_submission.exam_id)
        if not exam or exam.status != "in_progress":
            return False

        # Find participant
        participant = None
        for p in exam.participants:
            if p.participant_id == answer_submission.participant_id:
                participant = p
                break

        if not participant:
            return False

        # Check if correct question index
        if answer_submission.question_index != exam.current_question_index:
            return False

        # Check if already answered
        if participant.has_answered_current:
            return False

        # Record answer
        question = exam.questions[exam.current_question_index]
        is_correct = abs(answer_submission.answer - question.answer) < 0.01

        participant.answers[exam.current_question_index] = answer_submission.answer
        participant.scores[exam.current_question_index] = is_correct
        participant.has_answered_current = True

        if is_correct:
            participant.total_score += 1

        # Record in account service and quiz history
        if participant.participant_type == ParticipantType.HUMAN:
            self.account_service.record_answer(
                username=participant.participant_id,
                question=question.question_text,
                equation=question.equation,
                user_answer=answer_submission.answer,
                correct_answer=question.answer,
                category=question.category or 'unknown'
            )

        # Record in quiz history for RAG
        quiz_history = QuizHistory(
            username=participant.participant_id,
            question=question.question_text,
            user_equation=question.equation,
            user_answer=answer_submission.answer,
            correct_answer=question.answer,
            is_correct=is_correct,
            category=question.category or 'unknown',
            timestamp=datetime.now()
        )
        self.quiz_history_service.add_history(quiz_history)

        return True

    def check_all_answered_current(self, exam_id: str) -> bool:
        """
        Check if all participants have answered the current question

        Args:
            exam_id: ID of the exam

        Returns:
            True if all answered
        """
        exam = self.active_exams.get(exam_id)
        if not exam:
            return False

        return all(p.has_answered_current for p in exam.participants)

    def advance_to_next_question(self, exam_id: str) -> bool:
        """
        Advance to the next question (server-controlled)

        Args:
            exam_id: ID of the exam

        Returns:
            True if successful
        """
        exam = self.active_exams.get(exam_id)
        if not exam or exam.status != "in_progress":
            return False

        # Reset has_answered_current for all participants
        for p in exam.participants:
            p.has_answered_current = False

        # Advance to next question
        exam.current_question_index += 1

        # Check if exam is completed
        if exam.current_question_index >= len(exam.questions):
            exam.status = "completed"
            exam.completed_at = datetime.now()

        return True

    def get_exam_results(self, exam_id: str) -> Optional[Dict[str, Any]]:
        """
        Get final results of the exam

        Args:
            exam_id: ID of the exam

        Returns:
            Dictionary with exam results
        """
        exam = self.active_exams.get(exam_id)
        if not exam:
            return None

        results: Dict[str, Any] = {
            'exam_id': exam_id,
            'status': exam.status,
            'total_questions': len(exam.questions),
            'created_at': exam.created_at.isoformat(),
            'started_at': exam.started_at.isoformat() if exam.started_at else None,
            'completed_at': exam.completed_at.isoformat() if exam.completed_at else None,
            'participants': []
        }

        for participant in sorted(exam.participants, key=lambda p: -p.total_score):
            score_percentage = (participant.total_score / len(exam.questions) * 100) if exam.questions else 0
            results['participants'].append({
                'participant_id': participant.participant_id,
                'participant_type': participant.participant_type.value,
                'order': participant.order,
                'total_score': participant.total_score,
                'score_percentage': round(score_percentage, 2),
                'answers': participant.answers,
                'scores': participant.scores
            })

        return results

    def get_exam(self, exam_id: str) -> Optional[ImmersiveExam]:
        """Get exam by ID"""
        return self.active_exams.get(exam_id)

    def list_active_exams(self) -> List[str]:
        """List all active exam IDs"""
        return list(self.active_exams.keys())


if __name__ == "__main__":
    # Test the service
    service = ImmersiveExamService()

    # Create immersive exam
    config = ImmersiveExamConfig(
        difficulty_distribution={"easy": 2, "medium": 2, "hard": 1},
        reveal_strategy=RevealStrategy.REVEAL_TO_LATER_PARTICIPANTS
    )

    exam = service.create_immersive_exam(config)
    print(f"Created exam: {exam.exam_id}")
    print(f"Questions: {len(exam.questions)}")

    # Register participants
    service.register_participant(exam.exam_id, "student1", ParticipantType.HUMAN)
    service.register_participant(exam.exam_id, "basic_agent", ParticipantType.AGENT)
    print("Registered 2 participants")

    # Start exam
    service.start_exam(exam.exam_id)
    print("Exam started")

    # Get status
    status = service.get_exam_status(exam.exam_id, "student1")
    if status:
        print(f"Current question: {status.current_question_index + 1}/{status.total_questions}")
        print(f"Question: {status.current_question.question_text if status.current_question else 'N/A'}")
