#!/usr/bin/env python3
"""
Agent Registry Manager - Manages agents, tools, and capabilities in Neo4j

This module provides:
- Agent registration and lifecycle management
- Capability-based agent discovery
- Tool recommendation based on query requirements
- Workflow/execution chain generation
- Performance metrics tracking
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentInfo:
    """Information about an agent"""
    agent_id: str
    name: str
    role: str
    description: str
    status: str
    capabilities: List[str]
    tools: List[str]
    performance_metrics: Dict[str, Any]


@dataclass
class ToolInfo:
    """Information about a tool"""
    tool_id: str
    name: str
    tool_type: str
    description: str
    input_format: Dict[str, str]
    output_format: Dict[str, str]
    cost_estimate: float
    latency_ms: int
    success_rate: float


@dataclass
class CapabilityInfo:
    """Information about a capability"""
    capability_id: str
    name: str
    category: str
    description: str
    complexity_level: str
    prerequisites: List[str]


class AgentRegistryManager:
    """
    Manages the Agent-as-Graph registry in Neo4j.

    Provides methods for:
    - Agent discovery based on required capabilities
    - Tool selection based on query characteristics
    - Workflow generation based on dependencies
    - Performance metrics tracking
    """

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """
        Initialize the registry manager.

        Args:
            neo4j_uri: Neo4j connection URI (e.g., "bolt://localhost:7687")
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self._agent_cache = {}
        self._tool_cache = {}
        self._capability_cache = {}
        self._verify_schema()

    def _verify_schema(self):
        """Verify that the agent graph schema exists"""
        with self.driver.session() as session:
            try:
                result = session.run("MATCH (a:AGENT) RETURN count(a) as count")
                count = result.single()["count"]
                logger.info(f"Agent registry verified: {count} agents found")
            except Exception as e:
                logger.warning(f"Agent registry schema may not be initialized: {e}")

    def close(self):
        """Close database connection"""
        self.driver.close()

    # ==================== AGENT QUERIES ====================

    def get_all_agents(self) -> List[AgentInfo]:
        """Get all agents in the registry"""
        with self.driver.session() as session:
            query = """
            MATCH (a:AGENT)
            OPTIONAL MATCH (a)-[:HAS_CAPABILITY]->(c:CAPABILITY)
            OPTIONAL MATCH (a)-[:USES]->(t:TOOL)
            WITH a, collect(DISTINCT c.id) as capabilities, collect(DISTINCT t.id) as tools
            RETURN a.id as agent_id, a.name as name, a.role as role,
                   a.description as description, a.status as status,
                   capabilities, tools, a.performance_metrics as metrics
            """
            results = session.run(query)
            agents = []
            for record in results:
                agents.append(AgentInfo(
                    agent_id=record["agent_id"],
                    name=record["name"],
                    role=record["role"],
                    description=record["description"],
                    status=record["status"],
                    capabilities=record["capabilities"],
                    tools=record["tools"],
                    performance_metrics=record["metrics"] or {}
                ))
            return agents

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get details of a specific agent"""
        with self.driver.session() as session:
            query = """
            MATCH (a:AGENT {id: $agent_id})
            OPTIONAL MATCH (a)-[:HAS_CAPABILITY]->(c:CAPABILITY)
            OPTIONAL MATCH (a)-[:USES]->(t:TOOL)
            WITH a, collect(DISTINCT c.id) as capabilities, collect(DISTINCT t.id) as tools
            RETURN a.id as agent_id, a.name as name, a.role as role,
                   a.description as description, a.status as status,
                   capabilities, tools, a.performance_metrics as metrics
            """
            result = session.run(query, agent_id=agent_id).single()
            if not result:
                return None

            return AgentInfo(
                agent_id=result["agent_id"],
                name=result["name"],
                role=result["role"],
                description=result["description"],
                status=result["status"],
                capabilities=result["capabilities"],
                tools=result["tools"],
                performance_metrics=result["metrics"] or {}
            )

    def find_agents_for_task(self, required_capabilities: List[str]) -> List[Tuple[AgentInfo, float]]:
        """
        Find agents that have the required capabilities.

        Args:
            required_capabilities: List of capability IDs needed

        Returns:
            List of (AgentInfo, match_score) tuples sorted by match score
        """
        with self.driver.session() as session:
            # Find agents with matching capabilities
            query = """
            MATCH (a:AGENT)
            OPTIONAL MATCH (a)-[:HAS_CAPABILITY]->(c:CAPABILITY)
            WHERE c.id IN $required_caps OR $required_caps = []
            WITH a, count(DISTINCT c) as capability_count
            OPTIONAL MATCH (a)-[:USES]->(t:TOOL)
            WITH a, capability_count, collect(DISTINCT t.id) as tools
            OPTIONAL MATCH (a)-[:HAS_CAPABILITY]->(c2:CAPABILITY)
            WITH a, capability_count, tools, collect(DISTINCT c2.id) as all_capabilities
            WHERE capability_count > 0 OR size($required_caps) = 0
            RETURN a.id as agent_id, a.name as name, a.role as role,
                   a.description as description, a.status as status,
                   all_capabilities as capabilities, tools,
                   capability_count as matching_capabilities,
                   a.performance_metrics as metrics
            ORDER BY matching_capabilities DESC
            """

            results = session.run(query, required_caps=required_capabilities)

            agents_with_scores = []
            for record in results:
                matching = record["matching_capabilities"]
                total = len(record["capabilities"])
                match_score = matching / max(total, 1) if total > 0 else 0.0

                agent = AgentInfo(
                    agent_id=record["agent_id"],
                    name=record["name"],
                    role=record["role"],
                    description=record["description"],
                    status=record["status"],
                    capabilities=record["capabilities"],
                    tools=record["tools"],
                    performance_metrics=record["metrics"] or {}
                )
                agents_with_scores.append((agent, match_score))

            return agents_with_scores

    # ==================== TOOL QUERIES ====================

    def get_all_tools(self) -> List[ToolInfo]:
        """Get all available tools"""
        with self.driver.session() as session:
            query = """
            MATCH (t:TOOL)
            RETURN t.id as tool_id, t.name as name, t.type as tool_type,
                   t.description as description, t.input_format as input_format,
                   t.output_format as output_format, t.cost_estimate as cost,
                   t.latency_ms as latency, t.success_rate as success_rate
            ORDER BY t.name
            """
            results = session.run(query)
            tools = []
            for record in results:
                tools.append(ToolInfo(
                    tool_id=record["tool_id"],
                    name=record["name"],
                    tool_type=record["tool_type"],
                    description=record["description"],
                    input_format=record["input_format"] or {},
                    output_format=record["output_format"] or {},
                    cost_estimate=record["cost"] or 0.1,
                    latency_ms=record["latency"] or 1000,
                    success_rate=record["success_rate"] or 0.9
                ))
            return tools

    def get_tools_for_capability(self, capability_id: str) -> List[ToolInfo]:
        """Get all tools that implement a specific capability"""
        with self.driver.session() as session:
            query = """
            MATCH (c:CAPABILITY {id: $capability_id})<-[:REQUIRES]-(t:TOOL)
            RETURN t.id as tool_id, t.name as name, t.type as tool_type,
                   t.description as description, t.input_format as input_format,
                   t.output_format as output_format, t.cost_estimate as cost,
                   t.latency_ms as latency, t.success_rate as success_rate
            ORDER BY t.success_rate DESC
            """
            results = session.run(query, capability_id=capability_id)
            tools = []
            for record in results:
                tools.append(ToolInfo(
                    tool_id=record["tool_id"],
                    name=record["name"],
                    tool_type=record["tool_type"],
                    description=record["description"],
                    input_format=record["input_format"] or {},
                    output_format=record["output_format"] or {},
                    cost_estimate=record["cost"] or 0.1,
                    latency_ms=record["latency"] or 1000,
                    success_rate=record["success_rate"] or 0.9
                ))
            return tools

    # ==================== CAPABILITY QUERIES ====================

    def get_all_capabilities(self) -> List[CapabilityInfo]:
        """Get all capabilities in the registry"""
        with self.driver.session() as session:
            query = """
            MATCH (c:CAPABILITY)
            RETURN c.id as capability_id, c.name as name, c.category as category,
                   c.description as description, c.complexity_level as complexity,
                   c.prerequisites as prerequisites
            ORDER BY c.name
            """
            results = session.run(query)
            capabilities = []
            for record in results:
                capabilities.append(CapabilityInfo(
                    capability_id=record["capability_id"],
                    name=record["name"],
                    category=record["category"],
                    description=record["description"],
                    complexity_level=record["complexity"],
                    prerequisites=record["prerequisites"] or []
                ))
            return capabilities

    def get_capability(self, capability_id: str) -> Optional[CapabilityInfo]:
        """Get details of a specific capability"""
        with self.driver.session() as session:
            query = """
            MATCH (c:CAPABILITY {id: $capability_id})
            RETURN c.id as capability_id, c.name as name, c.category as category,
                   c.description as description, c.complexity_level as complexity,
                   c.prerequisites as prerequisites
            """
            result = session.run(query, capability_id=capability_id).single()
            if not result:
                return None

            return CapabilityInfo(
                capability_id=result["capability_id"],
                name=result["name"],
                category=result["category"],
                description=result["description"],
                complexity_level=result["complexity"],
                prerequisites=result["prerequisites"] or []
            )

    # ==================== WORKFLOW GENERATION ====================

    def get_agent_workflow(self, start_agent_id: str) -> List[str]:
        """
        Get the workflow execution chain starting from an agent.

        Follows DEPENDS_ON relationships to determine execution order.

        Args:
            start_agent_id: ID of the starting agent

        Returns:
            Ordered list of agent IDs to execute
        """
        with self.driver.session() as session:
            # Find all agents that depend on the starting agent (transitively)
            query = """
            MATCH path = (a:AGENT {id: $start_agent_id})<-[:DEPENDS_ON*]-(other:AGENT)
            WITH other, length(path) as depth
            RETURN other.id as agent_id
            ORDER BY depth
            UNION
            MATCH (a:AGENT {id: $start_agent_id})
            RETURN a.id as agent_id
            """
            results = session.run(query, start_agent_id=start_agent_id)
            workflow = [record["agent_id"] for record in results]
            return workflow

    def get_full_workflow(self) -> List[str]:
        """
        Get the default full multi-agent workflow.

        Returns the workflow order for processing a query with all agents.
        """
        workflow = [
            "agent_query_analyst",      # Step 1: Understand query
            "agent_search_specialist",   # Step 2: Execute search
            "agent_graph_navigator",     # Step 3: Enrich with graph (can run in parallel)
            "agent_analytics_aggregator", # Step 4: Aggregate results
            "agent_response_synthesizer", # Step 5: Generate answer
        ]
        return workflow

    # ==================== PERFORMANCE TRACKING ====================

    def update_agent_metrics(self, agent_id: str, success: bool, latency_ms: int):
        """
        Update agent performance metrics after execution.

        Args:
            agent_id: ID of the agent
            success: Whether execution was successful
            latency_ms: Execution time in milliseconds
        """
        with self.driver.session() as session:
            query = """
            MATCH (a:AGENT {id: $agent_id})
            SET a.performance_metrics = {
                success_rate: CASE
                    WHEN a.performance_metrics IS NULL THEN (CASE WHEN $success THEN 1.0 ELSE 0.0 END)
                    ELSE (a.performance_metrics.success_rate * a.performance_metrics.total_queries + (CASE WHEN $success THEN 1 ELSE 0 END)) / (a.performance_metrics.total_queries + 1)
                END,
                avg_latency_ms: CASE
                    WHEN a.performance_metrics IS NULL THEN $latency
                    ELSE (a.performance_metrics.avg_latency_ms * a.performance_metrics.total_queries + $latency) / (a.performance_metrics.total_queries + 1)
                END,
                total_queries: CASE
                    WHEN a.performance_metrics IS NULL THEN 1
                    ELSE a.performance_metrics.total_queries + 1
                END,
                last_updated: datetime()
            }
            RETURN a.id, a.performance_metrics
            """
            session.run(query, agent_id=agent_id, success=success, latency=latency_ms)

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get overall agent registry statistics"""
        with self.driver.session() as session:
            stats = {}

            # Count nodes
            for label in ["AGENT", "TOOL", "CAPABILITY"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count").single()
                stats[f"{label.lower()}_count"] = result["count"]

            # Count relationships
            for rel_type in ["USES", "HAS_CAPABILITY", "REQUIRES", "DEPENDS_ON"]:
                result = session.run(f"MATCH ()-[r:{rel_type}]-() RETURN count(r) as count").single()
                stats[f"{rel_type.lower()}_count"] = result["count"]

            return stats


def get_agent_registry(neo4j_uri: str = "bolt://localhost:7687",
                      neo4j_user: str = "neo4j",
                      neo4j_password: str = "siemensenergy") -> AgentRegistryManager:
    """
    Get or create a singleton agent registry manager.

    Args:
        neo4j_uri: Neo4j connection URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password

    Returns:
        AgentRegistryManager instance
    """
    return AgentRegistryManager(neo4j_uri, neo4j_user, neo4j_password)


if __name__ == "__main__":
    # Test the registry manager
    registry = get_agent_registry()

    print("\n" + "="*80)
    print("AGENT REGISTRY MANAGER - TEST")
    print("="*80)

    # Get registry stats
    stats = registry.get_agent_stats()
    print("\nRegistry Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # List all agents
    print("\n" + "-"*80)
    print("Available Agents:")
    print("-"*80)
    agents = registry.get_all_agents()
    for agent in agents:
        print(f"\n  {agent.name} (ID: {agent.agent_id})")
        print(f"    Role: {agent.role}")
        print(f"    Status: {agent.status}")
        print(f"    Capabilities: {', '.join(agent.capabilities) if agent.capabilities else 'None'}")
        print(f"    Tools: {len(agent.tools)} tools")

    # List all capabilities
    print("\n" + "-"*80)
    print("Available Capabilities:")
    print("-"*80)
    capabilities = registry.get_all_capabilities()
    for cap in capabilities[:5]:  # Show first 5
        print(f"\n  {cap.name} (ID: {cap.capability_id})")
        print(f"    Category: {cap.category}")
        print(f"    Complexity: {cap.complexity_level}")

    # Get workflow
    print("\n" + "-"*80)
    print("Default Workflow:")
    print("-"*80)
    workflow = registry.get_full_workflow()
    for i, agent_id in enumerate(workflow, 1):
        agent = registry.get_agent(agent_id)
        if agent:
            print(f"  {i}. {agent.name}")

    registry.close()
    print("\n" + "="*80 + "\n")
