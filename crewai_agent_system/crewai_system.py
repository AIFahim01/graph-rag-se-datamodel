#!/usr/bin/env python3
"""
CrewAI System Integration - Main entry point for using the CrewAI agent system

Combines query parser, agent discovery, orchestration, and response formatting
into a single cohesive system for processing natural language queries.
"""

from typing import Dict, Any, Optional, List
import logging

from crewai_agent_system.utils.query_parser import IntelligentQueryParser
from crewai_agent_system.utils.agent_registry import get_agent_registry
from crewai_agent_system.utils.agent_discovery import AgentDiscoveryEngine
from crewai_agent_system.utils.agent_orchestrator import AgentOrchestrator
from crewai_agent_system.utils.response_formatter import IntelligentResponseFormatter
from crewai_agent_system.utils.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


class CrewAIQuerySystem:
    """
    Complete CrewAI-based query processing system.

    Integrates all components for end-to-end query understanding and response generation.
    """

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        """
        Initialize the CrewAI system.

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.parser = IntelligentQueryParser()
        self.registry = get_agent_registry(neo4j_uri, neo4j_user, neo4j_password)
        self.discovery = AgentDiscoveryEngine(self.registry)
        self.orchestrator = AgentOrchestrator(self.registry, self.discovery)
        self.formatter = IntelligentResponseFormatter()
        self.tool_executor = ToolExecutor(neo4j_uri, neo4j_user, neo4j_password)
        logger.info("CrewAI Query System initialized")

    def process_query(self, query: str, confidence_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Process a natural language query end-to-end.

        Args:
            query: User's natural language query
            confidence_threshold: Minimum confidence for responses

        Returns:
            Dictionary with parsed query, execution plan, and formatted response
        """
        # Step 1: Parse the query
        parsed_query = self.parser.parse(query)
        logger.info(f"Parsed query: type={parsed_query.query_type.value}, "
                   f"classification={parsed_query.classification.value}")

        # Step 2: Create execution plan
        execution_plan = self.orchestrator.create_execution_plan(parsed_query)
        logger.info(f"Created execution plan with {len(execution_plan.steps)} steps")

        # Step 3: Discover best agents for this query
        agent_selections = self.discovery.discover_agents(parsed_query)
        logger.info(f"Discovered {len(agent_selections)} agents")

        # Step 4: Execute tools to get real data
        tool_results = self.tool_executor.execute_tools_for_query(parsed_query)
        logger.info(f"Tool execution completed: {len(tool_results.get('projects', []))} projects found")

        # Step 5: Prepare response data with real results
        # Build breakdown from tool results or generated from projects
        breakdown = tool_results.get("breakdown", {})
        if not breakdown and tool_results.get("projects"):
            breakdown = self._generate_breakdown(tool_results.get("projects", []))

        response_data = {
            "total_count": tool_results.get("total_count", 0),
            "projects": tool_results.get("projects", []),
            "breakdown": breakdown,
            "query_type": parsed_query.query_type.value,
            "technologies": parsed_query.technologies,
            "countries": parsed_query.countries,
            "companies": parsed_query.companies,
            "keywords": parsed_query.keywords,
            "agents_selected": [
                {
                    "name": sel.agent_name,
                    "role": sel.role,
                    "match_score": sel.match_score
                }
                for sel in agent_selections[:3]
            ],
            "execution_steps": tool_results.get("execution_steps", [])
        }

        # Only include statistics for statistics queries
        if parsed_query.query_type.value == "statistics":
            response_data["statistics"] = tool_results.get("statistics", {})

        # Step 6: Format the response with real data
        formatted_response = self.formatter.format_response(
            parsed_query,
            response_data,
            confidence=min(1.0, sum(sel.match_score for sel in agent_selections[:3]) / 3)
        )

        return {
            "query": query,
            "parsed_query": {
                "type": parsed_query.query_type.value,
                "classification": parsed_query.classification.value,
                "technologies": parsed_query.technologies,
                "countries": parsed_query.countries,
                "companies": parsed_query.companies,
            },
            "execution_plan": {
                "total_steps": len(execution_plan.steps),
                "agents": [
                    {
                        "agent_id": step.agent_id,
                        "agent_name": step.agent_name,
                        "role": step.role,
                        "capabilities": step.capabilities
                    }
                    for step in execution_plan.steps
                ]
            },
            "agent_selections": [
                {
                    "name": sel.agent_name,
                    "role": sel.role,
                    "match_score": f"{sel.match_score:.0%}",
                    "reasoning": sel.reasoning
                }
                for sel in agent_selections[:3]
            ],
            "response": {
                "answer": formatted_response.answer,
                "answer_type": formatted_response.answer_type,
                "confidence": formatted_response.confidence,
                "citations": formatted_response.citations,
            }
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """Get statistics about the CrewAI system"""
        registry_stats = self.registry.get_agent_stats()
        agents = self.registry.get_all_agents()

        return {
            "agents": {
                "total": registry_stats.get("agent_count", 0),
                "active": sum(1 for a in agents if a.status == "active"),
            },
            "tools": registry_stats.get("tool_count", 0),
            "capabilities": registry_stats.get("capability_count", 0),
            "relationships": {
                "uses": registry_stats.get("uses_count", 0),
                "has_capability": registry_stats.get("has_capability_count", 0),
                "requires": registry_stats.get("requires_count", 0),
                "depends_on": registry_stats.get("depends_on_count", 0),
            }
        }

    def _generate_breakdown(self, projects: List[Dict]) -> Dict[str, Any]:
        """Generate breakdown statistics from projects"""
        breakdown = {
            "by_technology": {},
            "by_year": {}
        }

        for project in projects:
            tech = project.get("technology", "Unknown")
            year = project.get("year", "Unknown")

            breakdown["by_technology"][tech] = breakdown["by_technology"].get(tech, 0) + 1
            breakdown["by_year"][str(year)] = breakdown["by_year"].get(str(year), 0) + 1

        return breakdown

    def close(self):
        """Close database connections"""
        self.registry.close()
        self.tool_executor.close()


def get_crewai_system() -> CrewAIQuerySystem:
    """Get or create a singleton CrewAI system"""
    return CrewAIQuerySystem()


if __name__ == "__main__":
    # Test the system
    system = get_crewai_system()

    # Test query
    query = "How many HVDC projects do we have in 2024?"
    print(f"\nProcessing query: {query}")
    print("="*80)

    result = system.process_query(query)

    print(f"\nParsed Query Type: {result['parsed_query']['type']}")
    print(f"Execution Plan: {result['execution_plan']['total_steps']} steps")
    print(f"Top Agent: {result['agent_selections'][0]['name'] if result['agent_selections'] else 'N/A'}")
    print(f"\nResponse:\n{result['response']['answer']}")

    # Print system stats
    stats = system.get_system_stats()
    print(f"\n\nSystem Statistics:")
    print(f"  Agents: {stats['agents']['active']}/{stats['agents']['total']} active")
    print(f"  Tools: {stats['tools']}")
    print(f"  Capabilities: {stats['capabilities']}")

    system.close()
