#!/usr/bin/env python3
"""
TEST SCRIPT: Multi-Step Agentic Query System
============================================
This is a standalone test to prototype the agentic query approach.
Does NOT modify existing code - run this to test the concept.

Features:
1. LLM analyzes query and creates execution plan
2. Executes multiple steps if needed (count, list, vector search)
3. Combines results and generates final answer
"""

import json
import requests
import re
import numpy as np
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "siemensenergy"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Using gpt-oss:120b - large context window for handling complex queries
LLM_MODEL = "gpt-oss:120b"

# Database schema for LLM
DB_SCHEMA = """
=== DATABASE SCHEMA ===
Node: PageChunk
Properties:
- chunk_id, text, project_id, project_name
- technology (HVDC, SynCon, SVC/STATCOM, Other)
- year (integer: 2021, 2022, 2024, 2025)
- customer, page, file_name
- embedding (vector for semantic search)

Node: Entity (Knowledge Graph)
- name: entity name (companies, technologies, locations, etc.)
- Connected via RELATES_TO relationships

Stats: 214,426 chunks, 370 projects, 131K+ entities
"""

# Available tools for the agent
AVAILABLE_TOOLS = """
=== AVAILABLE TOOLS ===

1. neo4j_count(filters) - Count projects matching filters
   Example: neo4j_count({"technology": "HVDC", "year": 2024})
   Returns: {"count": 45, "sample_projects": [...]}

2. neo4j_list_all(filters, limit) - List ALL projects matching filters
   Example: neo4j_list_all({"technology": "SynCon"}, limit=500)
   Returns: {"projects": [...], "total": 123}

3. vector_search(query, top_k) - Semantic search in document content
   Example: vector_search("projects in India", top_k=50)
   Returns: {"results": [...], "unique_projects": [...]}

4. entity_search(entity_name) - Find entity in knowledge graph
   Example: entity_search("India")
   Returns: {"found": true, "related_entities": [...], "projects": [...]}

5. aggregate_results(data) - Count/group results from previous steps
   Example: aggregate_results({"project_ids": [...]})
   Returns: {"unique_count": 25, "by_technology": {...}}

6. text_search(keyword, field, technology_filter) - Exact text search (not semantic)
   Example: text_search("India", "text")
   Example with filter: text_search("Germany", "text", technology_filter="HVDC")
   Returns: {"projects": [...], "total": 42}
   Use for: country names, company names, exact terms
   Note: Multiple words are treated as AND (must contain ALL words)
"""


