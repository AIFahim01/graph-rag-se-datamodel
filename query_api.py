#!/usr/bin/env python3
"""
ULTRATHINK - Query API for Frontend Integration
Provides comprehensive search capabilities for the vectorized document database
"""

import json
from typing import List, Dict, Optional, Any
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import numpy as np

class UltrathinkQueryAPI:
    """
    Query API for searching vectorized HVDC/SynCon project documents
    """

    def __init__(self):
        # Neo4j configuration
        self.neo4j_uri = "bolt://localhost:7687"
        self.neo4j_user = "neo4j"
        self.neo4j_password = "siemensenergy"
        self.node_label = "PageChunk"
        self.index_name = "page_embeddings_ultrathink"

        # Initialize connections
        self.driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )

        # Load embedding model
        print("Loading embedding model...")
        self.model = SentenceTransformer('BAAI/bge-large-en-v1.5', device='cpu')
        print("Model loaded successfully")

    def close(self):
        """Close database connection"""
        self.driver.close()

    def metadata_search(self,
                       technology: Optional[str] = None,
                       year: Optional[str] = None,
                       customer: Optional[str] = None,
                       project_id: Optional[str] = None,
                       limit: int = 100) -> List[Dict]:
        """
        Search by metadata fields only

        Args:
            technology: 'HVDC' or 'SynCon'
            year: '2021', '2022', '2024', '2025', 'ETC_2024', 'ETC_2025'
            customer: Customer name
            project_id: Specific project ID
            limit: Maximum results to return

        Returns:
            List of matching documents with metadata
        """
        # Build WHERE clause
        where_conditions = []
        params = {"limit": limit}

        if technology:
            where_conditions.append("c.technology = $technology")
            params["technology"] = technology

        if year:
            where_conditions.append("c.year = $year")
            params["year"] = year

        if customer:
            where_conditions.append("c.customer_normalized = $customer")
            params["customer"] = customer.upper()

        if project_id:
            where_conditions.append("c.project_id = $project_id")
            params["project_id"] = project_id

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        query = f"""
        MATCH (c:{self.node_label})
        WHERE {where_clause}
        RETURN c.chunk_id as chunk_id,
               c.project_id as project_id,
               c.project_name as project_name,
               c.technology as technology,
               c.year as year,
               c.customer as customer,
               c.page as page,
               c.file_name as file_name,
               c.text as text
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, **params)
            return [dict(record) for record in result]

    def vector_search(self,
                     query_text: str,
                     top_k: int = 10,
                     technology_filter: Optional[str] = None,
                     year_filter: Optional[str] = None,
                     customer_filter: Optional[str] = None) -> List[Dict]:
        """
        Semantic search using vector embeddings with optional filters

        Args:
            query_text: Natural language query
            top_k: Number of results to return
            technology_filter: Optional filter by technology
            year_filter: Optional filter by year
            customer_filter: Optional filter by customer

        Returns:
            List of semantically similar documents
        """
        # Generate query embedding
        query_embedding = self.model.encode([query_text])[0]

        # Build filter conditions
        filter_conditions = []
        if technology_filter:
            filter_conditions.append(f"node.technology = '{technology_filter}'")
        if year_filter:
            filter_conditions.append(f"node.year = '{year_filter}'")
        if customer_filter:
            filter_conditions.append(f"node.customer_normalized = '{customer_filter.upper()}'")

        where_clause = " AND ".join(filter_conditions) if filter_conditions else ""
        where_statement = f"WHERE {where_clause}" if where_clause else ""

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
               score
        ORDER BY score DESC
        LIMIT $top_k
        """

        with self.driver.session() as session:
            # Search more to account for filtering
            search_k = top_k * 5 if filter_conditions else top_k

            result = session.run(
                query,
                index_name=self.index_name,
                search_k=search_k,
                top_k=top_k,
                query_embedding=query_embedding.tolist()
            )

            return [dict(record) for record in result]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics

        Returns:
            Statistics about the document database
        """
        with self.driver.session() as session:
            # Total documents
            total_result = session.run(f"MATCH (c:{self.node_label}) RETURN count(c) as count")
            total_docs = total_result.single()['count']

            # By technology
            tech_result = session.run(f"""
                MATCH (c:{self.node_label})
                RETURN c.technology as technology, count(c) as count
                ORDER BY technology
            """)
            tech_stats = {record['technology']: record['count'] for record in tech_result}

            # By year
            year_result = session.run(f"""
                MATCH (c:{self.node_label})
                RETURN c.year as year, count(c) as count
                ORDER BY year
            """)
            year_stats = {record['year']: record['count'] for record in year_result}

            # By customer (top 10)
            customer_result = session.run(f"""
                MATCH (c:{self.node_label})
                RETURN c.customer as customer, count(c) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            customer_stats = {record['customer']: record['count'] for record in customer_result}

            return {
                "total_documents": total_docs,
                "by_technology": tech_stats,
                "by_year": year_stats,
                "top_customers": customer_stats
            }

    def answer_query(self, question: str) -> Dict[str, Any]:
        """
        Natural language question answering
        Analyzes the question and routes to appropriate search method

        Args:
            question: Natural language question

        Returns:
            Answer with supporting documents
        """
        question_lower = question.lower()

        # Parse question for filters
        technology = None
        year = None
        customer = None

        # Detect technology
        if 'hvdc' in question_lower:
            technology = 'HVDC'
        elif 'syncon' in question_lower or 'synchronous' in question_lower:
            technology = 'SynCon'

        # Detect year
        for y in ['2021', '2022', '2024', '2025']:
            if y in question:
                year = y
                break

        # Detect if it's a counting question
        is_count_question = any(word in question_lower for word in ['how many', 'count', 'number of', 'total'])

        # Detect if it's a listing question
        is_list_question = any(word in question_lower for word in ['which', 'what', 'list', 'show all'])

        if is_count_question:
            # Handle counting questions with metadata search
            results = self.metadata_search(
                technology=technology,
                year=year,
                limit=10000
            )

            # Group results
            projects = set()
            pages = []
            for r in results:
                projects.add(r['project_id'])
                pages.append({
                    'project': r['project_id'],
                    'page': r['page'],
                    'customer': r['customer']
                })

            answer = {
                'question': question,
                'answer_type': 'count',
                'count': len(results),
                'unique_projects': len(projects),
                'filters_applied': {
                    'technology': technology,
                    'year': year
                },
                'sample_results': results[:10]
            }

        elif is_list_question and (technology or year):
            # Handle listing questions with metadata search
            results = self.metadata_search(
                technology=technology,
                year=year,
                limit=1000
            )

            # Group by project
            projects = {}
            for r in results:
                pid = r['project_id']
                if pid not in projects:
                    projects[pid] = {
                        'project_id': pid,
                        'project_name': r['project_name'],
                        'customer': r['customer'],
                        'technology': r['technology'],
                        'year': r['year'],
                        'pages': []
                    }
                projects[pid]['pages'].append(r['page'])

            answer = {
                'question': question,
                'answer_type': 'list',
                'projects': list(projects.values()),
                'total_projects': len(projects),
                'total_pages': len(results),
                'filters_applied': {
                    'technology': technology,
                    'year': year
                }
            }

        else:
            # Handle semantic search questions
            results = self.vector_search(
                query_text=question,
                top_k=10,
                technology_filter=technology,
                year_filter=year
            )

            answer = {
                'question': question,
                'answer_type': 'semantic_search',
                'results': results,
                'filters_applied': {
                    'technology': technology,
                    'year': year
                }
            }

        return answer


