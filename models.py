"""
Data models for the GradeSchoolMathSolver-RAG system
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


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