class AgenticQuerySystem:
    """Multi-step query system that uses LLM to plan and execute queries"""

    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5', device='cpu')
        print("Model loaded!")

    def close(self):
        self.driver.close()

    # ==================== TOOL IMPLEMENTATIONS ====================

    def tool_neo4j_count(self, filters: Dict) -> Dict:
        """Count projects matching filters"""
        conditions = []
        if filters.get("technology"):
            conditions.append(f"c.technology = '{filters['technology']}'")
        if filters.get("year"):
            conditions.append(f"c.year = {filters['year']}")
        if filters.get("customer"):
            conditions.append(f"toLower(c.customer) CONTAINS toLower('{filters['customer']}')")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
        MATCH (c:PageChunk)
        {where_clause}
        RETURN count(DISTINCT c.project_id) as count,
               collect(DISTINCT {{
                   project_id: c.project_id,
                   project_name: c.project_name,
                   technology: c.technology,
                   year: c.year,
                   customer: c.customer
               }})[0..5] as sample_projects
        """

        with self.driver.session() as session:
            result = session.run(query).single()
            return {
                "count": result["count"],
                "sample_projects": result["sample_projects"],
                "filters_used": filters
            }

    def tool_neo4j_list_all(self, filters: Dict, limit: int = 500) -> Dict:
        """List all projects matching filters (no top-k limit for aggregation)"""
        conditions = []
        if filters.get("technology"):
            conditions.append(f"c.technology = '{filters['technology']}'")
        if filters.get("year"):
            conditions.append(f"c.year = {filters['year']}")
        if filters.get("customer"):
            conditions.append(f"toLower(c.customer) CONTAINS toLower('{filters['customer']}')")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
        MATCH (c:PageChunk)
        {where_clause}
        RETURN DISTINCT c.project_id as project_id,
               c.project_name as project_name,
               c.technology as technology,
               c.year as year,
               c.customer as customer
        ORDER BY c.project_id
        LIMIT {limit}
        """

        with self.driver.session() as session:
            results = list(session.run(query))
            projects = [dict(r) for r in results]
            return {
                "projects": projects,
                "total": len(projects),
                "filters_used": filters
            }

    def tool_vector_search(self, query: str, top_k: int = 50) -> Dict:
        """Semantic vector search - can use higher top_k for aggregation queries"""
        query_embedding = self.embedding_model.encode(query).tolist()

        cypher = """
        CALL db.index.vector.queryNodes('page_embeddings_ultrathink', $top_k, $embedding)
        YIELD node, score
        RETURN node.chunk_id as chunk_id,
               node.project_id as project_id,
               node.project_name as project_name,
               node.technology as technology,
               node.year as year,
               node.customer as customer,
               node.text as text,
               score
        ORDER BY score DESC
        """

        with self.driver.session() as session:
            results = list(session.run(cypher, embedding=query_embedding, top_k=top_k))

            # Extract unique projects
            seen_projects = set()
            unique_projects = []
            all_results = []

            for r in results:
                result_dict = dict(r)
                all_results.append(result_dict)

                pid = result_dict["project_id"]
                if pid and pid not in seen_projects:
                    seen_projects.add(pid)
                    unique_projects.append({
                        "project_id": pid,
                        "project_name": result_dict["project_name"],
                        "technology": result_dict["technology"],
                        "year": result_dict["year"],
                        "customer": result_dict["customer"],
                        "best_score": result_dict["score"]
                    })

            return {
                "results": all_results[:10],  # Top 10 for context
                "unique_projects": unique_projects,
                "total_chunks": len(all_results),
                "unique_project_count": len(unique_projects)
            }

    def tool_entity_search(self, entity_name: str) -> Dict:
        """Search for entity in knowledge graph and find related projects"""
        # Search for entity
        entity_query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($name)
        RETURN e.name as name
        LIMIT 10
        """

        # Find projects mentioning entity
        project_query = """
        MATCH (c:PageChunk)
        WHERE toLower(c.text) CONTAINS toLower($name)
        RETURN DISTINCT c.project_id as project_id,
               c.project_name as project_name,
               c.technology as technology,
               c.year as year,
               c.customer as customer
        LIMIT 100
        """

        with self.driver.session() as session:
            entities = [r["name"] for r in session.run(entity_query, name=entity_name)]
            projects = [dict(r) for r in session.run(project_query, name=entity_name)]

            return {
                "search_term": entity_name,
                "matching_entities": entities,
                "projects_mentioning": projects,
                "project_count": len(projects)
            }

    def tool_text_search(self, keyword: str, field: str = "text", limit: int = 500,
                         technology_filter: str = None) -> Dict:
        """Exact text search - finds documents containing keyword(s)

        If keyword contains spaces, searches for documents containing ALL words.
        """
        # Split keywords for multi-word search
        keywords = keyword.strip().split()

        if field == "text":
            if len(keywords) == 1:
                # Single keyword search
                where_clause = "WHERE toLower(c.text) CONTAINS toLower($keyword)"
            else:
                # Multi-keyword: must contain ALL words
                conditions = [f"toLower(c.text) CONTAINS toLower('{kw}')" for kw in keywords]
                where_clause = "WHERE " + " AND ".join(conditions)

            # Add technology filter if specified
            if technology_filter:
                where_clause += f" AND c.technology = '{technology_filter}'"

            query = f"""
            MATCH (c:PageChunk)
            {where_clause}
            RETURN DISTINCT c.project_id as project_id,
                   c.project_name as project_name,
                   c.technology as technology,
                   c.year as year,
                   c.customer as customer
            ORDER BY c.project_id
            LIMIT $limit
            """
        elif field == "customer":
            query = """
            MATCH (c:PageChunk)
            WHERE toLower(c.customer) CONTAINS toLower($keyword)
            RETURN DISTINCT c.project_id as project_id,
                   c.project_name as project_name,
                   c.technology as technology,
                   c.year as year,
                   c.customer as customer
            ORDER BY c.project_id
            LIMIT $limit
            """
        else:
            query = """
            MATCH (c:PageChunk)
            WHERE toLower(c.text) CONTAINS toLower($keyword)
               OR toLower(c.customer) CONTAINS toLower($keyword)
               OR toLower(c.project_name) CONTAINS toLower($keyword)
            RETURN DISTINCT c.project_id as project_id,
                   c.project_name as project_name,
                   c.technology as technology,
                   c.year as year,
                   c.customer as customer
            ORDER BY c.project_id
            LIMIT $limit
            """

        with self.driver.session() as session:
            results = list(session.run(query, keyword=keyword, limit=limit))
            projects = [dict(r) for r in results]
            return {
                "keyword": keyword,
                "field": field,
                "projects": projects,
                "total": len(projects)
            }

    def tool_aggregate_results(self, project_list: List[Dict]) -> Dict:
        """Aggregate and summarize project results"""
        if not project_list:
            return {"unique_count": 0, "by_technology": {}, "by_year": {}}

        by_tech = {}
        by_year = {}
        unique_ids = set()

        for p in project_list:
            pid = p.get("project_id")
            if pid:
                unique_ids.add(pid)

            tech = p.get("technology", "Unknown")
            by_tech[tech] = by_tech.get(tech, 0) + 1

            year = p.get("year", "Unknown")
            by_year[str(year)] = by_year.get(str(year), 0) + 1

        return {
            "unique_count": len(unique_ids),
            "by_technology": by_tech,
            "by_year": by_year
        }

    # ==================== LLM PLANNING ====================

    def plan_execution(self, user_query: str) -> Dict:
        """Use LLM to analyze query and create execution plan"""

        prompt = f"""{DB_SCHEMA}

