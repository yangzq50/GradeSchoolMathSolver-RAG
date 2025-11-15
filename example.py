"""Example usage of GradeSchoolMathSolver-RAG"""

from database import init_db, SessionLocal
from problem_generator import ProblemGenerator
from answer_tracker import AnswerTracker
from llama_interface import LlamaInterface
from rag_retrieval import RAGRetrieval

def main():
    """Demonstrate the GradeSchoolMathSolver-RAG workflow"""
    
    print("=" * 60)
    print("GradeSchoolMathSolver-RAG Example")
    print("=" * 60)
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    # Create components
    generator = ProblemGenerator()
    tracker = AnswerTracker(db)
    llama = LlamaInterface()
    rag = RAGRetrieval(db)
    
    # Step 1: Generate some problems
    print("\n1. Generating practice problems...")
    from database import MathProblem
    
    problems = []
    for i in range(10):
        problem_data = generator.generate_problem(difficulty=1)
        problem = MathProblem(**problem_data)
        db.add(problem)
        db.commit()
        db.refresh(problem)
        problems.append(problem)
        print(f"   Problem {problem.id}: {problem.problem_text}")
    
    # Step 2: Simulate a student answering questions
    print("\n2. Simulating student answers...")
    correct_count = 0
    
    for i, problem in enumerate(problems[:5]):
        # Simulate: answer correctly for even indices, incorrectly for odd
        if i % 2 == 0:
            answer = problem.correct_answer
        else:
            answer = problem.correct_answer + 1
        
        result = tracker.record_answer(problem.id, answer, time_taken=3.5)
        print(f"   {problem.problem_text}")
        print(f"   Student answered: {answer}")
        print(f"   {result['feedback']}")
        
        if result['is_correct']:
            correct_count += 1
    
    # Step 3: Show statistics
    print("\n3. Performance Statistics:")
    stats = tracker.get_performance_stats()
    print(f"   Total answers: {stats['total_answers']}")
    print(f"   Correct: {stats['correct_answers']}")
    print(f"   Incorrect: {stats['incorrect_answers']}")
    print(f"   Accuracy: {stats['accuracy']:.1f}%")
    print(f"   Average time: {stats['average_time']:.2f} seconds")
    
    # Step 4: Identify weak areas
    print("\n4. Weak Areas (need more practice):")
    weak_areas = tracker.get_weak_areas()
    for area in weak_areas[:3]:
        print(f"   {area['problem_type']}: {area['accuracy']:.1f}% accuracy ({area['correct_attempts']}/{area['total_attempts']})")
    
    # Step 5: Get adaptive recommendations
    print("\n5. Adaptive Practice Recommendations:")
    recommendations = rag.get_adaptive_problems(limit=5)
    for rec in recommendations:
        print(f"   {rec['problem_text']} - {rec['reason']}")
    
    # Step 6: Get a hint for a problem
    print("\n6. Getting a hint...")
    hint_problem = problems[0]
    hint = llama.generate_hint(hint_problem.problem_text, hint_problem.problem_type)
    print(f"   Problem: {hint_problem.problem_text}")
    print(f"   Hint: {hint}")
    
    # Step 7: Get an explanation
    print("\n7. Getting an explanation...")
    explanation = llama.generate_explanation(
        hint_problem.problem_text,
        hint_problem.correct_answer,
        hint_problem.problem_type
    )
    print(f"   Problem: {hint_problem.problem_text}")
    print(f"   Explanation: {explanation}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    
    db.close()

if __name__ == "__main__":
    main()
