#!/usr/bin/env python3
"""
CrewAI with Ollama - Autonomous Multi-Agent System with Local LLM

Uses Ollama as the LLM backend instead of OpenAI for local autonomous agents.
"""

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
from typing import Dict, List, Any, Optional
import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

# ==================== DATABASE TOOLS USING @tool DECORATOR ====================

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
                    return f"**Count Result**: {count} {technology} projects found. Sample projects: {', '.join(samples) if samples else 'None'}"
                else:
                    return f"**Count Result**: 0 {technology} projects found."
        except Exception as e:
            logger.error(f"Count error: {e}")
            return f"Error counting {technology} projects: {str(e)}"

    @tool("List All Projects")
    def list_projects_tool(self, technology: Optional[str] = None, limit: int = 100) -> str:
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
                     for i, p in enumerate(projects[:30])]
                )

                if len(projects) > 30:
                    project_list += f"\n  ... and {len(projects) - 30} more projects"

                return f"**List Result**: Found {len(projects)} projects:\n{project_list}"
        except Exception as e:
            logger.error(f"List error: {e}")
            return f"Error listing projects: {str(e)}"

    @tool("Search Projects by Location")
    def search_location_tool(self, country: str, limit: int = 100) -> str:
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
                     for i, p in enumerate(projects[:30])]
                )

                if len(projects) > 30:
                    project_list += f"\n  ... and {len(projects) - 30} more projects"

                return f"**Location Search**: Found {len(projects)} projects in {country}:\n{project_list}"
        except Exception as e:
            logger.error(f"Location search error: {e}")
            return f"Error searching {country}: {str(e)}"

    @tool("Search Projects by Company")
    def search_company_tool(self, company: str, limit: int = 100) -> str:
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
                     for i, p in enumerate(projects[:30])]
                )

                if len(projects) > 30:
                    project_list += f"\n  ... and {len(projects) - 30} more projects"

                return f"**Company Search**: Found {len(projects)} projects for {company}:\n{project_list}"
        except Exception as e:
            logger.error(f"Company search error: {e}")
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
                    return f"**Database Statistics**: {total} projects across technologies: {', '.join(techs)}"
                else:
                    return "Database appears empty."
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return f"Error getting statistics: {str(e)}"


# ==================== CREWAI AGENTS WITH OLLAMA ====================

class CrewAIOllama:
    """CrewAI setup using Ollama as the LLM backend"""

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy",
                 ollama_model: str = "gpt-oss:120b",
                 ollama_base_url: str = "http://localhost:11434"):
        """
        Initialize CrewAI with Ollama backend.

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            ollama_model: Ollama model to use
            ollama_base_url: Ollama API base URL
        """
        self.db_tools = DatabaseTools(neo4j_uri, neo4j_user, neo4j_password)
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url

        # Create LLM config for Ollama
        self.llm_config = {
            "model": ollama_model,
            "base_url": ollama_base_url,
        }

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
            goal="Understand user queries and classify them to determine the best retrieval approach",
            backstory="""You are an expert at analyzing project-related queries.
You understand:
- What type of query it is (count, list, search)
- What filters apply (technology, location, company)
- Which tools should be used
You provide clear analysis.""",
            llm=self.llm_config,
            verbose=True,
            allow_delegation=True,
        )

    def _create_researcher(self) -> Agent:
        """Create research agent with database tools"""
        return Agent(
            role="Research Specialist",
            goal="Retrieve and compile complete project data using database tools",
            backstory="""You are an expert researcher with full knowledge of the project database.
You have access to tools to:
- Count projects by technology
- List all projects with details
- Search by location and company
- Get database statistics
You retrieve COMPLETE data, not just samples. Always provide comprehensive results.""",
            tools=[
                self.db_tools.count_projects_tool,
                self.db_tools.list_projects_tool,
                self.db_tools.search_location_tool,
                self.db_tools.search_company_tool,
                self.db_tools.stats_tool,
            ],
            llm=self.llm_config,
            verbose=True,
            allow_delegation=False,
        )

    def _create_synthesizer(self) -> Agent:
        """Create response synthesis agent"""
        return Agent(
            role="Response Synthesizer",
            goal="Create clear, professional responses that directly answer user queries",
            backstory="""You are an expert communicator.
You:
- Summarize findings clearly
- Format data professionally
- Highlight key results
- Provide complete information
You craft responses that directly answer the user's question.""",
            llm=self.llm_config,
            verbose=True,
            allow_delegation=False,
        )

    def process_query(self, user_query: str) -> str:
        """
        Process a user query using the CrewAI crew with Ollama.

        Args:
            user_query: User's natural language query

        Returns:
            Final synthesized response
        """
        logger.info(f"\n{'='*100}")
        logger.info(f"CrewAI-Ollama Processing: {user_query}")
        logger.info(f"{'='*100}\n")

        # Create tasks for the crew
        analyze_task = Task(
            description=f"""Analyze this query carefully:
"{user_query}"

Determine:
1. What the user is asking for
2. What type of query it is (count, list, search)
3. What tools to use
4. What results should be returned""",
            expected_output="Clear analysis of the query and recommended approach",
            agent=self.query_analyzer,
        )

        research_task = Task(
            description=f"""Based on the analysis, retrieve ALL relevant project data for:
"{user_query}"

Use the available tools to get COMPLETE results.
Return ALL matching projects, not just samples.
Include technology and year for each project.""",
            expected_output="Complete list of all projects matching the query criteria",
            agent=self.researcher,
        )

        synthesis_task = Task(
            description=f"""Create a final professional response to the user:
"{user_query}"

Requirements:
1. Directly answer the question asked
2. Include ALL projects found
3. Format clearly and professionally
4. Make it easy to read and understand""",
            expected_output="Clear, professional answer with complete project information",
            agent=self.synthesizer,
        )

        # Execute the crew
        result = self.crew.kickoff(inputs={
            "task": user_query,
        })

        logger.info(f"{'='*100}")
        logger.info("Query Processing Complete")
        logger.info(f"{'='*100}\n")

        return str(result)

    def close(self):
        """Close database connections"""
        self.db_tools.close()
        logger.info("CrewAI-Ollama system closed")


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    print("\n" + "="*100)
    print("CREWAI WITH OLLAMA - AUTONOMOUS MULTI-AGENT SYSTEM")
    print("="*100)

    try:
        print("\nInitializing CrewAI with Ollama...")
        system = CrewAIOllama()
        print("✅ System initialized!")
        print("   - 3 Autonomous Agents")
        print("   - 5 Database Tools")
        print("   - Ollama LLM Backend")
        print("   - Sequential Multi-Agent Process")

        # Example queries
        queries = [
            "How many HVDC projects do we have?",
            "List all SynCon projects",
            "What projects are in Germany?",
        ]

        for query in queries:
            print(f"\n\nUser Query: {query}")
            print("-"*100)
            response = system.process_query(query)
            print(f"\nResponse:\n{response}")

        system.close()

        print("\n" + "="*100)
        print("✅ CREWAI-OLLAMA SYSTEM COMPLETE")
        print("="*100 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
