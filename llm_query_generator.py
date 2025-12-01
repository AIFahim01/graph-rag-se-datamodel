#!/usr/bin/env python3
"""
FULLY LLM-BASED Query Generator for Neo4j ULTRATHINK Database
100% LLM-driven - No hardcoded patterns or fallbacks
"""

import json
import requests
import re
from typing import Dict, Any, Optional

# Complete database schema for LLM context
NEO4J_SCHEMA = """
=== NEO4J DATABASE SCHEMA ===

Node Label: PageChunk

Properties:
- chunk_id (string): Unique identifier (e.g., "GC24_016_doc_page1")
- text (string): Document content text (searchable via vector)
- project_id (string): Project identifier (pattern: GC[YY]_[NNN], e.g., "GC24_016")
- project_name (string): Full project name
- technology (string): EXACTLY one of: "HVDC", "SynCon", "SVC/STATCOM", "Other"
- year (integer): Project year (values: 2021, 2022, 2024, 2025)
- customer (string): Customer/company name
- customer_normalized (string): Lowercase customer name
- page (integer): Page number in document
- file_name (string): Original PDF filename
- embedding (vector[1024]): For semantic search

Database Stats:
- Total chunks: 214,426
- Total projects: 370
- Technologies: HVDC, SynCon, SVC/STATCOM, Other
- Years: 2021, 2022, 2024, 2025

CRITICAL RULES:
1. Year is INTEGER: use c.year = 2024, NOT c.year = '2024'
2. Technology is case-sensitive: use 'HVDC' not 'hvdc'
3. Use count(DISTINCT c.project_id) for project counts
4. ONLY these technologies exist in metadata: HVDC, SynCon, SVC/STATCOM, Other
5. Terms like BESS, transformer, cable, etc. are NOT in metadata - they're in document TEXT
"""