# Example usage and test cases
if __name__ == "__main__":
    print("=" * 80)
    print("ULTRATHINK Query API - Test Suite")
    print("=" * 80)
    print()

    # Initialize API
    api = UltrathinkQueryAPI()

    # Test questions
    test_questions = [
        "Which projects have HVDC in 2025?",
        "How many HVDC documents are in the database?",
        "Show all SynCon projects from 2024",
        "What are the power requirements for HVDC converters?",
        "List all HVDC projects for year 2025",
        "Which customers have HVDC projects in 2024?",
        "transformer protection systems for HVDC",
    ]

    print("📊 Database Statistics:")
    print("-" * 40)
    stats = api.get_statistics()
    print(f"Total documents: {stats['total_documents']:,}")
    print(f"By technology: {stats['by_technology']}")
    print(f"By year: {stats['by_year']}")
    print(f"Top customers: {list(stats['top_customers'].keys())[:5]}")
    print()

    # Test each question
    for question in test_questions:
        print(f"❓ Question: {question}")
        print("-" * 40)

        answer = api.answer_query(question)

        if answer['answer_type'] == 'count':
            print(f"📊 Count: {answer['count']} documents")
            print(f"   Unique projects: {answer['unique_projects']}")
            print(f"   Filters: {answer['filters_applied']}")

        elif answer['answer_type'] == 'list':
            print(f"📋 Found {answer['total_projects']} projects:")
            for proj in answer['projects'][:5]:
                print(f"   - {proj['project_id']}: {proj['customer']} ({proj['year']}) - {len(proj['pages'])} pages")
            if answer['total_projects'] > 5:
                print(f"   ... and {answer['total_projects'] - 5} more")

        elif answer['answer_type'] == 'semantic_search':
            print(f"🔍 Semantic search results:")
            for i, result in enumerate(answer['results'][:3], 1):
                print(f"   {i}. {result['project_id']} (page {result['page']}) - {result['technology']}")
                print(f"      Score: {result.get('score', 0):.3f}")
                print(f"      Text preview: {result['text'][:100]}...")

        print()

    # Close connection
    api.close()

    print("=" * 80)
    print("✅ API test complete! Ready for frontend integration")
    print("=" * 80)