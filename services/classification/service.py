"""
Question Classification Service
Classifies math questions into predefined categories
"""
import re
import requests
from config import Config


class ClassificationService:
    """Service for classifying math questions"""

    def __init__(self):
        self.config = Config()
        self.categories = self.config.QUESTION_CATEGORIES

    def classify_question(self, equation: str, use_ai: bool = False) -> str:
        """
        Classify a math question into a category

        Args:
            equation: The mathematical equation
            use_ai: Whether to use AI model for classification

        Returns:
            Category name
        """
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
        Classify using AI model

        Args:
            equation: The mathematical equation

        Returns:
            Category name
        """
        categories_str = ", ".join(self.categories)
        prompt = f"""Classify the following math equation into ONE of these categories: {categories_str}

Equation: {equation}

Respond with ONLY the category name, nothing else."""

        try:
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
                category = result.get('response', '').strip().lower()

                # Validate the category
                if category in self.categories:
                    return category

        except Exception as e:
            print(f"Error classifying with AI: {e}")

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
