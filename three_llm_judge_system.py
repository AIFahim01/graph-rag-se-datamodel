#!/usr/bin/env python3
"""
Three-LLM Judge System for Intelligent Query Processing

Architecture:
1. LLM-1: Processes query via vector search
2. LLM-2: Processes query via metadata/Cypher
3. LLM-Judge: Evaluates both results and picks the best answer
"""

import asyncio
import requests
import json
from typing import Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import time

class ThreeLLMJudgeSystem:
    def __init__(self, neo4j_driver=None, embedding_model=None):
        self.backend_url = "http://localhost:8001"
        self.ollama_url = "http://localhost:11434"
        self.neo4j_driver = neo4j_driver
        self.embedding_model = embedding_model

    def execute_vector_search(self, query: str) -> Dict[str, Any]:
        """Path 1: Execute vector search for the query"""
        try:
            # Use the LLM search endpoint which does vector search
            response = requests.get(
                f"{self.backend_url}/api/llm-search",
                params={"q": query},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # Extract unique projects and counts
                projects_by_year = {}
                for result in data.get('results', []):
                    year = result.get('year')
                    project_id = result.get('project_id')
                    if year and project_id:
                        if year not in projects_by_year:
                            projects_by_year[year] = set()
                        projects_by_year[year].add(project_id)

                return {
                    "success": True,
                    "method": "vector_search",
                    "total_results": len(data.get('results', [])),
                    "projects_by_year": {year: list(projects) for year, projects in projects_by_year.items()},
                    "raw_results": data.get('results', [])[:5]  # First 5 for context
                }
        except Exception as e:
            return {
                "success": False,
                "method": "vector_search",
                "error": str(e)
            }

    def execute_metadata_query(self, query: str) -> Dict[str, Any]:
        """Path 2: Execute metadata/Cypher query"""
        try:
            # Parse query to extract year, technology, etc.
            year = None
            technology = None

            # Simple parsing for year
            import re
            year_match = re.search(r'\b(20\d{2})\b', query)
            if year_match:
                year = year_match.group(1)

            # Check for technology keywords
            tech_keywords = {
                'hvdc': 'HVDC',
                'syncon': 'SynCon',
                'svc': 'SVC',
                'statcom': 'STATCOM'
            }
            query_lower = query.lower()
            for keyword, tech in tech_keywords.items():
                if keyword in query_lower:
                    technology = tech
                    break

            # Use count endpoint for metadata query
            params = {}
            if year:
                params['year'] = year
            if technology:
                params['technology'] = technology

            response = requests.get(
                f"{self.backend_url}/api/count",
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "method": "metadata_query",
                    "filters": data.get('filters', {}),
                    "counts": data.get('counts', {}),
                    "project_ids": data.get('project_ids', []),
                    "message": data.get('message', '')
                }
        except Exception as e:
            return {
                "success": False,
                "method": "metadata_query",
                "error": str(e)
            }

    def judge_results(self, query: str, vector_result: Dict, metadata_result: Dict) -> Dict[str, Any]:
        """LLM Judge: Evaluate both results and pick the best answer"""

        # Prepare context for the judge
        prompt = f"""You are a judge LLM that must evaluate two different query results and determine the best answer.

User Query: "{query}"

Result from Vector Search (searches document content):
- Success: {vector_result.get('success', False)}
- Total results: {vector_result.get('total_results', 0)}
- Projects found: {json.dumps(vector_result.get('projects_by_year', {}), indent=2)}

Result from Metadata Query (direct database counts):
- Success: {metadata_result.get('success', False)}
- Counts: {json.dumps(metadata_result.get('counts', {}), indent=2)}
- Project IDs: {metadata_result.get('project_ids', [])[:10]}
- Message: {metadata_result.get('message', '')}

JUDGING RULES:
1. If the query asks for a specific YEAR count (like "2021 projects"), prefer METADATA result
2. If the query asks about LOCATIONS (Germany, Arab, etc.), prefer VECTOR result
3. If the query asks about specific TECHNOLOGY with year, prefer METADATA result
4. If both results are successful, choose the one with more specific/complete information
5. If one failed, use the successful one

Based on these rules, provide:
1. Which result to use (VECTOR or METADATA)
2. The final answer to the user's query
3. Brief reason for your choice

Format your response as JSON:
{{
  "chosen_method": "VECTOR" or "METADATA",
  "answer": "Your answer to the user",
  "reason": "Why you chose this method",
  "confidence": 0.0 to 1.0
}}
"""

        try:
            # Call judge LLM (using qwen3:14b for good reasoning)
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "qwen3:14b",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                    "format": "json"
                },
                timeout=30
            )

            if response.status_code == 200:
                llm_response = response.json().get('response', '{}')

                # Try to parse JSON response
                try:
                    judge_decision = json.loads(llm_response)
                    # Ensure required fields exist
                    if 'chosen_method' not in judge_decision:
                        judge_decision['chosen_method'] = "METADATA" if '2021' in query or '2022' in query else "VECTOR"
                    if 'answer' not in judge_decision:
                        judge_decision['answer'] = llm_response[:200]
                except:
                    # Fallback if JSON parsing fails
                    judge_decision = {
                        "chosen_method": "VECTOR" if vector_result.get('success') else "METADATA",
                        "answer": f"Parsed response: {llm_response[:200]}",
                        "reason": "JSON parsing failed, using fallback logic",
                        "confidence": 0.5
                    }

                # Add the actual results to the decision
                judge_decision['vector_result'] = vector_result
                judge_decision['metadata_result'] = metadata_result

                return judge_decision

        except Exception as e:
            # Fallback decision logic
            if metadata_result.get('success') and not vector_result.get('success'):
                chosen = "METADATA"
                answer = metadata_result.get('message', 'Metadata query succeeded')
            elif vector_result.get('success') and not metadata_result.get('success'):
                chosen = "VECTOR"
                answer = f"Found {vector_result.get('total_results', 0)} relevant results"
            else:
                chosen = "VECTOR"
                answer = "Both methods had issues, defaulting to vector search"

            return {
                "chosen_method": chosen,
                "answer": answer,
                "reason": f"Judge LLM failed: {str(e)}",
                "confidence": 0.3,
                "vector_result": vector_result,
                "metadata_result": metadata_result
            }

    def process_query(self, query: str) -> Dict[str, Any]:
        """Main method: Process query through all three LLMs"""

        print(f"Processing query: {query}")
        print("=" * 60)

        # Execute both paths in parallel
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both queries
            vector_future = executor.submit(self.execute_vector_search, query)
            metadata_future = executor.submit(self.execute_metadata_query, query)

            # Get results
            vector_result = vector_future.result()
            metadata_result = metadata_future.result()

        execution_time = time.time() - start_time
        print(f"Both searches completed in {execution_time:.2f} seconds")

        # Judge the results
        print("Sending to judge LLM...")
        judge_start = time.time()
        final_decision = self.judge_results(query, vector_result, metadata_result)
        judge_time = time.time() - judge_start
        print(f"Judge decision made in {judge_time:.2f} seconds")

        # Add timing information
        final_decision['execution_time'] = {
            'parallel_search': execution_time,
            'judge_decision': judge_time,
            'total': execution_time + judge_time
        }

        return final_decision


