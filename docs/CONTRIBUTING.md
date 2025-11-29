# Contributing to GradeSchoolMathSolver

Thank you for your interest in contributing!

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/GradeSchoolMathSolver.git
cd GradeSchoolMathSolver
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
cp .env.example .env
docker-compose up -d
pytest tests/ -v
```

## Code Standards

- Follow PEP 8 (max 120 characters)
- Use type hints and Google-style docstrings
- Run before submitting:
  ```bash
  flake8 . --max-line-length=120
  mypy . --ignore-missing-imports
  pytest tests/ -v --cov
  ```

## Submitting Changes

### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation

### Commit Messages
```
<type>: <short summary>

Types: feat, fix, refactor, docs, test, chore
```

### Pull Request Process
1. Ensure tests pass
2. Provide clear description
3. Reference related issues

## Service Structure

```
src/gradeschoolmathsolver/services/
├── account/          # User management
├── agent/            # RAG bot logic
├── classification/   # Question categorization
├── database/         # Database abstraction
├── exam/             # Exam orchestration
├── qa_generation/    # Question generation
├── quiz_history/     # RAG storage
└── teacher/          # Feedback service
```

## Releases and Publishing

### Creating a Release

Releases are automated via GitHub Actions when version tags are pushed:

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

This automatically:
- Creates a GitHub release with auto-generated notes
- Builds and publishes Docker images to Docker Hub
- Publishes the package to PyPI

### Semantic Versioning

- **MAJOR** (2.0.0): Breaking changes
- **MINOR** (1.1.0): New features (backward compatible)
- **PATCH** (1.0.1): Bug fixes

### Local Package Building

```bash
pip install build twine
python -m build
twine check dist/*
```

## Questions?

Open a GitHub issue or check the [docs/](.) directory.
