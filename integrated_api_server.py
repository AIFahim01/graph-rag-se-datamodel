#!/usr/bin/env python3
"""
ULTRATHINK - Integrated API Server with Image Support
Combines vector search with existing frontend viewer for HVDC/SynCon documents
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from typing import Optional, List, Dict
import json
from llm_query_generator import LLMQueryGenerator

# Initialize FastAPI
app = FastAPI(title="ULTRATHINK Vector DB API with Images")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration (from environment variables with fallbacks)
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "siemensenergy")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
NODE_LABEL = "PageChunk"
INDEX_NAME = "page_embeddings_ultrathink"

# Paths (from environment variables with fallbacks)
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/output"))
OUTPUT_COPY_DIR = Path("/home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/output_copy_test")

# Load embedding model (once at startup)
print("Loading embedding model...")
embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5', device='cpu')
print("Model loaded!")

# Neo4j connection
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Initialize LLM Query Generator
llm_generator = LLMQueryGenerator(model="qwen3-coder:latest")

# Mount static files for images
if OUTPUT_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(OUTPUT_DIR)), name="images")

@app.get("/api/search")
async def search(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(default=10, ge=1, le=50),
    technology: Optional[str] = Query(None, description="Filter by technology (HVDC/SynCon)"),
    year: Optional[str] = Query(None, description="Filter by year"),
    customer: Optional[str] = Query(None, description="Filter by customer")
):
    """Enhanced vector similarity search with image support"""

    try:
        # Check if this is a counting query
        query_lower = q.lower()
        is_count_query = any(word in query_lower for word in ['how many', 'count', 'number of', 'total'])

        # Parse technology and year from the query if not provided as filters
        if not technology:
            if 'hvdc' in query_lower:
                technology = 'HVDC'
            elif 'syncon' in query_lower:
                technology = 'SynCon'

        if not year:
            import re
            year_match = re.search(r'\b(202[0-9])\b', query_lower)
            if year_match:
                year = year_match.group(1)

        with driver.session() as session:
            # If this is a counting query, return count instead of doing vector search
            if is_count_query and (technology or year):
                # Build filter conditions for counting
                count_conditions = []
                if technology:
                    count_conditions.append(f"c.technology = '{technology}'")
                if year:
                    # Convert year to integer for comparison
                    count_conditions.append(f"c.year = {int(year)}")

                where_clause = f"WHERE {' AND '.join(count_conditions)}" if count_conditions else ""

                # Count matching documents
                count_query = f"""
                    MATCH (c:{NODE_LABEL})
                    {where_clause}
                    RETURN count(DISTINCT c.project_id) as project_count,
                           count(DISTINCT c.file_name) as file_count,
                           count(c) as chunk_count
                """

                result = session.run(count_query)
                counts = result.single()

                # Create a formatted response for count queries
                filter_desc = []
                if technology:
                    filter_desc.append(f"{technology}")
                if year:
                    filter_desc.append(f"year {year}")

                filter_text = " in " if filter_desc else ""
                filter_text += " ".join(filter_desc) if filter_desc else "all projects"

                summary = f"Found {counts['project_count']} projects with {filter_text}"
                if counts['project_count'] == 0:
                    summary = f"No projects found with {filter_text}"

                return {
                    "results": [{
                        "id": "count_result",
                        "title": f"Project Count for {filter_text}",
                        "description": summary,
                        "category": "STATISTICS",
                        "relevance": 1.0,
                        "content": f"Database contains {counts['project_count']} unique projects, {counts['file_count']} PDF files, and {counts['chunk_count']} document chunks matching your criteria.",
                        "tags": filter_desc,
                        "metadata": {
                            "query_type": "count",
                            "project_count": counts['project_count'],
                            "file_count": counts['file_count'],
                            "chunk_count": counts['chunk_count'],
                            "technology": technology,
                            "year": year
                        },
                        "source": "Database Statistics",
                        "createdAt": "2024-01-01"
                    }],
                    "query": q,
                    "count": 1,
                    "filters_applied": {
                        "technology": technology,
                        "year": year,
                        "customer": customer
                    },
                    "is_count_query": True
                }

            # Otherwise do normal vector search
            # Generate query embedding
            query_embedding = embedding_model.encode([q])[0].tolist()

            # Build filter conditions
            filter_conditions = []
            if technology:
                filter_conditions.append(f"node.technology = '{technology}'")
            if year:
                filter_conditions.append(f"node.year = {int(year)}")
            if customer:
                filter_conditions.append(f"node.customer_normalized = '{customer.upper()}'")

            where_clause = " AND ".join(filter_conditions) if filter_conditions else ""
            where_statement = f"WHERE {where_clause}" if where_clause else ""

            # Perform vector search
            query = f"""
            CALL db.index.vector.queryNodes($index_name, $search_k, $query_embedding)
            YIELD node, score
            {where_statement}
            RETURN node.chunk_id as chunk_id,
                   node.project_id as project_id,
                   node.project_name as project_name,
                   node.technology as technology,
                   node.year as year,
                   node.customer as customer,
                   node.page as page,
                   node.file_name as file_name,
                   node.text as text,
                   node.category as category,
                   node.page_image_relative as page_image,
                   node.total_images as total_images,
                   node.total_tables as total_tables,
                   score
            ORDER BY score DESC
            LIMIT $top_k
            """

            result = session.run(
                query,
                index_name=INDEX_NAME,
                search_k=top_k * 3 if filter_conditions else top_k,
                top_k=top_k,
                query_embedding=query_embedding
            )

            # Format results for frontend
            formatted_results = []
            for record in result:
                # Construct image URL if available
                image_url = None
                if record['page_image']:
                    # The page_image_relative path is like "GC21_001/page_images/page_0001.png"
                    image_url = f"/images/{record['page_image']}"

                formatted_results.append({
                    "id": record['chunk_id'],
                    "title": f"{record['project_id']} - {record['customer']}",
                    "description": (record['text'][:200] + "...") if record['text'] else "",
                    "category": record.get('category', 'unknown').upper(),
                    "relevance": float(record['score']),
                    "content": record['text'],
                    "tags": [
                        record['technology'],
                        f"Year {record['year']}",
                        f"Page {record['page']}"
                    ],
                    "metadata": {
                        "customer": record['customer'],
                        "project": record['project_id'],
                        "project_name": record['project_name'],
                        "page": record['page'],
                        "technology": record['technology'],
                        "year": record['year'],
                        "file_name": record['file_name'],
                        "total_images": record.get('total_images', 0),
                        "total_tables": record.get('total_tables', 0)
                    },
                    "image_url": image_url,
                    "source": record.get('file_name', 'Unknown'),
                    "createdAt": f"{record['year']}-01-01"
                })

            return {
                "results": formatted_results,
                "query": q,
                "count": len(formatted_results),
                "filters_applied": {
                    "technology": technology,
                    "year": year,
                    "customer": customer
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/count")
async def count_projects(
    technology: Optional[str] = Query(None, description="Filter by technology (HVDC/SynCon)"),
    year: Optional[str] = Query(None, description="Filter by year"),
    customer: Optional[str] = Query(None, description="Filter by customer")
):
    """Count projects, files, and chunks with optional filters"""
    try:
        with driver.session() as session:
            # Build filter conditions
            conditions = []
            if technology:
                conditions.append(f"c.technology = '{technology}'")
            if year:
                # Convert year to integer for comparison
                conditions.append(f"c.year = {int(year)}")
            if customer:
                conditions.append(f"c.customer_normalized = '{customer.upper()}'")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            # Count query
            query = f"""
                MATCH (c:{NODE_LABEL})
                {where_clause}
                RETURN count(DISTINCT c.project_id) as project_count,
                       count(DISTINCT c.file_name) as file_count,
                       count(c) as chunk_count,
                       collect(DISTINCT c.project_id) as project_ids
            """

            result = session.run(query)
            counts = result.single()

            # Get breakdown by year if filtering by technology
            year_breakdown = {}
            if technology and not year:
                year_query = f"""
                    MATCH (c:{NODE_LABEL})
                    WHERE c.technology = '{technology}'
                    RETURN c.year as year, count(DISTINCT c.project_id) as count
                    ORDER BY year
                """
                year_result = session.run(year_query)
                for record in year_result:
                    year_breakdown[str(record['year'])] = record['count']

            return {
                "success": True,
                "filters": {
                    "technology": technology,
                    "year": year,
                    "customer": customer
                },
                "counts": {
                    "projects": counts['project_count'],
                    "files": counts['file_count'],
                    "chunks": counts['chunk_count']
                },
                "project_ids": list(counts['project_ids'])[:10],  # First 10 project IDs
                "year_breakdown": year_breakdown if year_breakdown else None,
                "message": f"Found {counts['project_count']} projects" +
                          (f" with {technology} technology" if technology else "") +
                          (f" in year {year}" if year else "") +
                          (f" for customer {customer}" if customer else "")
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/llm-search")
async def llm_search(
    q: str = Query(..., description="Natural language query"),
    use_llm: bool = Query(default=True, description="Use LLM for query generation"),
    debug: bool = Query(default=False, description="Return debug information")
):
    """
    Natural language search using LLM to generate Cypher queries
    The LLM has the complete database schema and generates appropriate queries
    """
    try:
        # Generate query using LLM
        result = llm_generator.generate_query(q)

        if not result["success"]:
            return {
                "error": "Failed to generate query",
                "issues": result.get("issues", []),
                "debug": result if debug else None
            }

        with driver.session() as session:
            # Handle vector search
            if result["query_type"] == "vector":
                # Generate embedding for search text
                search_embedding = embedding_model.encode([result["search_text"]])[0].tolist()

                # Build filter conditions if any
                filters = result.get("filters", {})
                filter_conditions = []
                if filters.get("technology"):
                    filter_conditions.append(f"node.technology = '{filters['technology']}'")
                if filters.get("year"):
                    filter_conditions.append(f"node.year = {filters['year']}")

                where_clause = " AND ".join(filter_conditions) if filter_conditions else ""
                where_statement = f"WHERE {where_clause}" if where_clause else ""

                # Perform vector search
                cypher = f"""
                CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
                YIELD node, score
                {where_statement}
                RETURN node.chunk_id as chunk_id,
                       node.project_id as project_id,
                       node.technology as technology,
                       node.customer as customer,
                       node.year as year,
                       node.page as page,
                       node.text as text,
                       node.file_name as file_name,
                       node.page_image_relative as page_image_relative,
                       score
                ORDER BY score DESC
                LIMIT 20
                """

                cypher_result = session.run(
                    cypher,
                    index_name=INDEX_NAME,
                    top_k=50,
                    query_embedding=search_embedding
                )

                # Format results
                results = []
                for record in cypher_result:
                    results.append({
                        "chunk_id": record["chunk_id"],
                        "project_id": record["project_id"],
                        "technology": record["technology"],
                        "customer": record["customer"],
                        "year": record["year"],
                        "page": record["page"],
                        "text": record["text"][:500] + "..." if len(record["text"]) > 500 else record["text"],
                        "file_name": record["file_name"],
                        "page_image_relative": record["page_image_relative"],
                        "relevance": float(record["score"])
                    })

                response = {
                    "success": True,
                    "query_type": "vector_search",
                    "search_text": result["search_text"],
                    "results": results,
                    "count": len(results)
                }

                if debug:
                    response["debug"] = {
                        "generated_query": cypher,
                        "llm_result": result
                    }

                return response

            # Handle Cypher queries
            else:
                cypher = result.get("cypher")

                # If LLM returns NULL or None, treat it as a vector search
                if not cypher or cypher.upper() == "NULL" or cypher.upper() == "NONE":
                    # Switch to vector search
                    search_text = result.get("search_text", q)
                    search_embedding = embedding_model.encode([search_text])[0].tolist()

                    cypher = """
                    CALL db.index.vector.queryNodes('page_embeddings_ultrathink', 20, $embedding)
                    YIELD node, score
                    WHERE score > 0.1
                    RETURN node.chunk_id as chunk_id,
                           node.project_id as project_id,
                           node.project_name as project_name,
                           node.technology as technology,
                           node.customer as customer,
                           node.year as year,
                           node.page as page,
                           node.text as text,
                           node.file_name as file_name,
                           node.page_image_relative as page_image_relative,
                           score
                    ORDER BY score DESC
                    LIMIT 20
                    """

                    cypher_result = session.run(cypher, parameters={"embedding": search_embedding})

                    # Process as vector search results
                    results = []
                    for record in cypher_result:
                        results.append({
                            "chunk_id": record["chunk_id"],
                            "project_id": record["project_id"],
                            "project_name": record["project_name"],
                            "technology": record["technology"],
                            "customer": record["customer"],
                            "year": record["year"],
                            "page": record["page"],
                            "text": record["text"][:500] + "..." if len(record["text"]) > 500 else record["text"],
                            "file_name": record["file_name"],
                            "page_image_relative": record["page_image_relative"],
                            "relevance": float(record["score"])
                        })

                    return {
                        "success": True,
                        "query_type": "vector_search",
                        "search_text": search_text,
                        "results": results,
                        "count": len(results),
                        "message": "LLM indicated vector search needed for location/content query"
                    }

                # Execute the generated Cypher
                cypher_result = session.run(cypher)

                # Format results based on query pattern
                results = []
                for record in cypher_result:
                    # Convert Neo4j record to dict
                    record_dict = dict(record)

                    # Handle different result formats
                    if "project_count" in record_dict:
                        # Count query
                        results.append(record_dict)
                    elif "c" in record_dict:
                        # Full node return
                        node = record_dict["c"]
                        results.append({
                            "chunk_id": node.get("chunk_id"),
                            "project_id": node.get("project_id"),
                            "text": node.get("text", "")[:500] + "..." if len(node.get("text", "")) > 500 else node.get("text", ""),
                            "technology": node.get("technology"),
                            "year": node.get("year"),
                            "customer": node.get("customer"),
                            "page": node.get("page")
                        })
                    else:
                        # Generic result
                        results.append(record_dict)

                response = {
                    "success": True,
                    "query_type": "cypher",
                    "results": results,
                    "count": len(results)
                }

                if debug:
                    response["debug"] = {
                        "generated_cypher": cypher,
                        "parsed_entities": result.get("parsed", {}),
                        "llm_result": result
                    }

                return response

    except Exception as e:
        error_response = {
            "error": str(e),
            "query": q
        }

        if debug:
            import traceback
            error_response["traceback"] = traceback.format_exc()

        raise HTTPException(status_code=500, detail=error_response)

@app.get("/api/health")
async def health():
    """Health check with database statistics"""
    try:
        with driver.session() as session:
            result = session.run(f"MATCH (c:{NODE_LABEL}) RETURN count(c) as count")
            total_chunks = result.single()['count']

            result = session.run(f"""
                MATCH (c:{NODE_LABEL})
                RETURN count(DISTINCT c.project_id) as projects,
                       count(DISTINCT c.file_name) as files
            """)
            record = result.single()

            return {
                "status": "ok",
                "database": "neo4j",
                "chunks": total_chunks,
                "pdfs": record['files'],
                "projects": record['projects']
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/stats")
async def stats():
    """Get detailed database statistics"""
    try:
        with driver.session() as session:
            # Count by technology
            result = session.run(f"""
                MATCH (c:{NODE_LABEL})
                RETURN c.technology as technology, count(c) as count
                ORDER BY count DESC
            """)
            technologies = {record["technology"]: record["count"] for record in result}

            # Count by year
            result = session.run(f"""
                MATCH (c:{NODE_LABEL})
                RETURN c.year as year, count(c) as count
                ORDER BY year
            """)
            years = {str(record["year"]): record["count"] for record in result}

            # Get unique projects by technology
            result = session.run(f"""
                MATCH (c:{NODE_LABEL})
                WHERE c.technology = 'HVDC'
                RETURN DISTINCT c.project_id as project, c.project_name as name, c.year as year
                ORDER BY year, project
            """)
            hvdc_projects = [
                {"id": record["project"], "name": record["name"], "year": record["year"]}
                for record in result
            ]

            result = session.run(f"""
                MATCH (c:{NODE_LABEL})
                WHERE c.technology = 'SynCon'
                RETURN DISTINCT c.project_id as project, c.project_name as name, c.year as year
                ORDER BY year, project
            """)
            syncon_projects = [
                {"id": record["project"], "name": record["name"], "year": record["year"]}
                for record in result
            ]

            # Total statistics
            result = session.run(f"""
                MATCH (c:{NODE_LABEL})
                RETURN count(c) as total_chunks,
                       count(DISTINCT c.project_id) as total_projects,
                       count(DISTINCT c.file_name) as total_files
            """)
            totals = result.single()

            return {
                "total_projects": totals['total_projects'],
                "total_chunks": totals['total_chunks'],
                "total_pdfs": totals['total_files'],
                "projects_by_technology": technologies,
                "projects_by_year": years,
                "hvdc_projects": hvdc_projects,
                "hvdc_count": len(hvdc_projects),
                "syncon_projects": syncon_projects,
                "syncon_count": len(syncon_projects)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/image/{project_id}/{image_path:path}")
async def get_image(project_id: str, image_path: str):
    """Serve images from the output directory"""
    # The image_path already contains the full path structure
    # Try direct path first (when image_path starts with GC_)
    if image_path.startswith("GC_"):
        full_path = OUTPUT_DIR / image_path
    else:
        # Legacy path structure
        full_path = OUTPUT_DIR / project_id / image_path

    # Check if file exists
    if not full_path.exists() or not full_path.is_file():
        # Try alternative output directory with same logic
        if image_path.startswith("GC_"):
            alt_path = OUTPUT_COPY_DIR / image_path
        else:
            alt_path = OUTPUT_COPY_DIR / project_id / image_path

        if alt_path.exists() and alt_path.is_file():
            full_path = alt_path
        else:
            raise HTTPException(status_code=404, detail=f"Image not found at {full_path}")

    # Return the image
    return FileResponse(str(full_path))

@app.get("/api/projects")
async def list_projects(
    technology: Optional[str] = Query(None),
    year: Optional[str] = Query(None)
):
    """List all projects with filtering options"""
    try:
        with driver.session() as session:
            # Build filter conditions
            conditions = []
            if technology:
                conditions.append(f"c.technology = '{technology}'")
            if year:
                # Convert year to integer for comparison
                conditions.append(f"c.year = {int(year)}")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"""
                MATCH (c:{NODE_LABEL})
                {where_clause}
                RETURN DISTINCT
                    c.project_id as project_id,
                    c.project_name as project_name,
                    c.customer as customer,
                    c.technology as technology,
                    c.year as year,
                    count(c) as page_count
                ORDER BY c.year DESC, c.project_id
            """

            result = session.run(query)

            projects = []
            for record in result:
                projects.append({
                    "id": record['project_id'],
                    "name": record['project_name'],
                    "customer": record['customer'],
                    "technology": record['technology'],
                    "year": record['year'],
                    "pages": record['page_count']
                })

            return {
                "success": True,
                "count": len(projects),
                "projects": projects,
                "filters": {
                    "technology": technology,
                    "year": year
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/document/{chunk_id}")
async def get_document_details(chunk_id: str):
    """Get detailed information about a specific document chunk"""
    try:
        with driver.session() as session:
            query = f"""
                MATCH (c:{NODE_LABEL})
                WHERE c.chunk_id = $chunk_id
                RETURN c
            """

            result = session.run(query, chunk_id=chunk_id)
            record = result.single()

            if not record:
                raise HTTPException(status_code=404, detail="Document not found")

            chunk = record['c']

            # Build image URL if available
            image_url = None
            if chunk.get('page_image_relative'):
                image_url = f"/images/{chunk['page_image_relative']}"

            # Find related pages (same project)
            related_query = f"""
                MATCH (c:{NODE_LABEL})
                WHERE c.project_id = $project_id
                  AND c.chunk_id <> $chunk_id
                RETURN c.chunk_id as id, c.page as page, c.text as text
                ORDER BY c.page
                LIMIT 5
            """

            related_result = session.run(
                related_query,
                project_id=chunk['project_id'],
                chunk_id=chunk_id
            )

            related_pages = [
                {
                    "id": r['id'],
                    "page": r['page'],
                    "preview": (r['text'][:100] + "...") if r['text'] else ""
                }
                for r in related_result
            ]

            return {
                "success": True,
                "document": {
                    "chunk_id": chunk['chunk_id'],
                    "project_id": chunk['project_id'],
                    "project_name": chunk.get('project_name'),
                    "customer": chunk.get('customer'),
                    "technology": chunk.get('technology'),
                    "year": chunk.get('year'),
                    "page": chunk.get('page'),
                    "text": chunk.get('text'),
                    "file_name": chunk.get('file_name'),
                    "category": chunk.get('category'),
                    "image_url": image_url,
                    "total_pages": chunk.get('total_pages'),
                    "total_images": chunk.get('total_images'),
                    "total_tables": chunk.get('total_tables')
                },
                "related_pages": related_pages
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STREAMING ITERATIVE SEARCH ENDPOINT
# Pipeline: Metadata -> Graph Context -> Vector Search -> Answer Generation
# ============================================================================

from fastapi.responses import StreamingResponse
import requests

@app.get("/api/iterative-search-stream")
async def iterative_search_stream(
    q: str = Query(..., description="Natural language query"),
    top_k: int = Query(default=10, description="Number of results")
):
    """
    Streaming Iterative Search - sends results step by step as SSE events

    Pipeline:
    1. Metadata Filter (LLM-generated Cypher)
    2. Graph Context (Entity/Relationship search)
    3. Vector Search (semantic similarity with page images)
    4. Answer Generation (LLM with retry mechanism)
    """

    async def generate_stream():
        try:
            project_ids = []
            projects_data = []
            graph_entities = []
            graph_relationships = []
            graph_context = ""
            vector_results = []

            # ===== STEP 1: METADATA FILTER =====
            yield f"data: {json.dumps({'step': 'metadata_filter', 'status': 'started', 'message': 'Searching metadata...'})}\n\n"

            llm_result = llm_generator.generate_query(q)

            if llm_result.get("success") and llm_result.get("cypher"):
                cypher = llm_result["cypher"]
                try:
                    with driver.session() as session:
                        result = session.run(cypher)
                        records = list(result)

                        for r in records:
                            rd = dict(r)
                            pid = rd.get("project_id") or rd.get("c.project_id")
                            pname = rd.get("project_name") or rd.get("c.project_name")
                            if pid and pid not in project_ids:
                                project_ids.append(pid)
                                projects_data.append({
                                    "project_id": pid,
                                    "project_name": pname,
                                    "technology": rd.get("technology") or rd.get("c.technology"),
                                    "year": rd.get("year") or rd.get("c.year")
                                })

                    yield f"data: {json.dumps({'step': 'metadata_filter', 'status': 'complete', 'projects_found': len(project_ids), 'projects': projects_data[:20], 'cypher': cypher[:100]})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'step': 'metadata_filter', 'status': 'complete', 'projects_found': 0, 'message': f'Query error: {str(e)[:50]}'})}\n\n"
            else:
                yield f"data: {json.dumps({'step': 'metadata_filter', 'status': 'complete', 'projects_found': 0, 'message': 'No metadata query generated'})}\n\n"

            # ===== STEP 2: GRAPH CONTEXT =====
            yield f"data: {json.dumps({'step': 'graph_context', 'status': 'started', 'message': 'Searching knowledge graph...'})}\n\n"

            try:
                with driver.session() as session:
                    # Extract key terms from query for graph search
                    query_terms = [w for w in q.split() if len(w) > 2]

                    # Search for entities matching query terms
                    for term in query_terms[:5]:
                        entity_query = """
                        MATCH (e:Entity)
                        WHERE toLower(e.name) CONTAINS toLower($term)
                        RETURN e.name as name
                        LIMIT 10
                        """
                        result = session.run(entity_query, term=term)
                        for r in result:
                            if r["name"] and r["name"] not in graph_entities:
                                graph_entities.append(r["name"])

                    # Get relationships for found entities
                    if graph_entities:
                        rel_query = """
                        MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity)
                        WHERE e1.name IN $entities OR e2.name IN $entities
                        RETURN e1.name as source, r.relation_type as rel, e2.name as target
                        LIMIT 20
                        """
                        result = session.run(rel_query, entities=graph_entities[:20])
                        for r in result:
                            rel_str = f"{r['source']} {r['rel'] or 'related_to'} {r['target']}"
                            if rel_str not in graph_relationships:
                                graph_relationships.append(rel_str)

                    # Build graph context string
                    if graph_entities or graph_relationships:
                        graph_context = f"Related entities: {', '.join(graph_entities[:10])}. "
                        if graph_relationships:
                            graph_context += f"Knowledge: {'; '.join(graph_relationships[:10])}."
            except Exception as e:
                pass  # Graph search is optional, continue without it

            yield f"data: {json.dumps({'step': 'graph_context', 'status': 'complete', 'entities_found': len(graph_entities), 'relationships_found': len(graph_relationships), 'entities': graph_entities[:10], 'relationships': graph_relationships[:5]})}\n\n"

            # ===== STEP 3: VECTOR SEARCH =====
            search_mode = "scoped" if project_ids else "full"
            yield f"data: {json.dumps({'step': 'vector_search', 'status': 'started', 'message': f'Searching {search_mode} ({len(project_ids)} projects)...'})}\n\n"

            query_embedding = embedding_model.encode([q])[0].tolist()

            with driver.session() as session:
                if project_ids:
                    # Scoped search within metadata-filtered projects
                    vector_query = """
                    CALL db.index.vector.queryNodes($index_name, $top_k * 3, $query_embedding)
                    YIELD node, score
                    WHERE node.project_id IN $project_ids
                    RETURN node.chunk_id as chunk_id,
                           node.project_id as project_id,
                           node.project_name as project_name,
                           node.technology as technology,
                           node.year as year,
                           node.customer as customer,
                           node.text as text,
                           node.page as page,
                           node.file_name as file_name,
                           node.page_image_relative as page_image,
                           score
                    ORDER BY score DESC
                    LIMIT $top_k
                    """
                    result = session.run(
                        vector_query,
                        index_name=INDEX_NAME,
                        top_k=top_k,
                        query_embedding=query_embedding,
                        project_ids=project_ids[:100]
                    )
                else:
                    # Full vector search - first try text search for keywords
                    key_terms = [w for w in q.split() if len(w) > 3 and w[0].isupper()]
                    text_results = []

                    if key_terms:
                        for term in key_terms[:3]:
                            text_query = """
                            MATCH (c:PageChunk)
                            WHERE c.text CONTAINS $term
                            RETURN DISTINCT c.project_id as project_id,
                                   c.project_name as project_name,
                                   c.technology as technology,
                                   c.year as year,
                                   c.customer as customer
                            LIMIT 50
                            """
                            text_result = session.run(text_query, term=term)
                            for r in text_result:
                                pid = r["project_id"]
                                if pid and pid not in [t.get("project_id") for t in text_results]:
                                    text_results.append({
                                        "project_id": pid,
                                        "project_name": r["project_name"],
                                        "technology": r["technology"],
                                        "year": r["year"],
                                        "customer": r["customer"],
                                        "matched_term": term
                                    })

                    if text_results:
                        project_ids = [t["project_id"] for t in text_results]
                        projects_data = text_results
                        yield f"data: {json.dumps({'step': 'text_search', 'status': 'complete', 'projects_found': len(text_results), 'matched_terms': key_terms})}\n\n"

                        vector_query = """
                        CALL db.index.vector.queryNodes($index_name, $top_k * 2, $query_embedding)
                        YIELD node, score
                        WHERE node.project_id IN $project_ids
                        RETURN node.chunk_id as chunk_id,
                               node.project_id as project_id,
                               node.project_name as project_name,
                               node.technology as technology,
                               node.year as year,
                               node.customer as customer,
                               node.text as text,
                               node.page as page,
                               node.file_name as file_name,
                               node.page_image_relative as page_image,
                               score
                        ORDER BY score DESC
                        LIMIT $top_k
                        """
                        result = session.run(
                            vector_query,
                            index_name=INDEX_NAME,
                            top_k=top_k,
                            query_embedding=query_embedding,
                            project_ids=project_ids[:100]
                        )
                    else:
                        # Fallback to pure vector search
                        vector_query = """
                        CALL db.index.vector.queryNodes($index_name, $top_k * 2, $query_embedding)
                        YIELD node, score
                        WHERE score > 0.6
                        RETURN node.chunk_id as chunk_id,
                               node.project_id as project_id,
                               node.project_name as project_name,
                               node.technology as technology,
                               node.year as year,
                               node.customer as customer,
                               node.text as text,
                               node.page as page,
                               node.file_name as file_name,
                               node.page_image_relative as page_image,
                               score
                        ORDER BY score DESC
                        LIMIT $top_k
                        """
                        result = session.run(
                            vector_query,
                            index_name=INDEX_NAME,
                            top_k=top_k,
                            query_embedding=query_embedding
                        )

                for r in result:
                    vector_results.append({
                        "chunk_id": r["chunk_id"],
                        "project_id": r["project_id"],
                        "project_name": r["project_name"],
                        "technology": r["technology"],
                        "year": r["year"],
                        "customer": r["customer"],
                        "content": (r["text"] or "")[:500],
                        "page": r["page"],
                        "file_name": r["file_name"],
                        "page_image": r["page_image"],
                        "score": float(r["score"])
                    })

                # Extract unique projects from vector results if needed
                if not project_ids and vector_results:
                    seen_pids = set()
                    for vr in vector_results:
                        pid = vr.get("project_id")
                        if pid and pid not in seen_pids:
                            seen_pids.add(pid)
                            project_ids.append(pid)
                            projects_data.append({
                                "project_id": pid,
                                "project_name": vr.get("project_name"),
                                "technology": vr.get("technology"),
                                "year": vr.get("year")
                            })

            yield f"data: {json.dumps({'step': 'vector_search', 'status': 'complete', 'chunks_found': len(vector_results), 'projects_from_vector': len(projects_data) if search_mode == 'full' else 0, 'top_chunks': vector_results[:5]})}\n\n"

            # ===== STEP 4: GENERATE ANSWER =====
            yield f"data: {json.dumps({'step': 'answer_generation', 'status': 'started', 'message': 'Generating answer...'})}\n\n"

            # Build context with graph knowledge
            context_parts = []
            if graph_context:
                context_parts.append(f"KNOWLEDGE GRAPH: {graph_context}")

            for i, chunk in enumerate(vector_results[:5]):
                context_parts.append(f"Source {i+1} (Page {chunk.get('page', '?')}, {chunk.get('project_name', 'Unknown')}): {chunk.get('content', '')[:400]}")

            context = "\n\n".join(context_parts)

            answer_prompt = f"""Based on the following context, answer the user's question.

