#!/usr/bin/env python3
"""
Scale Test: ChromaDB vs Neo4j at Different Data Volumes
Tests performance degradation as dataset grows to find breaking point
"""

import sys
import json
import time
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print("=" * 80)
print("SCALE TEST: CHROMADB vs NEO4J PERFORMANCE")
print("=" * 80)

# Load all chunks
chunks_file = PROJECT_ROOT / "data" / "graphrag_complete" / "graphrag_chunks.json"
with open(chunks_file) as f:
    all_chunks = json.load(f)

print(f"\n✅ Loaded {len(all_chunks):,} total chunks available")

# Test at multiple scales
TEST_SCALES = [100, 500, 1000]
test_query = "HVDC converter station protection and control systems"

print(f"\n📌 Test Query: '{test_query}'")
print(f"📌 Test Scales: {TEST_SCALES}")

# Load embedding model ONCE
print(f"\n📥 Loading BGE model...")
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-large-en-v1.5')
query_embedding = model.encode([test_query])[0]
print(f"✅ Model loaded")

# Store results
results = {
    'test_query': test_query,
    'scales': {}
}

# =============================================================================
# RUN TESTS AT EACH SCALE
# =============================================================================

for scale in TEST_SCALES:
    print(f"\n" + "=" * 80)
    print(f"TESTING WITH {scale:,} CHUNKS")
    print("=" * 80)

    # Prepare data
    test_chunks = all_chunks[:scale]
    print(f"\n📊 Generating embeddings for {scale:,} chunks...")
    texts = [chunk['text'][:512] for chunk in test_chunks]

    embedding_start = time.time()
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    embedding_time = time.time() - embedding_start
    print(f"✅ Generated {len(embeddings):,} embeddings in {embedding_time:.1f}s")

    scale_results = {
        'chunk_count': scale,
        'embedding_generation_time': embedding_time,
        'chromadb': {},
        'neo4j': {}
    }

    # -------------------------------------------------------------------------
    # TEST CHROMADB
    # -------------------------------------------------------------------------
    print(f"\n📌 Testing ChromaDB with {scale:,} chunks...")

    try:
        import chromadb
        from chromadb.config import Settings

        chroma_client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            allow_reset=True
        ))

        collection = chroma_client.get_or_create_collection(
            name=f"test_scale_{scale}",
            metadata={"hnsw:space": "cosine"}
        )

        # Insert
        insert_start = time.time()
        collection.add(
            ids=[chunk['chunk_id'] for chunk in test_chunks],
            embeddings=embeddings.tolist(),
            documents=[chunk['text'][:500] for chunk in test_chunks],
            metadatas=[{
                'project': chunk['project'],
                'source': chunk['source']
            } for chunk in test_chunks]
        )
        insert_time = time.time() - insert_start

        # Query multiple times for average
        query_times = []
        for _ in range(5):
            start = time.time()
            chroma_results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=5
            )
            query_times.append(time.time() - start)

        avg_query_time = np.mean(query_times)
        std_query_time = np.std(query_times)

        scale_results['chromadb'] = {
            'insert_time': insert_time,
            'avg_query_time': avg_query_time,
            'std_query_time': std_query_time,
            'top_5_ids': chroma_results['ids'][0],
            'top_5_scores': [1 - d for d in chroma_results['distances'][0]],
            'success': True
        }

        print(f"✅ ChromaDB Results:")
        print(f"   Insert time: {insert_time:.2f}s ({scale/insert_time:.0f} chunks/sec)")
        print(f"   Avg query time: {avg_query_time*1000:.1f}ms ± {std_query_time*1000:.1f}ms")
        print(f"   Top score: {scale_results['chromadb']['top_5_scores'][0]:.4f}")

        # Cleanup
        chroma_client.reset()

    except Exception as e:
        print(f"❌ ChromaDB failed: {e}")
        scale_results['chromadb']['success'] = False

    # -------------------------------------------------------------------------
    # TEST NEO4J
    # -------------------------------------------------------------------------
    print(f"\n📌 Testing Neo4j with {scale:,} chunks...")

    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver("bolt://localhost:7687", auth=None)

        # Clear previous data
        with driver.session() as session:
            session.run("MATCH (c:TestChunk) DETACH DELETE c")
            session.run("DROP INDEX test_chunk_embeddings IF EXISTS")

        # Insert
        insert_start = time.time()
        with driver.session() as session:
            # Batch insert for efficiency
            batch_size = 100
            for i in range(0, len(test_chunks), batch_size):
                batch_chunks = test_chunks[i:i+batch_size]
                batch_embeddings = embeddings[i:i+batch_size]

                for chunk, embedding in zip(batch_chunks, batch_embeddings):
                    session.run("""
                        CREATE (c:TestChunk {
                            chunk_id: $chunk_id,
                            text: $text,
                            project: $project,
                            source: $source,
                            embedding: $embedding
                        })
                    """,
                        chunk_id=chunk['chunk_id'],
                        text=chunk['text'][:500],
                        project=chunk['project'],
                        source=chunk['source'],
                        embedding=embedding.tolist()
                    )

        insert_time = time.time() - insert_start

        # Create index
        index_start = time.time()
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

            # Wait for index
            for i in range(60):
                time.sleep(1)
                result = session.run("""
                    SHOW INDEXES
                    YIELD name, state
                    WHERE name = 'test_chunk_embeddings'
                    RETURN state
                """)
                record = result.single()
                if record and record['state'] == 'ONLINE':
                    break

        index_time = time.time() - index_start

        # Query multiple times for average
        query_times = []
        with driver.session() as session:
            for _ in range(5):
                start = time.time()
                result = session.run("""
                    CALL db.index.vector.queryNodes('test_chunk_embeddings', 5, $query_embedding)
                    YIELD node, score
                    RETURN node.chunk_id AS chunk_id,
                           score
                    ORDER BY score DESC
                """,
                    query_embedding=query_embedding.tolist()
                )
                neo4j_res = [dict(r) for r in result]
                query_times.append(time.time() - start)

        avg_query_time = np.mean(query_times)
        std_query_time = np.std(query_times)

        scale_results['neo4j'] = {
            'insert_time': insert_time,
            'index_time': index_time,
            'avg_query_time': avg_query_time,
            'std_query_time': std_query_time,
            'top_5_ids': [r['chunk_id'] for r in neo4j_res],
            'top_5_scores': [r['score'] for r in neo4j_res],
            'success': True
        }

        print(f"✅ Neo4j Results:")
        print(f"   Insert time: {insert_time:.2f}s ({scale/insert_time:.0f} chunks/sec)")
        print(f"   Index time: {index_time:.2f}s")
        print(f"   Avg query time: {avg_query_time*1000:.1f}ms ± {std_query_time*1000:.1f}ms")
        print(f"   Top score: {scale_results['neo4j']['top_5_scores'][0]:.4f}")

        # Cleanup
        with driver.session() as session:
            session.run("MATCH (c:TestChunk) DETACH DELETE c")
            session.run("DROP INDEX test_chunk_embeddings IF EXISTS")

        driver.close()

    except Exception as e:
        print(f"❌ Neo4j failed: {e}")
        import traceback
        traceback.print_exc()
        scale_results['neo4j']['success'] = False

    # Save scale results
    results['scales'][scale] = scale_results

