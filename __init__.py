"""GradeSchoolMathSolver-RAG - AI-powered Grade School Math Solver with RAG"""

__version__ = "1.0.0"
__author__ = "GradeSchoolMathSolver-RAG Team"

from .problem_generator import ProblemGenerator
from .answer_tracker import AnswerTracker
from .llama_interface import LlamaInterface
from .rag_retrieval import RAGRetrieval
from .database import init_db, get_db, MathProblem, Answer

__all__ = [
    "ProblemGenerator",
    "AnswerTracker",
    "LlamaInterface",
    "RAGRetrieval",
    "init_db",
    "get_db",
    "MathProblem",
    "Answer",
]
