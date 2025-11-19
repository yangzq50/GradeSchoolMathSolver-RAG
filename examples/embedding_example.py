#!/usr/bin/env python3
"""
Example script demonstrating the Embedding Service usage

This script shows how to use the embedding service to generate embeddings
for text inputs, which can be used for RAG (Retrieval-Augmented Generation)
applications.

Requirements:
- Docker Desktop with Model Runner enabled
- embeddinggemma:300M-Q8_0 model downloaded in Docker Desktop
- Python 3.11+ with gradeschoolmathsolver package installed

Run: python examples/embedding_example.py
"""

from gradeschoolmathsolver.services.embedding import EmbeddingService


def main():
    """Demonstrate embedding service functionality"""
    print("=" * 70)
    print("Embedding Service Example")
    print("=" * 70)
    print()

    # Initialize the service
    service = EmbeddingService()
    print("Service Configuration:")
    print(f"  - Enabled: {service.enabled}")
    print(f"  - Model URL: {service.model_url}")
    print(f"  - Model Name: {service.model_name}")
    print(f"  - Engine: {service.engine}")
    print()

    # Check if service is available
    print("Checking service availability...")
    if not service.is_available():
        print("❌ Embedding service is not available!")
        print()
        print("To use the embedding service:")
        print("1. Ensure Docker Desktop is running")
        print("2. Enable Docker Model Runner in Settings → Features in development")
        print("3. Download the 'embeddinggemma:300M-Q8_0' model in Docker Desktop")
        print("4. Verify the model is running at http://localhost:12434")
        print()
        return

    print("✅ Embedding service is available!")
    print()

    # Get embedding dimension
    dimension = service.get_embedding_dimension()
    print(f"Embedding dimension: {dimension}")
    print()

    # Example 1: Single text embedding
    print("-" * 70)
    print("Example 1: Single Text Embedding")
    print("-" * 70)

    text = "What is the sum of five and three?"
    print(f"Input: {text}")
    print()

    embedding = service.generate_embedding(text)
    if embedding:
        print("✅ Generated embedding:")
        print(f"   - Dimension: {len(embedding)}")
        print(f"   - First 10 values: {embedding[:10]}")
        print(f"   - Data type: {type(embedding[0])}")
    else:
        print("❌ Failed to generate embedding")
    print()

    # Example 2: Batch text embeddings
    print("-" * 70)
    print("Example 2: Batch Text Embeddings")
    print("-" * 70)

    texts = [
        "What is five plus three?",
        "Calculate ten minus four",
        "What is six times seven?",
        "Divide twenty by four"
    ]
    print(f"Input: {len(texts)} texts")
    for i, t in enumerate(texts, 1):
        print(f"  {i}. {t}")
    print()

    embeddings = service.generate_embeddings(texts)
    if embeddings:
        print(f"✅ Generated {len(embeddings)} embeddings:")
        for i, emb in enumerate(embeddings, 1):
            print(f"   {i}. Dimension: {len(emb)}, First 5 values: {emb[:5]}")
    else:
        print("❌ Failed to generate embeddings")
    print()

    # Example 3: Similarity comparison (conceptual)
    print("-" * 70)
    print("Example 3: Similarity Use Case")
    print("-" * 70)
    print()
    print("Embeddings can be used for similarity search in RAG applications:")
    print()
    print("1. Generate embeddings for historical questions:")
    question1 = "What is 5 + 3?"
    question2 = "What is the sum of 5 and 3?"
    question3 = "What is 10 - 4?"

    emb1 = service.generate_embedding(question1)
    emb2 = service.generate_embedding(question2)
    emb3 = service.generate_embedding(question3)

    if emb1 and emb2 and emb3:
        print(f"   - '{question1}' → {len(emb1)}-D vector")
        print(f"   - '{question2}' → {len(emb2)}-D vector")
        print(f"   - '{question3}' → {len(emb3)}-D vector")
        print()
        print("2. Use cosine similarity or other distance metrics to find similar questions")
        print("3. Retrieve relevant historical answers for RAG context")
        print()
        print("Note: Questions 1 and 2 should have similar embeddings (same semantic meaning)")
        print("      Question 3 should be different (different operation)")
    else:
        print("   (Unable to demonstrate - service unavailable)")
    print()

    # Example 4: Empty input handling
    print("-" * 70)
    print("Example 4: Error Handling")
    print("-" * 70)
    print()
    print("The service handles edge cases gracefully:")

    # Empty string
    result = service.generate_embedding("")
    print(f"   - Empty string: {result}")

    # Whitespace only
    result = service.generate_embedding("   ")
    print(f"   - Whitespace only: {result}")

    # Empty list
    result = service.generate_embeddings([])
    print(f"   - Empty list: {result}")
    print()

    print("=" * 70)
    print("Example completed successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("- Integrate embeddings into your RAG pipeline")
    print("- Store embeddings in a vector database (Elasticsearch, Milvus, etc.)")
    print("- Use similarity search to retrieve relevant context")
    print("- Enhance AI responses with retrieved information")
    print()


if __name__ == "__main__":
    main()
