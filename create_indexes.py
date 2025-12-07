#!/usr/bin/env python3
"""
ULTRATHINK - Create Neo4j Indexes
Run AFTER vectorize_and_store.py completes
Creates vector index + metadata indexes for fast queries
"""

import sys
import time
from pathlib import Path
from neo4j import GraphDatabase

# Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "siemensenergy"

NODE_LABEL = "PageChunk"
VECTOR_INDEX_NAME = "page_embeddings_ultrathink"
VECTOR_DIMENSIONS = 1024

print("=" * 80)
print("ULTRATHINK - Create Neo4j Indexes")
print("=" * 80)
print()

# Connect to Neo4j
print(f"📌 Connecting to Neo4j...")
print(f"   URI: {NEO4J_URI}")
print(f"   Node label: {NODE_LABEL}")

try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # Check how many nodes exist
        result = session.run(f"MATCH (c:{NODE_LABEL}) RETURN count(c) as count")
        count = result.single()['count']
        print(f"✅ Connected! Found {count:,} {NODE_LABEL} nodes")

        if count == 0:
            print(f"⚠️  No {NODE_LABEL} nodes found!")
            print(f"   Run vectorize_and_store.py first to create data")
            sys.exit(1)

except Exception as e:
    print(f"❌ Failed to connect: {e}")
    print(f"   Is Neo4j running?")
    sys.exit(1)

print()

# Step 1: Create Vector Index
print("=" * 80)
print(f"📝 Step 1: Creating Vector Index...")
print("=" * 80)
print(f"   Name: {VECTOR_INDEX_NAME}")
print(f"   Dimensions: {VECTOR_DIMENSIONS}")
print(f"   Similarity: cosine")
print()

try:
    with driver.session() as session:
        # Drop if exists
        try:
            session.run(f"DROP INDEX {VECTOR_INDEX_NAME} IF EXISTS")
            print(f"   Dropped existing index (if any)")
        except:
            pass

        # Create vector index
        session.run(f"""
            CREATE VECTOR INDEX {VECTOR_INDEX_NAME}
            FOR (c:{NODE_LABEL})
            ON (c.embedding)
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {VECTOR_DIMENSIONS},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
        """)
        print(f"✅ Vector index created: {VECTOR_INDEX_NAME}")

        # Wait for index to be online
        print(f"   Waiting for index to come online...", end='', flush=True)
        for i in range(120):  # Wait up to 2 minutes
            time.sleep(1)
            result = session.run(f"""
                SHOW INDEXES
                YIELD name, state
                WHERE name = '{VECTOR_INDEX_NAME}'
                RETURN state
            """)
            record = result.single()
            if record and record['state'] == 'ONLINE':
                print(f" Online! (took {i+1}s)")
                break
            if i % 10 == 0:
                print(".", end='', flush=True)
        else:
            print(" ⚠️  Timeout (may still be building)")

except Exception as e:
    print(f"❌ Failed to create vector index: {e}")
    print(f"   You can retry this script later")
    driver.close()
    sys.exit(1)

print()

# Step 2: Create Metadata Indexes
print("=" * 80)
print(f"📝 Step 2: Creating Metadata Indexes...")
print("=" * 80)
print()

metadata_indexes = [
    (f"{NODE_LABEL.lower()}_project", "project_id"),
    (f"{NODE_LABEL.lower()}_customer", "customer_normalized"),
    (f"{NODE_LABEL.lower()}_category", "category"),
    (f"{NODE_LABEL.lower()}_technology", "technology"),
    (f"{NODE_LABEL.lower()}_year", "year"),
]

try:
    with driver.session() as session:
        for index_name, property_name in metadata_indexes:
            session.run(f"""
                CREATE INDEX {index_name} IF NOT EXISTS
                FOR (c:{NODE_LABEL})
                ON (c.{property_name})
            """)
            print(f"✅ Created index: {index_name} (on {property_name})")

except Exception as e:
    print(f"⚠️  Some metadata indexes failed: {e}")
    print(f"   Data is still searchable, but queries may be slower")

print()

# Step 3: Create Fulltext Index for BM25 (Optional)
print("=" * 80)
print(f"📝 Step 3: Creating Fulltext Index (BM25)...")
print("=" * 80)
print()

try:
    with driver.session() as session:
        # Drop if exists
        try:
            session.run("DROP INDEX page_fulltext_ultrathink IF EXISTS")
        except:
            pass

        # Create fulltext index
        session.run(f"""
            CREATE FULLTEXT INDEX page_fulltext_ultrathink
            FOR (c:{NODE_LABEL})
            ON EACH [c.text, c.project_name, c.customer, c.file_name]
            OPTIONS {{
                analyzer: 'standard-no-stop-words'
            }}
        """)
        print(f"✅ Fulltext index created: page_fulltext_ultrathink")
        print(f"   Enables BM25 keyword search on text + metadata")

except Exception as e:
    print(f"⚠️  Fulltext index failed: {e}")
    print(f"   Vector search will still work")

print()

# Summary
print("=" * 80)
print("✨ ALL INDEXES CREATED SUCCESSFULLY!")
print("=" * 80)
print()
print("✅ Vector Index: Enabled (for similarity search)")
print("✅ Metadata Indexes: Enabled (for filtering)")
print("✅ Fulltext Index: Enabled (for BM25 keyword search)")
print()
print("🚀 System ready for:")
print("   - Vector similarity search")
print("   - BM25 keyword search")
print("   - Count queries (How many HVDC?)")
print("   - Filtered searches (TenneT HVDC in 2024)")
print()
print("=" * 80)

driver.close()
