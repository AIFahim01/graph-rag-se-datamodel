#!/usr/bin/env python3
"""
CrewAI Autonomous Agents with Tools

This module implements proper autonomous agents using the CrewAI framework.
Each agent has specific roles, goals, tools, and can handle multiple queries independently.
"""

from crewai import Agent, Crew, Process, Task
from crewai_tools import tool
from typing import Dict, List, Any, Optional
import logging
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ==================== DATABASE TOOLS ====================

class ProjectDatabaseTools:
    """Tools for accessing project database"""

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5', device='cpu')

    def close(self):
        self.driver.close()

    @tool
    def count_projects_by_technology(self, technology: str, year: Optional[int] = None) -> str:
        """
        Count projects matching a specific technology.

        Args:
            technology: Technology type (HVDC, SynCon, SVC/STATCOM, Other)
            year: Optional year filter

        Returns:
            Count and sample projects
        """
        try:
            conditions = [f"c.technology = '{technology}'"]
            if year:
                conditions.append(f"c.year = {year}")

            where_clause = "WHERE " + " AND ".join(conditions)

            query = f"""
            MATCH (c:PageChunk)
            {where_clause}
            RETURN count(DISTINCT c.project_id) as count,
                   collect(DISTINCT {{
                       project_id: c.project_id,
                       project_name: c.project_name,
                       technology: c.technology,
                       year: c.year
                   }})[0..5] as sample_projects
            """

            with self.driver.session() as session:
                result = session.run(query).single()
                count = result["count"] if result else 0
                samples = result["sample_projects"] if result else []
                return f"Found {count} {technology} projects. Sample: {[p['project_name'] for p in samples[:3]]}"
        except Exception as e:
            logger.error(f"Count projects error: {e}")
            return f"Error counting {technology} projects: {str(e)}"

    @tool
    def list_projects_by_filter(self, technology: Optional[str] = None,
                               country: Optional[str] = None,
                               company: Optional[str] = None,
                               limit: int = 100) -> str:
        """
        List projects matching multiple filters.

        Args:
            technology: Technology type (optional)
            country: Country name (optional)
            company: Company name (optional)
            limit: Maximum projects to return

        Returns:
            List of matching projects
        """
        try:
            if technology:
                conditions = [f"c.technology = '{technology}'"]
                where_clause = "WHERE " + " AND ".join(conditions)
            elif country or company:
                # Text search for country or company
                search_term = country or company
                return self._text_search(search_term, limit)
            else:
                where_clause = ""

            query = f"""
            MATCH (c:PageChunk)
            {where_clause}
            RETURN DISTINCT c.project_id as project_id,
                   c.project_name as project_name,
                   c.technology as technology,
                   c.year as year
            ORDER BY c.project_id
            LIMIT {limit}
            """

            with self.driver.session() as session:
                results = list(session.run(query))
                projects = [dict(r) for r in results]

                if not projects:
                    return "No projects found matching the criteria."

                project_names = [p['project_name'] for p in projects[:10]]
                total = len(projects)
                return f"Found {total} projects. First 10: {project_names}"
        except Exception as e:
            logger.error(f"List projects error: {e}")
            return f"Error listing projects: {str(e)}"

    def _text_search(self, keyword: str, limit: int = 100) -> str:
        """Text search for keywords like countries or companies"""
        try:
            query = f"""
            MATCH (c:PageChunk)
            WHERE toLower(c.text) CONTAINS toLower('{keyword}')
               OR toLower(c.project_name) CONTAINS toLower('{keyword}')
            RETURN DISTINCT c.project_id as project_id,
                   c.project_name as project_name,
                   c.technology as technology,
                   c.year as year
            ORDER BY c.project_id
            LIMIT {limit}
            """

            with self.driver.session() as session:
                results = list(session.run(query))
                projects = [dict(r) for r in results]

                if not projects:
                    return f"No projects found containing '{keyword}'."

                project_names = [p['project_name'] for p in projects[:10]]
                total = len(projects)
                return f"Found {total} projects containing '{keyword}'. First 10: {project_names}"
        except Exception as e:
            logger.error(f"Text search error: {e}")
            return f"Error searching for '{keyword}': {str(e)}"

    @tool
    def search_projects_by_location(self, country: str, limit: int = 100) -> str:
        """
        Search for projects in a specific country.

        Args:
            country: Country name
            limit: Maximum results

        Returns:
            List of projects in that country
        """
        return self._text_search(country, limit)

    @tool
    def search_projects_by_company(self, company_name: str, limit: int = 100) -> str:
        """
        Search for projects by company name.

        Args:
            company_name: Name of company
            limit: Maximum results

        Returns:
            List of projects associated with the company
        """
        return self._text_search(company_name, limit)

    @tool
    def get_project_statistics(self) -> str:
        """
        Get overall statistics about projects in the database.

        Returns:
            Database statistics
        """
        try:
            query = """
            MATCH (c:PageChunk)
            RETURN count(DISTINCT c.project_id) as total_projects,
                   count(DISTINCT c.technology) as technologies,
                   collect(DISTINCT c.technology) as tech_list
            """

            with self.driver.session() as session:
                result = session.run(query).single()
                if result:
                    total = result["total_projects"]
                    techs = result["tech_list"]
                    return f"Database contains {total} projects across {len(techs)} technologies: {techs}"
                else:
                    return "Database is empty."
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return f"Error retrieving statistics: {str(e)}"

    @tool
    def semantic_search_projects(self, query: str, top_k: int = 10) -> str:
        """
        Semantic search for projects using embeddings.

        Args:
            query: Search query
            top_k: Number of top results

        Returns:
            Semantically similar projects
        """
        try:
            query_embedding = self.embedding_model.encode(query).tolist()

            cypher = """
            CALL db.index.vector.queryNodes('page_embeddings_ultrathink', $top_k, $embedding)
            YIELD node, score
            RETURN DISTINCT node.project_id as project_id,
                   node.project_name as project_name,
                   node.technology as technology,
                   node.year as year,
                   score
            ORDER BY score DESC
            """

            with self.driver.session() as session:
                results = list(session.run(cypher, embedding=query_embedding, top_k=top_k))

                if not results:
                    return f"No semantic matches found for '{query}'."

                projects = [dict(r) for r in results]
                project_names = [p['project_name'] for p in projects[:5]]
                return f"Found {len(projects)} semantically similar projects. Top 5: {project_names}"
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return f"Error with semantic search: {str(e)}"


