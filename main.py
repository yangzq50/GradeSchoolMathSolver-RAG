"""FastAPI application for GradeSchoolMathSolver-RAG"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from database import init_db, get_db, MathProblem, Answer
from problem_generator import ProblemGenerator
from answer_tracker import AnswerTracker
from llama_interface import LlamaInterface
from rag_retrieval import RAGRetrieval
from config import API_HOST, API_PORT

# Initialize FastAPI app
app = FastAPI(
    title="GradeSchoolMathSolver-RAG API",
    description="AI-powered Grade School Math Solver with RAG",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
problem_generator = ProblemGenerator()
llama_interface = LlamaInterface()

# Pydantic models for API
class ProblemRequest(BaseModel):
    problem_type: Optional[str] = None
    difficulty: int = 1

class AnswerSubmission(BaseModel):
    problem_id: int
    user_answer: float
    time_taken: Optional[float] = None

class HintRequest(BaseModel):
    problem_id: int

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and components on startup"""
    init_db()
    print("Database initialized")
    
    # Note: LLaMA and RAG initialization is lazy to avoid startup delays
    # They will initialize on first use

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to GradeSchoolMathSolver-RAG API",
        "version": "1.0.0",
        "endpoints": {
            "generate_problem": "/api/problem/generate",
            "submit_answer": "/api/answer/submit",
            "get_hint": "/api/problem/hint",
            "get_stats": "/api/stats",
            "get_weak_areas": "/api/stats/weak-areas",
            "get_adaptive_problems": "/api/problem/adaptive"
        }
    }

@app.post("/api/problem/generate")
async def generate_problem(request: ProblemRequest, db: Session = Depends(get_db)):
    """
    Generate a new math problem
    
    Args:
        problem_type: Type of problem (addition, subtraction, multiplication, division)
        difficulty: Difficulty level (1-5)
    
    Returns:
        Generated problem details
    """
    try:
        # Generate problem
        problem_data = problem_generator.generate_problem(
            problem_type=request.problem_type,
            difficulty=request.difficulty
        )
        
        # Save to database
        problem = MathProblem(**problem_data)
        db.add(problem)
        db.commit()
        db.refresh(problem)
        
        # Index in RAG system
        rag = RAGRetrieval(db)
        rag.initialize()
        rag.index_problem(problem)
        
        return {
            "problem_id": problem.id,
            "problem_text": problem.problem_text,
            "problem_type": problem.problem_type,
            "difficulty": problem.difficulty
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/answer/submit")
async def submit_answer(submission: AnswerSubmission, db: Session = Depends(get_db)):
    """
    Submit an answer to a problem
    
    Args:
        problem_id: ID of the problem
        user_answer: Student's answer
        time_taken: Time taken to answer (optional)
    
    Returns:
        Feedback on the answer
    """
    try:
        tracker = AnswerTracker(db)
        result = tracker.record_answer(
            problem_id=submission.problem_id,
            user_answer=submission.user_answer,
            time_taken=submission.time_taken
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/problem/hint")
async def get_hint(request: HintRequest, db: Session = Depends(get_db)):
    """
    Get a hint for a problem
    
    Args:
        problem_id: ID of the problem
    
    Returns:
        Hint text
    """
    try:
        problem = db.query(MathProblem).filter(MathProblem.id == request.problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        # Initialize LLaMA interface if needed
        llama_interface.initialize()
        
        hint = llama_interface.generate_hint(
            problem_text=problem.problem_text,
            problem_type=problem.problem_type
        )
        
        return {"hint": hint}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/problem/{problem_id}/explanation")
async def get_explanation(problem_id: int, db: Session = Depends(get_db)):
    """
    Get an explanation for a problem
    
    Args:
        problem_id: ID of the problem
    
    Returns:
        Step-by-step explanation
    """
    try:
        problem = db.query(MathProblem).filter(MathProblem.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        # Initialize LLaMA interface if needed
        llama_interface.initialize()
        
        explanation = llama_interface.generate_explanation(
            problem_text=problem.problem_text,
            correct_answer=problem.correct_answer,
            problem_type=problem.problem_type
        )
        
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats(days: int = 7, db: Session = Depends(get_db)):
    """
    Get performance statistics
    
    Args:
        days: Number of days to look back (default: 7)
    
    Returns:
        Performance statistics
    """
    try:
        tracker = AnswerTracker(db)
        stats = tracker.get_performance_stats(days=days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/weak-areas")
async def get_weak_areas(db: Session = Depends(get_db)):
    """
    Get weak areas where more practice is needed
    
    Returns:
        List of problem types with accuracy statistics
    """
    try:
        tracker = AnswerTracker(db)
        weak_areas = tracker.get_weak_areas()
        return {"weak_areas": weak_areas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/problem/adaptive")
async def get_adaptive_problems(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get adaptive problems based on performance
    
    Args:
        limit: Maximum number of problems to return
    
    Returns:
        List of recommended problems
    """
    try:
        rag = RAGRetrieval(db)
        rag.initialize()
        problems = rag.get_adaptive_problems(limit=limit)
        return {"problems": problems}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/problem/{problem_id}")
async def get_problem(problem_id: int, db: Session = Depends(get_db)):
    """
    Get a specific problem by ID
    
    Args:
        problem_id: ID of the problem
    
    Returns:
        Problem details
    """
    try:
        problem = db.query(MathProblem).filter(MathProblem.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        return {
            "problem_id": problem.id,
            "problem_text": problem.problem_text,
            "problem_type": problem.problem_type,
            "difficulty": problem.difficulty
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/problems")
async def list_problems(
    skip: int = 0,
    limit: int = 10,
    problem_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List problems with optional filtering
    
    Args:
        skip: Number of problems to skip
        limit: Maximum number of problems to return
        problem_type: Filter by problem type
    
    Returns:
        List of problems
    """
    try:
        query = db.query(MathProblem)
        
        if problem_type:
            query = query.filter(MathProblem.problem_type == problem_type)
        
        problems = query.offset(skip).limit(limit).all()
        
        return {
            "problems": [{
                "problem_id": p.id,
                "problem_text": p.problem_text,
                "problem_type": p.problem_type,
                "difficulty": p.difficulty
            } for p in problems]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
