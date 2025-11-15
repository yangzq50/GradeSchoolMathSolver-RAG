"""Problem generator module for creating grade school math problems"""

import random
from typing import Dict, Tuple
from config import PROBLEM_TYPES, MIN_NUMBER, MAX_NUMBER

class ProblemGenerator:
    """Generates arithmetic problems for grade school students"""
    
    def __init__(self, min_num: int = MIN_NUMBER, max_num: int = MAX_NUMBER):
        self.min_num = min_num
        self.max_num = max_num
    
    def generate_addition(self, difficulty: int = 1) -> Tuple[str, float]:
        """Generate an addition problem"""
        num1 = random.randint(self.min_num, self.max_num * difficulty)
        num2 = random.randint(self.min_num, self.max_num * difficulty)
        problem = f"{num1} + {num2} = ?"
        answer = num1 + num2
        return problem, answer
    
    def generate_subtraction(self, difficulty: int = 1) -> Tuple[str, float]:
        """Generate a subtraction problem (always positive result)"""
        num1 = random.randint(self.min_num, self.max_num * difficulty)
        num2 = random.randint(self.min_num, num1)  # Ensure positive result
        problem = f"{num1} - {num2} = ?"
        answer = num1 - num2
        return problem, answer
    
    def generate_multiplication(self, difficulty: int = 1) -> Tuple[str, float]:
        """Generate a multiplication problem"""
        max_multiplier = min(12, self.max_num // 10 * difficulty)
        num1 = random.randint(self.min_num, max_multiplier)
        num2 = random.randint(self.min_num, max_multiplier)
        problem = f"{num1} × {num2} = ?"
        answer = num1 * num2
        return problem, answer
    
    def generate_division(self, difficulty: int = 1) -> Tuple[str, float]:
        """Generate a division problem with whole number results"""
        divisor = random.randint(2, 12)
        quotient = random.randint(self.min_num, self.max_num // 10 * difficulty)
        dividend = divisor * quotient
        problem = f"{dividend} ÷ {divisor} = ?"
        answer = quotient
        return problem, answer
    
    def generate_problem(self, problem_type: str = None, difficulty: int = 1) -> Dict[str, any]:
        """
        Generate a random math problem
        
        Args:
            problem_type: Type of problem (addition, subtraction, multiplication, division)
            difficulty: Difficulty level (1-5)
        
        Returns:
            Dictionary with problem_text, problem_type, correct_answer, and difficulty
        """
        if problem_type is None:
            problem_type = random.choice(PROBLEM_TYPES)
        
        if problem_type not in PROBLEM_TYPES:
            raise ValueError(f"Invalid problem type. Must be one of {PROBLEM_TYPES}")
        
        # Generate problem based on type
        if problem_type == "addition":
            problem_text, answer = self.generate_addition(difficulty)
        elif problem_type == "subtraction":
            problem_text, answer = self.generate_subtraction(difficulty)
        elif problem_type == "multiplication":
            problem_text, answer = self.generate_multiplication(difficulty)
        elif problem_type == "division":
            problem_text, answer = self.generate_division(difficulty)
        
        return {
            "problem_text": problem_text,
            "problem_type": problem_type,
            "correct_answer": float(answer),
            "difficulty": difficulty
        }