{AVAILABLE_TOOLS}

=== TOOL SELECTION RULES ===

CRITICAL RULE: The database has ONLY 3 structured metadata fields:
  1. technology: HVDC, SynCon, SVC/STATCOM, Other
  2. year: 2021, 2022, 2024, 2025 (integer)
  3. customer: project codes (NOT reliable for company names - use text_search for companies!)

EVERYTHING ELSE is stored in document TEXT content and requires text_search!

TOOL SELECTION:
1. neo4j_count / neo4j_list_all - ONLY for technology and year metadata
   Examples: "HVDC projects", "projects in 2024", "SynCon projects in 2022"
   WARNING: Do NOT use for company names - customer field contains project codes, not company names!

2. vector_search - For CONCEPTS and SHORT TERMS (understands meaning, avoids false matches):
   - Short acronyms: AI, ML, IoT, EV, etc. (avoids matching "training" when looking for "AI")
   - Conceptual queries: "renewable energy", "grid stability", "machine learning"
   - Technical concepts: "power quality", "frequency regulation", "voltage control"
   - Use with higher top_k (100-200) to get good project coverage, then aggregate

3. text_search - For EXACT proper nouns and long specific terms:
   - Countries: USA, Germany, India, Netherlands, Dubai, etc.
   - Months: January, February, March, etc.
   - Company names: TenneT, Siemens, ABB, Elia, etc. (searches project names AND document content)
   - Long technical terms: transformer, converter, substation, etc.

REASONING CHECKLIST:
- Is the query term in [HVDC, SynCon, SVC/STATCOM, Other]? → technology metadata
- Is the query term a 4-digit year [2021-2025]? → year metadata
- Is it a company/customer name? → text_search (NOT neo4j_count - customer field is unreliable!)
- Is it a short acronym (2-3 chars) or conceptual phrase? → vector_search (semantic)
- Is it a specific country or long term? → text_search (exact match)

=== YOUR TASK ===
Analyze the user's query and create an execution plan.

User Query: "{user_query}"

