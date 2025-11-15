"""Answer tracker module for tracking student performance"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from database import MathProblem, Answer
from datetime import datetime, timedelta

class AnswerTracker:
    """Tracks and analyzes student answers"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_answer(self, problem_id: int, user_answer: float, time_taken: Optional[float] = None) -> Dict:
        """
        Record a student's answer to a problem
        
        Args:
            problem_id: ID of the problem being answered
            user_answer: The student's answer
            time_taken: Time taken to answer in seconds
        
        Returns:
            Dictionary with feedback and correctness information
        """
        # Get the problem
        problem = self.db.query(MathProblem).filter(MathProblem.id == problem_id).first()
        if not problem:
            raise ValueError(f"Problem with ID {problem_id} not found")
        
        # Check if answer is correct
        is_correct = abs(user_answer - problem.correct_answer) < 0.01
        
        # Save answer to database
        answer = Answer(
            problem_id=problem_id,
            user_answer=user_answer,
            is_correct=is_correct,
            time_taken=time_taken
        )
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        
        return {
            "answer_id": answer.id,
            "is_correct": is_correct,
            "correct_answer": problem.correct_answer,
            "user_answer": user_answer,
            "problem_text": problem.problem_text,
            "feedback": "Correct! Well done!" if is_correct else f"Incorrect. The correct answer is {problem.correct_answer}"
        }
    
    def get_performance_stats(self, days: int = 7) -> Dict:
        """
        Get performance statistics for the last N days
        
        Args:
            days: Number of days to look back
        
        Returns:
            Dictionary with performance statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all answers from the period
        answers = self.db.query(Answer).filter(Answer.timestamp >= cutoff_date).all()
        
        if not answers:
            return {
                "total_answers": 0,
                "correct_answers": 0,
                "incorrect_answers": 0,
                "accuracy": 0.0,
                "average_time": 0.0
            }
        
        total = len(answers)
        correct = sum(1 for a in answers if a.is_correct)
        incorrect = total - correct
        
        times = [a.time_taken for a in answers if a.time_taken is not None]
        avg_time = sum(times) / len(times) if times else 0.0
        
        return {
            "total_answers": total,
            "correct_answers": correct,
            "incorrect_answers": incorrect,
            "accuracy": (correct / total * 100) if total > 0 else 0.0,
            "average_time": avg_time
        }
    
    def get_weak_areas(self) -> List[Dict]:
        """
        Identify problem types where the student needs more practice
        
        Returns:
            List of problem types with low accuracy
        """
        # Get all answers
        answers = self.db.query(Answer).all()
        
        if not answers:
            return []
        
        # Group by problem type
        type_stats = {}
        for answer in answers:
            problem = self.db.query(MathProblem).filter(MathProblem.id == answer.problem_id).first()
            if problem:
                if problem.problem_type not in type_stats:
                    type_stats[problem.problem_type] = {"correct": 0, "total": 0}
                type_stats[problem.problem_type]["total"] += 1
                if answer.is_correct:
                    type_stats[problem.problem_type]["correct"] += 1
        
        # Calculate accuracy and identify weak areas
        weak_areas = []
        for problem_type, stats in type_stats.items():
            accuracy = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
            weak_areas.append({
                "problem_type": problem_type,
                "accuracy": accuracy,
                "total_attempts": stats["total"],
                "correct_attempts": stats["correct"]
            })
        
        # Sort by accuracy (lowest first)
        weak_areas.sort(key=lambda x: x["accuracy"])
        
        return weak_areas
