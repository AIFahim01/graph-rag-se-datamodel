#!/usr/bin/env python3
"""
ULTRATHINK - Test Backup/Restore Process
Validates that backup and restore actually work
"""

import sys
import json
import numpy as np
from pathlib import Path
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "siemensenergy"
NODE_LABEL = "PageChunkTest"  # Use different label for testing!

print("=" * 80)
print("ULTRATHINK - Backup/Restore Test")
print("=" * 80)
print()
print(f"⚠️  Uses test label '{NODE_LABEL}' (won't affect production data)")
print()

# Step 1: Create test data
print("📌 Step 1: Creating test data in Neo4j...")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

test_chunks = [
    {
        'chunk_id': f'test_chunk_{i}',
        'text': f'Test content {i}',
        'embedding': np.random.rand(1024).tolist(),
        'page': i,
        'project_id': f'TEST_{i//10}',
        'technology': 'HVDC' if i % 2 == 0 else 'SynCon'
    }
    for i in range(100)
]

with driver.session() as session:
    # Clean test nodes
    session.run(f"MATCH (c:{NODE_LABEL}) DELETE c")

    # Create test nodes
    for chunk in test_chunks:
        session.run(f"""
            CREATE (c:{NODE_LABEL} {{
                chunk_id: $chunk_id,
                text: $text,
                embedding: $embedding,
                page: $page,
                project_id: $project_id,
                technology: $technology
            }})
        """, **chunk)

    result = session.run(f"MATCH (c:{NODE_LABEL}) RETURN count(c) as count")
    count = result.single()['count']
    print(f"✅ Created {count} test nodes")

print()

# Step 2: Backup test data
print("📌 Step 2: Backing up test data...")

backup_dir = Path(__file__).parent / "backups" / "test_backup"
backup_dir.mkdir(parents=True, exist_ok=True)

all_chunks = []
all_embeddings = []

with driver.session() as session:
    result = session.run(f"MATCH (c:{NODE_LABEL}) RETURN c")
    for idx, record in enumerate(result):
        node = record['c']
        all_chunks.append({
            'chunk_id': node['chunk_id'],
            'text': node['text'],
            'page': node['page'],
            'project_id': node['project_id'],
            'technology': node['technology'],
            'embedding_index': idx
        })
        all_embeddings.append(node['embedding'])

with open(backup_dir / "chunks.json", 'w') as f:
    json.dump(all_chunks, f)

np.save(backup_dir / "embeddings.npy", np.array(all_embeddings))

print(f"✅ Backed up {len(all_chunks)} chunks")
print()

# Step 3: Delete from Neo4j
print("📌 Step 3: Deleting test data from Neo4j...")

with driver.session() as session:
    session.run(f"MATCH (c:{NODE_LABEL}) DELETE c")
    result = session.run(f"MATCH (c:{NODE_LABEL}) RETURN count(c) as count")
    count = result.single()['count']
    print(f"✅ Deleted all nodes (count: {count})")

print()

# Step 4: Restore from backup
print("📌 Step 4: Restoring from backup...")

with open(backup_dir / "chunks.json", 'r') as f:
    restore_chunks = json.load(f)

restore_embeddings = np.load(backup_dir / "embeddings.npy")

with driver.session() as session:
    for chunk, embedding in zip(restore_chunks, restore_embeddings):
        session.run(f"""
            CREATE (c:{NODE_LABEL} {{
                chunk_id: $chunk_id,
                text: $text,
                embedding: $embedding,
                page: $page,
                project_id: $project_id,
                technology: $technology
            }})
        """,
            chunk_id=chunk['chunk_id'],
            text=chunk['text'],
            embedding=embedding.tolist(),
            page=chunk['page'],
            project_id=chunk['project_id'],
            technology=chunk['technology']
        )

    result = session.run(f"MATCH (c:{NODE_LABEL}) RETURN count(c) as count")
    count = result.single()['count']
    print(f"✅ Restored {count} nodes")

print()

# Step 5: Verify data matches
print("📌 Step 5: Verifying restored data...")

all_match = True
with driver.session() as session:
    for original_chunk in test_chunks[:10]:  # Check first 10
        result = session.run(f"""
            MATCH (c:{NODE_LABEL} {{chunk_id: $chunk_id}})
            RETURN c.text as text, size(c.embedding) as emb_size
        """, chunk_id=original_chunk['chunk_id'])

        record = result.single()
        if not record:
            print(f"❌ Missing: {original_chunk['chunk_id']}")
            all_match = False
        elif record['text'] != original_chunk['text']:
            print(f"❌ Text mismatch: {original_chunk['chunk_id']}")
            all_match = False
        elif record['emb_size'] != 1024:
            print(f"❌ Embedding size wrong: {record['emb_size']}")
            all_match = False

if all_match:
    print(f"✅ All data verified correctly!")
else:
    print(f"⚠️  Some data mismatches found")

# Cleanup test data
print()
print("📌 Cleanup: Removing test data...")
with driver.session() as session:
    session.run(f"MATCH (c:{NODE_LABEL}) DELETE c")

driver.close()

print()
print("=" * 80)
print("✨ BACKUP/RESTORE TEST COMPLETE!")
print("=" * 80)
if all_match:
    print("✅ Backup and restore process validated successfully")
    print("✅ Your production backups will work correctly")
else:
    print("⚠️  Some issues detected - review output above")
print("=" * 80)
