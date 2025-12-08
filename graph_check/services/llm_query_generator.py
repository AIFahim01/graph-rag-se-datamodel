"""
LLM-based Cypher Query Generator
Uses Llama to convert natural language to Cypher queries
"""

import json
import requests
from typing import Dict, Optional


class LLMQueryGenerator:
    """Generate Cypher queries from natural language using Llama"""

    def __init__(self, ollama_url: str = "http://localhost:11434/api/generate",
                 model: str = "llama3.2"):
        """
        Initialize LLM query generator

        Args:
            ollama_url: Ollama API URL
            model: Model name (e.g., llama3.2)
        """
        self.ollama_url = ollama_url
        self.model = model
        print(f"🤖 LLM Query Generator initialized with model: {model}")

    def _build_prompt(self, user_query: str, schema_info: str) -> str:
        """Build prompt for LLM"""
        prompt = f"""You are a Neo4j Cypher query expert. Convert natural language questions into Cypher queries.

Database Schema:
{schema_info}

Rules:
1. Generate ONLY the Cypher query, no explanations
2. For counting questions, use COUNT()
3. For "how many" questions, return count with alias
4. Use MATCH patterns appropriately
5. Return the query without markdown formatting or backticks

User Question: {user_query}

Cypher Query:"""
        return prompt

    def get_schema_info(self) -> str:
        """Get schema information for context"""
        schema = """
Node Labels:
- Project (properties: id, type)
- Chunk (properties: chunk_id, project_id, project_type, text_length, entity_count, relation_count)
- Entity (properties: name, mention_count, chunk_ids)

Relationship Types:
- RELATION (from Entity to Entity, properties: type, chunk_id, project_id, confidence)
- MENTIONS (from Chunk to Entity)

Example Queries:
1. Count HVDC projects:
   MATCH (p:Project {type: 'HVDC'}) RETURN count(p) as count

2. Find entities in project:
   MATCH (c:Chunk {project_type: 'HVDC'})-[:MENTIONS]->(e:Entity) RETURN DISTINCT e.name

3. Get relationships:
   MATCH (s:Entity)-[r:RELATION]->(o:Entity) RETURN s.name, r.type, o.name LIMIT 10
"""
        return schema

    def generate_cypher(self, user_query: str) -> Optional[str]:
        """
        Generate Cypher query from natural language

        Args:
            user_query: Natural language question

        Returns:
            Cypher query string or None if generation fails
        """
        print(f"\n🔮 Generating Cypher for: '{user_query}'")

        schema_info = self.get_schema_info()
        prompt = self._build_prompt(user_query, schema_info)

        try:
            # Call Ollama API
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for more deterministic output
                        "top_p": 0.9
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                cypher_query = result.get('response', '').strip()

                # Clean up query
                cypher_query = cypher_query.replace('```cypher', '').replace('```', '').strip()

                print(f"✅ Generated Cypher: {cypher_query}")
                return cypher_query
            else:
                print(f"❌ Ollama API error: {response.status_code}")
                return None

        except requests.exceptions.ConnectionError:
            print(f"❌ Could not connect to Ollama at {self.ollama_url}")
            print(f"   Make sure Ollama is running: ollama serve")
            return None
        except Exception as e:
            print(f"❌ Error generating query: {e}")
            return None

    def generate_cypher_with_fallback(self, user_query: str) -> str:
        """
        Generate Cypher with fallback to template-based generation

        Args:
            user_query: Natural language question

        Returns:
            Cypher query (LLM-generated or template-based)
        """
        # Try LLM first
        cypher = self.generate_cypher(user_query)

        if cypher:
            return cypher

        # Fallback to template-based generation
        print(f"⚠️  LLM generation failed, using template-based fallback")
        return self._template_based_generation(user_query)

    def _template_based_generation(self, user_query: str) -> str:
        """Simple template-based query generation as fallback"""
        query_lower = user_query.lower()

        # Count projects by type
        if "how many" in query_lower and "project" in query_lower:
            if "hvdc" in query_lower:
                return "MATCH (p:Project {type: 'HVDC'}) RETURN count(p) as count"
            elif "syncon" in query_lower:
                return "MATCH (p:Project {type: 'SynCon'}) RETURN count(p) as count"
            elif "owf" in query_lower:
                return "MATCH (p:Project {type: 'OWF'}) RETURN count(p) as count"
            else:
                return "MATCH (p:Project) RETURN p.type, count(p) as count"

        # Count entities
        if "how many" in query_lower and "entit" in query_lower:
            return "MATCH (e:Entity) RETURN count(e) as count"

        # List projects
        if "list" in query_lower and "project" in query_lower:
            return "MATCH (p:Project) RETURN p.id, p.type"

        # Default: return all project types
        return "MATCH (p:Project) RETURN DISTINCT p.type, count(p) as count"


def main():
    """Test the query generator"""
    from config import OLLAMA_API_URL, LLM_MODEL

    generator = LLMQueryGenerator(
        ollama_url=OLLAMA_API_URL,
        model=LLM_MODEL
    )

    # Test questions
    test_questions = [
        "How many HVDC projects are there?",
        "How many SynCon projects?",
        "List all project types",
        "How many entities are in the graph?",
    ]

    for question in test_questions:
        cypher = generator.generate_cypher_with_fallback(question)
        print(f"   Query: {question}")
        print(f"   Cypher: {cypher}")
        print()


if __name__ == "__main__":
    main()
