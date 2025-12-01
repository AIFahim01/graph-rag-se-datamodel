#!/usr/bin/env python3
"""
Test Query Script - Test "How many HVDC projects?" question
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import *
from services.llm_query_generator import LLMQueryGenerator
from services.query_executor import QueryExecutor


def main():
    print("\n" + "="*80)
    print("🧪 TESTING QUERY: How many HVDC projects?")
    print("="*80 + "\n")

    # Initialize components
    print("🔧 Initializing components...")
    query_gen = LLMQueryGenerator(
        ollama_url=OLLAMA_API_URL,
        model=LLM_MODEL
    )

    executor = QueryExecutor(
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
        neo4j_database=NEO4J_DATABASE,
        ollama_url=OLLAMA_API_URL,
        llm_model=LLM_MODEL
    )

    # Test question
    user_query = "How many HVDC projects?"

    print(f"\n💬 User Question: {user_query}")
    print("-" * 80)

    # Generate Cypher query
    cypher_query = query_gen.generate_cypher_with_fallback(user_query)

    print(f"\n📝 Generated Cypher Query:")
    print(f"   {cypher_query}")
    print("-" * 80)

    # Execute and get answer
    response = executor.answer_question(user_query, cypher_query)

    # Display results
    print(f"\n📊 Query Results:")
    print(f"   Found {response['results_count']} result(s)")
    if response['results']:
        for i, result in enumerate(response['results'], 1):
            print(f"   {i}. {result}")
    print("-" * 80)

    print(f"\n✅ Final Answer:")
    print(f"\n   {response['answer']}")
    print("\n" + "="*80)

    # Cleanup
    executor.close()

    # Also run a direct query to verify
    print(f"\n🔍 Verification - Direct Neo4j Query:")
    print(f"   Running: MATCH (p:Project) RETURN p.type, count(p) as count")

    executor2 = QueryExecutor(
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
        neo4j_database=NEO4J_DATABASE,
        ollama_url=OLLAMA_API_URL,
        llm_model=LLM_MODEL
    )

    verification = executor2.execute_cypher("MATCH (p:Project) RETURN p.id as project_id, p.type as project_type")
    print(f"\n   Projects in database:")
    for proj in verification:
        print(f"   - {proj['project_id']}: {proj['project_type']}")

    executor2.close()

    print("\n✨ Test complete!\n")


if __name__ == "__main__":
    main()