# ==================== AUTONOMOUS AGENTS ====================

class ProjectAnalysisAgents:
    """Factory for creating autonomous project analysis agents"""

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        self.tools = ProjectDatabaseTools(neo4j_uri, neo4j_user, neo4j_password)

    def create_query_analyst_agent(self) -> Agent:
        """
        Agent that analyzes and understands queries.
        Determines query type and requirements.
        """
        return Agent(
            role="Query Analyst",
            goal="Understand and classify user queries to determine the best approach for data retrieval",
            backstory="""You are an expert at understanding natural language queries about projects.
            You excel at identifying:
            - What the user is looking for (count, list, search)
            - What filters should be applied (technology, location, company)
            - What data sources to access (database, vector search)
            You provide clear analysis and recommendations.""",
            verbose=True,
            allow_delegation=False,
        )

    def create_research_agent(self) -> Agent:
        """
        Agent that retrieves project data from the database.
        Uses multiple tools to find projects.
        """
        return Agent(
            role="Research Specialist",
            goal="Retrieve and find projects from the database based on various criteria",
            backstory="""You are an expert researcher with deep knowledge of the project database.
            You are skilled at:
            - Counting projects by technology and year
            - Listing projects with detailed information
            - Searching by location and company
            - Finding projects semantically
            You use the available tools effectively to answer any project-related question.""",
            tools=[
                self.tools.count_projects_by_technology,
                self.tools.list_projects_by_filter,
                self.tools.search_projects_by_location,
                self.tools.search_projects_by_company,
                self.tools.get_project_statistics,
                self.tools.semantic_search_projects,
            ],
            verbose=True,
            allow_delegation=False,
        )

    def create_synthesizer_agent(self) -> Agent:
        """
        Agent that synthesizes findings into clear, comprehensive answers.
        """
        return Agent(
            role="Response Synthesizer",
            goal="Synthesize project data into clear, comprehensive, and well-structured answers",
            backstory="""You are an expert communicator who excels at:
            - Summarizing project information clearly
            - Formatting data in easy-to-understand ways
            - Providing context and insights
            - Highlighting key findings
            You create responses that directly answer the user's question with all relevant details.""",
            verbose=True,
            allow_delegation=False,
        )

    def create_crew(self) -> Crew:
        """
        Create a crew with all analysis agents working together.
        """
        return Crew(
            agents=[
                self.create_query_analyst_agent(),
                self.create_research_agent(),
                self.create_synthesizer_agent(),
            ],
            process=Process.sequential,
            verbose=True,
        )


# ==================== TASK DEFINITIONS ====================

