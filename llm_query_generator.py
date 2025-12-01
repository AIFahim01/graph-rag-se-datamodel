#!/usr/bin/env python3
"""
LLM-Based Query Generator for Neo4j ULTRATHINK Database
Translates natural language queries to Cypher queries using Ollama
"""

import json
import requests
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Complete database schema that's always included in prompts
NEO4J_SCHEMA = """
=== NEO4J DATABASE SCHEMA ===

Node Label: PageChunk

Properties:
- chunk_id (string): Unique identifier for each chunk (e.g., "GC24_016_doc_page1")
- text (string): Document content text (max 2000 characters)
- project_id (string): Project identifier (pattern: GC[YY]_[NNN], e.g., "GC24_016")
- project_name (string): Full project name
- technology (string): Technology type - EXACTLY one of: "HVDC", "SynCon", "SVC/STATCOM", "Other"
- year (integer): Year of the project (values: 2021, 2022, 2024, 2025)
- customer (string): Customer/company name
- customer_normalized (string): Lowercase customer name for matching
- category (string): Category type - one of: "hvdc", "syncon", "facts", "other"
- page (integer): Page number in the document
- file_name (string): Original PDF filename
- page_image_relative (string): Path to page image if available
- total_pages (integer): Total pages in document
- total_images (integer): Number of images in document
- total_tables (integer): Number of tables in document
- embedding (vector[1024]): Vector embedding using BAAI/bge-large-en-v1.5 model

Indexes:
- Vector Index: "page_embeddings_ultrathink" (for embedding property, 1024 dimensions)
- Property Indexes: chunk_id, project_id, technology, year, customer_normalized

Database Statistics:
- Total chunks: 214,426
- Total projects: 370
- Total PDFs: 9,627
- Technologies: HVDC (34 projects), SynCon (projects vary), SVC/STATCOM, Other
- Years available: 2021, 2022, 2024, 2025

IMPORTANT RULES:
1. Year is an INTEGER, not string. Use: c.year = 2024, NOT c.year = '2024'
2. Technology values are case-sensitive: use "HVDC" not "hvdc"
3. For customer matching, use customer_normalized with lowercase
4. Use DISTINCT when counting projects: count(DISTINCT c.project_id)
5. Vector search requires an embedding parameter
"""

# Few-shot examples to guide the LLM
FEW_SHOT_EXAMPLES = """
=== EXAMPLE QUERIES ===

Example 1:
User: "How many HVDC projects in 2024?"
Cypher:
MATCH (c:PageChunk)
WHERE c.technology = 'HVDC' AND c.year = 2024
RETURN count(DISTINCT c.project_id) as project_count

Example 2:
User: "Show all transformer protection documents"
Type: VECTOR_SEARCH
Search Text: "transformer protection systems relay settings"
Note: This requires vector search since we're looking for content

Example 3:
User: "List all SynCon projects"
Cypher:
MATCH (c:PageChunk)
WHERE c.technology = 'SynCon'
RETURN DISTINCT c.project_id, c.project_name, c.customer, c.year
ORDER BY c.year DESC, c.project_id

Example 4:
User: "How many projects do we have?"
Cypher:
MATCH (c:PageChunk)
RETURN count(DISTINCT c.project_id) as total_projects

Example 5:
User: "Find documents about harmonic filters"
Type: VECTOR_SEARCH
Search Text: "harmonic filters power quality THD distortion"

Example 6:
User: "Show HVDC projects for TenneT"
Cypher:
MATCH (c:PageChunk)
WHERE c.technology = 'HVDC' AND toLower(c.customer) CONTAINS 'tennet'
RETURN DISTINCT c.project_id, c.project_name, c.year
ORDER BY c.year DESC

Example 7:
User: "How many HVDC projects?"
Cypher:
MATCH (c:PageChunk)
WHERE c.technology = 'HVDC'
RETURN c.year as year, count(DISTINCT c.project_id) as project_count
ORDER BY year

Example 8:
User: "Recent projects"
Cypher:
MATCH (c:PageChunk)
WHERE c.year >= 2024
RETURN DISTINCT c.project_id, c.project_name, c.technology, c.customer, c.year
ORDER BY c.year DESC, c.project_id
LIMIT 20
"""


