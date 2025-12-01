#!/usr/bin/env python3
"""
ULTRATHINK - Continuous Backup Monitor
Runs alongside vectorization, backs up every 30 minutes
Keeps rolling backups (last 5) to save disk space
"""

import sys
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase

# Configuration
BACKUP_INTERVAL = 1800  # 30 minutes in seconds
MAX_BACKUPS = 5  # Keep last 5 backups only
MIN_BATCH_INTERVAL = 25  # Or backup every 25 batches

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "siemensenergy"
NODE_LABEL = "PageChunk"

CHECKPOINT_FILE = Path(__file__).parent / "logs" / "checkpoint.json"
BACKUP_DIR = Path(__file__).parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("ULTRATHINK - Continuous Backup Monitor")
print("=" * 80)
print(f"📂 Backup directory: {BACKUP_DIR}")
print(f"⏱️  Interval: {BACKUP_INTERVAL/60:.0f} minutes or {MIN_BATCH_INTERVAL} batches")
print(f"💾 Keeping: Last {MAX_BACKUPS} backups")
print()
print("Press Ctrl+C to stop")
print("=" * 80)
print()

last_backup_batch = 0
last_backup_time = 0

try:
    while True:
        # Check if checkpoint exists
        if not CHECKPOINT_FILE.exists():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for vectorization to start...")
            time.sleep(60)
            continue

        # Read checkpoint
        with open(CHECKPOINT_FILE, 'r') as f:
            checkpoint = json.load(f)

        current_batch = checkpoint.get('last_batch', 0)
        pages_processed = checkpoint.get('pages_processed', 0)
        current_time = time.time()

        # Determine if should backup
        batch_diff = current_batch - last_backup_batch
        time_diff = current_time - last_backup_time

        should_backup = False
        backup_reason = ""

        if batch_diff >= MIN_BATCH_INTERVAL:
            should_backup = True
            backup_reason = f"{batch_diff} batches completed"
        elif time_diff >= BACKUP_INTERVAL and current_batch > last_backup_batch:
            should_backup = True
            backup_reason = f"{time_diff/60:.0f} minutes elapsed"

        if not should_backup:
            # Show status
            next_batch_backup = last_backup_batch + MIN_BATCH_INTERVAL
            next_time_backup = (last_backup_time + BACKUP_INTERVAL - current_time) / 60
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: Batch {current_batch}/241, {pages_processed:,} pages | Next backup: batch {next_batch_backup} or {next_time_backup:.0f}m", end='\r')
            time.sleep(30)  # Check every 30 seconds
            continue

        # Perform backup
        print()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📌 Starting backup: {backup_reason}")

        # Connect to Neo4j
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

        # Count nodes
        with driver.session() as session:
            result = session.run(f"MATCH (c:{NODE_LABEL}) RETURN count(c) as count")
            node_count = result.single()['count']

        print(f"   Nodes to backup: {node_count:,}")

        # Create backup directory
        backup_name = f"incremental_batch_{current_batch:03d}_{TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')}"
        current_backup_path = BACKUP_DIR / backup_name
        current_backup_path.mkdir(exist_ok=True)

        # Export data
        all_chunks = []
        all_embeddings = []

        with driver.session() as session:
            result = session.run(f"MATCH (c:{NODE_LABEL}) RETURN c")

            for idx, record in enumerate(result):
                node = record['c']

                chunk_data = {
                    'chunk_id': node['chunk_id'],
                    'text': node['text'],
                    'page': node.get('page', 0),
                    'project_id': node.get('project_id', ''),
                    'year': node.get('year'),
                    'customer': node.get('customer', ''),
                    'technology': node.get('technology', ''),
                    'embedding_index': idx
                }

                all_chunks.append(chunk_data)

                if node.get('embedding'):
                    all_embeddings.append(node['embedding'])

        driver.close()

        # Save files
        with open(current_backup_path / "chunks_metadata.json", 'w') as f:
            json.dump(all_chunks, f)

        if all_embeddings:
            embeddings_array = np.array(all_embeddings, dtype=np.float32)
            np.save(current_backup_path / "embeddings.npy", embeddings_array)

        # Save backup info
        with open(current_backup_path / "backup_info.json", 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'batch': current_batch,
                'pages': pages_processed,
                'chunks': len(all_chunks),
                'embeddings': len(all_embeddings)
            }, f, indent=2)

        print(f"   ✅ Backup saved: {backup_name}")

        # Clean old backups (keep last 5)
        all_backups = sorted([d for d in BACKUP_DIR.iterdir() if d.is_dir() and d.name.startswith('incremental')])
        if len(all_backups) > MAX_BACKUPS:
            for old_backup in all_backups[:-MAX_BACKUPS]:
                print(f"   🗑️  Removing old backup: {old_backup.name}")
                import shutil
                shutil.rmtree(old_backup)

        last_backup_batch = current_batch
        last_backup_time = current_time

        print(f"   📊 Backups: {min(len(all_backups), MAX_BACKUPS)}/{MAX_BACKUPS} kept")
        print()

except KeyboardInterrupt:
    print("\n\n✅ Continuous backup stopped")
    print(f"Last backup: Batch {last_backup_batch}")
