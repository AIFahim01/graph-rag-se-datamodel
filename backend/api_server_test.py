#!/usr/bin/env python3
"""
FastAPI Backend for ULTRATHINK Test (Port 8001)
Queries new PageChunk nodes with page images support
"""

import sys
import os
import re
import json
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import numpy as np
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from storage.neo4j_vector_store_flexible import Neo4jVectorStoreFlexible

# Configuration
# Point to the actual output directory (3 levels up from frontend_viewer/backend)
BASE_OUTPUT_PATH = PROJECT_ROOT.parent / "output"  # /home/ib3/.../knowledge_graph_vector_GC_Data/output
NODE_LABEL = "PageChunk"  # New label for test
INDEX_NAME = "page_embeddings_ultrathink"  # New index

# Initialize FastAPI
app = FastAPI(title="ULTRATHINK Test API - Page-by-Page Search")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],  # Test on 3001
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load embedding model (once at startup)
print("Loading BGE model...")
embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5')
print("Model loaded!")

# Connect to Neo4j with new label
neo4j_store = Neo4jVectorStoreFlexible(
    uri="bolt://localhost:7687",
    auth=None,
    node_label=NODE_LABEL
)


def get_extracted_images_for_document(page_image_relative: str, source_file: str):
    """
    Get all extracted images and tables for a document (file-based, no regex)
    Also loads descriptions from picture_annotations.json

    Returns: (pictures_data, tables_data)
    """
    if not page_image_relative:
        return [], []

    doc_dir = BASE_OUTPUT_PATH / Path(page_image_relative).parent.parent

    # Load annotations file for descriptions
    annotations = {}
    annotations_file = doc_dir / "pictures" / f"{source_file} - picture_annotations.json"
    if annotations_file.exists():
        try:
            with open(annotations_file, 'r') as f:
                annotations = json.load(f)
        except:
            pass

    # Get pictures with descriptions
    pictures_data = []
    pictures_dir = doc_dir / "pictures"
    if pictures_dir.exists():
        picture_files = sorted(pictures_dir.glob(f"{source_file} - picture *.png"))
        for pic_file in picture_files:
            # Extract picture number from filename
            match = re.search(r'picture (\d+)\.png', pic_file.name)
            if match:
                pic_num = int(match.group(1))
                relative_path = str(pic_file.relative_to(BASE_OUTPUT_PATH))

                # Get description from annotations (0-indexed array)
                caption = annotations.get('caption_texts', [])[pic_num - 1] if pic_num <= len(annotations.get('caption_texts', [])) else ""
                annotation = annotations.get('annotation_texts', [])[pic_num - 1] if pic_num <= len(annotations.get('annotation_texts', [])) else ""
                description = annotation or caption or ""

                pictures_data.append({
                    'number': pic_num,
                    'url': f"/api/document-image/{relative_path}",
                    'description': description[:300] if description else ""  # Limit to 300 chars
                })

    # Get tables
    tables_data = []
    tables_dir = doc_dir / "tables"
    if tables_dir.exists():
        table_files = sorted(tables_dir.glob(f"{source_file} - table *.png"))
        for tbl_file in table_files:
            match = re.search(r'table (\d+)\.png', tbl_file.name)
            if match:
                tbl_num = int(match.group(1))
                relative_path = str(tbl_file.relative_to(BASE_OUTPUT_PATH))

                tables_data.append({
                    'number': tbl_num,
                    'url': f"/api/document-image/{relative_path}",
                    'description': ""  # Tables don't have annotations
                })

    return pictures_data, tables_data


@app.get("/api/search")
async def search(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(default=10, ge=1, le=50, description="Number of results")
):
    """Vector similarity search with page images"""

    # Generate query embedding
    query_embedding = embedding_model.encode([q])[0]

    # Search using new index
    results = neo4j_store.vector_search(
        query_embedding,
        top_k=top_k,
        index_name=INDEX_NAME
    )

    # Format for frontend
    formatted_results = []
    for i, chunk in enumerate(results):
        # Get extracted images/tables using file-based approach (safer than regex)
        pictures_data, tables_data = get_extracted_images_for_document(
            chunk.get('page_image_relative', ''),
            chunk.get('source_file', '')
        )

        formatted_results.append({
            "id": chunk['chunk_id'],
            "title": f"{chunk['project_id']} - {chunk.get('customer', 'Unknown')}",
            "description": chunk['text'][:200] + "...",
            "category": chunk.get('category', 'unknown').upper(),
            "relevance": float(chunk['score']),
            "content": chunk['text'],
            "tags": [
                chunk.get('category'),
                chunk.get('technology'),
                chunk.get('document_type')
            ],
            "metadata": {
                "customer": chunk.get('customer', 'Unknown'),
                "project": chunk.get('project_id'),
                "page": chunk.get('page', 0),
                "total_pages": chunk.get('total_pages', 0),
                "technology": chunk.get('technology', 'Unknown'),
                "file_name": chunk.get('file_name', ''),
                "total_images": chunk.get('total_images', 0),
                "total_tables": chunk.get('total_tables', 0),
                "page_image_url": f"/api/page-image/{chunk.get('page_image_relative', '')}" if chunk.get('page_image_relative') else None,
                "pictures": pictures_data,  # [{number, url, description}, ...]
                "tables": tables_data       # [{number, url, description}, ...]
            },
            "source": chunk.get('file_name', 'Unknown'),
            "createdAt": chunk.get('extracted_at', '2025-11-14')[:10]
        })

    return {
        "results": formatted_results,
        "query": q,
        "count": len(formatted_results),
        "index": INDEX_NAME,
        "node_label": NODE_LABEL
    }