RESPOND WITH JSON ONLY (no markdown, no explanation):
{{
    "query_type": "count|list|search|comparison|complex",
    "needs_full_count": true/false,
    "execution_steps": [
        {{"tool": "tool_name", "params": {{...}}, "purpose": "why this step"}}
    ],
    "reasoning": "brief explanation"
}}

EXAMPLES:

Query: "How many projects in India?"
{{
    "query_type": "count",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "text_search", "params": {{"keyword": "India", "field": "text"}}, "purpose": "Find all documents mentioning India"}},
        {{"tool": "aggregate_results", "params": {{}}, "purpose": "Count unique projects"}}
    ],
    "reasoning": "India is a COUNTRY - use text_search (not neo4j_count, countries are NOT metadata)."
}}

Query: "How many projects in Germany?"
{{
    "query_type": "count",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "text_search", "params": {{"keyword": "Germany", "field": "text"}}, "purpose": "Find all documents mentioning Germany"}},
        {{"tool": "aggregate_results", "params": {{}}, "purpose": "Count unique projects"}}
    ],
    "reasoning": "Germany is a COUNTRY - use text_search (not neo4j_count, countries are NOT metadata)."
}}

Query: "How many HVDC projects in 2024?"
{{
    "query_type": "count",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "neo4j_count", "params": {{"technology": "HVDC", "year": 2024}}, "purpose": "Count from metadata"}}
    ],
    "reasoning": "HVDC and year are metadata fields, direct count possible."
}}

Query: "List all SynCon projects"
{{
    "query_type": "list",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "neo4j_list_all", "params": {{"technology": "SynCon"}}, "purpose": "Get all SynCon projects"}}
    ],
    "reasoning": "SynCon is metadata field, can list directly."
}}

Query: "What BESS projects do we have?"
{{
    "query_type": "search",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "text_search", "params": {{"keyword": "BESS", "field": "text"}}, "purpose": "Search document content for BESS"}},
        {{"tool": "aggregate_results", "params": {{}}, "purpose": "List unique projects"}}
    ],
    "reasoning": "BESS is a technical term - use text_search for exact match."
}}

Query: "How many TenneT projects do we have?"
{{
    "query_type": "count",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "text_search", "params": {{"keyword": "TenneT", "field": "text"}}, "purpose": "Search for TenneT in project names and documents"}},
        {{"tool": "aggregate_results", "params": {{}}, "purpose": "Count unique projects"}}
    ],
    "reasoning": "TenneT is a COMPANY name - use text_search (NOT neo4j_count). Customer metadata field is unreliable for company names."
}}

Query: "Elia projects?"
{{
    "query_type": "list",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "text_search", "params": {{"keyword": "Elia", "field": "text"}}, "purpose": "Search for Elia in project names and documents"}},
        {{"tool": "aggregate_results", "params": {{}}, "purpose": "List unique projects"}}
    ],
    "reasoning": "Elia is a COMPANY name - use text_search to find all related projects."
}}

Query: "HVDC projects in Germany?"
{{
    "query_type": "count",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "text_search", "params": {{"keyword": "Germany", "field": "text", "technology_filter": "HVDC"}}, "purpose": "Find German projects filtered by HVDC technology"}}
    ],
    "reasoning": "Germany is a country (text_search), HVDC is metadata (technology_filter). Use text_search with technology_filter."
}}

Query: "SynCon projects in India?"
{{
    "query_type": "list",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "text_search", "params": {{"keyword": "India", "field": "text", "technology_filter": "SynCon"}}, "purpose": "Find India projects filtered by SynCon technology"}}
    ],
    "reasoning": "India is a country (text_search), SynCon is metadata (technology_filter). Use text_search with technology_filter."
}}

Query: "Projects done in January?"
{{
    "query_type": "count",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "text_search", "params": {{"keyword": "January", "field": "text"}}, "purpose": "Find documents mentioning January"}},
        {{"tool": "aggregate_results", "params": {{}}, "purpose": "Count unique projects"}}
    ],
    "reasoning": "January is a MONTH - not a metadata field. Use text_search to find documents mentioning January."
}}

