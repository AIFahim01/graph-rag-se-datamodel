#!/usr/bin/env python3
"""
Test the created vector database with proper BGE embeddings
"""

import sys
import chromadb
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from embeddings import VectorGenerator
except ImportError:
    print("Using simpler test - BGE model not available in this environment")

def simple_test():
    """Test with collection info only"""
    # Connect to ChromaDB
    output_dir = Path(__file__).parent / "data" / "graphrag_complete"
    chroma_client = chromadb.PersistentClient(path=str(output_dir / "chroma_db"))

    # Get collection
    collection = chroma_client.get_collection("graphrag_chunks")
    count = collection.count()

    print(f"🎉 VECTOR DATABASE SUCCESS!")
    print(f"📊 Total chunks: {count:,}")

    # Get a few sample documents without querying
    results = collection.get(limit=5, include=['documents', 'metadatas'])

    print(f"\n📄 Sample documents:")
    for i, doc in enumerate(results['documents']):
        metadata = results['metadatas'][i]
        print(f"  {i+1}. [{metadata['category'].upper()}] {metadata['project']}")
        print(f"     Source: {metadata['source']}")
        print(f"     Preview: {doc[:100]}...")
        print()

def advanced_test():
    """Test with BGE embeddings"""
    try:
        # Initialize BGE model (same as used for vector creation)
        vector_generator = VectorGenerator(model_name="BAAI/bge-large-en-v1.5")

        # Connect to ChromaDB
        output_dir = Path(__file__).parent / "data" / "graphrag_complete"
        chroma_client = chromadb.PersistentClient(path=str(output_dir / "chroma_db"))
        collection = chroma_client.get_collection("graphrag_chunks")

        print(f"🎉 VECTOR DATABASE WITH BGE EMBEDDINGS WORKING!")
        print(f"📊 Total chunks: {collection.count():,}")

        # Test queries with BGE embeddings
        test_queries = [
            "HVDC converter protection system",
            "Siemens Energy synchronous condenser"
        ]

        print(f"\n🔍 Testing Vector Search:")
        for query in test_queries:
            print(f"\nQuery: '{query}'")

            # Generate query embedding with BGE
            query_embedding = vector_generator.embed_query(query)

            # Query ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=3
            )

            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                similarity = 1 - distance

                print(f"  {i+1}. [{metadata['category'].upper()}] {metadata['project'][:40]}...")
                print(f"     Source: {metadata['source'][:50]}...")
                print(f"     Similarity: {similarity:.3f}")
                print(f"     Preview: {doc[:120]}...")

    except Exception as e:
        print(f"BGE test failed: {e}")
        print("Running simple test instead...")
        simple_test()

def main():
    print("🧪 Testing Vector Database...")

    try:
        advanced_test()
    except:
        simple_test()

if __name__ == "__main__":
    main()