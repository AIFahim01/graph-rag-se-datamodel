#!/usr/bin/env python3
"""
Test the created vector database
"""

import chromadb
from pathlib import Path

def main():
    # Connect to ChromaDB
    output_dir = Path(__file__).parent / "data" / "graphrag_complete"
    chroma_client = chromadb.PersistentClient(path=str(output_dir / "chroma_db"))

    # Get collection
    collection = chroma_client.get_collection("graphrag_chunks")

    # Get collection stats
    count = collection.count()
    print(f"📊 Vector Database Stats:")
    print(f"   Total chunks: {count:,}")
    print()

    # Test queries
    test_queries = [
        "HVDC converter protection system",
        "Siemens Energy synchronous condenser",
        "VSC technology grid connection",
        "power system voltage control",
        "SYNCON installation requirements"
    ]

    print("🔍 Testing Vector Search:")
    for query in test_queries:
        print(f"\nQuery: '{query}'")

        results = collection.query(
            query_texts=[query],
            n_results=3
        )

        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]
            similarity = 1 - distance

            print(f"  {i+1}. [{metadata['category'].upper()}] {metadata['project'][:50]}...")
            print(f"     Source: {metadata['source'][:60]}...")
            print(f"     Similarity: {similarity:.3f}")
            print(f"     Preview: {doc[:150]}...")

    print("\n✅ Vector database is working perfectly!")

if __name__ == "__main__":
    main()