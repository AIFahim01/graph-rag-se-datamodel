#!/usr/bin/env python3
"""
CrewAI Implementation - Autonomous Multi-Agent System

Uses the official CrewAI framework with proper agents, tools, and tasks.
"""

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
from typing import Dict, List, Any, Optional
import logging
from neo4j import GraphDatabase

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    logger.warning("Sentence Transformers not available - semantic search disabled")

logger = logging.getLogger(__name__)


# ==================== DATABASE TOOLS USING @tool DECORATOR ====================

class DatabaseTools:
    """Database tools for project queries"""

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        if EMBEDDING_AVAILABLE:
            self.embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5', device='cpu')
        else:
            self.embedding_model = None

    def close(self):
        """Close database connection"""
        self.driver.close()

    @tool("Count Projects by Technology")
    def count_projects_tool(self, technology: str, year: Optional[int] = None) -> str:
        """
        Count projects by technology and optional year.

        Args:
            technology: Technology type (HVDC, SynCon, SVC/STATCOM, Other)
            year: Optional year to filter

        Returns:
            Count of projects and sample names
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
                   collect(DISTINCT c.project_name)[0..5] as samples
            """

            with self.driver.session() as session:
                result = session.run(query).single()
                if result:
                    count = result["count"]
                    samples = result["samples"]
                    return f"Found {count} {technology} projects. Samples: {samples}"
                else:
                    return f"No {technology} projects found."
        except Exception as e:
            logger.error(f"Count error: {e}")
            return f"Error counting {technology} projects: {str(e)}"

    @tool("List All Projects")
    def list_projects_tool(self, technology: Optional[str] = None, limit: int = 500) -> str:
        """
        List all projects, optionally filtered by technology.

        Args:
            technology: Optional technology filter
            limit: Maximum projects to return

        Returns:
            List of matching projects
        """
        try:
            where_clause = f"WHERE c.technology = '{technology}'" if technology else ""

            query = f"""
            MATCH (c:PageChunk)
            {where_clause}
            RETURN DISTINCT c.project_id as id,
                   c.project_name as name,
                   c.technology as tech,
                   c.year as year
            ORDER BY c.project_id
            LIMIT {limit}
            """

            with self.driver.session() as session:
                results = list(session.run(query))
                projects = [dict(r) for r in results]

                if not projects:
                    return "No projects found."

                project_list = "\n".join(
                    [f"  {i+1}. {p['name']} (Tech: {p['tech']}, Year: {p['year']})"
                     for i, p in enumerate(projects[:20])]
                )

                if len(projects) > 20:
                    project_list += f"\n  ... and {len(projects) - 20} more projects"

                return f"Found {len(projects)} projects:\n{project_list}"
        except Exception as e:
            logger.error(f"List error: {e}")
            return f"Error listing projects: {str(e)}"

    @tool("Search Projects by Location")
    def search_location_tool(self, country: str, limit: int = 500) -> str:
        """
        Search for projects in a specific country.

        Args:
            country: Country name
            limit: Maximum results

        Returns:
            Projects in that country
        """
        try:
            query = f"""
            MATCH (c:PageChunk)
            WHERE toLower(c.text) CONTAINS toLower('{country}')
            RETURN DISTINCT c.project_id as id,
                   c.project_name as name,
                   c.technology as tech,
                   c.year as year
            ORDER BY c.project_id
            LIMIT {limit}
            """

            with self.driver.session() as session:
                results = list(session.run(query))
                projects = [dict(r) for r in results]

                if not projects:
                    return f"No projects found in {country}."

                project_list = "\n".join(
                    [f"  {i+1}. {p['name']} (Tech: {p['tech']}, Year: {p['year']})"
                     for i, p in enumerate(projects[:20])]
                )

                if len(projects) > 20:
                    project_list += f"\n  ... and {len(projects) - 20} more projects"

                return f"Found {len(projects)} projects in {country}:\n{project_list}"
        except Exception as e:
            logger.error(f"Location search error: {e}")
            return f"Error searching {country}: {str(e)}"

    @tool("Search Projects by Company")
    def search_company_tool(self, company: str, limit: int = 500) -> str:
        """
        Search for projects by company name.

        Args:
            company: Company name
            limit: Maximum results

        Returns:
            Projects associated with company
        """
        try:
            query = f"""
            MATCH (c:PageChunk)
            WHERE toLower(c.text) CONTAINS toLower('{company}')
               OR toLower(c.project_name) CONTAINS toLower('{company}')
            RETURN DISTINCT c.project_id as id,
                   c.project_name as name,
                   c.technology as tech,
                   c.year as year
            ORDER BY c.project_id
            LIMIT {limit}
            """

            with self.driver.session() as session:
                results = list(session.run(query))
                projects = [dict(r) for r in results]

                if not projects:
                    return f"No projects found for {company}."

                project_list = "\n".join(
                    [f"  {i+1}. {p['name']} (Tech: {p['tech']}, Year: {p['year']})"
                     for i, p in enumerate(projects[:20])]
                )

                if len(projects) > 20:
                    project_list += f"\n  ... and {len(projects) - 20} more projects"

                return f"Found {len(projects)} projects for {company}:\n{project_list}"
        except Exception as e:
            logger.error(f"Company search error: {e}")
            return f"Error searching {company}: {str(e)}"

    @tool("Semantic Search")
    def semantic_search_tool(self, query: str, top_k: int = 20) -> str:
        """
        Semantically search for projects using embeddings.

        Args:
            query: Search query
            top_k: Number of top results

        Returns:
            Semantically similar projects
        """
        if not self.embedding_model:
            return "Semantic search temporarily unavailable due to dependency issues. Try using location or company search instead."

        try:
            query_embedding = self.embedding_model.encode(query).tolist()

            cypher = """
            CALL db.index.vector.queryNodes('page_embeddings_ultrathink', $top_k, $embedding)
            YIELD node, score
            RETURN DISTINCT node.project_id as id,
                   node.project_name as name,
                   node.technology as tech,
                   node.year as year,
                   score
            ORDER BY score DESC
            """

            with self.driver.session() as session:
                results = list(session.run(cypher, embedding=query_embedding, top_k=top_k))

                if not results:
                    return f"No semantic matches found for '{query}'."

                projects = [dict(r) for r in results]
                project_list = "\n".join(
                    [f"  {i+1}. {p['name']} (Tech: {p['tech']}, Year: {p['year']}, Score: {p['score']:.2f})"
                     for i, p in enumerate(projects[:10])]
                )

                if len(projects) > 10:
                    project_list += f"\n  ... and {len(projects) - 10} more"

                return f"Found {len(projects)} semantic matches for '{query}':\n{project_list}"
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return f"Error with semantic search: {str(e)}"

    @tool("Get Database Statistics")
    def stats_tool(self) -> str:
        """Get overall database statistics"""
        try:
            query = """
            MATCH (c:PageChunk)
            RETURN count(DISTINCT c.project_id) as total_projects,
                   collect(DISTINCT c.technology) as technologies
            """

            with self.driver.session() as session:
                result = session.run(query).single()
                if result:
                    total = result["total_projects"]
                    techs = result["technologies"]
                    return f"Database: {total} projects, Technologies: {techs}"
                else:
                    return "Database appears empty."
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return f"Error getting statistics: {str(e)}"