@app.get("/api/result/{chunk_id}")
async def get_result_by_id(chunk_id: str):
    """Get single result by chunk ID"""
    # Search for this specific chunk
    try:
        # Simple text search to find the chunk by ID
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=None)

        with driver.session() as session:
            result = session.run(f"""
                MATCH (c:{NODE_LABEL})
                WHERE c.chunk_id = $chunk_id
                RETURN c
                LIMIT 1
            """, chunk_id=chunk_id)

            record = result.single()
            if not record:
                return {"error": "Result not found", "chunk_id": chunk_id}

            chunk = record['c']

            # Get extracted images/tables using file-based approach (safer)
            pictures_data, tables_data = get_extracted_images_for_document(
                chunk.get('page_image_relative', ''),
                chunk.get('source_file', '')
            )

            # Format response
            formatted = {
                "id": chunk['chunk_id'],
                "title": f"{chunk.get('project_id', 'Unknown')} - {chunk.get('customer', 'Unknown')}",
                "description": chunk['text'][:200] + "...",
                "category": chunk.get('category', 'unknown').upper(),
                "relevance": 1.0,
                "content": chunk['text'],
                "tags": [chunk.get('category'), chunk.get('technology'), chunk.get('document_type')],
                "metadata": {
                    "customer": chunk.get('customer', 'Unknown'),
                    "project": chunk.get('project_id'),
                    "page": chunk.get('page', 0),
                    "total_pages": chunk.get('total_pages', 0),
                    "technology": chunk.get('technology', 'Unknown'),
                    "file_name": chunk.get('file_name', ''),
                    "total_images": chunk.get('total_images', 0),
                    "total_tables": chunk.get('total_tables', 0),
                    "page_image_url": f"/api/page-image/{chunk.get('page_image_relative', '')}" if chunk.get('page_image_relative') else None,
                    "pictures": pictures_data,  # [{number, url, description}, ...]
                    "tables": tables_data       # [{number, url, description}, ...]
                },
                "source": chunk.get('file_name', 'Unknown'),
                "createdAt": chunk.get('extracted_at', '2025-11-14')[:10]
            }

        driver.close()
        return formatted

    except Exception as e:
        return {"error": str(e), "chunk_id": chunk_id}


@app.get("/api/page-image/{image_path:path}")
async def get_page_image(image_path: str):
    """Serve page PNG images"""
    full_path = BASE_OUTPUT_PATH / image_path

    if not full_path.exists():
        return {"error": "Image not found", "path": str(image_path)}

    return FileResponse(full_path)


@app.get("/api/document-image/{image_path:path}")
async def get_document_image(image_path: str):
    """Serve extracted document images (pictures/*.png, tables/*.png)"""
    full_path = BASE_OUTPUT_PATH / image_path

    if not full_path.exists():
        return {"error": "Image not found", "path": str(image_path)}

    return FileResponse(full_path)


@app.get("/api/health")
async def health():
    """Health check with stats"""
    chunk_count = neo4j_store.count_chunks()

    return {
        "status": "ok",
        "database": "neo4j",
        "node_label": NODE_LABEL,
        "index_name": INDEX_NAME,
        "chunks": chunk_count,
        "test_mode": True,
        "port": 8001
    }


@app.get("/api/stats")
async def stats():
    """Database statistics"""
    chunk_count = neo4j_store.count_chunks()

    return {
        "total_chunks": chunk_count,
        "node_label": NODE_LABEL,
        "index_name": INDEX_NAME,
        "test_project": "GC21_001_CCPP_Dils",
        "embedding_model": "BAAI/bge-large-en-v1.5",
        "embedding_dim": 1024
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 80)
    print("🚀 ULTRATHINK TEST API SERVER")
    print("=" * 80)
    print(f"Port: 8001")
    print(f"Neo4j Label: {NODE_LABEL}")
    print(f"Vector Index: {INDEX_NAME}")
    print(f"Base Path: {BASE_OUTPUT_PATH}")
    print(f"\nTest Frontend: http://localhost:3001")
    print(f"API Docs: http://localhost:8001/docs")
    print("=" * 80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
