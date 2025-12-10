#!/usr/bin/env python3
"""
Integrated Autonomous Agent System with Real Tools

Connects autonomous agents with actual database tools and execution.
"""

import logging
from typing import Dict, Any, Optional

from crewai_agent_system.autonomous_agents import (
    AutonomousAgentSystem,
    Tool,
    Task,
)
from crewai_agent_system.utils.tool_executor import ToolExecutor
from crewai_agent_system.utils.query_parser import IntelligentQueryParser

logger = logging.getLogger(__name__)


class IntegratedAutonomousSystem:
    """
    Complete autonomous agent system with real tools and execution.
    """

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        """
        Initialize the integrated system.

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.tool_executor = ToolExecutor(neo4j_uri, neo4j_user, neo4j_password)
        self.query_parser = IntelligentQueryParser()
        self.agent_system = AutonomousAgentSystem()

        # Create real tools from executor
        self._create_and_register_tools()

    def _create_and_register_tools(self):
        """Create Tool objects from tool executor methods"""
        tools = [
            Tool(
                name="count_projects",
                description="Count projects matching specific filters (technology, year, etc.)",
                func=lambda filters: self.tool_executor.tool_neo4j_count(filters)
            ),
            Tool(
                name="list_projects",
                description="List all projects matching specified filters with full details",
                func=lambda filters, limit=500: self.tool_executor.tool_neo4j_list_all(filters, limit)
            ),
            Tool(
                name="search_by_location",
                description="Search for projects in a specific location/country",
                func=lambda location: self.tool_executor.tool_text_search(location, field="text")
            ),
            Tool(
                name="search_by_company",
                description="Search for projects associated with a specific company",
                func=lambda company: self.tool_executor.tool_text_search(company, field="text")
            ),
            Tool(
                name="semantic_search",
                description="Semantically search for projects based on concepts and meanings",
                func=lambda query, top_k=50: self.tool_executor.tool_vector_search(query, top_k)
            ),
            Tool(
                name="entity_search",
                description="Search for entities and find related projects",
                func=lambda entity: self.tool_executor.tool_entity_search(entity)
            ),
        ]

        self.agent_system.register_tools(tools)
        logger.info(f"Registered {len(tools)} tools with agent system")

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using autonomous agents and real tools.

        Args:
            query: User's natural language query

        Returns:
            Complete result with analysis, research, and response
        """
        logger.info(f"\n{'='*100}")
        logger.info(f"INTEGRATED AUTONOMOUS SYSTEM - Processing Query")
        logger.info(f"{'='*100}")
        logger.info(f"Query: {query}\n")

        # Step 1: Parse the query
        parsed_query = self.query_parser.parse(query)
        logger.info(f"Query Analysis:")
        logger.info(f"  Type: {parsed_query.query_type.value}")
        logger.info(f"  Classification: {parsed_query.classification.value}")
        if parsed_query.technologies:
            logger.info(f"  Technologies: {parsed_query.technologies}")
        if parsed_query.countries:
            logger.info(f"  Countries: {parsed_query.countries}")
        if parsed_query.companies:
            logger.info(f"  Companies: {parsed_query.companies}")

        # Step 2: Use autonomous agents to process
        agent_results = self.agent_system.process_query(query)

        # Step 3: Execute actual tools based on parsed query
        tool_results = self.tool_executor.execute_tools_for_query(parsed_query)

        logger.info(f"\nTool Execution Results:")
        logger.info(f"  Total projects found: {tool_results.get('total_count', 0)}")
        logger.info(f"  Execution steps: {len(tool_results.get('execution_steps', []))}")

        # Step 4: Combine results
        final_result = {
            "original_query": query,
            "parsed_query": {
                "type": parsed_query.query_type.value,
                "classification": parsed_query.classification.value,
                "technologies": parsed_query.technologies,
                "countries": parsed_query.countries,
                "companies": parsed_query.companies,
            },
            "agent_analysis": agent_results["analysis"],
            "agent_research": agent_results["research"],
            "agent_synthesis": agent_results["response"],
            "tool_results": {
                "total_count": tool_results.get("total_count", 0),
                "projects": tool_results.get("projects", []),
                "execution_steps": tool_results.get("execution_steps", []),
            },
            "agents_involved": list(self.agent_system.agents.keys()),
            "tools_available": len(self.agent_system.agents["researcher"].tools),
        }

        logger.info(f"\n{'='*100}")
        logger.info("Query Processing Complete")
        logger.info(f"{'='*100}\n")

        return final_result

    def count_projects(self, technology: str, year: Optional[int] = None) -> Dict[str, Any]:
        """Count projects by technology and optional year"""
        filters = {"technology": technology}
        if year:
            filters["year"] = year

        query = f"How many {technology} projects do we have?"
        if year:
            query += f" in {year}?"

        return self.process_query(query)

    def list_projects(self, **criteria) -> Dict[str, Any]:
        """List projects with specified criteria"""
        if "technology" in criteria:
            query = f"List all {criteria['technology']} projects"
        elif "country" in criteria:
            query = f"List all projects in {criteria['country']}"
        elif "company" in criteria:
            query = f"Show me {criteria['company']} projects"
        else:
            query = "List projects"

        return self.process_query(query)

    def search_projects(self, search_term: str) -> Dict[str, Any]:
        """Search for projects by keyword"""
        query = f"Search for projects related to {search_term}"
        return self.process_query(query)

    def get_system_info(self) -> str:
        """Get information about the system"""
        info = self.agent_system.get_agent_info()
        stats = self.agent_system.get_system_stats()
        info += f"\nSystem Statistics:\n"
        info += f"  Queries Processed: {stats['queries_processed']}\n"
        info += f"  Total Tools Available: {stats['total_tools']}\n"
        return info

    def close(self):
        """Close all connections"""
        self.tool_executor.close()
        logger.info("System closed")


if __name__ == "__main__":
    print("\n" + "="*100)
    print("INTEGRATED AUTONOMOUS AGENT SYSTEM - WITH REAL TOOLS AND DATABASE")
    print("="*100)

    system = IntegratedAutonomousSystem()

    # Show system info
    print(system.get_system_info())

    # Test queries
    test_queries = [
        "How many HVDC projects do we have in 2024?",
        "List all SynCon projects",
        "Show me TenneT projects",
    ]

    for query in test_queries:
        print(f"\n\n{'='*100}")
        print(f"Query: {query}")
        print('='*100)

        result = system.process_query(query)

        print(f"\nResults Summary:")
        print(f"  Projects Found: {result['tool_results']['total_count']}")
        print(f"  Agents Used: {len(result['agents_involved'])}")
        print(f"  Tools Available: {result['tools_available']}")

    system.close()
    print("\n" + "="*100)
