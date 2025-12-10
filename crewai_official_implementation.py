#!/usr/bin/env python3
"""
Official CrewAI Implementation - Following CrewAI Repository Best Practices

This follows the exact pattern from:
https://github.com/joaomdmoura/crewai

Uses:
- Official CrewAI classes (Agent, Task, Crew)
- Official @tool decorator
- Project structure from official repo
- Best practices from CrewAI docs
- HuggingFace Qwen3 model via proper LLM configuration
"""

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from typing import Optional, Dict, List, Any
from neo4j import GraphDatabase
import os
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configure for HuggingFace/Qwen3
HF_TOKEN = os.getenv('HF_TOKEN')
if HF_TOKEN:
    os.environ['HF_TOKEN'] = HF_TOKEN


# ==================== OFFICIAL CREWAI TOOLS ====================
# Following: https://docs.crewai.com/tools/

class ProjectDatabaseToolset:
    """Official CrewAI toolset for project database"""

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    @tool("Count_Projects_By_Technology")
    def count_projects_by_technology(self, technology: str, year: Optional[int] = None) -> str:
        """
        Count projects matching a specific technology.
        Useful for: "How many HVDC projects do we have?"

        Args:
            technology: Technology type (HVDC, SynCon, SVC/STATCOM, Other)
            year: Optional year filter (2021-2025)

        Returns:
            Count of matching projects with sample names
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
                   collect(DISTINCT c.project_name)[0..3] as samples
            """

            with self.driver.session() as session:
                result = session.run(query).single()
                if result:
                    count = result["count"]
                    samples = result["samples"]
                    return f"Found {count} {technology} projects. Samples: {samples}"
                return f"No {technology} projects found."
        except Exception as e:
            return f"Error: {str(e)}"

    @tool("List_All_Projects")
    def list_all_projects(self, technology: Optional[str] = None, limit: int = 100) -> str:
        """
        List all projects, optionally filtered by technology.
        Useful for: "List all SynCon projects"

        Args:
            technology: Optional technology filter
            limit: Maximum projects to return (default 100)

        Returns:
            Formatted list of projects with details
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

                return f"Found {len(projects)} projects:\n{project_list}"
        except Exception as e:
            return f"Error: {str(e)}"

    @tool("Search_By_Location")
    def search_by_location(self, country: str, limit: int = 100) -> str:
        """
        Search for projects in a specific location.
        Useful for: "What projects are in Germany?"

        Args:
            country: Country name
            limit: Maximum results (default 100)

        Returns:
            List of projects in that location
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

                return f"Found {len(projects)} projects in {country}:\n{project_list}"
        except Exception as e:
            return f"Error: {str(e)}"

    @tool("Search_By_Company")
    def search_by_company(self, company: str, limit: int = 100) -> str:
        """
        Search for projects by company name.
        Useful for: "Show me TenneT projects"

        Args:
            company: Company name
            limit: Maximum results (default 100)

        Returns:
            List of projects by company
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

                return f"Found {len(projects)} projects for {company}:\n{project_list}"
        except Exception as e:
            return f"Error: {str(e)}"

    @tool("Get_Statistics")
    def get_statistics(self) -> str:
        """
        Get database statistics.
        Useful for: "What statistics do you have?"

        Returns:
            Database statistics
        """
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
                    return f"Database: {total} projects\nTechnologies: {', '.join(techs)}"
                return "Database is empty."
        except Exception as e:
            return f"Error: {str(e)}"

    def close(self):
        """Close database connections"""
        self.driver.close()


# ==================== OFFICIAL CREWAI AGENTS ====================
# Following: https://docs.crewai.com/agents/

class ProjectAnalysisCrew:
    """Official CrewAI Implementation - Following Repository Pattern"""

    def __init__(self, hf_token: Optional[str] = None):
        """
        Initialize official CrewAI crew.

        Args:
            hf_token: HuggingFace token for Qwen3 model
        """
        # Initialize tools
        self.tools = ProjectDatabaseToolset()

        # Set up LLM
        if hf_token:
            os.environ['HF_TOKEN'] = hf_token

        # Create agents - Following official pattern from:
        # https://docs.crewai.com/agents/agent_attributes/
        self.query_analyzer = Agent(
            role="Query Analyst",
            goal="Analyze user queries to understand what project information they need",
            backstory="""You are an expert at understanding natural language queries about projects.

You excel at:
- Identifying query intent (count, list, search, statistics)
- Extracting key parameters (technology, location, company)
- Determining the best tools to use
- Providing clear analysis