CONTEXT:
{context}

QUESTION: {q}

INSTRUCTIONS:
- Answer based on the provided context
- Be specific and cite sources when possible
- If the context mentions project counts or lists, use that information
- Keep the answer concise but complete

Answer:"""

            # LLM call with retry mechanism
            max_retries = 3
            final_answer = None
            last_error = None

            for attempt in range(max_retries):
                try:
                    timeout_seconds = 120 + (attempt * 60)  # 120s, 180s, 240s (2-4 min)
                    yield f"data: {json.dumps({'step': 'answer_generation', 'status': 'retry', 'attempt': attempt + 1, 'max_retries': max_retries, 'timeout': timeout_seconds})}\n\n"

                    answer_response = requests.post(
                        f"{OLLAMA_HOST}/api/generate",
                        json={
                            "model": "gpt-oss:120b",
                            "prompt": answer_prompt,
                            "stream": False,
                            "options": {"temperature": 0.3}
                        },
                        timeout=timeout_seconds
                    )
                    if answer_response.status_code == 200:
                        final_answer = answer_response.json().get("response", "").strip()
                        # Remove thinking tags if present
                        if "<think>" in final_answer:
                            import re
                            final_answer = re.sub(r'<think>.*?</think>', '', final_answer, flags=re.DOTALL).strip()
                        break
                except requests.exceptions.Timeout:
                    last_error = f"Timeout after {timeout_seconds}s"
                    if attempt < max_retries - 1:
                        yield f"data: {json.dumps({'step': 'answer_generation', 'status': 'timeout', 'message': f'Retrying... ({attempt + 2}/{max_retries})'})}\n\n"
                except Exception as e:
                    last_error = str(e)
                    break

            if not final_answer:
                final_answer = f"Found {len(projects_data)} projects. Top results from: {', '.join([p.get('project_name', p.get('project_id', 'Unknown'))[:30] for p in projects_data[:5]])}."
                if last_error:
                    final_answer += f" (Note: LLM answer generation failed: {last_error})"

            yield f"data: {json.dumps({'step': 'answer_generation', 'status': 'complete', 'answer': final_answer})}\n\n"

            # ===== COMPLETE =====
            yield f"data: {json.dumps({'step': 'complete', 'summary': {'projects': len(projects_data), 'chunks': len(vector_results)}, 'all_projects': projects_data})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ==================== GRAPH VISUALIZATION ENDPOINTS ====================

@app.get("/api/graph-viz")
async def graph_visualization(
    q: str = Query(default="", description="Search query for entities"),
    entity: str = Query(default="", description="Specific entity to center on"),
    depth: int = Query(default=1, description="Depth of relationships to explore"),
    limit: int = Query(default=50, description="Maximum nodes to return")
):
    """
    Get graph data for visualization.
    Returns nodes and links in a format suitable for force-graph visualization.
    """
    try:
        with driver.session() as session:
            nodes = []
            links = []
            node_ids = set()

            if entity:
                # Get neighborhood of specific entity
                result = session.run("""
                    MATCH (center:Entity {name: $entity})
                    OPTIONAL MATCH (center)-[r:RELATES_TO]-(neighbor:Entity)
                    WITH center, collect(DISTINCT {
                        node: neighbor,
                        rel: r,
                        direction: CASE WHEN startNode(r) = center THEN 'out' ELSE 'in' END
                    })[0..$limit] as neighbors
                    RETURN center, neighbors
                """, entity=entity, limit=limit)

                record = result.single()
                if record:
                    center = record["center"]
                    if center:
                        node_ids.add(center["name"])
                        nodes.append({
                            "id": center["name"],
                            "name": center["name"],
                            "group": "center",
                            "size": 20
                        })

                        for neighbor_data in record["neighbors"]:
                            if neighbor_data["node"]:
                                neighbor = neighbor_data["node"]
                                if neighbor["name"] not in node_ids:
                                    node_ids.add(neighbor["name"])
                                    nodes.append({
                                        "id": neighbor["name"],
                                        "name": neighbor["name"],
                                        "group": "neighbor",
                                        "size": 10
                                    })

                                # Add link
                                if neighbor_data["direction"] == "out":
                                    links.append({
                                        "source": center["name"],
                                        "target": neighbor["name"]
                                    })
                                else:
                                    links.append({
                                        "source": neighbor["name"],
                                        "target": center["name"]
                                    })

            elif q:
                # Search for entities matching query
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE toLower(e.name) CONTAINS toLower($search_term)
                    WITH e LIMIT 10
                    OPTIONAL MATCH (e)-[r:RELATES_TO]-(neighbor:Entity)
                    WITH e, collect(DISTINCT neighbor)[0..5] as neighbors
                    RETURN e as entity, neighbors
                """, search_term=q)

                for record in result:
                    entity_node = record["entity"]
                    if entity_node and entity_node["name"] not in node_ids:
                        node_ids.add(entity_node["name"])
                        nodes.append({
                            "id": entity_node["name"],
                            "name": entity_node["name"],
                            "group": "match",
                            "size": 15
                        })

                        for neighbor in record["neighbors"]:
                            if neighbor and neighbor["name"] not in node_ids:
                                node_ids.add(neighbor["name"])
                                nodes.append({
                                    "id": neighbor["name"],
                                    "name": neighbor["name"],
                                    "group": "neighbor",
                                    "size": 8
                                })

                            if neighbor:
                                links.append({
                                    "source": entity_node["name"],
                                    "target": neighbor["name"]
                                })

            else:
                # Default: show some interesting entities
                result = session.run("""
                    MATCH (e:Entity)-[r:RELATES_TO]->(e2:Entity)
                    WITH e, count(r) as degree
                    ORDER BY degree DESC
                    LIMIT 10
                    MATCH (e)-[r:RELATES_TO]-(neighbor:Entity)
                    WITH e, collect(DISTINCT neighbor)[0..5] as neighbors
                    RETURN e as entity, neighbors
                """)

                for record in result:
                    entity_node = record["entity"]
                    if entity_node and entity_node["name"] not in node_ids:
                        node_ids.add(entity_node["name"])
                        nodes.append({
                            "id": entity_node["name"],
                            "name": entity_node["name"],
                            "group": "hub",
                            "size": 15
                        })

                        for neighbor in record["neighbors"]:
                            if neighbor and neighbor["name"] not in node_ids:
                                node_ids.add(neighbor["name"])
                                nodes.append({
                                    "id": neighbor["name"],
                                    "name": neighbor["name"],
                                    "group": "neighbor",
                                    "size": 8
                                })

                            if neighbor:
                                links.append({
                                    "source": entity_node["name"],
                                    "target": neighbor["name"]
                                })

            return {
                "nodes": nodes,
                "links": links,
                "stats": {
                    "node_count": len(nodes),
                    "link_count": len(links)
                }
            }

    except Exception as e:
        return {"error": str(e), "nodes": [], "links": []}


