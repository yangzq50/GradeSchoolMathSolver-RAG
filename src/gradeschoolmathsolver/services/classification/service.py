"""
Question Classification Service
Classifies math questions into predefined categories with robust error handling
"""
import re
from gradeschoolmathsolver.config import Config
from gradeschoolmathsolver import model_access


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
            # Use centralized model access
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful math classification assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response_text = model_access.generate_text_completion(messages, timeout=self.timeout)
            
            if response_text:
                category = response_text.strip().lower()
                # Validate the category
                if category in self.categories:
                    return category

        except Exception as e:
            print(f"Error classifying with AI: {e}, falling back to rule-based")

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
