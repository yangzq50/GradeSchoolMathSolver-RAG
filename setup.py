"""Setup script for GradeSchoolMathSolver-RAG"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="grade-school-math-solver-rag",
    version="1.0.0",
    author="GradeSchoolMathSolver-RAG Team",
    description="AI-powered Grade School Math Solver with RAG",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yangzq50/GradeSchoolMathSolver-RAG",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mathsolver=main:main",
        ],
    },
)
