"""
Teacher Service
Provides educational feedback for incorrect answers
"""
import requests
from typing import Optional
from config import Config
from models import TeacherFeedback


class TeacherService:
    """Service for generating educational feedback on wrong answers"""
    
    def __init__(self):
        self.config = Config()
        self.enabled = self.config.TEACHER_SERVICE_ENABLED
    
    def generate_feedback(
        self,
        equation: str,
        question: str,
        correct_answer: float,
        user_answer: float
    ) -> Optional[TeacherFeedback]:
        """
        Generate feedback for a wrong answer
        
        Args:
            equation: The mathematical equation
            question: The question text
            correct_answer: The correct answer
            user_answer: The user's incorrect answer
            
        Returns:
            TeacherFeedback object with explanation, or None if service is disabled
        """
        if not self.enabled:
            return None
        
        # Try AI-based feedback first
        feedback_text = self._generate_ai_feedback(
            equation, question, correct_answer, user_answer
        )
        
        # Fallback to template-based feedback if AI fails
        if not feedback_text:
            feedback_text = self._generate_template_feedback(
                equation, question, correct_answer, user_answer
            )
        
        # Parse feedback into structured parts
        explanation = feedback_text
        feedback_summary = f"Your answer of {user_answer} is incorrect. The correct answer is {correct_answer}."
        
        return TeacherFeedback(
            equation=equation,
            question=question,
            correct_answer=correct_answer,
            user_answer=user_answer,
            feedback=feedback_summary,
            explanation=explanation
        )
    
    def _generate_ai_feedback(
        self,
        equation: str,
        question: str,
        correct_answer: float,
        user_answer: float
    ) -> Optional[str]:
        """
        Generate feedback using AI model
        
        Returns:
            Feedback text or None if AI unavailable
        """
        try:
            prompt = f"""You are a helpful math teacher. A student answered a math question incorrectly.

Question: {question}
Equation: {equation}
Student's Answer: {user_answer}
Correct Answer: {correct_answer}

Please provide:
1. A brief explanation of why the student's answer is wrong
2. Step-by-step guidance on how to solve the problem correctly
3. The correct solution process

Keep your explanation clear, encouraging, and educational. Focus on helping the student understand the concept, not just giving them the answer."""

            response = requests.post(
                f"{self.config.AI_MODEL_URL}/api/generate",
                json={
                    "model": self.config.AI_MODEL_NAME,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            
        except Exception as e:
            print(f"Error generating AI feedback: {e}")
        
        return None
    
    def _generate_template_feedback(
        self,
        equation: str,
        question: str,
        correct_answer: float,
        user_answer: float
    ) -> str:
        """
        Generate template-based feedback as fallback
        
        Returns:
            Template-based feedback text
        """
        # Determine operation type from equation
        operation = self._identify_operation(equation)
        
        # Calculate the difference between answers
        difference = abs(correct_answer - user_answer)
        
        feedback = f"""Let me help you understand where you went wrong:

**Your Answer:** {user_answer}
**Correct Answer:** {correct_answer}
**Difference:** {difference}

**How to solve this problem:**

The equation is: {equation}

"""
        
        if operation == "addition":
            feedback += """When adding numbers:
1. Line up the numbers by place value (ones, tens, hundreds)
2. Add from right to left (ones first, then tens, etc.)
3. Carry over when a column sum is 10 or more

"""
        elif operation == "subtraction":
            feedback += """When subtracting numbers:
1. Line up the numbers by place value
2. Subtract from right to left
3. Borrow from the next column when needed

"""
        elif operation == "multiplication":
            feedback += """When multiplying numbers:
1. Multiply each digit of the first number by each digit of the second
2. Line up the partial products correctly
3. Add all partial products together

"""
        elif operation == "division":
            feedback += """When dividing numbers:
1. Determine how many times the divisor fits into the dividend
2. Multiply the divisor by that number
3. Subtract from the dividend and bring down the next digit
4. Repeat until done

"""
        else:
            feedback += """When solving equations with multiple operations:
1. Follow the order of operations (PEMDAS/BODMAS)
2. Parentheses first
3. Then multiplication and division (left to right)
4. Finally addition and subtraction (left to right)

"""
        
        feedback += f"""**To get the correct answer of {correct_answer}:**
Work through the equation step by step, following the rules above. Double-check your calculations at each step!

Keep practicing, and you'll master this! 💪"""
        
        return feedback
    
    def _identify_operation(self, equation: str) -> str:
        """
        Identify the primary operation in the equation
        
        Returns:
            Operation type string
        """
        if '(' in equation:
            return "complex"
        elif '*' in equation and '+' not in equation and '-' not in equation:
            return "multiplication"
        elif '/' in equation:
            return "division"
        elif '+' in equation and '-' not in equation:
            return "addition"
        elif '-' in equation and '+' not in equation:
            return "subtraction"
        else:
            return "mixed"


if __name__ == "__main__":
    # Test the service
    service = TeacherService()
    
    # Test cases
    test_cases = [
        {
            "equation": "5 + 3",
            "question": "What is five plus three?",
            "correct_answer": 8.0,
            "user_answer": 7.0
        },
        {
            "equation": "12 - 7",
            "question": "What is twelve minus seven?",
            "correct_answer": 5.0,
            "user_answer": 6.0
        },
        {
            "equation": "6 * 4",
            "question": "What is six times four?",
            "correct_answer": 24.0,
            "user_answer": 20.0
        }
    ]
    
    print("=" * 60)
    print("Teacher Service Test")
    print("=" * 60)
    print(f"Service Enabled: {service.enabled}\n")
    
    for idx, test in enumerate(test_cases, 1):
        print(f"\nTest Case {idx}:")
        print(f"Question: {test['question']}")
        print(f"Equation: {test['equation']}")
        print(f"User Answer: {test['user_answer']}")
        print(f"Correct Answer: {test['correct_answer']}")
        
        feedback = service.generate_feedback(
            equation=test['equation'],
            question=test['question'],
            correct_answer=test['correct_answer'],
            user_answer=test['user_answer']
        )
        
        if feedback:
            print(f"\nFeedback Summary: {feedback.feedback}")
            print(f"\nExplanation:\n{feedback.explanation}")
        else:
            print("Teacher service is disabled")
        
        print("-" * 60)
