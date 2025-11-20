"""
Setup script for GradeSchoolMathSolver-RAG package
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gradeschoolmathsolver",
    version="1.0.0",
    author="yangzq50",
    description="An AI-powered Grade School Math Solver with RAG",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yangzq50/GradeSchoolMathSolver-RAG",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        "gradeschoolmathsolver.web_ui": ["templates/*.html", "templates/**/*.html"],
    },
    entry_points={
        "console_scripts": [
            "gradeschoolmathsolver=gradeschoolmathsolver.web_ui.app:main",
        ],
    },
)