# =============================================================================
# FINAL ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("SCALE PERFORMANCE ANALYSIS")
print("=" * 80)

print(f"\n{'Scale':<10} {'ChromaDB (ms)':<15} {'Neo4j (ms)':<15} {'Speedup':<12} {'Result Match':<15}")
print(f"{'-'*10} {'-'*15} {'-'*15} {'-'*12} {'-'*15}")

for scale in TEST_SCALES:
    scale_data = results['scales'][scale]

    if scale_data['chromadb'].get('success') and scale_data['neo4j'].get('success'):
        chroma_time = scale_data['chromadb']['avg_query_time'] * 1000
        neo4j_time = scale_data['neo4j']['avg_query_time'] * 1000

        speedup = chroma_time / neo4j_time if neo4j_time > 0 else 0
        speedup_str = f"{speedup:.2f}x" if chroma_time < neo4j_time else f"1/{neo4j_time/chroma_time:.2f}x"

        # Check result overlap
        chroma_ids = set(scale_data['chromadb']['top_5_ids'])
        neo4j_ids = set(scale_data['neo4j']['top_5_ids'])
        overlap = len(chroma_ids & neo4j_ids)
        overlap_pct = f"{overlap}/5 ({overlap*20}%)"

        print(f"{scale:<10,} {chroma_time:<15.1f} {neo4j_time:<15.1f} {speedup_str:<12} {overlap_pct:<15}")

# =============================================================================
# PERFORMANCE DEGRADATION ANALYSIS
# =============================================================================

print(f"\n" + "=" * 80)
print("PERFORMANCE DEGRADATION (as data grows)")
print("=" * 80)

if all(results['scales'][s]['neo4j'].get('success') for s in TEST_SCALES):
    print(f"\n📊 Neo4j Query Time Growth:")
    print(f"   {'Chunks':<10} {'Query Time':<15} {'Growth Rate':<20}")
    print(f"   {'-'*10} {'-'*15} {'-'*20}")

    prev_time = None
    for scale in TEST_SCALES:
        query_time = results['scales'][scale]['neo4j']['avg_query_time'] * 1000
        if prev_time:
            growth = query_time / prev_time
            growth_str = f"{growth:.2f}x slower"
        else:
            growth_str = "baseline"

        print(f"   {scale:<10,} {query_time:<15.1f}ms {growth_str:<20}")
        prev_time = query_time

