"""
Query Executor and Answer Generator
Execute Cypher queries and generate natural language answers
"""

import json
import requests
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase


class QueryExecutor:
    """Execute Cypher queries and generate answers"""

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                 neo4j_database: str, ollama_url: str, llm_model: str):
        """
        Initialize query executor

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            neo4j_database: Database name
            ollama_url: Ollama API URL
            llm_model: LLM model name
        """
        print(f"🔌 Initializing Query Executor...")

        # Connect to Neo4j
        # Handle auth - if password is empty/None, try without auth
        if neo4j_password == "" or neo4j_password is None:
            self.driver = GraphDatabase.driver(neo4j_uri, auth=None)
        else:
            self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.database = neo4j_database

        # LLM configuration
        self.ollama_url = ollama_url
        self.llm_model = llm_model

        print(f"✅ Query Executor ready!")

    def close(self):
        """Close connections"""
        if self.driver:
            self.driver.close()

    def execute_cypher(self, cypher_query: str) -> List[Dict[str, Any]]:
        """
        Execute Cypher query in Neo4j

        Args:
            cypher_query: Cypher query string

        Returns:
            List of result records as dictionaries
        """
        print(f"\n⚡ Executing Cypher query...")
        print(f"   Query: {cypher_query}")

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher_query)
                records = [dict(record) for record in result]

            print(f"✅ Query executed successfully!")
            print(f"   Results: {len(records)} records")

            return records

        except Exception as e:
            print(f"❌ Query execution error: {e}")
            return []

    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format query results as text"""
        if not results:
            return "No results found."

        # Convert to readable format
        formatted = []
        for i, record in enumerate(results[:10], 1):  # Limit to 10 results
            formatted.append(f"{i}. {json.dumps(record, indent=2)}")

        if len(results) > 10:
            formatted.append(f"... and {len(results) - 10} more results")

        return "\n".join(formatted)

    def generate_answer(self, user_query: str, cypher_query: str,
                       query_results: List[Dict[str, Any]]) -> str:
        """
        Generate natural language answer from query results using LLM

        Args:
            user_query: Original user question
            cypher_query: Executed Cypher query
            query_results: Query results

        Returns:
            Natural language answer
        """
        print(f"\n🤖 Generating natural language answer...")

        # Format results for LLM
        results_text = self.format_results(query_results)

        prompt = f"""You are a helpful assistant answering questions about technical projects in a knowledge graph database.

User Question: {user_query}

Cypher Query Executed: {cypher_query}

Query Results:
{results_text}

Task: Provide a clear, concise answer to the user's question based on the query results.
- If the results contain counts, state the numbers clearly
- If the results contain lists, summarize them
- Be direct and factual
- Use the project type names as they appear (HVDC, SynCon, OWF, etc.)

Answer:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()
                print(f"✅ Answer generated!")
                return answer
            else:
                print(f"⚠️  LLM API error, using fallback")
                return self._fallback_answer(query_results)

        except Exception as e:
            print(f"⚠️  Error generating answer: {e}")
            return self._fallback_answer(query_results)

    def _fallback_answer(self, query_results: List[Dict[str, Any]]) -> str:
        """Generate simple answer without LLM"""
        if not query_results:
            return "No results found in the knowledge graph."

        # Simple formatting
        if len(query_results) == 1 and 'count' in query_results[0]:
            count = query_results[0]['count']
            return f"Found {count} matching items in the knowledge graph."

        return f"Found {len(query_results)} results: {self.format_results(query_results)}"

    def answer_question(self, user_query: str, cypher_query: str) -> Dict[str, Any]:
        """
        Complete question answering pipeline

        Args:
            user_query: User's natural language question
            cypher_query: Generated Cypher query

        Returns:
            Dictionary with query results and answer
        """
        print(f"\n{'='*80}")
        print(f"💬 Question: {user_query}")
        print(f"{'='*80}")

        # Execute query
        results = self.execute_cypher(cypher_query)

        # Generate answer
        answer = self.generate_answer(user_query, cypher_query, results)

        return {
            'question': user_query,
            'cypher_query': cypher_query,
            'results_count': len(results),
            'results': results,
            'answer': answer
        }


def main():
    """Test the query executor"""
    from config import (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE,
                       OLLAMA_API_URL, LLM_MODEL)

    executor = QueryExecutor(
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
        neo4j_database=NEO4J_DATABASE,
        ollama_url=OLLAMA_API_URL,
        llm_model=LLM_MODEL
    )

    # Test queries
    test_cases = [
        {
            'question': "How many HVDC projects are there?",
            'cypher': "MATCH (p:Project {type: 'HVDC'}) RETURN count(p) as count"
        },
        {
            'question': "List all project types",
            'cypher': "MATCH (p:Project) RETURN DISTINCT p.type, count(p) as count"
        }
    ]

    for test in test_cases:
        response = executor.answer_question(test['question'], test['cypher'])
        print(f"\n📝 Answer: {response['answer']}")
        print()

    executor.close()


if __name__ == "__main__":
    main()
