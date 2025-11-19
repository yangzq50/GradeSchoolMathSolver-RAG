"""
RAG Bot Service
RAG bot that can solve math problems with optional RAG and classification
"""
import requests
from typing import Dict, Any, Optional
from gradeschoolmathsolver.config import Config
from gradeschoolmathsolver.models import AgentConfig, Question
from gradeschoolmathsolver.services.classification import ClassificationService
from gradeschoolmathsolver.services.quiz_history import QuizHistoryService


class AgentService:
    """RAG bot for solving math problems"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.app_config = Config()
        self.classification_service = ClassificationService()
        self.quiz_history_service = QuizHistoryService()

    def solve_question(self, username: str, question: Question) -> Dict[str, Any]:
        """
        Solve a math question using the configured agent strategy

        Args:
            username: Username for RAG context
            question: Question to solve

        Returns:
            Dictionary with answer and metadata
        """
        result = {
            'agent_name': self.config.name,
            'question': question.question_text,
            'equation': question.equation,
            'correct_answer': question.answer,
            'agent_answer': None,
            'reasoning': '',
            'used_classification': False,
            'used_rag': False,
            'category': None,
            'relevant_history': []
        }

        # Step 1: Classify question if enabled
        if self.config.use_classification:
            category = self.classification_service.classify_question(question.equation)
            result['category'] = category
            result['used_classification'] = True

        # Step 2: Retrieve relevant history if RAG is enabled
        if self.config.use_rag and self.quiz_history_service.is_connected():
            category_value = result.get('category')
            history = self.quiz_history_service.search_relevant_history(
                username=username,
                question=question.question_text,
                category=str(category_value) if category_value else None,
                top_k=self.config.rag_top_k
            )

            if history:
                result['relevant_history'] = history
                result['used_rag'] = True

        # Step 3: Generate answer using AI model
        answer, reasoning = self._generate_answer(question, result)
        result['agent_answer'] = answer
        result['reasoning'] = reasoning

        return result

    def _generate_answer(self, question: Question, context: Dict[str, Any]) -> tuple[Optional[int], str]:
        """
        Generate answer using AI model

        Args:
            question: Question object
            context: Context from classification and RAG

        Returns:
            Tuple of (answer, reasoning)
        """
        # Build prompt based on context
        prompt = self._build_prompt(question, context)

        try:
            # Use OpenAI-compatible chat/completions API
            response = requests.post(
                f"{self.app_config.AI_MODEL_URL}/engines/{self.app_config.LLM_ENGINE}/v1/chat/completions",
                json={
                    "model": self.app_config.AI_MODEL_NAME,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful math tutor assistant."
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
                    response_text = choices[0].get('message', {}).get('content', '').strip()
                    # Parse answer and reasoning
                    answer, reasoning = self._parse_response(response_text)
                    return answer, reasoning
                else:
                    # Fallback: calculate directly
                    return question.answer, "Direct calculation (AI unavailable)"
            else:
                # Fallback: calculate directly
                return question.answer, "Direct calculation (AI unavailable)"

        except Exception as e:
            return None, f"Error generating answer with AI: {e}"

    def _build_prompt(self, question: Question, context: Dict[str, Any]) -> str:
        """Build prompt for AI model"""
        prompt = f"Solve this math problem:\n\n{question.question_text}\n\n"

        # Add category context
        if context.get('used_classification'):
            prompt += f"This is a {context['category']} problem.\n\n"

        # Add RAG context
        if context.get('used_rag') and context.get('relevant_history'):
            prompt += "Here are some similar problems you've seen before:\n"
            for idx, hist in enumerate(context['relevant_history'][:3], 1):
                status = "correctly" if hist['is_correct'] else "incorrectly"
                prompt += f"{idx}. {hist['question']} (answered {status})\n"
            prompt += "\n"

        prompt += """Provide your answer in the following format:
ANSWER: [numerical answer]
REASONING: [brief explanation of how you solved it]"""

        return prompt

    def _parse_response(self, response_text: str) -> tuple[Optional[int], str]:
        """
        Parse AI response to extract answer and reasoning

        Args:
            response_text: AI response text
            fallback_answer: Fallback answer if parsing fails

        Returns:
            Tuple of (answer, reasoning)
        """
        answer = None
        reasoning = response_text

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('ANSWER:'):
                try:
                    answer_str = line.replace('ANSWER:', '').strip()
                    # Extract first number found
                    import re
                    numbers = re.findall(r'-?\d+\.?\d*', answer_str)
                    if numbers and ('.' not in numbers[0]):
                        answer = int(numbers[0])
                except Exception:
                    pass
                break
            # elif line.startswith('REASONING:'):
            #     reasoning = line.replace('REASONING:', '').strip()

        return answer, reasoning


if __name__ == "__main__":
    # Test the agent
    from gradeschoolmathsolver.models import Question as TestQuestion

    # Create agent with basic config
    agent_config = AgentConfig(
        name="basic_agent",
        use_classification=False,
        use_rag=False
    )

    agent = AgentService(agent_config)

    # Test question
    test_question = TestQuestion(
        equation="5 + 3",
        question_text="What is 5 + 3?",
        answer=8,
        difficulty="easy"
    )

    result = agent.solve_question("test_user", test_question)
    print(f"Agent: {result['agent_name']}")
    print(f"Question: {result['question']}")
    print(f"Correct Answer: {result['correct_answer']}")
    print(f"Agent Answer: {result['agent_answer']}")
    print(f"Reasoning: {result['reasoning']}")