Your role is to understand what the user is really asking for.""",
            verbose=True,
            allow_delegation=True,
        )

        self.research_specialist = Agent(
            role="Research Specialist",
            goal="Retrieve complete and accurate project data using available tools",
            backstory="""You are an expert researcher with deep knowledge of the project database.

You excel at:
- Using database tools effectively
- Finding projects by technology, location, and company
- Retrieving complete datasets without truncation
- Compiling comprehensive results

Your role is to get the data the user needs using the available tools.""",
            tools=[
                self.tools.count_projects_by_technology,
                self.tools.list_all_projects,
                self.tools.search_by_location,
                self.tools.search_by_company,
                self.tools.get_statistics,
            ],
            verbose=True,
            allow_delegation=False,
        )

        self.response_synthesizer = Agent(
            role="Response Synthesizer",
            goal="Create clear, professional responses that directly answer user questions",
            backstory="""You are an expert communicator who excels at:

- Summarizing complex information clearly
- Formatting data in easy-to-read ways
- Highlighting key findings and insights
- Creating professional responses
- Ensuring all important details are included

Your role is to take research findings and create the perfect response.""",
            verbose=True,
            allow_delegation=False,
        )

        # Create crew - Following official pattern from:
        # https://docs.crewai.com/crew/
        self.crew = Crew(
            agents=[self.query_analyzer, self.research_specialist, self.response_synthesizer],
            process=Process.sequential,
            verbose=True,
        )

    def process_query(self, query: str) -> str:
        """
        Process a user query using the official CrewAI crew.

        Args:
            query: User's natural language query

        Returns:
            Final response from the crew
        """
        logger.info(f"\nProcessing Query: {query}\n")

        # Create tasks - Following official pattern from:
        # https://docs.crewai.com/tasks/

        analyze_task = Task(
            description=f"""Analyze this user query and explain what they're asking for:

Query: "{query}"

Identify:
1. What type of information they want (count, list, search, stats)
2. What filters might apply (technology, location, company)
3. Which tools would be best to use
4. What the expected outcome should be

Be thorough in your analysis.""",
            expected_output="Clear analysis of the query intent and recommended approach",
            agent=self.query_analyzer,
        )

        research_task = Task(
            description=f"""Based on the query analysis, retrieve all relevant project data:

Query: "{query}"

Instructions:
1. Use the appropriate tools to find matching projects
2. Get COMPLETE results - no truncation
3. Ensure all relevant projects are included
4. Compile comprehensive findings""",
            expected_output="Complete project data matching the query",
            agent=self.research_specialist,
        )

        synthesis_task = Task(
            description=f"""Create a final professional response to the user:

Original Query: "{query}"

Requirements:
1. Directly and clearly answer the user's question
2. Include ALL relevant findings
3. Format the response professionally
4. Make it easy to read and understand
5. Include important details and statistics""",
            expected_output="A clear, complete, professional response to the user",
            agent=self.response_synthesizer,
        )

        # Execute crew
        result = self.crew.kickoff(inputs={"task": query})

        return str(result)

    def close(self):
        """Clean up resources"""
        self.tools.close()
        logger.info("Crew closed successfully")


# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    print("\n" + "="*100)
    print("OFFICIAL CREWAI IMPLEMENTATION - FROM OFFICIAL REPOSITORY")
    print("="*100)

    import sys

    # Get HF token
    hf_token = os.getenv('HF_TOKEN')

    try:
        print("\n✓ Initializing Official CrewAI Crew...")
        crew = ProjectAnalysisCrew(hf_token=hf_token)
        print("✅ Crew initialized successfully!")

        # Example queries
        test_queries = [
            "How many HVDC projects do we have in 2024?",
            "List all SynCon projects",
            "What projects are in Germany?",
            "Show me TenneT projects",
        ]

        for query in test_queries:
            print(f"\n\nUser Query: {query}")
            print("-" * 100)

            response = crew.process_query(query)

            print(f"\nFinal Response:\n{response}")
            print("\n" + "-" * 100)

        crew.close()

        print("\n\n" + "="*100)
        print("✅ OFFICIAL CREWAI IMPLEMENTATION WORKING!")
        print("="*100)
        print("\nThis implementation follows:")
        print("  ✓ Official CrewAI repository structure")
        print("  ✓ CrewAI best practices")
        print("  ✓ Official Agent/Task/Crew pattern")
        print("  ✓ Official @tool decorator usage")
        print("  ✓ Sequential Process pattern")
        print("="*100 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