# ==================== CREWAI AGENT DEFINITIONS ====================

class CrewAIProjectAnalysis:
    """CrewAI setup for project analysis with autonomous agents"""

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        """Initialize CrewAI system with database tools"""

        self.db_tools = DatabaseTools(neo4j_uri, neo4j_user, neo4j_password)

        # Create agents
        self.query_analyzer = self._create_query_analyzer()
        self.researcher = self._create_researcher()
        self.synthesizer = self._create_synthesizer()

        # Create crew
        self.crew = Crew(
            agents=[self.query_analyzer, self.researcher, self.synthesizer],
            process=Process.sequential,
            verbose=True,
        )

    def _create_query_analyzer(self) -> Agent:
        """Create query analysis agent"""
        return Agent(
            role="Query Analyzer",
            goal="Understand and classify user queries to determine the best data retrieval approach",
            backstory="""You are an expert at understanding project-related queries.
You identify:
- What type of query it is (count, list, search)
- What filters should apply (technology, location, company)
- Which tools should be used to answer it
You provide clear, actionable analysis.""",
            verbose=True,
            allow_delegation=True,
        )

    def _create_researcher(self) -> Agent:
        """Create research agent with tools"""
        return Agent(
            role="Research Specialist",
            goal="Retrieve and analyze project data using available tools and database queries",
            backstory="""You are an expert researcher with deep knowledge of the project database.
You excel at:
- Using count and list tools effectively
- Searching by location and company
- Performing semantic searches
- Compiling complete and accurate results
You have access to multiple tools to find any project information.""",
            tools=[
                self.db_tools.count_projects_tool,
                self.db_tools.list_projects_tool,
                self.db_tools.search_location_tool,
                self.db_tools.search_company_tool,
                self.db_tools.semantic_search_tool,
                self.db_tools.stats_tool,
            ],
            verbose=True,
            allow_delegation=False,
        )

    def _create_synthesizer(self) -> Agent:
        """Create response synthesis agent"""
        return Agent(
            role="Response Synthesizer",
            goal="Create clear, comprehensive answers that directly address the user's query",
            backstory="""You are an expert communicator who synthesizes complex information.
You:
- Summarize findings clearly
- Format data for easy understanding
- Highlight key results
- Provide context and insights
You create professional, well-structured responses.""",
            verbose=True,
            allow_delegation=False,
        )

    def process_query(self, user_query: str) -> str:
        """
        Process a user query using the CrewAI crew.

        Args:
            user_query: User's natural language query

        Returns:
            Final synthesized response
        """
        logger.info(f"\n{'='*100}")
        logger.info(f"CrewAI Processing: {user_query}")
        logger.info(f"{'='*100}\n")

        # Create tasks for the crew
        analyze_task = Task(
            description=f"""Analyze this query and determine the best approach:
"{user_query}"

Identify:
1. What the user wants to know
2. What type of data retrieval is needed
3. Which tools should be used""",
            expected_output="Clear analysis of the query and recommended approach",
            agent=self.query_analyzer,
        )

        research_task = Task(
            description=f"""Based on the analysis, retrieve all relevant project data for:
"{user_query}"

Use the appropriate tools to get comprehensive results.
Provide ALL matching projects, not just samples.""",
            expected_output="Complete list of all projects matching the query",
            agent=self.researcher,
        )

        synthesis_task = Task(
            description=f"""Create a final, comprehensive response for the user's query:
"{user_query}"

Make sure to:
1. Directly answer the question
2. Include ALL relevant projects or counts
3. Format clearly for the user
4. Provide insights if relevant""",
            expected_output="Professional, well-structured final answer",
            agent=self.synthesizer,
        )

        # Execute the crew
        result = self.crew.kickoff(inputs={
            "task": user_query,
            "analyze_task": analyze_task,
            "research_task": research_task,
            "synthesis_task": synthesis_task,
        })

        logger.info(f"{'='*100}")
        logger.info("Query Processing Complete")
        logger.info(f"{'='*100}\n")

        return str(result)

    def close(self):
        """Close database connections"""
        self.db_tools.close()
        logger.info("CrewAI system closed")


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    print("\n" + "="*100)
    print("CREWAI AUTONOMOUS MULTI-AGENT SYSTEM FOR PROJECT ANALYSIS")
    print("="*100)

    system = CrewAIProjectAnalysis()

    # Example queries
    queries = [
        "How many HVDC projects do we have in 2024?",
        "List all SynCon projects",
        "Show me TenneT projects",
        "What projects are in Germany?",
    ]

    for query in queries:
        print(f"\n\nUser Query: {query}")
        print("-"*100)

        try:
            response = system.process_query(query)
            print(f"\nFinal Response:\n{response}")
        except Exception as e:
            print(f"Error processing query: {e}")
            import traceback
            traceback.print_exc()

    system.close()
    print("\n" + "="*100)
    print("System demonstration complete!")
    print("="*100 + "\n")
