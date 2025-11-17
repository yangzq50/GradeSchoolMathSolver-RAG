"""
QA Generation Service
Generates grade school math quiz problems based on difficulty level with retry logic
"""
import random
from typing import Tuple
import requests
from requests.exceptions import RequestException, Timeout
from models import Question
from config import Config


def format_number(value: float) -> str:
    """
    Format a number to display as integer if it's a whole number, otherwise as float.

    Args:
        value: The number to format

    Returns:
        String representation of the number
    """
    if value == int(value):
        return str(int(value))
    return str(value)


class QAGenerationService:
    """
    Service for generating math questions

    This service generates mathematical equations and converts them to natural language
    questions using AI models with fallback to template-based generation.

    Attributes:
        config: Configuration object
        max_retries: Maximum number of API retry attempts
        timeout: API request timeout in seconds
    """

    def __init__(self, max_retries: int = 3, timeout: int = 30):
        self.config = Config()
        self.max_retries = max_retries
        self.timeout = timeout

    def generate_equation(self, difficulty: str) -> Tuple[str, int]:
        """
        Generate a mathematical equation based on difficulty level

        Args:
            difficulty: 'easy', 'medium', or 'hard'

        Returns:
            Tuple of (equation_string, answer)

        Raises:
            ValueError: If difficulty level is invalid
        """
        if difficulty not in ['easy', 'medium', 'hard']:
            raise ValueError(f"Invalid difficulty: {difficulty}. Must be 'easy', 'medium', or 'hard'")

        if difficulty == 'easy':
            return self._generate_easy_equation()
        elif difficulty == 'medium':
            return self._generate_medium_equation()
        else:
            return self._generate_hard_equation()

    def _generate_easy_equation(self) -> Tuple[str, int]:
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

        return equation, answer

    def _generate_medium_equation(self) -> Tuple[str, int]:
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

        return equation, answer

    def _generate_hard_equation(self) -> Tuple[str, int]:
        """Generate hard equations: parentheses, division, larger numbers"""
        num1 = random.randint(2, 20)
        num2 = random.randint(2, 20)
        num3 = random.randint(1, 10)

        equation_type = random.choice(['parentheses_div', 'complex_mult', 'multi_op'])

        if equation_type == 'parentheses_div':
            # Ensure clean division
            # Use (num2 * num1 + num3 * num1) / num1 = num2 + num3
            equation = f"{num2 * num1} + {num3 * num1} / {num1}"
            answer = num2 + num3
        elif equation_type == 'complex_mult':
            equation = f"({num1} + {num2}) * {num3}"
            answer = (num1 + num2) * num3
        else:
            # Multiple operations with parentheses
            num4 = random.randint(1, 20)
            equation = f"{num1} * ({num2} + {num3}) - {num4}"
            answer = num1 * (num2 + num3) - num4

        return equation, answer

    def _try_ai_question_generation(self, prompt: str) -> str:
        """
        Try to generate question using AI API

        Args:
            prompt: Prompt for the AI model

        Returns:
            Generated question text or empty string if failed
        """
        try:
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
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                choices = result.get('choices', [])
                if choices:
                    content = choices[0].get('message', {}).get('content', '').strip()
                    if content:
                        return content
            return ""
        except (Timeout, RequestException):
            return ""

    def generate_question_text(self, equation: str, answer: int) -> str:
        """
        Generate natural language question from equation using AI model with retry logic

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

        # Try with AI model first with retries
        for attempt in range(self.max_retries):
            result = self._try_ai_question_generation(prompt)
            if result:
                return result

            if attempt < self.max_retries - 1:
                print(f"AI generation attempt {attempt + 1}/{self.max_retries} failed, retrying...")

        # Fallback if all retries fail
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
