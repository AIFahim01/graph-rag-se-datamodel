#!/usr/bin/env python3
"""
ULTRATHINK - Restore Embeddings from Local Backup to Neo4j
Restores PageChunk nodes from backup files
"""

import sys
import json
import numpy as np
from pathlib import Path
from tqdm import tqdm
from neo4j import GraphDatabase

if len(sys.argv) < 2:
    print("Usage: python restore_embeddings.py <backup_directory>")
    print("Example: python restore_embeddings.py backups/ultrathink_backup_20251128_153045")
    sys.exit(1)

backup_dir = Path(sys.argv[1])

if not backup_dir.exists():
    print(f"❌ Backup directory not found: {backup_dir}")
    sys.exit(1)

print("=" * 80)
print("ULTRATHINK - Restore Embeddings from Backup")
print("=" * 80)
print(f"📂 Source: {backup_dir}")
print()

# Load backup info
info_file = backup_dir / "backup_info.json"
with open(info_file, 'r') as f:
    info = json.load(f)

print(f"📋 Backup Info:")
print(f"   Date: {info['backup_date']}")
print(f"   Chunks: {info['total_chunks']:,}")
print(f"   Embeddings: {info['total_embeddings']:,}")
print(f"   Embedding dim: {info['embedding_dim']}")
print()

# Load data
print(f"📌 Loading backup files...")
chunks_file = backup_dir / info['files']['metadata']
embeddings_file = backup_dir / info['files']['embeddings']

with open(chunks_file, 'r') as f:
    chunks = json.load(f)
print(f"✅ Loaded metadata: {len(chunks):,} chunks")

embeddings = np.load(embeddings_file)
print(f"✅ Loaded embeddings: {embeddings.shape}")
print()

# Connect to Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "siemensenergy"
NODE_LABEL = info.get('node_label', 'PageChunk')

print(f"📌 Connecting to Neo4j...")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Ask for confirmation
print()
print(f"⚠️  This will create {len(chunks):,} {NODE_LABEL} nodes in Neo4j")
response = input("Continue? (yes/no): ")
if response.lower() != 'yes':
    print("Cancelled.")
    sys.exit(0)

print()
print(f"📌 Restoring to Neo4j...")

BATCH_SIZE = 1000
with driver.session() as session:
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Restoring"):
        batch_chunks = chunks[i:i+BATCH_SIZE]
        batch_embeddings = embeddings[i:i+BATCH_SIZE]

        for chunk, embedding in zip(batch_chunks, batch_embeddings):
            session.run(f"""
                CREATE (c:{NODE_LABEL} {{
                    chunk_id: $chunk_id,
                    text: $text,
                    embedding: $embedding,
                    page: $page,
                    project_id: $project_id,
                    project_name: $project_name,
                    year: $year,
                    customer: $customer,
                    customer_normalized: $customer_normalized,
                    category: $category,
                    technology: $technology,
                    file_name: $file_name,
                    total_pages: $total_pages,
                    total_images: $total_images,
                    total_tables: $total_tables,
                    page_image_relative: $page_image_relative
                }})
            """,
                chunk_id=chunk['chunk_id'],
                text=chunk['text'],
                embedding=embedding.tolist(),
                page=chunk['page'],
                project_id=chunk['project_id'],
                project_name=chunk['project_name'],
                year=chunk['year'],
                customer=chunk['customer'],
                customer_normalized=chunk.get('customer', ''),
                category=chunk['category'],
                technology=chunk['technology'],
                file_name=chunk['file_name'],
                total_pages=chunk['total_pages'],
                total_images=chunk['total_images'],
                total_tables=chunk['total_tables'],
                page_image_relative=chunk['page_image_relative']
            )

driver.close()

print()
print("=" * 80)
print("✨ RESTORE COMPLETE!")
print("=" * 80)
print(f"✅ Restored {len(chunks):,} PageChunk nodes")
print(f"✅ All embeddings restored")
print()
print("🚀 Next: Run create_indexes.py to enable search")