class LLMQueryGenerator:
    """Generate Cypher queries from natural language using Ollama"""

    def __init__(self, model: str = "qwen3:14b"):
        """
        Initialize the query generator

        Args:
            model: Ollama model to use (default: qwen3:14b - better model for complex queries)
        """
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"
        self.schema = NEO4J_SCHEMA
        self.examples = FEW_SHOT_EXAMPLES

    def detect_query_type(self, query: str) -> Tuple[str, Optional[str]]:
        """
        Let the LLM decide if query needs vector search or metadata search
        No hardcoded patterns - pure LLM interpretation

        Returns:
            (query_type, search_text) - "vector" or "metadata", and search text if vector
        """
        # Let the LLM itself decide what kind of search is needed
        prompt = f"""Given this query: "{query}"

Analyze if this query needs:
1. VECTOR search - for finding content in documents (locations, concepts, specific information)
2. METADATA search - for exact counts by known fields (technology=HVDC, year=2024)

If the query mentions locations (Germany, France, etc.) or needs to search document content, return: VECTOR
If the query asks for counts of specific metadata fields (how many HVDC in 2024), return: METADATA

Respond with ONLY one word: VECTOR or METADATA"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": 0.1,
                    "stream": False
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                decision = result.get('response', '').strip().upper()

                if "METADATA" in decision:
                    return "metadata", None
                else:
                    # Default to vector search - no hardcoded enhancements
                    return "vector", query

        except Exception as e:
            print(f"Error in LLM query type detection: {e}")

        # Default to vector search if LLM fails
        return "vector", query

    def parse_natural_language(self, query: str) -> Dict[str, Any]:
        """
        Let LLM parse natural language query to extract entities and intent
        """
        result = {
            "original_query": query,
            "query_type": "metadata",  # or "vector"
            "entities": {}
        }

        # Detect query type using LLM
        query_type, search_text = self.detect_query_type(query)
        result["query_type"] = query_type
        if search_text:
            result["search_text"] = search_text

        # Let LLM extract entities and intent - no hardcoded patterns
        # The LLM will handle this in generate_cypher_with_ollama
        return result

    def generate_cypher_with_ollama(self, query: str, parsed: Dict[str, Any]) -> str:
        """
        Use Ollama to generate Cypher query from natural language
        """
        # Build the prompt with better instructions for location queries
        prompt = f"""{self.schema}

{self.examples}

=== YOUR TASK ===
Convert the following natural language query to a Cypher query.

User Query: "{query}"

Important Rules:
- If the query mentions LOCATIONS (Germany, France, UK, etc.), this needs VECTOR SEARCH, return NULL
- If the query mentions company names not in metadata (TenneT, Amprion, etc.), return NULL for vector search
- NEVER use cosineSimilarity, vector(), or embedding functions in Cypher queries
- Vector search is handled separately - for location/content search, return NULL
- If asking "How many HVDC?" without a specific year, show breakdown by year
- Year is an INTEGER (use c.year = 2024, not c.year = '2024')
- Technology values are case-sensitive (use 'HVDC' not 'hvdc')
- Use count(DISTINCT c.project_id) for counting projects
- For recent/latest, use c.year >= 2024
- DO NOT mix metadata queries with vector search operations

