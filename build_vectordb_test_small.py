#!/usr/bin/env python3
"""
ULTRATHINK Test Vectorization - Small Data (GC21_001 Project Only)
Creates page-by-page vectors with metadata in separate Neo4j index
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from tqdm import tqdm
import numpy as np

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "graph-rag-se-datamodel" / "src"))

from sentence_transformers import SentenceTransformer
from storage.neo4j_vector_store_flexible import Neo4jVectorStoreFlexible

print("=" * 80)
print("ULTRATHINK TEST: PAGE-BY-PAGE VECTORIZATION (GC21_001 ONLY)")
print("=" * 80)

# Configuration
MARKDOWN_DIR = project_root / "output"
TEST_PROJECT = "GC21_001_CCPP_Dils"  # Test with ONE project only
BATCH_SIZE = 50  # Smaller batches for test
NODE_LABEL = "PageChunk"  # NEW label (separate from old "Chunk")
INDEX_NAME = "page_embeddings_ultrathink"  # NEW index

# Step 1: Scan for test project page files
print(f"\n📌 Step 1: Scanning for {TEST_PROJECT} page files...")
print(f"   Input: {MARKDOWN_DIR}")

# Find all page files in test project (search in GC_2021 folder)
test_project_path = MARKDOWN_DIR / "GC_2021" / TEST_PROJECT
if test_project_path.exists():
    all_page_files = list(test_project_path.rglob("*page *.md"))
else:
    # Fallback: search everywhere
    all_page_files = [f for f in MARKDOWN_DIR.rglob("*page *.md") if TEST_PROJECT in str(f)]

print(f"✅ Found {len(all_page_files)} page files in test project")

if len(all_page_files) == 0:
    print(f"❌ No page files found for {TEST_PROJECT}")
    sys.exit(1)

# Step 2: Process page files and extract metadata
print(f"\n📌 Step 2: Processing {TEST_PROJECT} pages with metadata...")

all_chunks = []
processed_count = 0
skipped_count = 0

for page_file in tqdm(all_page_files, desc="Processing pages"):
    try:
        # Extract project folder (format: GCyy_nnn_ProjectName)
        # Skip year folders like GC_2021, find actual project like GC21_001_CCPP_Dils
        project_folder = None
        for part in page_file.parts:
            # Match pattern: GC followed by 2 digits, underscore, 3 digits
            if part.startswith('GC') and len(part) > 6 and part[2:4].isdigit() and part[5:8].isdigit():
                project_folder = part
                break

        if not project_folder or TEST_PROJECT not in project_folder:
            skipped_count += 1
            continue

        # Extract page number from filename
        page_match = re.search(r'page (\d+)', page_file.stem)
        if not page_match:
            skipped_count += 1
            continue

        page_number = int(page_match.group(1))

        # Read page content
        with open(page_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if len(content) < 50:  # Skip very short pages
            skipped_count += 1
            continue

        # Extract document name
        doc_name = page_file.stem.rsplit(' - page', 1)[0]

        # Read metadata.json if available
        metadata_file = page_file.parent / f"{doc_name} - metadata.json"
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

        # Extract project info from folder name
        parts = project_folder.split('_', 2)
        project_id = '_'.join(parts[:2]) if len(parts) >= 2 else project_folder
        project_name = parts[2] if len(parts) >= 3 else project_folder

        # Extract customer
        customer_parts = project_name.split('_')
        customer = customer_parts[0] if customer_parts else "Unknown"

        # Determine document type from path
        doc_path_lower = str(page_file).lower()
        if 'contract' in doc_path_lower or 'auftrag' in doc_path_lower:
            doc_type = 'contract'
        elif 'data' in doc_path_lower or 'technical' in doc_path_lower:
            doc_type = 'technical'
        elif 'deliverable' in doc_path_lower:
            doc_type = 'deliverable'
        else:
            doc_type = 'other'

        # Determine technology and category
        project_lower = project_folder.lower()
        if 'hvdc' in project_lower:
            technology = 'HVDC'
            category = 'hdvc'
        elif 'syncon' in project_lower or 'synchronous' in project_lower:
            technology = 'SynCon'
            category = 'syncon'
        elif 'svc' in project_lower or 'statcom' in project_lower:
            technology = 'SVC/STATCOM'
            category = 'facts'
        else:
            technology = 'Other'
            category = 'other'

        # Build relative image path
        page_image_name = f"{doc_name} - page {page_number}.png"
        page_image_relative = str(page_file.parent / "pages" / page_image_name).replace(str(MARKDOWN_DIR) + "/", "")

        # Create chunk with rich metadata
        chunk = {
            'chunk_id': f"{project_id}_{doc_name}_page{page_number}",
            'text': content[:2000],  # Limit to 2000 chars
            'page': page_number,
            'project_id': project_id,
            'project_name': project_name,
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

            # Page image path (relative)
            'page_image_relative': page_image_relative
        }
        all_chunks.append(chunk)
        processed_count += 1

    except Exception as e:
        print(f"❌ Error processing {page_file.name}: {e}")
        skipped_count += 1
        continue

print(f"\n✅ Processed {processed_count} pages")
print(f"⚠️  Skipped {skipped_count} pages")
print(f"📊 Total chunks: {len(all_chunks)}")

if len(all_chunks) == 0:
    print("❌ No chunks created. Exiting.")
    sys.exit(1)

# Step 3: Generate embeddings
print(f"\n📌 Step 3: Generating embeddings...")
print(f"   Model: BAAI/bge-large-en-v1.5 (1024 dimensions)")
print(f"   Batch size: {BATCH_SIZE}")

print(f"📥 Loading BGE model...")
model = SentenceTransformer('BAAI/bge-large-en-v1.5')
print(f"✅ Model loaded")

# Generate embeddings in batches
embeddings_list = []
start_time = time.time()

for batch_num in tqdm(range(0, len(all_chunks), BATCH_SIZE), desc="Generating embeddings"):
    batch_chunks = all_chunks[batch_num:batch_num+BATCH_SIZE]
    texts = [chunk['text'][:512] for chunk in batch_chunks]

    batch_embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)
    embeddings_list.append(batch_embeddings)

# Combine all embeddings
all_embeddings = np.vstack(embeddings_list)

embedding_time = time.time() - start_time
print(f"✅ Generated {len(all_embeddings)} embeddings in {embedding_time:.1f} seconds")
print(f"   Shape: {all_embeddings.shape}")

# Step 4: Store in Neo4j with NEW index
print(f"\n📌 Step 4: Storing in Neo4j...")
print(f"   Node Label: {NODE_LABEL} (NEW - separate from old 'Chunk')")
print(f"   Index Name: {INDEX_NAME} (NEW)")

try:
    # Connect to Neo4j with flexible store
    vector_store = Neo4jVectorStoreFlexible(
        uri="bolt://localhost:7687",
        auth=None,
        node_label=NODE_LABEL  # Use new label
    )

    # Create NEW vector index (separate from old one)
    print(f"📝 Creating vector index: {INDEX_NAME}...")
    vector_store.create_vector_index(
        index_name=INDEX_NAME,
        dimensions=1024
    )

    # Create metadata indexes
    print(f"📝 Creating metadata indexes...")
    vector_store.create_metadata_indexes()

    # Store in batches
    print(f"\n💾 Storing {len(all_chunks)} chunks...")
    for batch_num in tqdm(range(0, len(all_chunks), BATCH_SIZE), desc="Storing to Neo4j"):
        batch_chunks = all_chunks[batch_num:batch_num+BATCH_SIZE]
        batch_embeddings = all_embeddings[batch_num:batch_num+BATCH_SIZE]

        vector_store.store_chunk_batch(batch_chunks, batch_embeddings)

    vector_store.close()

    total_time = time.time() - start_time

    print("\n" + "=" * 80)
    print("✨ TEST VECTORIZATION COMPLETE!")
    print("=" * 80)
    print(f"📊 Statistics:")
    print(f"   Project: {TEST_PROJECT}")
    print(f"   Pages processed: {processed_count}")
    print(f"   Chunks created: {len(all_chunks)}")
    print(f"   Processing time: {total_time/60:.1f} minutes")
    print(f"\n🔍 Neo4j Details:")
    print(f"   Node label: {NODE_LABEL}")
    print(f"   Index name: {INDEX_NAME}")
    print(f"   Old data: UNTOUCHED (still using 'Chunk' label)")
    print(f"\n🚀 Next Steps:")
    print(f"   1. Start test backend: python frontend_viewer/backend/api_server_test.py")
    print(f"   2. Start test frontend: cd frontend_viewer/frontend && PORT=3001 npm run dev")
    print(f"   3. Visit: http://localhost:3001")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error storing to Neo4j: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
