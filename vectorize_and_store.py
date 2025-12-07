#!/usr/bin/env python3
"""
ULTRATHINK Vectorization - Data Storage Only (No Indexing)
Processes all 240,806 pages and stores in Neo4j
Indexing done separately with create_indexes.py
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
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'vectorize_data.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "graph-rag-se-datamodel" / "src"))

from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

logger.info("=" * 80)
logger.info("ULTRATHINK VECTORIZATION - DATA STORAGE (No Indexing)")
logger.info("=" * 80)

# Configuration
MARKDOWN_DIR = project_root / "output"
BATCH_SIZE = 1000  # Pages per batch
CHECKPOINT_FILE = LOG_DIR / "checkpoint.json"
STATS_FILE = LOG_DIR / "vectorization_stats.json"

NODE_LABEL = "PageChunk"

# Neo4j connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "siemensenergy"

# Try to load checkpoint
checkpoint = {}
if CHECKPOINT_FILE.exists():
    with open(CHECKPOINT_FILE, 'r') as f:
        checkpoint = json.load(f)
    logger.info(f"📂 Resuming from checkpoint: {checkpoint.get('pages_processed', 0)} pages completed")
else:
    logger.info("🆕 Starting fresh vectorization")

# Step 1: Scan all page files
logger.info(f"\n📌 Step 1: Scanning for page files in {MARKDOWN_DIR}")
all_page_files = []

# Scan all year folders
for year_folder in ['GC_2021', 'GC_2022', 'GC_2024', 'GC_2025', 'GC_ETC_2024', 'GC_ETC_2025']:
    year_path = MARKDOWN_DIR / year_folder
    if year_path.exists():
        page_files = list(year_path.rglob("*page *.md"))
        all_page_files.extend(page_files)
        logger.info(f"   {year_folder}: {len(page_files)} pages")

all_page_files = sorted(all_page_files)
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

# Step 2: Load embedding model
logger.info(f"\n📌 Step 2: Loading embedding model...")
logger.info(f"   Model: BAAI/bge-large-en-v1.5")
logger.info(f"   Dimensions: 1024")

import torch

# Force CPU - Blackwell GPUs not yet supported by sentence-transformers
logger.info(f"   Device: CPU (Blackwell GPU support coming soon)")
logger.info(f"   Note: You have 4x RTX PRO 6000 GPUs ready for future use!")

model = SentenceTransformer('BAAI/bge-large-en-v1.5', device='cpu')
logger.info(f"✅ Model loaded on CPU")

# Step 3: Connect to Neo4j (No index creation!)
logger.info(f"\n📌 Step 3: Connecting to Neo4j...")
logger.info(f"   URI: {NEO4J_URI}")
logger.info(f"   Node label: {NODE_LABEL}")

try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    # Test connection
    with driver.session() as session:
        session.run("RETURN 1")
    logger.info(f"✅ Neo4j connected")
except Exception as e:
    logger.error(f"❌ Failed to connect to Neo4j: {e}")
    logger.error(f"   Check: Is Neo4j running? Are credentials correct?")
    sys.exit(1)

# Step 4: Process and store pages (NO INDEXING)
logger.info(f"\n📌 Step 4: Processing {len(remaining_files)} pages...")
logger.info(f"   Batch size: {BATCH_SIZE} pages")
logger.info(f"   ⚠️  NO INDEXING - Data storage only!")
logger.info(f"   Run create_indexes.py after this completes")

start_time = time.time()
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
                if part.startswith('GC') and len(part) > 6:
                    if part[2:4].isdigit() and '_' in part and part[5:8].isdigit():
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

            # Extract YEAR from project_id
            year = None
            year_match = re.search(r'GC(\d{2})_', project_id)
            if year_match:
                year_int = int(year_match.group(1))
                year = 2000 + year_int if year_int >= 20 else 1900 + year_int

            # Extract customer
            customer_parts = project_name.split('_')
            customer = customer_parts[0] if customer_parts else "Unknown"

            # Determine technology
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

            # Create chunk (will embed and store)
            chunk = {
                'chunk_id': f"{project_id}_{doc_name}_page{page_number}",
                'text': content[:2000],
                'page': page_number,
                'project_id': project_id,
                'project_name': project_name,
                'year': year,
                'customer': customer,
                'customer_normalized': customer.lower(),
                'category': category,
                'technology': technology,
                'document_type': doc_type,
                'source_file': doc_name,
                'page_file': page_file.name,
                'file_name': metadata.get('file_name', doc_name),
                'file_path': metadata.get('file_path', ''),
                'extracted_at': metadata.get('extracted_at', ''),
                'total_pages': metadata.get('pages', 0),
                'total_images': metadata.get('images', 0),
                'total_tables': metadata.get('tables', 0),
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

    # Generate embeddings
    logger.info(f"🧠 Generating {len(batch_chunks)} embeddings...")
    texts = [chunk['text'][:512] for chunk in batch_chunks]
    batch_embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)

    # Store in Neo4j (No index operations!)
    logger.info(f"💾 Storing {len(batch_chunks)} chunks to Neo4j...")

    with driver.session() as session:
        for chunk, embedding in zip(batch_chunks, batch_embeddings):
            # Simple CREATE (no index needed)
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
                    document_type: $document_type,
                    source_file: $source_file,
                    page_file: $page_file,
                    file_name: $file_name,
                    file_path: $file_path,
                    extracted_at: $extracted_at,
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
                customer_normalized=chunk['customer_normalized'],
                category=chunk['category'],
                technology=chunk['technology'],
                document_type=chunk['document_type'],
                source_file=chunk['source_file'],
                page_file=chunk['page_file'],
                file_name=chunk['file_name'],
                file_path=chunk['file_path'],
                extracted_at=chunk['extracted_at'],
                total_pages=chunk['total_pages'],
                total_images=chunk['total_images'],
                total_tables=chunk['total_tables'],
                page_image_relative=chunk['page_image_relative']
            )

    logger.info(f"✅ Batch {batch_num + 1} stored successfully")

    # Update checkpoint
    processed_files.update([str(f) for f in batch_files])
    checkpoint = {
        'last_batch': batch_num + 1,
        'pages_processed': len(processed_files),
        'processed_files': list(processed_files),
        'errors': error_count,
        'timestamp': datetime.now().isoformat(),
        'start_time': checkpoint.get('start_time', datetime.now().isoformat())
    }

    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f)

    # Progress report
    elapsed = time.time() - start_time
    speed = processed_count / elapsed if elapsed > 0 else 0
    remaining = len(remaining_files) - processed_count
    eta_seconds = remaining / speed if speed > 0 else 0

    logger.info(f"")
    logger.info(f"PROGRESS REPORT:")
    logger.info(f"   Pages stored: {len(processed_files)}/{len(all_page_files)} ({len(processed_files)/len(all_page_files)*100:.1f}%)")
    logger.info(f"   Batch size: {len(batch_chunks)} pages")
    logger.info(f"   Errors: {error_count} ({error_count/len(all_page_files)*100:.2f}%)")
    logger.info(f"   Speed: {speed:.2f} pages/sec")
    logger.info(f"   Elapsed: {elapsed/60:.1f} minutes")
    logger.info(f"   ETA: {eta_seconds/60:.1f} minutes remaining")
    logger.info("=" * 80)

# Close connection
driver.close()
total_time = time.time() - start_time

# Final summary
logger.info("")
logger.info("=" * 80)
logger.info("✨ VECTORIZATION DATA STORAGE COMPLETE!")
logger.info("=" * 80)
logger.info(f"📊 Statistics:")
logger.info(f"   Total pages: {len(all_page_files)}")
logger.info(f"   Processed: {len(processed_files)}")
logger.info(f"   Errors: {error_count} ({error_count/len(all_page_files)*100:.2f}%)")
logger.info(f"   Time: {total_time/3600:.2f} hours")
logger.info(f"   Speed: {len(processed_files)/total_time:.2f} pages/sec")
logger.info(f"")
logger.info(f"🔍 Neo4j Status:")
logger.info(f"   Node label: {NODE_LABEL}")
logger.info(f"   Chunks stored: {len(processed_files)}")
logger.info(f"   ⚠️  NO INDEXES YET - Run create_indexes.py next!")
logger.info("=" * 80)

# Save final stats
with open(STATS_FILE, 'w') as f:
    json.dump({
        'total_pages': len(all_page_files),
        'processed': len(processed_files),
        'errors': error_count,
        'time_hours': total_time / 3600,
        'speed_pages_per_sec': len(processed_files) / total_time,
        'completed_at': datetime.now().isoformat()
    }, f, indent=2)

logger.info(f"\n💾 Stats saved to: {STATS_FILE}")
logger.info(f"\n🚀 Next step: Run create_indexes.py to enable search")