If this query needs to search document content (locations, companies, concepts), return: NULL
Otherwise, generate ONLY a valid Neo4j Cypher query for metadata search:
"""

        # Call Ollama
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": 0.1,  # Low temperature for consistency
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                cypher = result.get('response', '').strip()

                # Clean up the response (remove markdown if present)
                cypher = cypher.replace('```cypher', '').replace('```', '').strip()

                # Check if LLM incorrectly returned a type indicator instead of a query
                if cypher.upper().startswith('TYPE: VECTOR_SEARCH') or 'TYPE: VECTOR_SEARCH' in cypher.upper():
                    # This should be a vector search, not a cypher query
                    return None

                return cypher
            else:
                return None

        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return None

    def generate_fallback_cypher(self, parsed: Dict[str, Any]) -> str:
        """
        Generate Cypher query using rule-based approach (fallback if LLM fails)
        Let the LLM handle specific entity extraction - fallback only for basic patterns
        """
        entities = parsed.get('entities', {})
        intent = parsed.get('intent', 'query')
        query_lower = parsed.get('original_query', '').lower()

        # Build WHERE conditions only from what was parsed
        conditions = []
        if 'year' in entities:
            conditions.append(f"c.year = {entities['year']}")
        elif entities.get('year_filter') == 'recent':
            conditions.append("c.year >= 2024")

        where_clause = " AND ".join(conditions) if conditions else ""
        where_statement = f"WHERE {where_clause}" if where_clause else ""

        # Generate query based on intent
        if intent == "count":
            return f"""
            MATCH (c:PageChunk)
            {where_statement}
            RETURN count(DISTINCT c.project_id) as project_count
            """

        elif intent == "list":
            return f"""
            MATCH (c:PageChunk)
            {where_statement}
            RETURN DISTINCT c.project_id, c.project_name, c.technology, c.customer, c.year
            ORDER BY c.year DESC, c.project_id
            LIMIT 50
            """

        else:
            # Default query - for content searches, use vector search instead
            if any(word in query_lower for word in ['about', 'related to', 'concerning', 'regarding']):
                # This should trigger vector search instead
                return None

            # Basic metadata query
            return f"""
            MATCH (c:PageChunk)
            {where_statement}
            RETURN DISTINCT c.project_id, c.project_name, c.technology, c.customer, c.year
            LIMIT 20
            """

    def validate_cypher(self, cypher: str) -> Tuple[bool, List[str]]:
        """
        Validate generated Cypher query for common issues

        Returns:
            (is_valid, list_of_issues)
        """
        issues = []

        # Check for common mistakes
        if "c.year = '" in cypher or 'c.year = "' in cypher:
            issues.append("Year should be integer, not string")

        # Check for invalid property names
        valid_props = [
            'chunk_id', 'text', 'project_id', 'project_name', 'technology',
            'year', 'customer', 'customer_normalized', 'category', 'page',
            'file_name', 'embedding', 'page_image_relative', 'total_pages',
            'total_images', 'total_tables'
        ]

        # Extract properties used in query
        prop_pattern = r'c\.(\w+)'
        used_props = re.findall(prop_pattern, cypher)
        for prop in used_props:
            if prop not in valid_props:
                issues.append(f"Invalid property: c.{prop}")

        # Check for dangerous operations
        dangerous = ['DELETE', 'DETACH', 'DROP', 'CREATE INDEX', 'CREATE CONSTRAINT']
        for keyword in dangerous:
            if keyword in cypher.upper():
                issues.append(f"Dangerous operation: {keyword}")

        return len(issues) == 0, issues

    def fix_common_issues(self, cypher: str) -> str:
        """
        Fix common issues in generated Cypher
        """
        # Fix year as string
        cypher = re.sub(r"c\.year = '(\d+)'", r"c.year = \1", cypher)
        cypher = re.sub(r'c\.year = "(\d+)"', r"c.year = \1", cypher)

        # Ensure DISTINCT for project counts
        if "count(c.project_id)" in cypher:
            cypher = cypher.replace("count(c.project_id)", "count(DISTINCT c.project_id)")

        return cypher

    def generate_query(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Main method to generate query from natural language

        Returns dictionary with:
            - success: bool
            - query_type: "cypher" or "vector"
            - cypher: Generated Cypher query (if applicable)
            - search_text: Text for vector search (if applicable)
            - parsed: Parsed entities and intent
            - issues: Any validation issues
        """
        # Parse the query
        parsed = self.parse_natural_language(natural_language_query)

        # If it's a vector search query
        if parsed["query_type"] == "vector":
            return {
                "success": True,
                "query_type": "vector",
                "search_text": parsed.get("search_text", natural_language_query),
                "parsed": parsed,
                "filters": parsed.get("entities", {})
            }

        # Generate Cypher query using LLM
        cypher = self.generate_cypher_with_ollama(natural_language_query, parsed)

        # Check if LLM returned NULL indicating vector search is needed
        if cypher and (cypher.upper().startswith("NULL") or cypher.upper().startswith("NONE")):
            # Switch to vector search
            return {
                "success": True,
                "query_type": "vector",
                "search_text": natural_language_query,
                "parsed": parsed,
                "filters": parsed.get("entities", {}),
                "message": "LLM indicated vector search needed for location/content query"
            }

        # Fallback to rule-based if LLM fails
        if not cypher:
            print("LLM generation failed, using rule-based fallback")
            cypher = self.generate_fallback_cypher(parsed)

        # Fix common issues
        cypher = self.fix_common_issues(cypher)

        # Validate
        is_valid, issues = self.validate_cypher(cypher)

        return {
            "success": is_valid,
            "query_type": "cypher",
            "cypher": cypher,
            "parsed": parsed,
            "issues": issues
        }


# Test the generator if run directly
if __name__ == "__main__":
    generator = LLMQueryGenerator()

    # Test queries
    test_queries = [
        "How many HVDC projects in 2024?",
        "Show all SynCon projects",
        "How many projects do we have?",
        "Find documents about transformer protection",
        "List recent HVDC projects",
        "Show projects for TenneT",
        "How many HVDC projects?",  # Should show breakdown by year
        "Search for harmonic filter specifications",
        "What projects were delivered in 2025?",
        "Count all projects by technology"
    ]

    print("Testing LLM Query Generator")
    print("=" * 80)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)

        result = generator.generate_query(query)

        if result["success"]:
            if result["query_type"] == "cypher":
                print("Generated Cypher:")
                print(result["cypher"])
            else:
                print(f"Vector Search for: {result['search_text']}")
                if result.get("filters"):
                    print(f"With filters: {result['filters']}")
        else:
            print(f"Failed to generate query. Issues: {result['issues']}")

        print()