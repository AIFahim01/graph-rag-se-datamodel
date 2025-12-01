#!/usr/bin/env python3
"""
ULTRATHINK - Backup Embeddings from Neo4j to Local Files
Exports all PageChunk nodes with embeddings to local storage
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from neo4j import GraphDatabase

# Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "siemensenergy"
NODE_LABEL = "PageChunk"

BACKUP_DIR = Path(__file__).parent / "backups"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

print("=" * 80)
print("ULTRATHINK - Backup Embeddings to Local Storage")
print("=" * 80)
print()

# Create backup directory
BACKUP_DIR.mkdir(exist_ok=True)
backup_path = BACKUP_DIR / f"ultrathink_backup_{TIMESTAMP}"
backup_path.mkdir(exist_ok=True)

print(f"📁 Backup location: {backup_path}")
print()

# Connect to Neo4j
print(f"📌 Connecting to Neo4j...")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Count total nodes
with driver.session() as session:
    result = session.run(f"MATCH (c:{NODE_LABEL}) RETURN count(c) as count")
    total_count = result.single()['count']
    print(f"✅ Found {total_count:,} {NODE_LABEL} nodes")

if total_count == 0:
    print("❌ No data to backup!")
    sys.exit(1)

print()
print(f"📌 Exporting data...")

# Export in batches
BATCH_SIZE = 1000
all_chunks = []
all_embeddings = []
chunk_to_idx = {}

with driver.session() as session:
    # Get all nodes
    result = session.run(f"""
        MATCH (c:{NODE_LABEL})
        RETURN c
    """)

    for idx, record in enumerate(tqdm(result, total=total_count, desc="Exporting")):
        node = record['c']

        # Store metadata
        chunk_data = {
            'chunk_id': node['chunk_id'],
            'text': node['text'],
            'page': node.get('page', 0),
            'project_id': node.get('project_id', ''),
            'project_name': node.get('project_name', ''),
            'year': node.get('year'),
            'customer': node.get('customer', ''),
            'technology': node.get('technology', ''),
            'category': node.get('category', ''),
            'file_name': node.get('file_name', ''),
            'total_pages': node.get('total_pages', 0),
            'total_images': node.get('total_images', 0),
            'total_tables': node.get('total_tables', 0),
            'page_image_relative': node.get('page_image_relative', ''),
            'embedding_index': idx  # Maps to embeddings array
        }

        all_chunks.append(chunk_data)
        chunk_to_idx[node['chunk_id']] = idx

        # Store embedding
        if node.get('embedding'):
            all_embeddings.append(node['embedding'])

driver.close()

print()
print(f"📌 Saving to disk...")

# Save metadata (JSON)
chunks_file = backup_path / "chunks_metadata.json"
with open(chunks_file, 'w') as f:
    json.dump(all_chunks, f, indent=2)
print(f"✅ Saved metadata: {chunks_file} ({len(all_chunks):,} chunks)")

# Save embeddings (NumPy array - efficient!)
if all_embeddings:
    embeddings_array = np.array(all_embeddings, dtype=np.float32)
    embeddings_file = backup_path / "embeddings.npy"
    np.save(embeddings_file, embeddings_array)
    print(f"✅ Saved embeddings: {embeddings_file}")
    print(f"   Shape: {embeddings_array.shape}")
    print(f"   Size: {embeddings_file.stat().st_size / 1024 / 1024:.1f} MB")

# Save chunk_id to index mapping
mapping_file = backup_path / "chunk_to_index.json"
with open(mapping_file, 'w') as f:
    json.dump(chunk_to_idx, f, indent=2)
print(f"✅ Saved index mapping: {mapping_file}")

# Save backup info
info = {
    'backup_timestamp': TIMESTAMP,
    'backup_date': datetime.now().isoformat(),
    'total_chunks': len(all_chunks),
    'total_embeddings': len(all_embeddings),
    'node_label': NODE_LABEL,
    'embedding_dim': len(all_embeddings[0]) if all_embeddings else 0,
    'files': {
        'metadata': 'chunks_metadata.json',
        'embeddings': 'embeddings.npy',
        'mapping': 'chunk_to_index.json'
    }
}

info_file = backup_path / "backup_info.json"
with open(info_file, 'w') as f:
    json.dump(info, f, indent=2)
print(f"✅ Saved backup info: {info_file}")

print()
print("=" * 80)
print("✨ BACKUP COMPLETE!")
print("=" * 80)
print(f"📂 Location: {backup_path}")
print(f"📊 Files:")
print(f"   - chunks_metadata.json ({len(all_chunks):,} chunks)")
print(f"   - embeddings.npy ({embeddings_array.shape if all_embeddings else 'N/A'})")
print(f"   - chunk_to_index.json (mapping)")
print(f"   - backup_info.json (metadata)")
print()
print(f"💾 Total size: {sum(f.stat().st_size for f in backup_path.glob('*')) / 1024 / 1024:.1f} MB")
print("=" * 80)
print()
print("📝 To restore:")
print("   python restore_embeddings.py backups/ultrathink_backup_TIMESTAMP")
