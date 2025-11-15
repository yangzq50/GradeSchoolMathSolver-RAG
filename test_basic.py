"""Simple test script to verify the GradeSchoolMathSolver-RAG functionality"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, SessionLocal, MathProblem, Answer
from problem_generator import ProblemGenerator
from answer_tracker import AnswerTracker
from llama_interface import LlamaInterface
from rag_retrieval import RAGRetrieval

def test_problem_generator():
    """Test problem generation"""
    print("\n=== Testing Problem Generator ===")
    generator = ProblemGenerator()
    
    # Test each problem type
    for problem_type in ["addition", "subtraction", "multiplication", "division"]:
        problem = generator.generate_problem(problem_type=problem_type, difficulty=1)
        print(f"{problem_type.capitalize()}: {problem['problem_text']} = {problem['correct_answer']}")
    
    print("✓ Problem generator works!")

def test_database():
    """Test database operations"""
    print("\n=== Testing Database ===")
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    # Create a test problem
    generator = ProblemGenerator()
    problem_data = generator.generate_problem(problem_type="addition", difficulty=1)
    
    problem = MathProblem(**problem_data)
    db.add(problem)
    db.commit()
    db.refresh(problem)
    
    print(f"Saved problem: {problem.problem_text} (ID: {problem.id})")
    
    # Query it back
    retrieved = db.query(MathProblem).filter(MathProblem.id == problem.id).first()
    assert retrieved.problem_text == problem.problem_text
    
    print("✓ Database operations work!")
    
    db.close()
    return problem.id

def test_answer_tracker(problem_id):
    """Test answer tracking"""
    print("\n=== Testing Answer Tracker ===")
    
    db = SessionLocal()
    tracker = AnswerTracker(db)
    
    # Get the problem
    problem = db.query(MathProblem).filter(MathProblem.id == problem_id).first()
    print(f"Problem: {problem.problem_text}")
    
    # Submit correct answer
    result = tracker.record_answer(problem_id, problem.correct_answer, time_taken=2.5)
    print(f"Correct answer result: {result['feedback']}")
    assert result['is_correct'] == True
    
    # Submit incorrect answer
    result = tracker.record_answer(problem_id, problem.correct_answer + 1, time_taken=3.0)
    print(f"Incorrect answer result: {result['feedback']}")
    assert result['is_correct'] == False
    
    # Get stats
    stats = tracker.get_performance_stats()
    print(f"Stats: {stats}")
    
    # Get weak areas
    weak_areas = tracker.get_weak_areas()
    print(f"Weak areas: {weak_areas}")
    
    print("✓ Answer tracker works!")
    
    db.close()

def test_llama_interface():
    """Test LLaMA interface (fallback mode)"""
    print("\n=== Testing LLaMA Interface (Fallback Mode) ===")
    
    llama = LlamaInterface()
    
    # Test hint generation
    hint = llama.generate_hint("5 + 3 = ?", "addition")
    print(f"Hint: {hint}")
    
    # Test explanation generation
    explanation = llama.generate_explanation("5 + 3 = ?", 8, "addition")
    print(f"Explanation: {explanation}")
    
    print("✓ LLaMA interface works (fallback mode)!")

def test_rag_retrieval():
    """Test RAG retrieval"""
    print("\n=== Testing RAG Retrieval ===")
    
    db = SessionLocal()
    rag = RAGRetrieval(db)
    
    # Get adaptive problems
    problems = rag.get_adaptive_problems(limit=5)
    print(f"Adaptive problems: {len(problems)} problems recommended")
    
    for p in problems[:3]:
        print(f"  - {p['problem_text']} (reason: {p['reason']})")
    
    print("✓ RAG retrieval works!")
    
    db.close()

def main():
    """Run all tests"""
    print("=" * 50)
    print("GradeSchoolMathSolver-RAG Test Suite")
    print("=" * 50)
    
    try:
        # Test problem generator
        test_problem_generator()
        
        # Test database
        problem_id = test_database()
        
        # Test answer tracker
        test_answer_tracker(problem_id)
        
        # Test LLaMA interface
        test_llama_interface()
        
        # Test RAG retrieval
        test_rag_retrieval()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
