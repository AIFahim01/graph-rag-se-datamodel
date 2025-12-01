#!/usr/bin/env python3
"""
FastAPI Backend for Vector DB Viewer Frontend
Connects Neo4j vector database to Next.js frontend
"""

import sys
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from storage.neo4j_vector_store import Neo4jVectorStore
sys.path.insert(0, str(Path(__file__).parent))
from query_enhancer import QueryEnhancer

# Initialize FastAPI
app = FastAPI(title="HVDC/SynCon Vector DB API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load embedding model (once at startup)
embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5')
neo4j_store = Neo4jVectorStore(uri="bolt://localhost:7687", auth=None)
query_enhancer = QueryEnhancer()

@app.get("/api/search")
async def search(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(default=10, ge=1, le=50, description="Number of results to return")
):
    """Enhanced vector similarity search with query expansion"""

    # Extract intent and apply filters
    intent = query_enhancer.extract_intent(q)

    # Generate query variations
    query_variations = query_enhancer.expand_query(q)

    # Search with all variations and fuse results
    all_results = {}
    for query_var in query_variations:
        query_embedding = embedding_model.encode([query_var])[0]
        results = neo4j_store.vector_search(
            query_embedding,
            top_k=max(20, top_k * 2),  # Fetch more to allow for deduplication
            filters=intent.get('filters', {})
        )

        # Track best score per chunk
        for result in results:
            chunk_id = result['chunk_id']
            if chunk_id not in all_results or result['score'] > all_results[chunk_id]['score']:
                all_results[chunk_id] = result

    # Sort by score and take top_k results
    results = sorted(all_results.values(), key=lambda x: x['score'], reverse=True)[:top_k]

    # Format for frontend
    formatted_results = []
    for i, chunk in enumerate(results):
        formatted_results.append({
            "id": chunk['chunk_id'],
            "title": f"{chunk['project_id']} - {chunk.get('customer', 'Unknown')}",
            "description": chunk['text'][:200] + "...",
            "category": chunk.get('category', 'unknown').upper(),
            "relevance": float(chunk['score']),
            "content": chunk['text'],
            "tags": [chunk.get('category'), chunk.get('project_type'), chunk.get('document_type')],
            "metadata": {
                "customer": chunk.get('customer', 'Unknown'),
                "project": chunk.get('project_id'),
                "page": chunk.get('page', 0),
                "technology": chunk.get('technology', 'Unknown')
            },
            "source": chunk.get('source', 'Unknown'),
            "createdAt": "2025-11-13"
        })

    return {
        "results": formatted_results,
        "query": q,
        "count": len(formatted_results)
    }

@app.get("/api/health")
async def health():
    return {"status": "ok", "database": "neo4j", "chunks": 18437, "pdfs": 1082, "projects": 61}

@app.get("/api/stats")
async def stats():
    """Get database statistics including project counts by category"""
    # Query Neo4j for actual stats
    try:
        with neo4j_store.driver.session() as session:
            # Count unique projects by category
            result = session.run("""
                MATCH (c:Chunk)
                WITH DISTINCT c.project_id as project, c.category as category
                RETURN category, count(project) as count
                ORDER BY count DESC
            """)
            categories = {record["category"]: record["count"] for record in result}

            # Get total unique projects
            result = session.run("""
                MATCH (c:Chunk)
                RETURN count(DISTINCT c.project_id) as total
            """)
            total_projects = result.single()["total"]

            # Get list of HVDC projects
            result = session.run("""
                MATCH (c:Chunk)
                WHERE c.category = 'hvdc'
                RETURN DISTINCT c.project_id as project
                ORDER BY project
            """)
            hvdc_projects = [record["project"] for record in result]

            # Get list of SynCon projects
            result = session.run("""
                MATCH (c:Chunk)
                WHERE c.category = 'syncon'
                RETURN DISTINCT c.project_id as project
                ORDER BY project
            """)
            syncon_projects = [record["project"] for record in result]

        return {
            "total_projects": total_projects,
            "total_chunks": 18437,
            "total_pdfs": 1082,
            "projects_by_category": categories,
            "hvdc_projects": hvdc_projects,
            "hvdc_count": len(hvdc_projects),
            "syncon_projects": syncon_projects,
            "syncon_count": len(syncon_projects)
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_projects": 61,
            "hvdc_count": "unknown",
            "syncon_count": "unknown"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
