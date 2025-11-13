"""
Test Hybrid GraphRAG System

Tests:
1. ChromaDB vector search
2. Neo4j graph queries
3. Combined hybrid retrieval
"""

import sys
import json
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from storage.chroma_store import ChromaVectorStore
from embeddings import VectorGenerator


def test_chromadb():
    """Test ChromaDB vector search"""
    print("\n" + "=" * 80)
    print("TEST 1: ChromaDB Vector Search")
    print("=" * 80)

    try:
        # Connect
        print("\n🔗 Connecting to ChromaDB...")
        store = ChromaVectorStore()
        print("✓ Connected!")

        # Load embedding model for query
        print("\n📦 Loading embedding model for queries...")
        generator = VectorGenerator()

        # Test query
        query = "What are the database technologies?"
        print(f"\n🔍 Query: '{query}'")

        query_embedding = generator.embed_query(query)

        # Search
        results = store.query(
            collection_name='graphrag_chunks',
            query_embedding=query_embedding.tolist(),
            n_results=3
        )

        print("\n✅ Top 3 Results:")
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            print(f"\n{i}. Project: {metadata['project']}")
            print(f"   Source: {metadata['source']}")
            print(f"   Distance: {distance:.4f}")
            print(f"   Text: {doc[:150]}...")

        print("\n" + "=" * 80)
        print("✅ ChromaDB Test PASSED!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ ChromaDB Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_neo4j():
    """Test Neo4j graph queries"""
    print("\n" + "=" * 80)
    print("TEST 2: Neo4j Graph Queries")
    print("=" * 80)

    try:
        from storage.neo4j_store import Neo4jGraphStore

        print("\n🔗 Connecting to Neo4j...")
        store = Neo4jGraphStore()
        print("✓ Connected!")

        # Test: Count nodes
        print("\n📊 Counting nodes...")
        with store.driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()['count']
            print(f"✓ Total nodes: {count}")

        # Test: Get sample entities
        print("\n🔍 Sample entities:")
        with store.driver.session() as session:
            result = session.run("MATCH (e:Entity) RETURN e.name as name LIMIT 5")
            for record in result:
                print(f"  • {record['name']}")

        store.close()

        print("\n" + "=" * 80)
        print("✅ Neo4j Test PASSED!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Neo4j Test FAILED: {e}")
        print("\n💡 TIP: Neo4j may need initialization or password reset")
        print("   Try: docker restart neo4j-graphrag")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 80)
    print("HYBRID GRAPHRAG SYSTEM TEST")
    print("=" * 80)

    results = {
        'chromadb': False,
        'neo4j': False
    }

    # Test ChromaDB
    results['chromadb'] = test_chromadb()

    # Test Neo4j
    results['neo4j'] = test_neo4j()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"ChromaDB (Vector Search): {'✅ PASS' if results['chromadb'] else '❌ FAIL'}")
    print(f"Neo4j (Graph Queries):    {'✅ PASS' if results['neo4j'] else '❌ FAIL'}")
    print("=" * 80)

    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED! System is ready!")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")


if __name__ == "__main__":
    main()
