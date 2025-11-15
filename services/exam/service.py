"""
Exam Service
Manages exams for users and agents
"""
from datetime import datetime
from typing import List, Dict, Any
from models import Question, ExamRequest, QuizHistory
from services.qa_generation import QAGenerationService
from services.classification import ClassificationService
from services.account import AccountService
from services.quiz_history import QuizHistoryService
from services.agent import AgentService
from services.agent_management import AgentManagementService
from services.teacher import TeacherService


class ExamService:
    """Service for conducting exams"""

    def __init__(self):
        self.qa_service = QAGenerationService()
        self.classification_service = ClassificationService()
        self.account_service = AccountService()
        self.quiz_history_service = QuizHistoryService()
        self.agent_management = AgentManagementService()
        self.teacher_service = TeacherService()

    def create_exam(self, request: ExamRequest) -> List[Question]:
        """
        Create an exam with specified parameters

        Args:
            request: ExamRequest with exam parameters

        Returns:
            List of Question objects
        """
        questions = []

        for _ in range(request.question_count):
            question = self.qa_service.generate_question(request.difficulty)

            # Classify the question
            category = self.classification_service.classify_question(question.equation)
            question.category = category

            questions.append(question)

        return questions

    def process_human_exam(self, request: ExamRequest,
                           questions: List[Question],
                           answers: List[float]) -> Dict[str, Any]:
        """
        Process exam results for a human user with pre-generated questions

        Args:
            request: ExamRequest
            questions: List of Question objects (already generated)
            answers: List of user answers

        Returns:
            Exam results with teacher feedback
        """
        # Ensure user exists
        if not self.account_service.get_user(request.username):
            self.account_service.create_user(request.username)

        # Process answers
        results = []
        correct_count = 0

        for idx, (question, user_answer) in enumerate(zip(questions, answers)):
            is_correct = abs(user_answer - question.answer) < 0.01
            if is_correct:
                correct_count += 1

            # Record in account service
            self.account_service.record_answer(
                username=request.username,
                question=question.question_text,
                equation=question.equation,
                user_answer=user_answer,
                correct_answer=question.answer,
                category=question.category or 'unknown'
            )

            # Record in quiz history service
            quiz_history = QuizHistory(
                username=request.username,
                question=question.question_text,
                user_equation=question.equation,
                user_answer=user_answer,
                correct_answer=question.answer,
                is_correct=is_correct,
                category=question.category or 'unknown',
                timestamp=datetime.now()
            )
            self.quiz_history_service.add_history(quiz_history)

            # Generate teacher feedback for wrong answers
            teacher_feedback = None
            if not is_correct:
                teacher_feedback = self.teacher_service.generate_feedback(
                    equation=question.equation,
                    question=question.question_text,
                    correct_answer=question.answer,
                    user_answer=user_answer
                )

            result_item = {
                'question_number': idx + 1,
                'question': question.question_text,
                'equation': question.equation,
                'user_answer': user_answer,
                'correct_answer': question.answer,
                'is_correct': is_correct,
                'category': question.category
            }

            # Add teacher feedback if available
            if teacher_feedback:
                result_item['teacher_feedback'] = teacher_feedback.model_dump()

            results.append(result_item)

        score = (correct_count / len(questions)) * 100 if questions else 0

        return {
            'username': request.username,
            'difficulty': request.difficulty,
            'total_questions': len(questions),
            'correct_answers': correct_count,
            'score': round(score, 2),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

    def conduct_human_exam(self, request: ExamRequest,
                           answers: List[float]) -> Dict[str, Any]:
        """
        Conduct exam for a human user

        Args:
            request: ExamRequest
            answers: List of user answers

        Returns:
            Exam results
        """
        # Generate questions
        questions = self.create_exam(request)

        # Process with the new method
        return self.process_human_exam(request, questions, answers)

    def conduct_agent_exam(self, request: ExamRequest) -> Dict[str, Any]:
        """
        Conduct exam for an AI agent

        Args:
            request: ExamRequest with agent_name specified

        Returns:
            Exam results
        """
        if not request.agent_name:
            raise ValueError("Agent name is required for agent exam")

        # Get agent configuration
        agent_config = self.agent_management.get_agent(request.agent_name)
        if not agent_config:
            raise ValueError(f"Agent '{request.agent_name}' not found")

        # Create agent instance
        agent = AgentService(agent_config)

        # Generate questions
        questions = self.create_exam(request)

        # Process with agent
        results = []
        correct_count = 0

        for idx, question in enumerate(questions):
            agent_result = agent.solve_question(request.username, question)

            is_correct = abs(agent_result['agent_answer'] - question.answer) < 0.01
            if is_correct:
                correct_count += 1

            # Record in quiz history service
            quiz_history = QuizHistory(
                username=request.username,
                question=question.question_text,
                user_equation=question.equation,
                user_answer=agent_result['agent_answer'],
                correct_answer=question.answer,
                is_correct=is_correct,
                category=question.category or 'unknown',
                timestamp=datetime.now()
            )
            self.quiz_history_service.add_history(quiz_history)

            results.append({
                'question_number': idx + 1,
                'question': question.question_text,
                'equation': question.equation,
                'agent_answer': agent_result['agent_answer'],
                'correct_answer': question.answer,
                'is_correct': is_correct,
                'category': question.category,
                'reasoning': agent_result.get('reasoning', ''),
                'used_rag': agent_result.get('used_rag', False),
                'used_classification': agent_result.get('used_classification', False)
            })

        score = (correct_count / len(questions)) * 100 if questions else 0

        return {
            'agent_name': request.agent_name,
            'username': request.username,
            'difficulty': request.difficulty,
            'total_questions': len(questions),
            'correct_answers': correct_count,
            'score': round(score, 2),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the service
    service = ExamService()

    # Create test exam
    request = ExamRequest(
        username="test_user",
        difficulty="easy",
        question_count=3
    )

    questions = service.create_exam(request)
    print(f"Generated {len(questions)} questions:")
    for idx, q in enumerate(questions, 1):
        print(f"{idx}. {q.question_text}")
        print(f"   Equation: {q.equation} = {q.answer}")
        print(f"   Category: {q.category}")