Query: "How many projects in USA in January?"
{{
    "query_type": "count",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "text_search", "params": {{"keyword": "USA January", "field": "text"}}, "purpose": "Find documents mentioning both USA and January"}},
        {{"tool": "aggregate_results", "params": {{}}, "purpose": "Count unique projects"}}
    ],
    "reasoning": "USA is a country, January is a month - neither is metadata. Use text_search with both terms (AND search)."
}}

Query: "Projects in Netherlands?"
{{
    "query_type": "count",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "text_search", "params": {{"keyword": "Netherlands", "field": "text"}}, "purpose": "Find documents mentioning Netherlands"}},
        {{"tool": "aggregate_results", "params": {{}}, "purpose": "Count unique projects"}}
    ],
    "reasoning": "Netherlands is a COUNTRY - not a metadata field. Use text_search."
}}

Query: "Offshore HVDC projects?"
{{
    "query_type": "list",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "text_search", "params": {{"keyword": "offshore", "field": "text", "technology_filter": "HVDC"}}, "purpose": "Find offshore mentions filtered by HVDC technology"}}
    ],
    "reasoning": "Offshore is a location type (text_search), HVDC is metadata (technology_filter)."
}}

Query: "How many AI projects do we have?"
{{
    "query_type": "count",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "vector_search", "params": {{"query": "artificial intelligence AI machine learning neural network", "top_k": 200}}, "purpose": "Semantic search for AI-related content"}},
        {{"tool": "aggregate_results", "params": {{}}, "purpose": "Count unique projects from results"}}
    ],
    "reasoning": "AI is a short 2-letter acronym - text_search would match false positives like 'training', 'contain', etc. Use vector_search for semantic understanding."
}}

Query: "Projects related to AI and grid?"
{{
    "query_type": "search",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "vector_search", "params": {{"query": "artificial intelligence AI machine learning grid power system", "top_k": 200}}, "purpose": "Semantic search for AI+grid related content"}},
        {{"tool": "aggregate_results", "params": {{}}, "purpose": "List unique projects from results"}}
    ],
    "reasoning": "AI is a short acronym prone to false matches. Use vector_search with expanded terms for semantic understanding."
}}

Query: "ML and IoT projects?"
{{
    "query_type": "search",
    "needs_full_count": true,
    "execution_steps": [
        {{"tool": "vector_search", "params": {{"query": "machine learning ML IoT internet of things sensors smart devices", "top_k": 200}}, "purpose": "Semantic search for ML and IoT content"}},
        {{"tool": "aggregate_results", "params": {{}}, "purpose": "List unique projects"}}
    ],
    "reasoning": "ML and IoT are short acronyms - use vector_search for semantic understanding to avoid false matches."
}}

NOW ANALYZE THIS QUERY AND RESPOND WITH JSON:
Query: "{user_query}"

