# Contributing to GradeSchoolMathSolver

Thank you for your interest in contributing! This document provides guidelines and best practices for contributing to this project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Architecture Overview](#architecture-overview)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain a welcoming environment

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git
- Basic understanding of Flask and Elasticsearch

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/GradeSchoolMathSolver.git
   cd GradeSchoolMathSolver
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start infrastructure services**
   ```bash
   docker-compose up -d
   ```

6. **Run tests to verify setup**
   ```bash
   pytest tests/ -v
   ```

## 📝 Code Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: Maximum 120 characters
- **Imports**: Group into standard library, third-party, and local imports
- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **Type hints**: Use type hints for all function parameters and return values

### Code Quality Tools

Run these before submitting:

```bash
# Linting
flake8 . --max-line-length=120

# Type checking
mypy . --ignore-missing-imports

# Testing
pytest tests/ -v --cov
```

### Example Code Structure

```python
"""
Module description

Brief explanation of what this module does and its purpose.
"""
from typing import Optional, List
import requests
from config import Config


class MyService:
    """
    Service description
    
    Detailed explanation of the service's purpose and functionality.
    
    Attributes:
        config: Configuration object
        
    Example:
        >>> service = MyService()
        >>> result = service.do_something("input")
    """
    
    def __init__(self):
        """Initialize the service with configuration."""
        self.config = Config()
    
    def do_something(self, param: str) -> Optional[str]:
        """
        Do something with the parameter
        
        Args:
            param: Description of the parameter
            
        Returns:
            Result string or None if operation fails
            
        Raises:
            ValueError: If param is empty
        """
        if not param:
            raise ValueError("param cannot be empty")
        
        try:
            # Implementation
            return f"Result: {param}"
        except Exception as e:
            print(f"Error: {e}")
            return None
```

## 🧪 Testing Guidelines

### Writing Tests

1. **Test file naming**: `test_<module_name>.py`
2. **Test function naming**: `test_<functionality>_<scenario>`
3. **Use fixtures**: For common setup and teardown
4. **Mock external services**: Don't rely on external APIs in tests

### Test Structure

```python
def test_feature_with_valid_input():
    """Test feature with valid input"""
    # Arrange
    service = MyService()
    input_data = "valid_input"
    
    # Act
    result = service.do_something(input_data)
    
    # Assert
    assert result is not None
    assert "Result" in result


def test_feature_with_invalid_input():
    """Test feature handles invalid input gracefully"""
    service = MyService()
    
    with pytest.raises(ValueError):
        service.do_something("")
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_basic.py -v

# Run with coverage report
pytest tests/ --cov --cov-report=html

# Run tests matching pattern
pytest tests/ -k "test_account" -v
```

## 🔄 Submitting Changes

### Branch Naming Convention

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### Commit Message Format

```
<type>: <short summary>

<detailed description if needed>

<reference to issue if applicable>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `test`: Test additions or changes
- `chore`: Maintenance tasks

Example:
```
feat: Add retry logic for AI API calls

Implements exponential backoff retry mechanism for improved
reliability when communicating with external AI services.

Fixes #123
```

### Pull Request Process

1. **Update your branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout your-branch
   git rebase main
   ```

2. **Ensure all tests pass**
   ```bash
   pytest tests/ -v
   flake8 .
   mypy .
   ```

3. **Create pull request**
   - Provide clear description of changes
   - Reference related issues
   - Include screenshots for UI changes
   - Ensure CI/CD passes

4. **Address review feedback**
   - Respond to all comments
   - Make requested changes
   - Re-request review after updates

## 🏗️ Architecture Overview

### Service Structure

```
services/
├── account/          # User management and statistics
├── agent/            # RAG bot logic
├── agent_management/ # Agent configuration
├── classification/   # Question classification
├── exam/            # Exam orchestration
├── immersive_exam/  # Synchronized exams
├── mistake_review/  # Mistake tracking
├── qa_generation/   # Question generation
├── quiz_history/    # RAG history storage
└── teacher/         # Educational feedback
```

### Key Design Principles

1. **Separation of Concerns**: Each service has a single responsibility
2. **Dependency Injection**: Services are loosely coupled
3. **Error Handling**: Always handle exceptions gracefully
4. **Input Validation**: Validate all user inputs
5. **Logging**: Use print statements (to be migrated to logging framework)

### Adding a New Service

1. Create service directory: `services/my_service/`
2. Add `__init__.py` and `service.py`
3. Implement service class with clear interface
4. Add comprehensive docstrings
5. Create tests in `tests/test_my_service.py`
6. Update documentation

### Adding a New Endpoint

1. Add route handler in `web_ui/app.py`
2. Validate input using Pydantic models
3. Call appropriate service method
4. Handle errors and return appropriate status codes
5. Add API documentation in README.md

## 🐛 Reporting Issues

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Error messages and stack traces

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative approaches considered
- Impact on existing functionality

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Elasticsearch Python Client](https://elasticsearch-py.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## ❓ Questions?

- Open a GitHub issue with the `question` label
- Check existing issues and discussions
- Review the documentation in the `docs/` directory

Thank you for contributing to GradeSchoolMathSolver! 🎉
