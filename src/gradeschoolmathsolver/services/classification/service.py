"""
Question Classification Service
Classifies math questions into predefined categories with robust error handling
"""
import re
import requests
from requests.exceptions import RequestException, Timeout
from gradeschoolmathsolver.config import Config


class ClassificationService:
    """
    Service for classifying math questions

    This service classifies mathematical equations into categories using either
    rule-based pattern matching or AI-based classification with fallback support.

    Attributes:
        config: Configuration object
        categories: List of valid question categories
        timeout: API request timeout in seconds
    """

    def __init__(self, timeout: int = 30):
        self.config = Config()
        self.categories = self.config.QUESTION_CATEGORIES
        self.timeout = timeout

    def classify_question(self, equation: str, use_ai: bool = False) -> str:
        """
        Classify a math question into a category

        Args:
            equation: The mathematical equation (string)
            use_ai: Whether to use AI model for classification

        Returns:
            Category name (always returns a valid category)
        """
        if not equation or not isinstance(equation, str):
            return 'mixed_operations'  # Default fallback

        if use_ai:
            return self._classify_with_ai(equation)
        else:
            return self._classify_rule_based(equation)

    def _classify_rule_based(self, equation: str) -> str:
        """
        Rule-based classification using pattern matching

        Args:
            equation: The mathematical equation

        Returns:
            Category name
        """
        # Check for parentheses
        if '(' in equation or ')' in equation:
            return 'parentheses'

        # Check for division
        if '/' in equation:
            # Check if it's a fraction
            if re.search(r'\d+/\d+(?!\d)', equation):
                return 'fractions'
            return 'division'

        # Count different operations
        has_add = '+' in equation
        has_sub = '-' in equation and not equation.startswith('-')
        has_mult = '*' in equation

        operations_count = sum([has_add, has_sub, has_mult])

        # Multiple operations
        if operations_count > 1:
            return 'mixed_operations'

        # Single operations
        if has_mult:
            return 'multiplication'
        elif has_add:
            return 'addition'
        elif has_sub:
            return 'subtraction'

        return 'mixed_operations'

    def _classify_with_ai(self, equation: str) -> str:
        """
        Classify using AI model with fallback to rule-based classification

        Args:
            equation: The mathematical equation

        Returns:
            Category name (guaranteed to be valid)
        """
        categories_str = ", ".join(self.categories)
        prompt = f"""Classify the following math equation into ONE of these categories: {categories_str}

Equation: {equation}

Respond with ONLY the category name, nothing else."""

        try:
            # Use OpenAI-compatible chat/completions API
            response = requests.post(
                f"{self.config.AI_MODEL_URL}/engines/{self.config.LLM_ENGINE}/v1/chat/completions",
                json={
                    "model": self.config.AI_MODEL_NAME,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful math classification assistant."
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
                # Extract content from OpenAI-compatible response
                choices = result.get('choices', [])
                if choices:
                    category = str(choices[0].get('message', {}).get('content', '')).strip().lower()
                    # Validate the category
                    if category in self.categories:
                        return category

        except Timeout:
            print("Timeout classifying with AI, falling back to rule-based")
        except RequestException as e:
            print(f"API error classifying with AI: {e}, falling back to rule-based")
        except Exception as e:
            print(f"Unexpected error classifying with AI: {e}, falling back to rule-based")

        # Fallback to rule-based
        return self._classify_rule_based(equation)


if __name__ == "__main__":
    # Test the service
    service = ClassificationService()

    test_equations = [
        "5 + 3",
        "10 - 4",
        "6 * 7",
        "12 / 4",
        "5 + 3 - 2",
        "(4 + 5) * 2",
        "3/4 + 1/2"
    ]

    print("Rule-based Classification:")
    for eq in test_equations:
        category = service.classify_question(eq, use_ai=False)
        print(f"{eq} -> {category}")