JSON:"""

        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": LLM_MODEL, "prompt": prompt, "temperature": 0.1, "stream": False},
                timeout=60
            )

            if response.status_code == 200:
                llm_response = response.json().get("response", "").strip()

                # Clean and parse JSON
                llm_response = re.sub(r'```json\s*', '', llm_response)
                llm_response = re.sub(r'```\s*', '', llm_response)
                llm_response = re.sub(r'<think>.*?</think>', '', llm_response, flags=re.DOTALL)

                # Find JSON object
                json_match = re.search(r'\{[\s\S]*\}', llm_response)
                if json_match:
                    return json.loads(json_match.group())

        except Exception as e:
            print(f"Error in planning: {e}")

        # Fallback plan
        return {
            "query_type": "search",
            "needs_full_count": False,
            "execution_steps": [
                {"tool": "vector_search", "params": {"query": user_query, "top_k": 50}, "purpose": "Default search"}
            ],
            "reasoning": "Fallback to vector search"
        }

    # ==================== EXECUTION ====================

    def execute_plan(self, plan: Dict) -> Dict:
        """Execute the planned steps and collect results"""
        results = []
        all_projects = []

        print(f"\n{'='*60}")
        print(f"Executing plan: {plan.get('reasoning', 'No reasoning')}")
        print(f"{'='*60}")

        for i, step in enumerate(plan.get("execution_steps", [])):
            tool_name = step.get("tool")
            params = step.get("params", {})
            purpose = step.get("purpose", "")

            print(f"\nStep {i+1}: {tool_name}")
            print(f"  Purpose: {purpose}")
            print(f"  Params: {params}")

            # Execute tool
            if tool_name == "neo4j_count":
                result = self.tool_neo4j_count(params)
                # ALSO fetch project list for count queries so we have data to return
                list_result = self.tool_neo4j_list_all(params, limit=500)
                if "projects" in list_result:
                    all_projects.extend(list_result["projects"])
            elif tool_name == "neo4j_list_all":
                result = self.tool_neo4j_list_all(params, params.get("limit", 500))
                if "projects" in result:
                    all_projects.extend(result["projects"])
            elif tool_name == "vector_search":
                result = self.tool_vector_search(params.get("query", ""), params.get("top_k", 50))
                if "unique_projects" in result:
                    all_projects.extend(result["unique_projects"])
            elif tool_name == "entity_search":
                result = self.tool_entity_search(params.get("entity_name", ""))
                if "projects_mentioning" in result:
                    all_projects.extend(result["projects_mentioning"])
            elif tool_name == "text_search":
                result = self.tool_text_search(
                    params.get("keyword", ""),
                    params.get("field", "text"),
                    params.get("limit", 500),
                    params.get("technology_filter", None)
                )
                if "projects" in result:
                    all_projects.extend(result["projects"])
            elif tool_name == "aggregate_results":
                result = self.tool_aggregate_results(all_projects)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            print(f"  Result summary: {self._summarize_result(result)}")
            results.append({"step": i+1, "tool": tool_name, "result": result})

        return {
            "plan": plan,
            "step_results": results,
            "all_projects_collected": all_projects
        }

    def _summarize_result(self, result: Dict) -> str:
        """Create a brief summary of a result"""
        if "count" in result:
            return f"Count: {result['count']}"
        if "total" in result:
            return f"Total: {result['total']} projects"
        if "unique_project_count" in result:
            return f"Found {result['unique_project_count']} unique projects"
        if "project_count" in result:
            return f"Found {result['project_count']} projects"
        if "unique_count" in result:
            return f"Aggregated: {result['unique_count']} unique projects"
        return str(result)[:100]

    # ==================== ANSWER GENERATION ====================

    def generate_answer(self, user_query: str, execution_results: Dict) -> str:
        """Use LLM to generate final answer from execution results"""

        # Prepare context from results
        context_parts = []
        for step_result in execution_results.get("step_results", []):
            tool = step_result["tool"]
            result = step_result["result"]

            if tool == "neo4j_count":
                count = result.get('count', 0)
                context_parts.append(f"EXACT COUNT FROM DATABASE: {count} projects")
                if result.get("sample_projects"):
                    samples = result["sample_projects"][:3]
                    context_parts.append(f"(Showing 3 samples of {count} total): {json.dumps(samples, indent=2)}")

            elif tool == "neo4j_list_all":
                context_parts.append(f"Listed {result.get('total', 0)} projects from database")
                if result.get("projects"):
                    samples = result["projects"][:5]
                    context_parts.append(f"Sample: {json.dumps(samples, indent=2)}")

            elif tool == "vector_search":
                context_parts.append(f"Vector search found {result.get('unique_project_count', 0)} unique projects")
                if result.get("unique_projects"):
                    samples = result["unique_projects"][:5]
                    context_parts.append(f"Top matches: {json.dumps(samples, indent=2)}")

            elif tool == "text_search":
                keyword = result.get('keyword', '')
                total = result.get('total', 0)
                context_parts.append(f"Found {total} projects mentioning '{keyword}'")
                if result.get("projects"):
                    samples = result["projects"][:5]
                    context_parts.append(f"Sample projects matching '{keyword}': {json.dumps(samples, indent=2)}")

            elif tool == "aggregate_results":
                context_parts.append(f"Aggregation: {result.get('unique_count', 0)} unique projects")
                if result.get("by_technology"):
                    context_parts.append(f"By technology: {result['by_technology']}")
                if result.get("by_year"):
                    context_parts.append(f"By year: {result['by_year']}")

        context = "\n".join(context_parts)

        # Also include raw project list for counting
        all_projects = execution_results.get("all_projects_collected", [])
        unique_project_ids = set(p.get("project_id") for p in all_projects if p.get("project_id"))

        # Include graph context if available (knowledge graph enrichment)
        graph_context = execution_results.get("graph_context", {})
        graph_info = ""
        if graph_context:
            entities = graph_context.get("entities", [])
            relationships = graph_context.get("relationships", [])
            if entities:
                entity_names = [e.get("name", "") for e in entities if e.get("name")]
                if entity_names:
                    graph_info += f"\nRELATED ENTITIES FROM KNOWLEDGE GRAPH: {', '.join(entity_names[:10])}"
            if relationships:
                tech_summary = [f"{r.get('technology', 'Unknown')} ({r.get('chunk_count', 0)} docs)"
                               for r in relationships if r.get('technology')]
                if tech_summary:
                    graph_info += f"\nTECHNOLOGY DISTRIBUTION: {', '.join(tech_summary[:5])}"

        prompt = f"""You are answering a question about project documents in our database.

