"""
Data models for the GradeSchoolMathSolver-RAG system
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class Question(BaseModel):
    """Math question model"""
    equation: str
    question_text: str
    answer: float
    difficulty: str
    category: Optional[str] = None


class UserAnswer(BaseModel):
    """User's answer to a question"""
    username: str
    question: str
    equation: str
    user_answer: float
    correct_answer: float
    is_correct: bool
    category: str
    timestamp: datetime


class UserStats(BaseModel):
    """User statistics model"""
    username: str
    total_questions: int
    correct_answers: int
    overall_correctness: float
    recent_100_score: float


class QuizHistory(BaseModel):
    """Quiz history record for RAG"""
    username: str
    question: str
    user_equation: str
    user_answer: float
    correct_answer: float
    is_correct: bool
    category: str
    timestamp: datetime


class AgentConfig(BaseModel):
    """AI Agent configuration"""
    name: str
    use_classification: bool = False
    use_rag: bool = False
    rag_top_k: int = 5
    include_incorrect_history: bool = True


class ExamRequest(BaseModel):
    """Exam request model"""
    username: str
    difficulty: str
    question_count: int
    agent_name: Optional[str] = None


class RevealStrategy(str, Enum):
    """Reveal strategy for immersive exams"""
    NONE = "none"
    REVEAL_ALL_AFTER_ROUND = "reveal_all_after_round"
    REVEAL_TO_LATER_PARTICIPANTS = "reveal_to_later_participants"


class ParticipantType(str, Enum):
    """Type of participant"""
    HUMAN = "human"
    AGENT = "agent"


class ImmersiveExamConfig(BaseModel):
    """Configuration for an immersive exam"""
    exam_mode: str = "immersive"
    difficulty_distribution: Dict[str, int]  # e.g., {"easy": 3, "medium": 4, "hard": 3}
    reveal_strategy: RevealStrategy = RevealStrategy.NONE
    time_per_question: Optional[int] = None  # seconds, None for no time limit


class ImmersiveParticipant(BaseModel):
    """Participant in an immersive exam"""
    participant_id: str  # username or agent_name
    participant_type: ParticipantType
    order: int  # Position in answering order
    answers: List[Optional[float]] = []  # Answers submitted for each question
    scores: List[bool] = []  # Correctness for each question
    total_score: float = 0.0
    has_answered_current: bool = False


class ImmersiveExam(BaseModel):
    """Immersive exam state"""
    exam_id: str
    config: ImmersiveExamConfig
    questions: List[Question]
    participants: List[ImmersiveParticipant] = []
    current_question_index: int = 0
    status: str = "waiting"  # waiting, in_progress, completed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ImmersiveExamAnswer(BaseModel):
    """Answer submission for immersive exam"""
    exam_id: str
    participant_id: str
    question_index: int
    answer: float


class ImmersiveExamStatus(BaseModel):
    """Status response for immersive exam"""
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
    """Feedback from teacher service for wrong answers"""
    equation: str
    question: str
    correct_answer: float
    user_answer: float
    feedback: str
    explanation: str
