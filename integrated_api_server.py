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

# Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "siemensenergy"
NODE_LABEL = "PageChunk"
INDEX_NAME = "page_embeddings_ultrathink"

# Paths
OUTPUT_DIR = Path("/home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/output")
OUTPUT_COPY_DIR = Path("/home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/output_copy_test")

# Load embedding model (once at startup)
print("Loading embedding model...")
embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5', device='cpu')
print("Model loaded!")

# Neo4j connection
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Initialize LLM Query Generator
llm_generator = LLMQueryGenerator(model="qwen3:8b")

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
    print("  GET  /api/llm-search          - Natural language search using LLM")
    print("  GET  /api/count               - Count projects with filters")
    print("  GET  /api/projects            - List all projects")
    print("  GET  /api/document/{id}       - Get document details")
    print("  GET  /api/image/{project}/{path} - Serve document images")
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=8001)