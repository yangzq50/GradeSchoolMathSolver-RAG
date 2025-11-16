"""
QA Generation Service
Generates grade school math quiz problems based on difficulty level
"""
import random
from typing import Tuple
import requests
from models import Question
from config import Config


class QAGenerationService:
    """Service for generating math questions"""

    def __init__(self):
        self.config = Config()

    def generate_equation(self, difficulty: str) -> Tuple[str, float]:
        """
        Generate a mathematical equation based on difficulty level

        Args:
            difficulty: 'easy', 'medium', or 'hard'

        Returns:
            Tuple of (equation_string, answer)
        """
        if difficulty == 'easy':
            return self._generate_easy_equation()
        elif difficulty == 'medium':
            return self._generate_medium_equation()
        else:
            return self._generate_hard_equation()

    def _generate_easy_equation(self) -> Tuple[str, float]:
        """Generate easy equations: single operation, small numbers (1-20)"""
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 20)
        operation = random.choice(['+', '-'])

        if operation == '+':
            equation = f"{num1} + {num2}"
            answer = num1 + num2
        else:
            # Ensure no negative results for easy level
            if num1 < num2:
                num1, num2 = num2, num1
            equation = f"{num1} - {num2}"
            answer = num1 - num2

        return equation, float(answer)

    def _generate_medium_equation(self) -> Tuple[str, float]:
        """Generate medium equations: multiple operations, numbers (1-50)"""
        num1 = random.randint(1, 50)
        num2 = random.randint(1, 50)
        num3 = random.randint(1, 20)

        operation_type = random.choice(['add_sub', 'mult_add', 'mult_sub'])

        if operation_type == 'add_sub':
            equation = f"{num1} + {num2} - {num3}"
            answer = num1 + num2 - num3
        elif operation_type == 'mult_add':
            equation = f"{num1} * {num2} + {num3}"
            answer = num1 * num2 + num3
        else:
            equation = f"{num1} * {num2} - {num3}"
            answer = num1 * num2 - num3

        return equation, float(answer)

    def _generate_hard_equation(self) -> Tuple[str, float]:
        """Generate hard equations: parentheses, division, larger numbers"""
        num1 = random.randint(2, 20)
        num2 = random.randint(2, 20)
        num3 = random.randint(1, 10)

        equation_type = random.choice(['parentheses_div', 'complex_mult', 'multi_op'])

        if equation_type == 'parentheses_div':
            # Ensure clean division
            product = num1 * num3
            equation = f"({num2} + {product}) / {num1}"
            answer = (num2 + product) / num1
        elif equation_type == 'complex_mult':
            equation = f"({num1} + {num2}) * {num3}"
            answer = (num1 + num2) * num3
        else:
            # Multiple operations with parentheses
            equation = f"{num1} * ({num2} + {num3}) - {random.randint(1, 20)}"
            answer = eval(equation)

        return equation, float(answer)

    def generate_question_text(self, equation: str, answer: float) -> str:
        """
        Generate natural language question from equation using AI model

        Args:
            equation: Mathematical equation
            answer: Correct answer

        Returns:
            Natural language question text
        """
        prompt = f"""Generate a simple, clear word problem for this math equation: {equation} = {answer}

The word problem should:
- Be appropriate for grade school students
- Use real-world scenarios (e.g., apples, toys, money, etc.)
- Be easy to understand
- Lead naturally to the equation

Only provide the word problem text, nothing else."""

        try:
            # Use OpenAI-compatible chat/completions API
            response = requests.post(
                f"{self.config.AI_MODEL_URL}/engines/{self.config.LLM_ENGINE}/v1/chat/completions",
                json={
                    "model": self.config.AI_MODEL_NAME,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful math teacher creating grade school word problems."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                # Extract content from OpenAI-compatible response
                choices = result.get('choices', [])
                if choices:
                    return choices[0].get('message', {}).get('content', '').strip()
                else:
                    # Fallback to simple template
                    return self._generate_simple_question(equation)
            else:
                # Fallback to simple template
                return self._generate_simple_question(equation)

        except Exception as e:
            print(f"Error generating question with AI: {e}")
            return self._generate_simple_question(equation)

    def _generate_simple_question(self, equation: str) -> str:
        """Fallback method to generate simple question without AI"""
        templates = [
            f"What is the result of {equation}?",
            f"Calculate: {equation}",
            f"Solve the following: {equation}",
            f"What does {equation} equal?"
        ]
        return random.choice(templates)

    def generate_question(self, difficulty: str) -> Question:
        """
        Generate a complete question with equation, text, and answer

        Args:
            difficulty: 'easy', 'medium', or 'hard'

        Returns:
            Question object
        """
        equation, answer = self.generate_equation(difficulty)
        question_text = self.generate_question_text(equation, answer)

        return Question(
            equation=equation,
            question_text=question_text,
            answer=answer,
            difficulty=difficulty
        )


if __name__ == "__main__":
    # Test the service
    service = QAGenerationService()

    for difficulty in ['easy', 'medium', 'hard']:
        print(f"\n{difficulty.upper()} Question:")
        question = service.generate_question(difficulty)
        print(f"Equation: {question.equation} = {question.answer}")
        print(f"Question: {question.question_text}")