# =============================================================================
# GO/NO-GO DECISION CRITERIA
# =============================================================================

print(f"\n" + "=" * 80)
print("GO/NO-GO DECISION FOR 10,924 CHUNKS")
print("=" * 80)

# Check if 1000-chunk test passed
if 1000 in results['scales'] and results['scales'][1000]['neo4j'].get('success'):
    neo4j_1000_time = results['scales'][1000]['neo4j']['avg_query_time'] * 1000

    print(f"\n📊 Neo4j @ 1,000 chunks: {neo4j_1000_time:.1f}ms average query time")

    # Extrapolate to 10,924 chunks (assuming logarithmic growth for HNSW)
    # HNSW complexity is O(log n), so growth should be sub-linear
    estimated_10k_time = neo4j_1000_time * np.log(10924) / np.log(1000)

    print(f"📈 Estimated @ 10,924 chunks: {estimated_10k_time:.1f}ms (extrapolated)")

    # Decision criteria
    print(f"\n🎯 Decision Criteria:")
    print(f"   ✅ Good:      < 100ms")
    print(f"   ⚠️  Acceptable: 100-300ms")
    print(f"   ❌ Too slow:  > 300ms")

    print(f"\n🚦 VERDICT:")
    if estimated_10k_time < 100:
        print(f"   ✅ GO - Neo4j will be FAST at full scale ({estimated_10k_time:.1f}ms)")
        print(f"   Recommended: Proceed with Neo4j consolidation")
    elif estimated_10k_time < 300:
        print(f"   ⚠️  CONDITIONAL GO - Neo4j acceptable but not optimal ({estimated_10k_time:.1f}ms)")
        print(f"   Recommended: Proceed if unified architecture is priority")
        print(f"   Alternative: Keep ChromaDB if pure speed is critical")
    else:
        print(f"   ❌ NO-GO - Neo4j too slow at scale ({estimated_10k_time:.1f}ms)")
        print(f"   Recommended: Keep ChromaDB for vector storage")

    # Compare to current hybrid approach
    print(f"\n📌 Current Architecture (ChromaDB + Neo4j dual-DB):")
    if 1000 in results['scales'] and results['scales'][1000]['chromadb'].get('success'):
        chroma_1000_time = results['scales'][1000]['chromadb']['avg_query_time'] * 1000
        estimated_hybrid = chroma_1000_time + 100 + 50  # Vector + Graph + Fusion
        print(f"   ChromaDB vector search: {chroma_1000_time:.1f}ms")
        print(f"   + Neo4j graph traversal: ~100ms")
        print(f"   + Python fusion: ~50ms")
        print(f"   = Total hybrid: ~{estimated_hybrid:.1f}ms")

        print(f"\n📌 Proposed Architecture (Neo4j unified):")
        print(f"   Single Neo4j query (vector + graph): ~{estimated_10k_time + 100:.1f}ms")

        if (estimated_10k_time + 100) < estimated_hybrid:
            improvement = ((estimated_hybrid - (estimated_10k_time + 100)) / estimated_hybrid) * 100
            print(f"   ✅ {improvement:.0f}% FASTER than current hybrid approach!")
        else:
            degradation = (((estimated_10k_time + 100) - estimated_hybrid) / estimated_hybrid) * 100
            print(f"   ⚠️  {degradation:.0f}% slower than current hybrid approach")

else:
    print(f"❌ 1000-chunk test failed - cannot extrapolate to full scale")

# Save results
output_file = PROJECT_ROOT / "docs" / "performance" / "scale_test_chromadb_vs_neo4j.json"
with open(output_file, 'w') as f:
    # Convert numpy types for JSON serialization
    json_results = {}
    for scale, data in results['scales'].items():
        json_results[str(scale)] = {
            'chunk_count': data['chunk_count'],
            'embedding_time': float(data['embedding_generation_time']),
            'chromadb': {
                k: (float(v) if isinstance(v, (np.floating, float)) else
                    [float(x) for x in v] if isinstance(v, list) else v)
                for k, v in data['chromadb'].items()
            } if data['chromadb'] else {},
            'neo4j': {
                k: (float(v) if isinstance(v, (np.floating, float)) else
                    [float(x) for x in v] if isinstance(v, list) else v)
                for k, v in data['neo4j'].items()
            } if data['neo4j'] else {}
        }

    final_results = {
        'test_query': results['test_query'],
        'scales': json_results
    }
    json.dump(final_results, f, indent=2)

print(f"\n💾 Detailed results saved to: {output_file}")
print(f"\n✨ Scale test completed!")
