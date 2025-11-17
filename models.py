"""
Data models for the GradeSchoolMathSolver-RAG system

This module defines all Pydantic models used throughout the application for:
- Question generation and representation
- User management and statistics
- Quiz history and RAG functionality
- Agent (RAG bot) configuration
- Immersive exam management
- Teacher feedback
- Mistake review tracking
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class Question(BaseModel):
    """
    Represents a math question with its metadata

    Attributes:
        equation: Mathematical equation (e.g., "5 + 3")
        question_text: Natural language question text
        answer: Correct numerical answer
        difficulty: Difficulty level ('easy', 'medium', or 'hard')
        category: Optional category classification
    """
    equation: str
    question_text: str
    answer: int
    difficulty: str
    category: Optional[str] = None


class UserAnswer(BaseModel):
    """
    Represents a user's submitted answer to a question

    Attributes:
        username: User's unique identifier
        question: Question text that was answered
        equation: Mathematical equation that was answered
        user_answer: User's submitted answer
        correct_answer: Correct answer for validation
        is_correct: Whether the user's answer was correct
        category: Question category
        timestamp: When the answer was submitted
    """
    username: str
    question: str
    equation: str
    user_answer: float
    correct_answer: float
    is_correct: bool
    category: str
    timestamp: datetime


class UserStats(BaseModel):
    """
    Represents user performance statistics

    Attributes:
        username: User's unique identifier
        total_questions: Total number of questions answered
        correct_answers: Number of correct answers
        overall_correctness: Overall correctness percentage (0-100)
        recent_100_score: Correctness percentage for last 100 questions
    """
    username: str
    total_questions: int
    correct_answers: int
    overall_correctness: float
    recent_100_score: float


class QuizHistory(BaseModel):
    """
    Quiz history record for RAG (Retrieval-Augmented Generation)

    This model stores historical question-answer pairs for similarity search
    and personalized learning recommendations.

    Attributes:
        username: User's unique identifier
        question: Question text
        user_equation: Equation used for the question
        user_answer: User's submitted answer
        correct_answer: Correct answer
        is_correct: Whether the answer was correct
        category: Question category
        timestamp: When the question was answered
    """
    username: str
    question: str
    user_equation: str
    user_answer: float
    correct_answer: float
    is_correct: bool
    category: str
    timestamp: datetime


class AgentConfig(BaseModel):
    """
    Configuration for a RAG bot (agent)

    Attributes:
        name: Unique agent identifier
        use_classification: Whether to classify questions before solving
        use_rag: Whether to use retrieval-augmented generation
        rag_top_k: Number of similar questions to retrieve (default: 5)
        include_incorrect_history: Whether to include incorrect answers in RAG
    """
    name: str
    use_classification: bool = False
    use_rag: bool = False
    rag_top_k: int = Field(default=5, ge=1, le=20)
    include_incorrect_history: bool = True


class ExamRequest(BaseModel):
    """
    Request model for creating an exam

    Attributes:
        username: User taking the exam
        difficulty: Difficulty level ('easy', 'medium', or 'hard')
        question_count: Number of questions in the exam (1-20)
        agent_name: Optional agent name for bot exams
    """
    username: str
    difficulty: str
    question_count: int = Field(ge=1, le=20)
    agent_name: Optional[str] = None


class RevealStrategy(str, Enum):
    """
    Strategy for revealing answers in immersive exams

    - NONE: No participant sees others' answers
    - REVEAL_ALL_AFTER_ROUND: Everyone sees all answers after each round
    - REVEAL_TO_LATER_PARTICIPANTS: Later participants see earlier answers
    """
    NONE = "none"
    REVEAL_ALL_AFTER_ROUND = "reveal_all_after_round"
    REVEAL_TO_LATER_PARTICIPANTS = "reveal_to_later_participants"


class ParticipantType(str, Enum):
    """
    Type of exam participant

    - HUMAN: Human user
    - AGENT: AI agent/bot
    """
    HUMAN = "human"
    AGENT = "agent"


class ImmersiveExamConfig(BaseModel):
    """
    Configuration for an immersive (synchronized) exam

    Attributes:
        exam_mode: Mode identifier (always "immersive")
        difficulty_distribution: Dict mapping difficulty to question count
        reveal_strategy: Strategy for revealing other participants' answers
        time_per_question: Optional time limit per question in seconds
    """
    exam_mode: str = "immersive"
    difficulty_distribution: Dict[str, int]
    reveal_strategy: RevealStrategy = RevealStrategy.NONE
    time_per_question: Optional[int] = Field(default=None, ge=10)


class ImmersiveParticipant(BaseModel):
    """
    Participant in an immersive exam

    Attributes:
        participant_id: Username or agent name
        participant_type: Type of participant (human or agent)
        order: Position in answering order (0-indexed)
        answers: List of submitted answers (None if not yet answered)
        scores: List of correctness for each answer
        total_score: Total number of correct answers
        has_answered_current: Whether participant answered current question
    """
    participant_id: str
    participant_type: ParticipantType
    order: int = Field(ge=0)
    answers: List[Optional[float]] = []
    scores: List[bool] = []
    total_score: float = 0.0
    has_answered_current: bool = False


class ImmersiveExam(BaseModel):
    """
    Complete state of an immersive exam

    Attributes:
        exam_id: Unique exam identifier (UUID)
        config: Exam configuration
        questions: List of questions for the exam
        participants: List of registered participants
        current_question_index: Index of current question (0-indexed)
        status: Exam status ('waiting', 'in_progress', 'completed')
        created_at: When the exam was created
        started_at: When the exam started (None if not started)
        completed_at: When the exam completed (None if not completed)
    """
    exam_id: str
    config: ImmersiveExamConfig
    questions: List[Question]
    participants: List[ImmersiveParticipant] = []
    current_question_index: int = Field(default=0, ge=0)
    status: str = "waiting"
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ImmersiveExamAnswer(BaseModel):
    """
    Answer submission for an immersive exam

    Attributes:
        exam_id: Exam identifier
        participant_id: Participant identifier
        question_index: Index of question being answered
        answer: Submitted numerical answer
    """
    exam_id: str
    participant_id: str
    question_index: int = Field(ge=0)
    answer: float


class ImmersiveExamStatus(BaseModel):
    """
    Status response for an immersive exam

    Provides current state information for a specific participant.

    Attributes:
        exam_id: Exam identifier
        status: Current exam status
        current_question_index: Index of current question
        total_questions: Total number of questions in exam
        current_question: Current question object (None if exam complete)
        time_remaining: Seconds remaining for current question
        participants_answered: Number who answered current question
        total_participants: Total number of participants
        can_see_previous_answers: Whether participant can see others' answers
        previous_answers: List of visible previous answers
    """
    exam_id: str
    status: str
    current_question_index: int
    total_questions: int
    current_question: Optional[Question] = None
    time_remaining: Optional[int] = None
    participants_answered: int = 0
    total_participants: int = 0
    can_see_previous_answers: bool = False
    previous_answers: List[Dict[str, Any]] = []


class TeacherFeedback(BaseModel):
    """
    Educational feedback for incorrect answers

    Attributes:
        equation: Mathematical equation that was answered
        question: Question text
        correct_answer: Correct answer
        user_answer: User's incorrect answer
        feedback: Brief feedback message
        explanation: Detailed step-by-step explanation
    """
    equation: str
    question: str
    correct_answer: float
    user_answer: float
    feedback: str
    explanation: str


class MistakeReview(BaseModel):
    """
    Record of a mistake available for review

    Attributes:
        mistake_id: Unique identifier for the mistake
        username: User who made the mistake
        question: Question text
        equation: Mathematical equation
        user_answer: User's incorrect answer
        correct_answer: Correct answer
        category: Question category
        timestamp: When the mistake was made
        reviewed: Whether the mistake has been reviewed
    """
    mistake_id: int
    username: str
    question: str
    equation: str
    user_answer: float
    correct_answer: float
    category: str
    timestamp: datetime
    reviewed: bool


class MistakeReviewRequest(BaseModel):
    """
    Request to mark a mistake as reviewed

    Attributes:
        username: User requesting to mark as reviewed
        mistake_id: ID of the mistake to mark as reviewed
    """
    username: str
    mistake_id: int