def test_three_llm_system():
    """Test the three-LLM judge system with various queries"""

    system = ThreeLLMJudgeSystem()

    test_queries = [
        "How many projects we have done in 2021?",
        "How many Germany projects in 2022?",
        "List all HVDC projects",
        "Is there any project in Arab countries?",
        "Count all projects by year"
    ]

    for query in test_queries:
        print("\n" + "="*80)
        print(f"QUERY: {query}")
        print("="*80)

        result = system.process_query(query)

        print(f"\n✓ Chosen Method: {result.get('chosen_method', 'Unknown')}")
        print(f"✓ Confidence: {result.get('confidence', 'N/A')}")
        print(f"✓ Reason: {result.get('reason', 'No reason provided')}")
        print(f"\nFINAL ANSWER:")
        print(result.get('answer', 'No answer generated'))
        print(f"\nExecution time: {result['execution_time']['total']:.2f}s")

        # Show brief summary of both results
        if result.get('vector_result', {}).get('success'):
            print(f"  Vector: {result['vector_result']['total_results']} results")
        if result.get('metadata_result', {}).get('success'):
            counts = result['metadata_result'].get('counts', {})
            print(f"  Metadata: {counts.get('projects', 0)} projects")


if __name__ == "__main__":
    test_three_llm_system()