@app.get("/api/graph-stats")
async def graph_stats():
    """Get knowledge graph statistics"""
    try:
        with driver.session() as session:
            entities = session.run("MATCH (e:Entity) RETURN count(e) as c").single()["c"]
            relationships = session.run("MATCH ()-[r:RELATES_TO]->() RETURN count(r) as c").single()["c"]

            # Top entities by connections
            top_entities = session.run("""
                MATCH (e:Entity)-[r:RELATES_TO]-()
                WITH e.name as name, count(r) as connections
                ORDER BY connections DESC
                LIMIT 10
                RETURN name, connections
            """).data()

            return {
                "entities": entities,
                "relationships": relationships,
                "top_entities": top_entities
            }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/entity-search")
async def entity_search(q: str = Query(..., description="Entity name to search")):
    """Search for entities by name"""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (e:Entity)
                WHERE toLower(e.name) CONTAINS toLower($search_term)
                RETURN e.name as name
                ORDER BY size(e.name)
                LIMIT 20
            """, search_term=q)

            return {"entities": [r["name"] for r in result]}
    except Exception as e:
        return {"error": str(e), "entities": []}


# ============================================================================
# AGENTIC QUERY ENDPOINT (NEW)
# Uses gpt-oss:120b for intelligent query planning and execution
# ============================================================================

from test_agentic_query import AgenticQuerySystem

# Initialize agentic system (lazy loading)
_agentic_system = None

def get_agentic_system():
    global _agentic_system
    if _agentic_system is None:
        print("Initializing Agentic Query System...")
        _agentic_system = AgenticQuerySystem()
        print("Agentic Query System ready!")
    return _agentic_system


@app.get("/api/agentic-search")
async def agentic_search(
    q: str = Query(..., description="Natural language query"),
    debug: bool = Query(default=False, description="Return debug information")
):
    """
    Agentic Search - LLM-powered intelligent query planning

    Uses gpt-oss:120b to:
    1. Analyze query intent (count, list, search)
    2. Select appropriate tools (neo4j_count, text_search, vector_search)
    3. Execute multi-step queries if needed
    4. Generate comprehensive answer

    Handles:
    - Metadata queries: "How many HVDC projects in 2024?"
    - Location queries: "Projects in Germany?"
    - Technical queries: "BESS projects?"
    - Combined queries: "HVDC projects in Germany?"
    - Semantic queries: "Grid stability solutions?"
    """
    try:
        system = get_agentic_system()
        result = system.query(q)

        # Format response
        response = {
            "success": True,
            "query": q,
            "total_projects": len(result.get("execution_results", {}).get("all_projects_collected", [])),
            "answer": result.get("answer", ""),
            "query_type": result.get("plan", {}).get("query_type", "unknown"),
            "tools_used": [s.get("tool") for s in result.get("plan", {}).get("execution_steps", [])],
        }

        # Add project list
        projects = result.get("execution_results", {}).get("all_projects_collected", [])

        # Deduplicate by project_id
        seen_pids = set()
        unique_projects = []
        for p in projects:
            pid = p.get("project_id")
            if pid and pid not in seen_pids:
                seen_pids.add(pid)
                unique_projects.append({
                    "project_id": pid,
                    "project_name": p.get("project_name"),
                    "technology": p.get("technology"),
                    "year": p.get("year"),
                    "customer": p.get("customer")
                })

        response["projects"] = unique_projects[:100]  # Limit to 100 for response size
        response["total_projects"] = len(unique_projects)

        # Technology breakdown
        tech_breakdown = {}
        year_breakdown = {}
        for p in unique_projects:
            tech = p.get("technology") or "Unknown"
            tech_breakdown[tech] = tech_breakdown.get(tech, 0) + 1
            year = str(p.get("year") or "Unknown")
            year_breakdown[year] = year_breakdown.get(year, 0) + 1

        response["by_technology"] = tech_breakdown
        response["by_year"] = year_breakdown

        if debug:
            response["debug"] = {
                "plan": result.get("plan"),
                "step_results": result.get("execution_results", {}).get("step_results", [])
            }

        return response

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "query": q,
            "traceback": traceback.format_exc() if debug else None
        }


@app.get("/api/agentic-search-stream")
async def agentic_search_stream(
    q: str = Query(..., description="Natural language query"),
    top_k: int = Query(default=30, description="Number of results for answer context")
):
    """
    Streaming Agentic Search - sends results step by step as SSE events

    Pipeline:
    1. Planning (LLM decides tools)
    2. Tool Execution (text_search, vector_search, neo4j_count, etc.)
    3. Answer Generation
    """

    async def generate_stream():
        try:
            system = get_agentic_system()

            # ===== STEP 1: PLANNING =====
            yield f"data: {json.dumps({'step': 'planning', 'status': 'started', 'message': 'Analyzing query...'})}\n\n"

            plan = system.plan_execution(q)
            tools_planned = [s.get("tool") for s in plan.get("execution_steps", [])]

            yield f"data: {json.dumps({'step': 'planning', 'status': 'complete', 'query_type': plan.get('query_type'), 'tools': tools_planned, 'reasoning': plan.get('reasoning', '')[:100]})}\n\n"

            # ===== STEP 2: EXECUTION =====
            yield f"data: {json.dumps({'step': 'execution', 'status': 'started', 'message': f'Executing {len(tools_planned)} tools...'})}\n\n"

            execution_results = system.execute_plan(plan)
            all_projects = execution_results.get("all_projects_collected", [])

            # Deduplicate
            seen_pids = set()
            unique_projects = []
            for p in all_projects:
                pid = p.get("project_id")
                if pid and pid not in seen_pids:
                    seen_pids.add(pid)
                    unique_projects.append({
                        "project_id": pid,
                        "project_name": p.get("project_name"),
                        "technology": p.get("technology"),
                        "year": p.get("year")
                    })

            yield f"data: {json.dumps({'step': 'execution', 'status': 'complete', 'projects_found': len(unique_projects), 'projects': unique_projects[:20]})}\n\n"

            # ===== STEP 2.5: FETCH DETAILED CHUNKS WITH IMAGES =====
            yield f"data: {json.dumps({'step': 'vector_search', 'status': 'started', 'message': 'Fetching document details...'})}\n\n"

            # Do a vector search to get detailed chunks with images for the reference panel
            # Uses same BAAI/bge-large-en-v1.5 model as the index (1024 dimensions)
            top_chunks = []
            try:
                query_embedding = embedding_model.encode([q])[0].tolist()

                # If we have specific projects, search within those using vector index
                if unique_projects:
                    project_ids = [p["project_id"] for p in unique_projects[:50]]
                    # Use db.index.vector.queryNodes procedure with post-filtering
                    # Need large search_k since we filter after vector search
                    vector_query = """
                    CALL db.index.vector.queryNodes($index_name, $search_k, $query_embedding)
                    YIELD node, score
                    WHERE node.project_id IN $project_ids
                    RETURN node.chunk_id as chunk_id, node.project_id as project_id, node.project_name as project_name,
                           node.technology as technology, node.year as year, node.customer as customer,
                           node.page as page, node.file_name as file_name, node.text as content,
                           node.page_image_relative as page_image, score
                    ORDER BY score DESC
                    LIMIT $top_k
                    """
                    with driver.session() as session:
                        # Search 500 candidates to find results from specific projects
                        result = session.run(vector_query,
                                           index_name=INDEX_NAME,
                                           search_k=500,
                                           query_embedding=query_embedding,
                                           project_ids=project_ids,
                                           top_k=top_k)
                        for record in result:
                            top_chunks.append({
                                "chunk_id": record["chunk_id"],
                                "project_id": record["project_id"],
                                "project_name": record["project_name"],
                                "technology": record["technology"],
                                "year": record["year"],
                                "customer": record["customer"],
                                "page": record["page"],
                                "file_name": record["file_name"],
                                "content": record["content"][:500] if record["content"] else "",
                                "page_image": record["page_image"],
                                "score": record["score"]
                            })
                else:
                    # Full vector search using the index
                    vector_query = """
                    CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
                    YIELD node, score
                    RETURN node.chunk_id as chunk_id, node.project_id as project_id, node.project_name as project_name,
                           node.technology as technology, node.year as year, node.customer as customer,
                           node.page as page, node.file_name as file_name, node.text as content,
                           node.page_image_relative as page_image, score
                    """
                    with driver.session() as session:
                        result = session.run(vector_query,
                                           index_name=INDEX_NAME,
                                           query_embedding=query_embedding,
                                           top_k=top_k)
                        for record in result:
                            top_chunks.append({
                                "chunk_id": record["chunk_id"],
                                "project_id": record["project_id"],
                                "project_name": record["project_name"],
                                "technology": record["technology"],
                                "year": record["year"],
                                "customer": record["customer"],
                                "page": record["page"],
                                "file_name": record["file_name"],
                                "content": record["content"][:500] if record["content"] else "",
                                "page_image": record["page_image"],
                                "score": record["score"]
                            })
            except Exception as e:
                print(f"Vector search for chunks failed: {e}")

            yield f"data: {json.dumps({'step': 'vector_search', 'status': 'complete', 'chunks_found': len(top_chunks), 'top_chunks': top_chunks})}\n\n"

            # ===== STEP 2.7: GRAPH CONTEXT =====
            yield f"data: {json.dumps({'step': 'graph_context', 'status': 'started', 'message': 'Fetching graph relationships...'})}\n\n"

            graph_context = {"entities": [], "relationships": []}
            try:
                # Get entities mentioned in top chunks (use project names as entity search)
                entity_names = list(set([p.get("project_name", "") for p in unique_projects[:20] if p.get("project_name")]))

                if entity_names:
                    with driver.session() as session:
                        # Find related entities through MENTIONS and RELATES_TO
                        entity_query = """
                        MATCH (e:Entity)
                        WHERE any(name IN $names WHERE toLower(e.name) CONTAINS toLower(name))
                        WITH e LIMIT 20
                        OPTIONAL MATCH (e)-[r:RELATES_TO]->(e2:Entity)
                        RETURN e.name as entity, e.type as entity_type,
                               collect(DISTINCT {target: e2.name, rel_type: type(r)})[0..5] as relations
                        LIMIT 10
                        """
                        result = session.run(entity_query, names=entity_names)
                        for record in result:
                            graph_context["entities"].append({
                                "name": record["entity"],
                                "type": record["entity_type"],
                                "relations": record["relations"]
                            })

                        # Also get technology/customer relationships
                        if unique_projects:
                            tech_query = """
                            MATCH (p:PageChunk)
                            WHERE p.project_id IN $project_ids
                            RETURN DISTINCT p.technology as technology, p.customer as customer,
                                   count(p) as chunk_count
                            ORDER BY chunk_count DESC
                            LIMIT 10
                            """
                            project_ids = [p["project_id"] for p in unique_projects[:50]]
                            result = session.run(tech_query, project_ids=project_ids)
                            for record in result:
                                graph_context["relationships"].append({
                                    "technology": record["technology"],
                                    "customer": record["customer"],
                                    "chunk_count": record["chunk_count"]
                                })
            except Exception as e:
                print(f"Graph context failed: {e}")

            yield f"data: {json.dumps({'step': 'graph_context', 'status': 'complete', 'entities_found': len(graph_context['entities']), 'relationships_found': len(graph_context['relationships'])})}\n\n"

            # ===== STEP 3: ANSWER GENERATION =====
            yield f"data: {json.dumps({'step': 'answer_generation', 'status': 'started', 'message': 'Generating answer...'})}\n\n"

            # Group projects by technology and year for better context
            by_technology = {}
            by_year = {}
            for p in unique_projects:
                tech = p.get("technology", "Unknown")
                year = p.get("year", "Unknown")
                by_technology[tech] = by_technology.get(tech, 0) + 1
                by_year[year] = by_year.get(year, 0) + 1

            # Use the actual execution_results from execute_plan (has correct tool names)
            # Just add the additional context (graph_context, breakdowns)
            execution_results["graph_context"] = graph_context
            execution_results["by_technology"] = by_technology
            execution_results["by_year"] = by_year

            answer = system.generate_answer(q, execution_results)

            yield f"data: {json.dumps({'step': 'answer_generation', 'status': 'complete', 'answer': answer})}\n\n"

            # ===== COMPLETE =====
            yield f"data: {json.dumps({'step': 'complete', 'summary': {'projects': len(unique_projects), 'chunks': len(top_chunks)}, 'all_projects': unique_projects, 'top_chunks': top_chunks})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    import uvicorn
    print("=" * 80)
    print("ULTRATHINK Integrated API Server")
    print("=" * 80)
    print(f"✅ Neo4j connected: {NEO4J_URI}")
    print(f"✅ Output directory: {OUTPUT_DIR}")
    print(f"✅ Images served from: /images/*")
    print()
    print("Starting server on http://localhost:8001")
    print("Frontend can connect from: http://localhost:3000")
    print()
    print("Available endpoints:")
    print("  GET  /api/health              - Health check")
    print("  GET  /api/stats               - Database statistics")
    print("  GET  /api/search              - Vector search with filters")
    print("  GET  /api/llm-search          - Natural language search using LLM (old)")
    print("  GET  /api/agentic-search      - NEW: Intelligent query with gpt-oss:120b")
    print("  GET  /api/agentic-search-stream - NEW: Streaming agentic search")
    print("  GET  /api/count               - Count projects with filters")
    print("  GET  /api/projects            - List all projects")
    print("  GET  /api/document/{id}       - Get document details")
    print("  GET  /api/image/{project}/{path} - Serve document images")
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=8001)