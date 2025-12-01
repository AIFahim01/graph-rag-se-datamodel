#!/usr/bin/env python3
"""
ULTRATHINK Full Vectorization - All 240,806 Pages
Background-safe with logging, checkpointing, and failure recovery
Supports: Vector search + BM25 + Count queries
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import numpy as np
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/vectorization_full.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "graph-rag-se-datamodel" / "src"))

from sentence_transformers import SentenceTransformer
from storage.neo4j_vector_store_flexible import Neo4jVectorStoreFlexible

print("=" * 80)
print("ULTRATHINK FULL VECTORIZATION: 240,806 Pages")
print("=" * 80)

# Configuration
MARKDOWN_DIR = project_root / "output"
BATCH_SIZE = 1000  # Pages per batch
CHECKPOINT_FILE = project_root / "logs" / "checkpoint.json"
STATS_FILE = project_root / "logs" / "vectorization_stats.json"

NODE_LABEL = "PageChunk"
INDEX_NAME = "page_embeddings_ultrathink"

# Load checkpoint if exists
checkpoint = {}
if CHECKPOINT_FILE.exists():
    with open(CHECKPOINT_FILE, 'r') as f:
        checkpoint = json.load(f)
    logger.info(f"📂 Loaded checkpoint: {checkpoint.get('pages_processed', 0)} pages completed")
else:
    logger.info("🆕 Starting fresh vectorization")

# Step 1: Scan all page files
logger.info(f"\n📌 Step 1: Scanning all page files in {MARKDOWN_DIR}")
all_page_files = sorted(list(MARKDOWN_DIR.rglob("*page *.md")))
logger.info(f"✅ Found {len(all_page_files)} total page files")

# Resume from checkpoint
processed_files = set(checkpoint.get('processed_files', []))
remaining_files = [f for f in all_page_files if str(f) not in processed_files]

logger.info(f"📊 Status:")
logger.info(f"   Total pages: {len(all_page_files)}")
logger.info(f"   Already processed: {len(processed_files)}")
logger.info(f"   Remaining: {len(remaining_files)}")

if len(remaining_files) == 0:
    logger.info("✅ All pages already processed!")
    sys.exit(0)

# Step 2: Load model
logger.info(f"\n📌 Step 2: Loading BGE model...")
model = SentenceTransformer('BAAI/bge-large-en-v1.5')
logger.info(f"✅ Model loaded (1024 dimensions)")

# Step 3: Connect to Neo4j
logger.info(f"\n📌 Step 3: Connecting to Neo4j...")
vector_store = Neo4jVectorStoreFlexible(
    uri="bolt://localhost:7687",
    auth=None,
    node_label=NODE_LABEL
)

# Create indexes if first run
if not checkpoint:
    logger.info(f"📝 Creating vector index: {INDEX_NAME}")
    vector_store.create_vector_index(index_name=INDEX_NAME, dimensions=1024)

    logger.info(f"📝 Creating metadata indexes...")
    vector_store.create_metadata_indexes()

# Step 4: Process in batches
logger.info(f"\n📌 Step 4: Processing {len(remaining_files)} pages in batches...")

start_time = time.time()
all_chunks = []
all_embeddings = []
processed_count = 0
error_count = 0
total_batches = (len(remaining_files) + BATCH_SIZE - 1) // BATCH_SIZE

for batch_num, i in enumerate(range(0, len(remaining_files), BATCH_SIZE)):
    batch_files = remaining_files[i:i+BATCH_SIZE]
    batch_chunks = []

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"BATCH {batch_num + 1}/{total_batches} ({((batch_num + 1) / total_batches * 100):.1f}%)")
    logger.info("=" * 80)

    # Process files in batch
    for page_file in tqdm(batch_files, desc=f"Batch {batch_num + 1}", ncols=80):
        try:
            # Extract project folder (GC24_005_ProjectName)
            project_folder = None
            for part in page_file.parts:
                if part.startswith('GC') and len(part) > 6 and part[2:4].isdigit() and part[5:8].isdigit():
                    project_folder = part
                    break

            if not project_folder:
                continue

            # Extract page number
            page_match = re.search(r'page (\d+)', page_file.stem)
            if not page_match:
                continue

            page_number = int(page_match.group(1))

            # Read page content
            with open(page_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if len(content) < 50:
                continue

            # Extract document name
            doc_name = page_file.stem.rsplit(' - page', 1)[0]

            # Read metadata.json
            metadata_file = page_file.parent / f"{doc_name} - metadata.json"
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

            # Extract project info
            parts = project_folder.split('_', 2)
            project_id = '_'.join(parts[:2]) if len(parts) >= 2 else project_folder
            project_name = parts[2] if len(parts) >= 3 else project_folder

            # Extract YEAR from project_id (GC24_005 → 2024)
            year = None
            year_match = re.search(r'GC(\d{2})_', project_id)
            if year_match:
                year = 2000 + int(year_match.group(1))

            # Extract customer
            customer_parts = project_name.split('_')
            customer = customer_parts[0] if customer_parts else "Unknown"

            # Determine technology and category
            project_lower = project_folder.lower()
            if 'hvdc' in project_lower:
                technology = 'HVDC'
                category = 'hvdc'
            elif 'syncon' in project_lower or 'synchronous' in project_lower:
                technology = 'SynCon'
                category = 'syncon'
            elif 'svc' in project_lower or 'statcom' in project_lower:
                technology = 'SVC/STATCOM'
                category = 'facts'
            else:
                technology = 'Other'
                category = 'other'

            # Document type from path
            doc_path_lower = str(page_file).lower()
            if 'contract' in doc_path_lower or 'auftrag' in doc_path_lower:
                doc_type = 'contract'
            elif 'data' in doc_path_lower or 'technical' in doc_path_lower:
                doc_type = 'technical'
            elif 'deliverable' in doc_path_lower:
                doc_type = 'deliverable'
            else:
                doc_type = 'other'

            # Build relative image path
            page_image_name = f"{doc_name} - page {page_number}.png"
            page_image_relative = str(page_file.parent / "pages" / page_image_name).replace(str(MARKDOWN_DIR) + "/", "")

            # Create chunk
            chunk = {
                'chunk_id': f"{project_id}_{doc_name}_page{page_number}",
                'text': content[:2000],
                'page': page_number,
                'project_id': project_id,
                'project_name': project_name,
                'year': year,  # NEW - For year-based queries
                'customer': customer,
                'customer_normalized': customer.lower(),
                'category': category,
                'technology': technology,
                'document_type': doc_type,
                'source_file': doc_name,
                'page_file': page_file.name,

                # From metadata.json
                'file_name': metadata.get('file_name', doc_name),
                'file_path': metadata.get('file_path', ''),
                'extracted_at': metadata.get('extracted_at', ''),
                'total_pages': metadata.get('pages', 0),
                'total_images': metadata.get('images', 0),
                'total_tables': metadata.get('tables', 0),
                'relative_parents': metadata.get('relative_parents', []),

                # Page image path
                'page_image_relative': page_image_relative
            }

            batch_chunks.append(chunk)
            processed_count += 1

        except Exception as e:
            error_count += 1
            logger.error(f"Error processing {page_file.name}: {e}")
            continue

    if not batch_chunks:
        logger.warning(f"Batch {batch_num + 1} empty, skipping...")
        continue

    # Generate embeddings for batch
    logger.info(f"🧠 Generating embeddings for {len(batch_chunks)} pages...")
    texts = [chunk['text'][:512] for chunk in batch_chunks]
    batch_embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)

    # Store in Neo4j
    logger.info(f"💾 Storing {len(batch_chunks)} chunks to Neo4j...")
    vector_store.store_chunk_batch(batch_chunks, batch_embeddings)

    # Update checkpoint
    processed_files.update([str(f) for f in batch_files])
    checkpoint = {
        'last_batch': batch_num + 1,
        'pages_processed': len(processed_files),
        'processed_files': list(processed_files),
        'errors': error_count,
        'timestamp': datetime.now().isoformat()
    }

    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f)

    # Statistics
    elapsed = time.time() - start_time
    speed = processed_count / elapsed if elapsed > 0 else 0
    remaining = len(remaining_files) - processed_count
    eta_seconds = remaining / speed if speed > 0 else 0

    logger.info(f"")
    logger.info(f"📊 PROGRESS REPORT:")
    logger.info(f"   Pages processed: {len(processed_files)}/{len(all_page_files)} ({len(processed_files)/len(all_page_files)*100:.1f}%)")
    logger.info(f"   This batch: {len(batch_chunks)} pages")
    logger.info(f"   Errors: {error_count}")
    logger.info(f"   Speed: {speed:.2f} pages/sec")
    logger.info(f"   Elapsed: {elapsed/60:.1f} minutes")
    logger.info(f"   ETA: {eta_seconds/60:.1f} minutes remaining")
    logger.info("=" * 80)

# Final summary
vector_store.close()
total_time = time.time() - start_time

logger.info("")
logger.info("=" * 80)
logger.info("✨ ULTRATHINK FULL VECTORIZATION COMPLETE!")
logger.info("=" * 80)
logger.info(f"📊 Final Statistics:")
logger.info(f"   Total pages processed: {len(processed_files)}")
logger.info(f"   Errors: {error_count} ({error_count/len(all_page_files)*100:.2f}%)")
logger.info(f"   Total time: {total_time/3600:.2f} hours")
logger.info(f"   Average speed: {len(processed_files)/total_time:.2f} pages/sec")
logger.info(f"")
logger.info(f"🔍 Neo4j Details:")
logger.info(f"   Node label: {NODE_LABEL}")
logger.info(f"   Index name: {INDEX_NAME}")
logger.info(f"   Total chunks: {len(processed_files)}")
logger.info("=" * 80)

# Save final stats
final_stats = {
    'total_pages': len(all_page_files),
    'processed': len(processed_files),
    'errors': error_count,
    'total_time_hours': total_time / 3600,
    'average_speed': len(processed_files) / total_time,
    'completed_at': datetime.now().isoformat()
}

with open(STATS_FILE, 'w') as f:
    json.dump(final_stats, f, indent=2)

logger.info(f"💾 Stats saved to: {STATS_FILE}")
