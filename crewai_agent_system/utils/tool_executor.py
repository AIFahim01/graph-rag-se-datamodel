#!/usr/bin/env python3
"""
Tool Executor - Executes actual tools and retrieves real data

This module executes the actual tools from test_agentic_query.py to get real
project data from Neo4j and vector search, instead of returning mock data.
"""

from typing import Dict, List, Any, Optional
import logging
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

from crewai_agent_system.utils.query_parser import ParsedQuery

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes actual tools to retrieve real project data"""

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        """
        Initialize tool executor with database connections.

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        self.embedding_model = None
        self._init_connections()

    def _init_connections(self):
        """Initialize Neo4j and embedding model connections"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j connection established")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}. Tool execution will return empty results.")
            self.driver = None

        try:
            logger.info("Loading embedding model...")
            self.embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5', device='cpu')
            logger.info("Embedding model loaded")
        except Exception as e:
            logger.warning(f"Embedding model load failed: {e}. Vector search will not work.")
            self.embedding_model = None

    def close(self):
        """Close database connections"""
        if self.driver:
            self.driver.close()

    # ==================== TOOL IMPLEMENTATIONS ====================

    def tool_neo4j_count(self, filters: Dict) -> Dict:
        """Count projects matching filters"""
        if not self.driver:
            return {"count": 0, "sample_projects": [], "filters_used": filters}

        try:
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
                if result:
                    return {
                        "count": result["count"],
                        "sample_projects": result["sample_projects"],
                        "filters_used": filters
                    }
        except Exception as e:
            logger.error(f"neo4j_count error: {e}")

        return {"count": 0, "sample_projects": [], "filters_used": filters}

    def tool_neo4j_list_all(self, filters: Dict, limit: int = 500) -> Dict:
        """List all projects matching filters"""
        if not self.driver:
            return {"projects": [], "total": 0, "filters_used": filters}

        try:
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
        except Exception as e:
            logger.error(f"neo4j_list_all error: {e}")

        return {"projects": [], "total": 0, "filters_used": filters}

    def tool_vector_search(self, query: str, top_k: int = 50) -> Dict:
        """Semantic vector search"""
        if not self.driver or not self.embedding_model:
            return {
                "results": [],
                "unique_projects": [],
                "total_chunks": 0,
                "unique_project_count": 0
            }

        try:
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
                    "results": all_results[:10],
                    "unique_projects": unique_projects,
                    "total_chunks": len(all_results),
                    "unique_project_count": len(unique_projects)
                }
        except Exception as e:
            logger.error(f"vector_search error: {e}")

        return {
            "results": [],
            "unique_projects": [],
            "total_chunks": 0,
            "unique_project_count": 0
        }

    def tool_entity_search(self, entity_name: str) -> Dict:
        """Search for entity and find related projects"""
        if not self.driver:
            return {
                "search_term": entity_name,
                "matching_entities": [],
                "projects_mentioning": [],
                "project_count": 0
            }

        try:
            entity_query = """
            MATCH (e:Entity)
            WHERE toLower(e.name) CONTAINS toLower($name)
            RETURN e.name as name
            LIMIT 10
            """

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
        except Exception as e:
            logger.error(f"entity_search error: {e}")

        return {
            "search_term": entity_name,
            "matching_entities": [],
            "projects_mentioning": [],
            "project_count": 0
        }

    def tool_text_search(self, keyword: str, field: str = "text", limit: int = 500,
                        technology_filter: str = None) -> Dict:
        """Exact text search for proper nouns and specific terms"""
        if not self.driver:
            return {"keyword": keyword, "field": field, "projects": [], "total": 0}

        try:
            keywords = keyword.strip().split()

            if field == "text":
                if len(keywords) == 1:
                    where_clause = "WHERE toLower(c.text) CONTAINS toLower($keyword)"
                else:
                    conditions = [f"toLower(c.text) CONTAINS toLower('{kw}')" for kw in keywords]
                    where_clause = "WHERE " + " AND ".join(conditions)

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
        except Exception as e:
            logger.error(f"text_search error: {e}")

        return {"keyword": keyword, "field": field, "projects": [], "total": 0}

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

    # ==================== EXECUTION COORDINATION ====================

    def execute_tools_for_query(self, parsed_query: ParsedQuery) -> Dict[str, Any]:
        """
        Execute appropriate tools based on parsed query to get real data.

        Args:
            parsed_query: ParsedQuery object with query analysis

        Returns:
            Dictionary with execution results
        """
        results = {
            "execution_steps": [],
            "final_data": None,
            "projects": [],
            "total_count": 0,
            "statistics": {},
            "error": None
        }

        try:
            # Determine which tools to execute based on query characteristics
            if parsed_query.query_type.value == "count":
                return self._execute_count_query(parsed_query, results)
            elif parsed_query.query_type.value == "list":
                return self._execute_list_query(parsed_query, results)
            elif parsed_query.query_type.value == "search":
                return self._execute_search_query(parsed_query, results)
            else:
                # Default: try metadata search first, then text search
                return self._execute_default_query(parsed_query, results)

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            results["error"] = str(e)
            return results

    def _execute_count_query(self, parsed_query: ParsedQuery, results: Dict) -> Dict:
        """Execute count query using metadata filters"""
        filters = {}

        # Build filters from parsed query
        if parsed_query.technologies:
            # Count for each technology, then sum
            tech_count = 0
            by_tech = {}
            for tech in parsed_query.technologies:
                result = self.tool_neo4j_count({"technology": tech, "year": parsed_query.years[0] if parsed_query.years else None})
                count = result.get("count", 0)
                by_tech[tech] = count
                tech_count += count

            results["execution_steps"].append({
                "tool": "neo4j_count",
                "purpose": f"Count projects with technologies: {parsed_query.technologies}",
                "result_count": tech_count
            })

            results["total_count"] = tech_count
            # For count queries, use breakdown instead of statistics
            results["breakdown"] = {
                "by_technology": by_tech,
                "by_year": {}
            }

        elif parsed_query.countries:
            # Use text search for countries
            result = self.tool_text_search(parsed_query.countries[0], field="text")
            results["execution_steps"].append({
                "tool": "text_search",
                "purpose": f"Search for projects in {parsed_query.countries[0]}",
                "result_count": result.get("total", 0)
            })

            results["projects"] = result.get("projects", [])
            results["total_count"] = result.get("total", 0)

        elif parsed_query.companies:
            # Use text search for companies
            result = self.tool_text_search(parsed_query.companies[0], field="text")
            results["execution_steps"].append({
                "tool": "text_search",
                "purpose": f"Search for {parsed_query.companies[0]} projects",
                "result_count": result.get("total", 0)
            })

            results["projects"] = result.get("projects", [])
            results["total_count"] = result.get("total", 0)

        return results

    def _execute_list_query(self, parsed_query: ParsedQuery, results: Dict) -> Dict:
        """Execute list query to get project details"""
        filters = {}

        if parsed_query.technologies:
            filters["technology"] = parsed_query.technologies[0]

        if parsed_query.years:
            filters["year"] = parsed_query.years[0]

        if filters:
            result = self.tool_neo4j_list_all(filters)
            results["execution_steps"].append({
                "tool": "neo4j_list_all",
                "purpose": f"List projects matching filters: {filters}",
                "result_count": result.get("total", 0)
            })
            results["projects"] = result.get("projects", [])
            results["total_count"] = result.get("total", 0)

        # If no metadata matches, try text search for countries/companies
        if not results["projects"] and parsed_query.countries:
            result = self.tool_text_search(parsed_query.countries[0], field="text")
            results["execution_steps"].append({
                "tool": "text_search",
                "purpose": f"Search for projects in {parsed_query.countries[0]}",
                "result_count": result.get("total", 0)
            })
            results["projects"] = result.get("projects", [])
            results["total_count"] = result.get("total", 0)

        if not results["projects"] and parsed_query.companies:
            result = self.tool_text_search(parsed_query.companies[0], field="text")
            results["execution_steps"].append({
                "tool": "text_search",
                "purpose": f"Search for {parsed_query.companies[0]} projects",
                "result_count": result.get("total", 0)
            })
            results["projects"] = result.get("projects", [])
            results["total_count"] = result.get("total", 0)

        return results

    def _execute_search_query(self, parsed_query: ParsedQuery, results: Dict) -> Dict:
        """Execute semantic search query"""
        # Build search query from keywords
        search_query = " ".join(parsed_query.keywords)

        if search_query:
            result = self.tool_vector_search(search_query, top_k=50)
            results["execution_steps"].append({
                "tool": "vector_search",
                "purpose": f"Semantic search for: {search_query}",
                "result_count": result.get("unique_project_count", 0)
            })

            projects = result.get("unique_projects", [])
            results["projects"] = projects
            results["total_count"] = len(projects)

        return results

    def _execute_default_query(self, parsed_query: ParsedQuery, results: Dict) -> Dict:
        """Default execution strategy"""
        # Try metadata search first
        if parsed_query.technologies:
            return self._execute_count_query(parsed_query, results)
        elif parsed_query.countries:
            return self._execute_list_query(parsed_query, results)
        elif parsed_query.companies:
            return self._execute_list_query(parsed_query, results)
        elif parsed_query.keywords:
            return self._execute_search_query(parsed_query, results)

        return results


def get_tool_executor() -> ToolExecutor:
    """Get or create a tool executor"""
    return ToolExecutor()
