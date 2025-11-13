#!/usr/bin/env python3
"""
Fair Comparison: ChromaDB vs Neo4j Vector Storage
Tests BOTH databases with IDENTICAL data and queries
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print("=" * 80)
print("CHROMADB vs NEO4J VECTOR STORAGE COMPARISON")
print("=" * 80)

# Setup: Load sample chunks
print("\n📌 Setup: Loading 10 sample chunks...")
chunks_file = PROJECT_ROOT / "data" / "graphrag_complete" / "graphrag_chunks.json"
with open(chunks_file) as f:
    all_chunks = json.load(f)

sample_chunks = all_chunks[:10]
print(f"✅ Loaded {len(sample_chunks)} chunks from {sample_chunks[0]['project']}")

# Setup: Generate embeddings ONCE (same for both DBs)
print("\n📌 Setup: Generating embeddings with BGE model...")
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-large-en-v1.5')
print(f"✅ Loaded BGE model (1024 dimensions)")

texts = [chunk['text'][:512] for chunk in sample_chunks]
embeddings = model.encode(texts, show_progress_bar=False)
print(f"✅ Generated {len(embeddings)} embeddings (will be used for BOTH tests)")

# Test query (same for both)
test_query = "HVDC converter station protection and control systems"
query_embedding = model.encode([test_query])[0]
print(f"\n📌 Test Query: '{test_query}'")

# =============================================================================
# TEST 1: CHROMADB
# =============================================================================

print("\n" + "=" * 80)
print("TEST 1: CHROMADB VECTOR SEARCH")
print("=" * 80)

chromadb_results = []
chromadb_time = 0

try:
    import chromadb
    from chromadb.config import Settings

    # Create temporary ChromaDB client
    chroma_client = chromadb.Client(Settings(
        anonymized_telemetry=False,
        allow_reset=True
    ))

    # Create collection
    collection = chroma_client.get_or_create_collection(
        name="test_comparison",
        metadata={"hnsw:space": "cosine"}
    )

    print("✅ ChromaDB client created")

    # Insert chunks with embeddings
    print(f"\n📥 Inserting {len(sample_chunks)} chunks into ChromaDB...")
    collection.add(
        ids=[chunk['chunk_id'] for chunk in sample_chunks],
        embeddings=embeddings.tolist(),
        documents=[chunk['text'][:500] for chunk in sample_chunks],
        metadatas=[{
            'project': chunk['project'],
            'source': chunk['source'],
            'page': chunk['page']
        } for chunk in sample_chunks]
    )
    print("✅ Chunks inserted into ChromaDB")

    # Query ChromaDB
    print(f"\n🔍 Querying ChromaDB...")
    start_time = time.time()

    chroma_results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=5,
        include=['documents', 'metadatas', 'distances']
    )

    chromadb_time = time.time() - start_time

    # Parse results
    for i in range(len(chroma_results['ids'][0])):
        chromadb_results.append({
            'rank': i + 1,
            'chunk_id': chroma_results['ids'][0][i],
            'score': 1 - chroma_results['distances'][0][i],  # Convert distance to similarity
            'text': chroma_results['documents'][0][i][:150],
            'project': chroma_results['metadatas'][0][i]['project'],
            'source': chroma_results['metadatas'][0][i]['source']
        })

    print(f"✅ ChromaDB search completed in {chromadb_time*1000:.1f}ms")
    print(f"   Retrieved {len(chromadb_results)} results")

    # Display results
    print("\n📊 ChromaDB Top Results:")
    for res in chromadb_results:
        print(f"\n   Rank {res['rank']}: Score {res['score']:.4f}")
        print(f"   Project: {res['project']}")
        print(f"   Text: {res['text']}...")

    # Cleanup
    chroma_client.reset()
    chromadb_success = True

except Exception as e:
    print(f"❌ ChromaDB test failed: {e}")
    import traceback
    traceback.print_exc()
    chromadb_success = False

# =============================================================================
# TEST 2: NEO4J
# =============================================================================

print("\n" + "=" * 80)
print("TEST 2: NEO4J VECTOR SEARCH")
print("=" * 80)

neo4j_results = []
neo4j_time = 0

try:
    from neo4j import GraphDatabase

    # Connect to Neo4j
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=None)
    print("✅ Connected to Neo4j")

    # Check version
    with driver.session() as session:
        result = session.run("CALL dbms.components() YIELD versions RETURN versions")
        version = result.single()['versions'][0]
        print(f"✅ Neo4j version: {version}")

    # Clear test data
    with driver.session() as session:
        session.run("MATCH (c:TestChunk) DETACH DELETE c")
        session.run("DROP INDEX test_chunk_embeddings IF EXISTS")

    # Insert chunks with embeddings
    print(f"\n📥 Inserting {len(sample_chunks)} chunks into Neo4j...")
    with driver.session() as session:
        for chunk, embedding in zip(sample_chunks, embeddings):
            session.run("""
                CREATE (c:TestChunk {
                    chunk_id: $chunk_id,
                    text: $text,
                    project: $project,
                    source: $source,
                    page: $page,
                    embedding: $embedding
                })
            """,
                chunk_id=chunk['chunk_id'],
                text=chunk['text'][:500],
                project=chunk['project'],
                source=chunk['source'],
                page=chunk['page'],
                embedding=embedding.tolist()
            )

    print("✅ Chunks inserted into Neo4j")

    # Create vector index
    print(f"\n📝 Creating vector index...")
    with driver.session() as session:
        session.run("""
            CREATE VECTOR INDEX test_chunk_embeddings
            FOR (c:TestChunk)
            ON (c.embedding)
            OPTIONS {
                indexConfig: {
                    `vector.dimensions`: 1024,
                    `vector.similarity_function`: 'cosine'
                }
            }
        """)

        # Wait for index to be online
        for i in range(30):
            time.sleep(1)
            result = session.run("""
                SHOW INDEXES
                YIELD name, state
                WHERE name = 'test_chunk_embeddings'
                RETURN state
            """)
            record = result.single()
            if record and record['state'] == 'ONLINE':
                print(f"✅ Vector index ONLINE (took {i+1}s)")
                break

    # Query Neo4j
    print(f"\n🔍 Querying Neo4j...")
    with driver.session() as session:
        start_time = time.time()

        result = session.run("""
            CALL db.index.vector.queryNodes('test_chunk_embeddings', 5, $query_embedding)
            YIELD node, score
            RETURN node.chunk_id AS chunk_id,
                   node.text AS text,
                   node.project AS project,
                   node.source AS source,
                   score
            ORDER BY score DESC
        """,
            query_embedding=query_embedding.tolist()
        )

        neo4j_time = time.time() - start_time

        # Parse results
        for i, record in enumerate(result, 1):
            neo4j_results.append({
                'rank': i,
                'chunk_id': record['chunk_id'],
                'score': record['score'],
                'text': record['text'][:150],
                'project': record['project'],
                'source': record['source']
            })

    print(f"✅ Neo4j search completed in {neo4j_time*1000:.1f}ms")
    print(f"   Retrieved {len(neo4j_results)} results")

    # Display results
    print("\n📊 Neo4j Top Results:")
    for res in neo4j_results:
        print(f"\n   Rank {res['rank']}: Score {res['score']:.4f}")
        print(f"   Project: {res['project']}")
        print(f"   Text: {res['text']}...")

    # Cleanup
    with driver.session() as session:
        session.run("MATCH (c:TestChunk) DETACH DELETE c")
        session.run("DROP INDEX test_chunk_embeddings IF EXISTS")

    driver.close()
    neo4j_success = True

except Exception as e:
    print(f"❌ Neo4j test failed: {e}")
    import traceback
    traceback.print_exc()
    neo4j_success = False

# =============================================================================
# COMPARISON RESULTS
# =============================================================================

print("\n" + "=" * 80)
print("COMPARISON RESULTS")
print("=" * 80)

if chromadb_success and neo4j_success:
    print(f"\n⚡ Performance Comparison:")
    print(f"   ChromaDB: {chromadb_time*1000:.1f}ms")
    print(f"   Neo4j:    {neo4j_time*1000:.1f}ms")

    speedup = chromadb_time / neo4j_time if neo4j_time > 0 else 0
    if chromadb_time < neo4j_time:
        print(f"   Winner: ChromaDB ({chromadb_time/neo4j_time:.2f}x faster)")
    else:
        print(f"   Winner: Neo4j ({neo4j_time/chromadb_time:.2f}x faster)")

    print(f"\n📊 Result Quality Comparison:")
    print(f"\n   {'Rank':<6} {'ChromaDB Score':<15} {'Neo4j Score':<15} {'Match?':<10}")
    print(f"   {'-'*6} {'-'*15} {'-'*15} {'-'*10}")

    for i in range(5):
        chroma_score = chromadb_results[i]['score'] if i < len(chromadb_results) else 0
        neo4j_score = neo4j_results[i]['score'] if i < len(neo4j_results) else 0
        chroma_id = chromadb_results[i]['chunk_id'] if i < len(chromadb_results) else 'N/A'
        neo4j_id = neo4j_results[i]['chunk_id'] if i < len(neo4j_results) else 'N/A'
        match = "✅ Same" if chroma_id == neo4j_id else "❌ Different"

        print(f"   {i+1:<6} {chroma_score:<15.4f} {neo4j_score:<15.4f} {match:<10}")

    # Check result overlap
    chroma_ids = set(r['chunk_id'] for r in chromadb_results)
    neo4j_ids = set(r['chunk_id'] for r in neo4j_results)
    overlap = len(chroma_ids & neo4j_ids)
    overlap_pct = (overlap / 5) * 100

    print(f"\n📈 Result Overlap:")
    print(f"   Common chunks in top-5: {overlap}/5 ({overlap_pct:.0f}%)")
    print(f"   ChromaDB only: {chroma_ids - neo4j_ids}")
    print(f"   Neo4j only: {neo4j_ids - chroma_ids}")

    # Ranking comparison
    print(f"\n🎯 Ranking Comparison (which chunk ranked where):")
    all_ids = chroma_ids | neo4j_ids
    for chunk_id in sorted(all_ids):
        chroma_rank = next((r['rank'] for r in chromadb_results if r['chunk_id'] == chunk_id), None)
        neo4j_rank = next((r['rank'] for r in neo4j_results if r['chunk_id'] == chunk_id), None)
        print(f"   Chunk {chunk_id[:20]}... → ChromaDB: {chroma_rank or 'N/A'}, Neo4j: {neo4j_rank or 'N/A'}")

    # Final recommendation
    print(f"\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)

    score_diff = abs(chromadb_time - neo4j_time)
    if score_diff < 50:  # Less than 50ms difference
        print(f"✅ Performance is similar (difference: {score_diff:.1f}ms)")
        print(f"   Both are fast enough for production use")
        print(f"\n🎯 RECOMMENDATION: Use Neo4j for unified architecture")
        print(f"   Benefits:")
        print(f"   - Single database (simpler infrastructure)")
        print(f"   - Unified vector + graph queries")
        print(f"   - Result overlap: {overlap_pct:.0f}% (similar quality)")
    elif chromadb_time < neo4j_time:
        diff_factor = neo4j_time / chromadb_time
        print(f"⚠️  ChromaDB is {diff_factor:.2f}x faster ({chromadb_time*1000:.1f}ms vs {neo4j_time*1000:.1f}ms)")
        if diff_factor > 2:
            print(f"   🎯 RECOMMENDATION: Keep ChromaDB for vector queries")
        else:
            print(f"   🎯 RECOMMENDATION: Neo4j acceptable if unified arch is priority")
    else:
        diff_factor = chromadb_time / neo4j_time
        print(f"✅ Neo4j is {diff_factor:.2f}x faster! ({neo4j_time*1000:.1f}ms vs {chromadb_time*1000:.1f}ms)")
        print(f"   🎯 RECOMMENDATION: Definitely use Neo4j")

elif chromadb_success:
    print(f"✅ ChromaDB working: {chromadb_time*1000:.1f}ms")
    print(f"❌ Neo4j not tested")

elif neo4j_success:
    print(f"❌ ChromaDB not tested")
    print(f"✅ Neo4j working: {neo4j_time*1000:.1f}ms")

else:
    print(f"❌ Both tests failed - check database connectivity")

print("\n✨ Comparison test completed!")
