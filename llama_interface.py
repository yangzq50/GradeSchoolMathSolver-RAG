"""LLaMA-1B interface for generating hints and explanations"""

from typing import Optional, Dict
import os

class LlamaInterface:
    """Interface for LLaMA-1B model to provide hints and explanations"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize the LLaMA interface
        
        Args:
            model_name: Name of the model to use (default from config)
        """
        self.model_name = model_name or os.getenv("LLAMA_MODEL_NAME", "meta-llama/Llama-3.2-1B")
        self.model = None
        self.tokenizer = None
        self._initialized = False
    
    def initialize(self):
        """
        Lazy initialization of the model
        Note: Requires transformers library and model access
        """
        if self._initialized:
            return
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                load_in_8bit=True  # Use 8-bit quantization to reduce memory
            )
            self._initialized = True
        except Exception as e:
            print(f"Warning: Could not initialize LLaMA model: {e}")
            print("The system will work in fallback mode without LLM assistance.")
    
    def generate_hint(self, problem_text: str, problem_type: str) -> str:
        """
        Generate a hint for a math problem
        
        Args:
            problem_text: The problem text
            problem_type: Type of problem (addition, subtraction, etc.)
        
        Returns:
            A helpful hint
        """
        if not self._initialized:
            # Fallback hints without LLM
            return self._get_fallback_hint(problem_type)
        
        try:
            prompt = f"""You are a helpful math tutor. Provide a short hint for this problem without giving away the answer:

Problem: {problem_text}
Problem Type: {problem_type}

Hint:"""
            
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.7,
                do_sample=True
            )
            
            hint = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract only the generated hint part
            hint = hint.split("Hint:")[-1].strip()
            
            return hint
        except Exception as e:
            print(f"Error generating hint: {e}")
            return self._get_fallback_hint(problem_type)
    
    def generate_explanation(self, problem_text: str, correct_answer: float, problem_type: str) -> str:
        """
        Generate an explanation for how to solve a problem
        
        Args:
            problem_text: The problem text
            correct_answer: The correct answer
            problem_type: Type of problem
        
        Returns:
            A step-by-step explanation
        """
        if not self._initialized:
            # Fallback explanation without LLM
            return self._get_fallback_explanation(problem_text, correct_answer, problem_type)
        
        try:
            prompt = f"""You are a helpful math tutor. Explain step-by-step how to solve this problem:

Problem: {problem_text}
Answer: {correct_answer}

Explanation:"""
            
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True
            )
            
            explanation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract only the generated explanation part
            explanation = explanation.split("Explanation:")[-1].strip()
            
            return explanation
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return self._get_fallback_explanation(problem_text, correct_answer, problem_type)
    
    def _get_fallback_hint(self, problem_type: str) -> str:
        """Provide simple hints without LLM"""
        hints = {
            "addition": "Think about counting up from the first number.",
            "subtraction": "Think about counting down or taking away from the first number.",
            "multiplication": "Remember that multiplication is repeated addition.",
            "division": "Think about how many times the second number fits into the first number."
        }
        return hints.get(problem_type, "Break the problem down into smaller steps.")
    
    def _get_fallback_explanation(self, problem_text: str, correct_answer: float, problem_type: str) -> str:
        """Provide simple explanation without LLM"""
        return f"To solve {problem_text}, work through the {problem_type} step by step. The answer is {correct_answer}."