USER QUESTION: "{user_query}"

EXECUTION RESULTS:
{context}
{graph_info}

TOTAL UNIQUE PROJECTS FOUND: {len(unique_project_ids)}

IMPORTANT RULES:
- The results show projects whose documents mention the searched terms
- If they asked for a count, give the exact number
- If they asked for a list, provide the project names
- Include technology breakdown if available
- Be concise and natural - just answer the question directly
- NEVER mention internal technical details like "text search", "database query", "metadata", etc.
- Answer as if you naturally found this information

ANSWER:"""

        try:
            response = requests.post(
                OLLAMA_URL,
                json={"model": LLM_MODEL, "prompt": prompt, "temperature": 0.3, "stream": False},
                timeout=120
            )

            if response.status_code == 200:
                answer = response.json().get("response", "").strip()
                # Remove thinking tags
                answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
                return answer

        except Exception as e:
            print(f"Error generating answer: {e}")

        return f"Found {len(unique_project_ids)} unique projects matching your query."

    # ==================== MAIN QUERY METHOD ====================

    def query(self, user_query: str) -> Dict:
        """Main method: analyze, plan, execute, and answer"""
        print(f"\n{'#'*60}")
        print(f"QUERY: {user_query}")
        print(f"{'#'*60}")

        # Step 1: Plan
        print("\n[1] PLANNING...")
        plan = self.plan_execution(user_query)
        print(f"Plan: {json.dumps(plan, indent=2)}")

        # Step 2: Execute
        print("\n[2] EXECUTING...")
        execution_results = self.execute_plan(plan)

        # Step 3: Generate Answer
        print("\n[3] GENERATING ANSWER...")
        answer = self.generate_answer(user_query, execution_results)

        return {
            "query": user_query,
            "plan": plan,
            "execution_results": execution_results,
            "answer": answer
        }


# ==================== TEST ====================

def main():
    """Run test queries"""

    test_queries = [
        # Metadata queries (should use neo4j_count/list)
        "How many HVDC projects in 2024?",
        "List all SynCon projects",

        # Content queries (should use vector_search + aggregate)
        "How many projects in India?",
        "What BESS projects do we have?",
        "Do we have projects in Germany?",

        # Complex queries
        "Compare HVDC vs SynCon project counts",
        "Which countries have the most projects?",
    ]

    system = AgenticQuerySystem()

    try:
        for query in test_queries:
            result = system.query(query)

            print(f"\n{'='*60}")
            print("FINAL ANSWER:")
            print(f"{'='*60}")
            print(result["answer"])
            print(f"\n{'='*60}\n")

            input("Press Enter for next query...")

    finally:
        system.close()


if __name__ == "__main__":
    main()