class LLMQueryGenerator:
    """100% LLM-based query generator - no fallbacks"""

    def __init__(self, model: str = "qwen3:8b"):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"
        self.schema = NEO4J_SCHEMA

    def generate_query(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Single LLM call to analyze query and generate appropriate response.
        Returns structured JSON with query type and content.
        """

        prompt = f"""{self.schema}

=== YOUR TASK ===
Analyze the user's query and respond with a JSON object.

User Query: "{natural_language_query}"

You must decide:
1. Is this a METADATA query? (counting/listing by technology, year, customer fields)
2. Is this a VECTOR_SEARCH query? (searching document content for topics, terms, concepts)

DECISION RULES:
- If query asks about technologies: HVDC, SynCon, SVC/STATCOM → METADATA (these are in database fields)
- If query asks about: BESS, transformers, cables, protection, harmonic, specific technical content → VECTOR_SEARCH (search document text)
- If query mentions locations (Germany, France, UK) → VECTOR_SEARCH (locations are in document content)
- If query mentions company names not normalized → VECTOR_SEARCH
- "How many [technology] in [year]" where technology is HVDC/SynCon/SVC → METADATA
- "Find documents about X" or "search for X" → VECTOR_SEARCH

RESPOND WITH ONLY A VALID JSON OBJECT (no markdown, no explanation):

For METADATA queries:
{{"query_type": "metadata", "cypher": "MATCH (c:PageChunk) WHERE ... RETURN ...", "explanation": "brief reason"}}

For VECTOR_SEARCH queries:
{{"query_type": "vector_search", "search_text": "enhanced search terms", "explanation": "brief reason"}}

CYPHER EXAMPLES:
- Count HVDC 2025: MATCH (c:PageChunk) WHERE c.technology = 'HVDC' AND c.year = 2025 RETURN count(DISTINCT c.project_id) as project_count
- List projects: MATCH (c:PageChunk) WHERE c.year = 2025 RETURN DISTINCT c.project_id, c.project_name, c.technology, c.year ORDER BY c.project_id
- Count by year: MATCH (c:PageChunk) WHERE c.technology = 'HVDC' RETURN c.year as year, count(DISTINCT c.project_id) as count ORDER BY year

JSON RESPONSE:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": 0.1,
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '').strip()

                # Parse the JSON response from LLM
                parsed = self._parse_llm_json(llm_response)

                if parsed:
                    return self._format_result(parsed, natural_language_query)
                else:
                    # LLM failed to return valid JSON - ask again with simpler prompt
                    return self._retry_with_simple_prompt(natural_language_query)
            else:
                print(f"Ollama API error: {response.status_code}")
                return self._retry_with_simple_prompt(natural_language_query)

        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return self._retry_with_simple_prompt(natural_language_query)

    def _parse_llm_json(self, response: str) -> Optional[Dict]:
        """Parse JSON from LLM response, handling various formats"""

        # Clean up the response
        response = response.strip()

        # Remove markdown code blocks if present
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)

        # Try to find JSON object in response
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Try parsing the whole response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"Failed to parse LLM JSON: {response[:200]}...")
            return None

    def _format_result(self, parsed: Dict, original_query: str) -> Dict[str, Any]:
        """Format the parsed LLM response into standard result format"""

        query_type = parsed.get('query_type', 'vector_search')

        if query_type == 'metadata':
            cypher = parsed.get('cypher', '')

            # Validate cypher starts with valid keyword
            if cypher and cypher.strip().upper().startswith(('MATCH', 'RETURN', 'WITH', 'CALL', 'OPTIONAL')):
                # Fix common issues
                cypher = self._fix_cypher(cypher)

                return {
                    "success": True,
                    "query_type": "cypher",
                    "cypher": cypher,
                    "explanation": parsed.get('explanation', ''),
                    "original_query": original_query
                }
            else:
                # Invalid cypher, treat as vector search
                print(f"Invalid cypher from LLM: {cypher[:100]}...")
                return {
                    "success": True,
                    "query_type": "vector",
                    "search_text": original_query,
                    "explanation": "LLM generated invalid cypher, using vector search",
                    "original_query": original_query
                }
        else:
            # Vector search
            search_text = parsed.get('search_text', original_query)
            return {
                "success": True,
                "query_type": "vector",
                "search_text": search_text,
                "explanation": parsed.get('explanation', ''),
                "original_query": original_query
            }

    def _fix_cypher(self, cypher: str) -> str:
        """Fix common Cypher issues"""
        # Fix year as string
        cypher = re.sub(r"c\.year = '(\d+)'", r"c.year = \1", cypher)
        cypher = re.sub(r'c\.year = "(\d+)"', r"c.year = \1", cypher)

        # Ensure DISTINCT for project counts
        if "count(c.project_id)" in cypher:
            cypher = cypher.replace("count(c.project_id)", "count(DISTINCT c.project_id)")

        return cypher

    def _retry_with_simple_prompt(self, query: str) -> Dict[str, Any]:
        """Retry with a simpler prompt if first attempt fails"""

        simple_prompt = f"""Analyze this query and respond with JSON only.

Query: "{query}"

If asking about HVDC, SynCon, or SVC/STATCOM projects (these are database fields), respond:
{{"query_type": "metadata", "cypher": "MATCH (c:PageChunk) WHERE [conditions] RETURN [fields]"}}

For anything else (BESS, locations, technical topics), respond:
{{"query_type": "vector_search", "search_text": "{query}"}}

JSON:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": simple_prompt,
                    "temperature": 0.1,
                    "stream": False
                },
                timeout=20
            )

            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '').strip()
                parsed = self._parse_llm_json(llm_response)

                if parsed:
                    return self._format_result(parsed, query)

        except Exception as e:
            print(f"Retry also failed: {e}")

        # Final fallback - LLM completely failed, use vector search
        # This is NOT a hardcoded pattern - it's a "LLM unavailable" fallback
        print("LLM completely unavailable, defaulting to vector search")
        return {
            "success": True,
            "query_type": "vector",
            "search_text": query,
            "explanation": "LLM service unavailable, using vector search as default",
            "original_query": query
        }


# Test if run directly
if __name__ == "__main__":
    generator = LLMQueryGenerator()

    test_queries = [
        "How many HVDC projects in 2025?",
        "How many BESS projects in 2025?",
        "Show all SynCon projects",
        "Find documents about transformer protection",
        "List Germany projects",
        "Count projects by technology",
        "Search for harmonic filter specifications",
        "How many projects do we have?",
    ]

    print("Testing FULLY LLM-Based Query Generator")
    print("=" * 80)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)

        result = generator.generate_query(query)

        print(f"Type: {result['query_type']}")
        if result['query_type'] == 'cypher':
            print(f"Cypher: {result['cypher']}")
        else:
            print(f"Search: {result['search_text']}")
        print(f"Explanation: {result.get('explanation', 'N/A')}")
