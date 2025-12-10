#!/usr/bin/env python3
"""
Agent Discovery Engine - Find and select agents based on query requirements

This module provides intelligent agent discovery by:
- Analyzing query characteristics to determine required capabilities
- Finding agents with matching capabilities
- Scoring and ranking agents by relevance
- Building optimal agent teams for multi-agent execution
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import logging

from crewai_agent_system.utils.query_parser import ParsedQuery, QueryType, DataRequirement
from crewai_agent_system.utils.agent_registry import AgentRegistryManager, AgentInfo

logger = logging.getLogger(__name__)


@dataclass
class AgentSelection:
    """Information about a selected agent for a task"""
    agent_id: str
    agent_name: str
    role: str
    match_score: float  # 0.0-1.0, how well the agent matches the requirement
    required_capabilities: List[str]
    available_capabilities: List[str]
    tools: List[str]
    reasoning: str


class AgentDiscoveryEngine:
    """
    Intelligent agent discovery and selection for query-driven multi-agent systems.

    Capabilities:
    - Find agents that match query requirements
    - Score agents by capability match
    - Build optimal agent teams
    - Handle fallback strategies if no perfect match
    """

    # Capability mappings for different query types
    QUERY_TYPE_CAPABILITIES = {
        QueryType.COUNT: ["aggregation", "metadata_filtering", "semantic_search", "text_search"],
        QueryType.LIST: ["search", "semantic_search", "text_search", "graph_traversal"],
        QueryType.SEARCH: ["semantic_search", "text_search", "graph_traversal"],
        QueryType.COMPARISON: ["aggregation", "search", "nlg"],
        QueryType.STATISTICS: ["aggregation", "semantic_search", "text_search"],
        QueryType.COMPLEX: ["query_planning", "semantic_search", "text_search", "aggregation", "nlg"],
    }

    # Capability requirements based on query classification
    CLASSIFICATION_CAPABILITIES = {
        "quantitative": ["aggregation", "metadata_filtering"],
        "qualitative": ["semantic_search", "text_search", "nlg"],
        "hybrid": ["semantic_search", "text_search", "aggregation", "nlg"],
    }

    # Default workflow agents
    DEFAULT_WORKFLOW = [
        "agent_query_analyst",
        "agent_search_specialist",
        "agent_graph_navigator",
        "agent_analytics_aggregator",
        "agent_response_synthesizer",
    ]

    def __init__(self, registry: AgentRegistryManager):
        """
        Initialize the discovery engine.

        Args:
            registry: AgentRegistryManager instance for accessing agent information
        """
        self.registry = registry
        self._agent_cache = {}
        self._load_agent_cache()

    def _load_agent_cache(self):
        """Load all agents into memory for fast access"""
        agents = self.registry.get_all_agents()
        self._agent_cache = {agent.agent_id: agent for agent in agents}
        logger.info(f"Loaded {len(self._agent_cache)} agents into cache")

    def discover_agents(self, parsed_query: ParsedQuery) -> List[AgentSelection]:
        """
        Discover agents needed to answer the given query.

        Args:
            parsed_query: ParsedQuery object with analysis of the user's query

        Returns:
            List of AgentSelection objects ranked by relevance
        """
        # Determine required capabilities based on query characteristics
        required_capabilities = self._determine_required_capabilities(parsed_query)

        # Find agents that have these capabilities
        matching_agents = self._find_matching_agents(required_capabilities)

        if not matching_agents:
            logger.warning(f"No agents found for capabilities {required_capabilities}, using default team")
            return self._get_default_team(parsed_query)

        # Score and rank agents
        ranked_agents = self._score_agents(matching_agents, required_capabilities)

        return ranked_agents

    def discover_workflow(self, parsed_query: ParsedQuery) -> List[str]:
        """
        Get the optimal agent workflow for executing the query.

        Returns a sequence of agent IDs to execute in order.

        Args:
            parsed_query: ParsedQuery object

        Returns:
            Ordered list of agent IDs to execute
        """
        # For now, use the default workflow which is optimized for most queries
        # In the future, this could be customized based on query characteristics
        workflow = self.registry.get_full_workflow()

        # Verify all agents in workflow are available
        available_agent_ids = set(self._agent_cache.keys())
        workflow = [aid for aid in workflow if aid in available_agent_ids]

        return workflow

    def _determine_required_capabilities(self, parsed_query: ParsedQuery) -> List[str]:
        """
        Determine which capabilities are needed based on the parsed query.

        Args:
            parsed_query: ParsedQuery object

        Returns:
            List of capability IDs required (with cap_ prefix)
        """
        capabilities = set()

        # Add capabilities based on query type
        query_caps = self.QUERY_TYPE_CAPABILITIES.get(parsed_query.query_type, [])
        capabilities.update(query_caps)

        # Add capabilities based on classification
        classification_caps = self.CLASSIFICATION_CAPABILITIES.get(parsed_query.classification.value, [])
        capabilities.update(classification_caps)

        # Add specific capabilities based on query requirements
        if parsed_query.requires_semantic:
            capabilities.add("semantic_search")
        if parsed_query.requires_exact_match:
            capabilities.add("text_search")
        if parsed_query.needs_aggregation:
            capabilities.add("aggregation")

        # For complex queries, ensure query planning capability
        if parsed_query.query_type == QueryType.COMPLEX:
            capabilities.add("query_planning")

        # Normalize capability names to use cap_ prefix to match Neo4j stored IDs
        normalized = set()
        for cap in capabilities:
            if not cap.startswith("cap_"):
                cap = "cap_" + cap
            normalized.add(cap)

        return list(normalized)

    def _find_matching_agents(self, required_capabilities: List[str]) -> List[Tuple[AgentInfo, float]]:
        """
        Find agents that have the required capabilities.

        Args:
            required_capabilities: List of required capability IDs

        Returns:
            List of (AgentInfo, match_score) tuples
        """
        if not required_capabilities:
            # If no specific capabilities required, return all agents
            return [(agent, 1.0) for agent in self._agent_cache.values() if agent.status == "active"]

        matching_agents = []

        for agent in self._agent_cache.values():
            if agent.status != "active":
                continue

            # Count matching capabilities
            agent_caps_set = set(agent.capabilities)
            required_caps_set = set(required_capabilities)
            matching_caps = agent_caps_set & required_caps_set

            if len(matching_caps) > 0:
                # Calculate match score: what percentage of required capabilities does this agent have
                match_score = len(matching_caps) / max(len(required_caps_set), 1)
                matching_agents.append((agent, match_score))

        # If no perfect matches, return all active agents as fallback
        if not matching_agents:
            return [(agent, 0.3) for agent in self._agent_cache.values() if agent.status == "active"]

        return sorted(matching_agents, key=lambda x: x[1], reverse=True)

    def _score_agents(
        self,
        matching_agents: List[Tuple[AgentInfo, float]],
        required_capabilities: List[str]
    ) -> List[AgentSelection]:
        """
        Score and rank agents by how well they match requirements.

        Args:
            matching_agents: List of (AgentInfo, match_score) tuples
            required_capabilities: List of required capability IDs

        Returns:
            List of AgentSelection objects ranked by score
        """
        selections = []

        for agent, match_score in matching_agents:
            # Boost score based on agent performance metrics
            performance_boost = self._get_performance_boost(agent)
            final_score = min(1.0, match_score + performance_boost)

            # Get matched capabilities
            agent_caps_set = set(agent.capabilities)
            required_caps_set = set(required_capabilities)
            matched_caps = list(agent_caps_set & required_caps_set)
            unmatched_caps = list(required_caps_set - agent_caps_set)

            reasoning = f"Agent has {len(matched_caps)}/{len(required_capabilities)} required capabilities. "
            reasoning += f"Performance score: {performance_boost:.2f}. "
            if unmatched_caps:
                reasoning += f"Missing: {', '.join(unmatched_caps)}"

            selection = AgentSelection(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                role=agent.role,
                match_score=final_score,
                required_capabilities=required_capabilities,
                available_capabilities=agent.capabilities,
                tools=agent.tools,
                reasoning=reasoning,
            )
            selections.append(selection)

        return sorted(selections, key=lambda x: x.match_score, reverse=True)

    def _get_performance_boost(self, agent: AgentInfo) -> float:
        """
        Calculate a performance boost based on agent metrics.

        Agents with higher success rates get a small boost.

        Args:
            agent: AgentInfo object

        Returns:
            Float between 0.0 and 0.1 for boost
        """
        if not agent.performance_metrics:
            return 0.05

        success_rate = agent.performance_metrics.get("success_rate", 0.85)
        # Convert success rate (0.0-1.0) to boost (0.0-0.1)
        boost = (success_rate - 0.8) * 0.5  # 0.8 success = 0.0 boost, 1.0 success = 0.1 boost
        return max(0.0, min(0.1, boost))

    def _get_default_team(self, parsed_query: ParsedQuery) -> List[AgentSelection]:
        """
        Get the default agent team when no specific match is found.

        Args:
            parsed_query: ParsedQuery object

        Returns:
            List of AgentSelection objects for the default team
        """
        selections = []

        for agent_id in self.DEFAULT_WORKFLOW:
            agent = self._agent_cache.get(agent_id)
            if not agent:
                continue

            selection = AgentSelection(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                role=agent.role,
                match_score=0.8,  # Lower score since this is fallback
                required_capabilities=[],
                available_capabilities=agent.capabilities,
                tools=agent.tools,
                reasoning="Default team member (no specific capability match)",
            )
            selections.append(selection)

        return selections

    def get_agent_details(self, agent_id: str) -> Optional[AgentInfo]:
        """Get detailed information about a specific agent"""
        return self._agent_cache.get(agent_id)

    def get_all_agents(self) -> List[AgentInfo]:
        """Get all available agents"""
        return list(self._agent_cache.values())

    def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """Get capabilities of a specific agent"""
        agent = self._agent_cache.get(agent_id)
        if agent:
            return agent.capabilities
        return []

    def print_discovery_report(self, parsed_query: ParsedQuery, selections: List[AgentSelection]):
        """Print a human-readable discovery report"""
        print("\n" + "="*80)
        print("AGENT DISCOVERY REPORT")
        print("="*80)
        print(f"\nQuery: {parsed_query.original_query}")
        print(f"Type: {parsed_query.query_type.value}")
        print(f"Classification: {parsed_query.classification.value}")
        print(f"Data Requirement: {parsed_query.data_requirement.value}")

        print("\n" + "-"*80)
        print("SELECTED AGENTS")
        print("-"*80)

        for i, selection in enumerate(selections, 1):
            print(f"\n{i}. {selection.agent_name}")
            print(f"   ID: {selection.agent_id}")
            print(f"   Role: {selection.role}")
            print(f"   Match Score: {selection.match_score:.2%}")
            print(f"   Reasoning: {selection.reasoning}")
            if selection.tools:
                print(f"   Tools: {', '.join(selection.tools[:3])}" +
                      (f" +{len(selection.tools)-3} more" if len(selection.tools) > 3 else ""))

        print("\n" + "="*80)


def get_agent_discovery_engine(registry: AgentRegistryManager) -> AgentDiscoveryEngine:
    """
    Get or create an agent discovery engine.

    Args:
        registry: AgentRegistryManager instance

    Returns:
        AgentDiscoveryEngine instance
    """
    return AgentDiscoveryEngine(registry)


if __name__ == "__main__":
    # Test the agent discovery engine
    from crewai_agent_system.utils.query_parser import IntelligentQueryParser

    parser = IntelligentQueryParser()
    registry = AgentRegistryManager("bolt://localhost:7687", "neo4j", "siemensenergy")
    engine = AgentDiscoveryEngine(registry)

    # Test queries
    test_queries = [
        "How many HVDC projects do we have in 2024?",
        "List all SynCon projects in Germany",
        "What AI and grid-related projects are there?",
        "Give me details about TenneT projects",
    ]

    for query in test_queries:
        print("\n")
        parsed = parser.parse(query)
        selections = engine.discover_agents(parsed)
        engine.print_discovery_report(parsed, selections)

    registry.close()
