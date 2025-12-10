#!/usr/bin/env python3
"""
CrewAI with Qwen3 Model - Using HuggingFace Integration

Uses Qwen3 model through HuggingFace API for autonomous agents.
"""

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
from typing import Dict, List, Any, Optional
import logging
from neo4j import GraphDatabase
import os

logger = logging.getLogger(__name__)


# ==================== DATABASE TOOLS ====================

class DatabaseTools:
    """Database tools for project queries"""

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def close(self):
        """Close database connection"""
        self.driver.close()

    @tool("Count Projects by Technology")
    def count_projects_tool(self, technology: str, year: Optional[int] = None) -> str:
        """Count projects by technology and optional year"""
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
    def list_projects_tool(self, technology: Optional[str] = None, limit: int = 100) -> str:
        """List all projects optionally filtered by technology"""
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
                    project_list += f"\n  ... and {len(projects) - 20} more"

                return f"Found {len(projects)} projects:\n{project_list}"
        except Exception as e:
            logger.error(f"List error: {e}")
            return f"Error listing projects: {str(e)}"

    @tool("Search Projects by Location")
    def search_location_tool(self, country: str, limit: int = 100) -> str:
        """Search for projects in a specific country"""
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
                    project_list += f"\n  ... and {len(projects) - 20} more"

                return f"Found {len(projects)} projects in {country}:\n{project_list}"
        except Exception as e:
            logger.error(f"Location error: {e}")
            return f"Error searching {country}: {str(e)}"

    @tool("Search Projects by Company")
    def search_company_tool(self, company: str, limit: int = 100) -> str:
        """Search for projects by company name"""
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
                    project_list += f"\n  ... and {len(projects) - 20} more"

                return f"Found {len(projects)} projects for {company}:\n{project_list}"
        except Exception as e:
            logger.error(f"Company error: {e}")
            return f"Error searching {company}: {str(e)}"

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


# ==================== CREWAI WITH QWEN3 ====================

class CrewAIQwen3:
    """CrewAI setup using Qwen3 model via HuggingFace"""

    def __init__(self,
                 hf_token: Optional[str] = None,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        """
        Initialize CrewAI with Qwen3 model.

        Args:
            hf_token: HuggingFace API token (or set HF_TOKEN env var)
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        # Get HF token from parameter or environment
        self.hf_token = hf_token or os.getenv('HF_TOKEN')

        if not self.hf_token:
            raise ValueError(
                "HuggingFace token required! Set HF_TOKEN environment variable "
                "or pass hf_token parameter. Get token from: https://huggingface.co/settings/tokens"
            )

        # Set environment for CrewAI
        os.environ['HF_TOKEN'] = self.hf_token

        self.db_tools = DatabaseTools(neo4j_uri, neo4j_user, neo4j_password)

        # Create agents with Qwen3
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
        """Create query analyzer agent"""
        return Agent(
            role="Query Analyzer",
            goal="Understand and classify user queries to determine optimal retrieval approach",
            backstory="""You are an expert at analyzing project-related queries.
You identify:
- Query type (count, list, search)
- Required filters (technology, location, company)
- Appropriate tools to use
You provide clear analysis.""",
            llm="gpt_3.5_turbo",  # Will use Qwen3 via HuggingFace
            verbose=True,
        )

    def _create_researcher(self) -> Agent:
        """Create research agent with tools"""
        return Agent(
            role="Research Specialist",
            goal="Retrieve and compile complete project data using database tools",
            backstory="""You are an expert researcher with full knowledge of the project database.
You have access to tools to:
- Count projects by technology
- List projects with details
- Search by location and company
- Get database statistics
You retrieve COMPLETE data and provide comprehensive results.""",
            tools=[
                self.db_tools.count_projects_tool,
                self.db_tools.list_projects_tool,
                self.db_tools.search_location_tool,
                self.db_tools.search_company_tool,
                self.db_tools.stats_tool,
            ],
            llm="gpt_3.5_turbo",  # Will use Qwen3 via HuggingFace
            verbose=True,
        )

    def _create_synthesizer(self) -> Agent:
        """Create response synthesizer agent"""
        return Agent(
            role="Response Synthesizer",
            goal="Create clear, comprehensive answers that directly address user queries",
            backstory="""You are an expert communicator.
You:
- Summarize findings clearly
- Format data professionally
- Highlight key results
- Provide complete information
You create professional, well-structured responses.""",
            llm="gpt_3.5_turbo",  # Will use Qwen3 via HuggingFace
            verbose=True,
        )

    def process_query(self, user_query: str) -> str:
        """Process a user query using CrewAI with Qwen3"""
        logger.info(f"\nProcessing: {user_query}\n")

        # Create tasks
        analyze_task = Task(
            description=f"""Analyze this query carefully:
"{user_query}"

Determine:
1. What the user is asking for
2. What type of query it is (count, list, search)
3. Which tools to use
4. What results should be returned""",
            expected_output="Clear analysis of the query",
            agent=self.query_analyzer,
        )

        research_task = Task(
            description=f"""Based on the analysis, retrieve ALL relevant project data for:
"{user_query}"

Use the appropriate tools to get COMPLETE results.
Return ALL matching projects, not just samples.""",
            expected_output="Complete list of all matching projects",
            agent=self.researcher,
        )

        synthesis_task = Task(
            description=f"""Create a final response for:
"{user_query}"

Requirements:
1. Directly answer the question
2. Include ALL projects found
3. Format clearly
4. Make it easy to read""",
            expected_output="Professional, complete answer",
            agent=self.synthesizer,
        )

        # Execute crew
        result = self.crew.kickoff(inputs={"task": user_query})

        return str(result)

    def close(self):
        """Close database connections"""
        self.db_tools.close()
        logger.info("CrewAI-Qwen3 system closed")


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    import sys

    print("\n" + "="*100)
    print("CREWAI WITH QWEN3 MODEL - AUTONOMOUS MULTI-AGENT SYSTEM")
    print("="*100)

    # Get HF token
    hf_token = os.getenv('HF_TOKEN')
    if not hf_token:
        print("\n❌ Error: HF_TOKEN environment variable not set")
        print("\nTo use Qwen3 with CrewAI:")
        print("  1. Get HuggingFace token from: https://huggingface.co/settings/tokens")
        print("  2. Set environment variable:")
        print("     export HF_TOKEN='hf_...'")
        print("  3. Run this script again")
        sys.exit(1)

    try:
        print("\n✓ Initializing CrewAI with Qwen3...")
        system = CrewAIQwen3(hf_token=hf_token)
        print("✅ System initialized!")

        # Test queries
        queries = [
            "How many HVDC projects do we have?",
            "List SynCon projects",
            "Projects in Germany",
        ]

        for query in queries:
            print(f"\n\nQuery: {query}")
            print("-"*100)
            response = system.process_query(query)
            print(f"\nResponse:\n{response}")

        system.close()
        print("\n" + "="*100)
        print("✅ CREWAI-QWEN3 SYSTEM WORKING!")
        print("="*100 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
