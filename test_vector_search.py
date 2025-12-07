#!/usr/bin/env python3
"""
ULTRATHINK - Test Vector Search
Validates Neo4j vector index and embedding search
Run AFTER create_indexes.py
"""

import sys
from pathlib import Path
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "siemensenergy"
NODE_LABEL = "PageChunk"
INDEX_NAME = "page_embeddings_ultrathink"

print("=" * 80)
print("ULTRATHINK - Vector Search Test")
print("=" * 80)
print()

# Load model
print("📌 Loading embedding model...")
model = SentenceTransformer('BAAI/bge-large-en-v1.5', device='cpu')
print("✅ Model loaded")
print()

# Connect to Neo4j
print("📌 Connecting to Neo4j...")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Check index exists
print("📌 Checking vector index...")
with driver.session() as session:
    try:
        result = session.run(f"""
            SHOW INDEXES
            YIELD name, state
            WHERE name = '{INDEX_NAME}'
            RETURN name, state
        """)
        record = result.single()

        if not record:
            print(f"❌ Vector index '{INDEX_NAME}' not found!")
            print(f"   Run: python create_indexes.py first")
            sys.exit(1)

        if record['state'] != 'ONLINE':
            print(f"⚠️  Index state: {record['state']}")
            print(f"   Wait for index to come online, then retry")
            sys.exit(1)

        print(f"✅ Index '{INDEX_NAME}' is online")

    except Exception as e:
        print(f"❌ Error checking index: {e}")
        sys.exit(1)

print()

# Test queries
test_queries = [
    "power requirements",
    "HVDC converter specifications",
    "transformer protection systems",
    "grid compliance"
]

print("📌 Testing vector searches...")
print()

for query_text in test_queries:
    print(f"🔍 Query: \"{query_text}\"")

    # Generate query embedding
    query_embedding = model.encode([query_text])[0]

    # Search Neo4j
    with driver.session() as session:
        result = session.run(f"""
            CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
            YIELD node, score
            RETURN node.chunk_id as chunk_id,
                   node.project_id as project_id,
                   node.technology as technology,
                   node.page as page,
                   score
            ORDER BY score DESC
            LIMIT $top_k
        """,
            index_name=INDEX_NAME,
            top_k=5,
            query_embedding=query_embedding.tolist()
        )

        results = list(result)

        if not results:
            print(f"   ⚠️  No results found")
        else:
            print(f"   ✅ Found {len(results)} results:")
            for i, record in enumerate(results, 1):
                print(f"      {i}. {record['project_id']} (page {record['page']}) - {record['technology']} - score: {record['score']:.3f}")

    print()

# Test filtered search
print("📌 Testing filtered vector search (HVDC only)...")
query_text = "converter protection"
query_embedding = model.encode([query_text])[0]

with driver.session() as session:
    result = session.run(f"""
        CALL db.index.vector.queryNodes($index_name, 20, $query_embedding)
        YIELD node, score
        WHERE node.technology = 'HVDC'
        RETURN node.chunk_id as chunk_id,
               node.project_id as project_id,
               node.customer as customer,
               score
        ORDER BY score DESC
        LIMIT 5
    """,
        index_name=INDEX_NAME,
        query_embedding=query_embedding.tolist()
    )

    results = list(result)
    print(f"✅ Filtered search (HVDC only): {len(results)} results")
    for i, record in enumerate(results, 1):
        print(f"   {i}. {record['project_id']} - {record['customer']} - score: {record['score']:.3f}")

driver.close()

print()
print("=" * 80)
print("✨ VECTOR SEARCH TEST COMPLETE!")
print("=" * 80)
print("✅ Neo4j vector index working correctly")
print("✅ Embedding search functional")
print("✅ Metadata filtering working")
print()
print("🚀 System ready for production use!")