class ProjectAnalysisTasks:
    """Factory for creating analysis tasks"""

    @staticmethod
    def create_analysis_task(query: str) -> Task:
        """
        Create a dynamic analysis task for any query.
        """
        return Task(
            description=f"""Analyze and answer the following project-related query comprehensively:
            "{query}"

            Your response should include:
            1. Analysis of what the user is looking for
            2. The data retrieved from the database
            3. A clear, structured answer with all relevant projects or statistics
            4. Any patterns or insights you notice""",
            expected_output="""A comprehensive response that includes:
            - Clear understanding of what was requested
            - All relevant projects or statistics from the database
            - Properly formatted list or count of results
            - Key insights or patterns identified""",
        )

    @staticmethod
    def create_count_task(technology: str, year: Optional[int] = None) -> Task:
        """Create a task to count projects by technology and year."""
        if year:
            description = f"Count how many {technology} projects we have in {year} and provide sample projects."
        else:
            description = f"Count how many {technology} projects we have in the database and provide sample projects."

        return Task(
            description=description,
            expected_output=f"Total count of {technology} projects with a list of sample projects",
        )

    @staticmethod
    def create_list_task(filters: Dict[str, str]) -> Task:
        """Create a task to list projects with specific filters."""
        filter_str = ", ".join([f"{k}: {v}" for k, v in filters.items()])
        return Task(
            description=f"List all projects matching: {filter_str}. Include project names, technology, and year for each.",
            expected_output=f"A complete numbered list of all projects matching {filter_str}",
        )

    @staticmethod
    def create_search_task(search_term: str) -> Task:
        """Create a task to search for projects."""
        return Task(
            description=f"Search for projects related to '{search_term}' using available tools. Include all matching projects.",
            expected_output=f"A complete list of all projects matching '{search_term}'",
        )


# ==================== AUTONOMOUS SYSTEM ====================

class CrewAIAutonomousSystem:
    """
    Autonomous multi-agent system using CrewAI framework.
    Handles multiple types of queries with autonomous agents.
    """

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        self.agents_factory = ProjectAnalysisAgents(neo4j_uri, neo4j_user, neo4j_password)
        self.crew = self.agents_factory.create_crew()

    def process_query(self, query: str) -> str:
        """
        Process a user query using autonomous agents.

        Args:
            query: User's natural language query

        Returns:
            Response from the agent crew
        """
        logger.info(f"Processing query: {query}")

        # Create a task for this query
        task = ProjectAnalysisTasks.create_analysis_task(query)
        task.agent = self.crew.agents[0]  # Assign to query analyst

        # Execute the crew
        result = self.crew.kickoff(inputs={"query": query})

        logger.info(f"Query completed")
        return result

    def count_projects(self, technology: str, year: Optional[int] = None) -> str:
        """
        Count projects by technology and optional year.

        Args:
            technology: Technology type
            year: Optional year filter

        Returns:
            Count and sample projects
        """
        logger.info(f"Counting {technology} projects" + (f" in {year}" if year else ""))
        task = ProjectAnalysisTasks.create_count_task(technology, year)
        result = self.crew.kickoff(inputs={
            "technology": technology,
            "year": year
        })
        return result

    def list_projects(self, **filters) -> str:
        """
        List projects with specified filters.

        Args:
            **filters: Filter criteria (technology, country, company, etc.)

        Returns:
            List of matching projects
        """
        logger.info(f"Listing projects with filters: {filters}")
        task = ProjectAnalysisTasks.create_list_task(filters)
        result = self.crew.kickoff(inputs=filters)
        return result

    def search_projects(self, search_term: str) -> str:
        """
        Search for projects by keyword.

        Args:
            search_term: Search keyword

        Returns:
            List of matching projects
        """
        logger.info(f"Searching for projects: {search_term}")
        task = ProjectAnalysisTasks.create_search_task(search_term)
        result = self.crew.kickoff(inputs={"search_term": search_term})
        return result

    def close(self):
        """Close database connections"""
        self.agents_factory.tools.close()


if __name__ == "__main__":
    # Example usage
    print("\n" + "="*80)
    print("CREWAI AUTONOMOUS AGENTS SYSTEM")
    print("="*80)

    system = CrewAIAutonomousSystem()

    # Example queries
    queries = [
        "How many HVDC projects do we have in 2024?",
        "List all SynCon projects",
        "What projects are in Germany?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 80)
        result = system.process_query(query)
        print(f"\nResponse:\n{result}\n")

    system.close()
    print("="*80)
