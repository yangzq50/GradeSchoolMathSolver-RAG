# Examples

This directory contains example scripts demonstrating various features of the GradeSchoolMathSolver-RAG system.

## Embedding Service Example

**File**: `embedding_example.py`

A comprehensive demonstration of the Embedding Service functionality, showing how to:
- Initialize the embedding service
- Check service availability
- Generate single text embeddings
- Generate batch embeddings
- Use embeddings for similarity search in RAG
- Handle edge cases and errors

### Usage

```bash
# Ensure you have the package installed
pip install -e .

# Run the example
python examples/embedding_example.py
```

### Prerequisites

1. **Docker Desktop** with Model Runner enabled
2. **embeddinggemma:300M-Q8_0** model downloaded in Docker Desktop
3. **Python 3.11+** with gradeschoolmathsolver package installed

### Expected Output

When the embedding service is available, the script will:
- Display service configuration
- Show embedding dimensions (typically 768 or 256 depending on model)
- Generate embeddings for sample questions
- Demonstrate batch processing
- Show how embeddings can be used for similarity search

When the service is unavailable, the script will:
- Provide clear error messages
- Give step-by-step instructions for setup
- Exit gracefully

### What You'll Learn

- How to initialize and configure the EmbeddingService
- How to check if the embedding service is available
- How to generate embeddings for single and multiple texts
- How embeddings can be used in RAG applications
- How the service handles errors and edge cases

## Adding More Examples

To add new examples:

1. Create a new Python file in this directory
2. Add appropriate documentation at the top
3. Follow the pattern of clear output and error handling
4. Update this README with information about your example
