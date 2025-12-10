#!/usr/bin/env python3
"""
Agent Orchestrator - Coordinates multi-agent execution for query processing

This module provides orchestration by:
- Discovering agents needed for a query
- Building execution plans
- Managing agent communication
- Coordinating tool execution
- Handling errors and fallbacks
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from datetime import datetime

from crewai_agent_system.utils.query_parser import ParsedQuery
from crewai_agent_system.utils.agent_discovery import AgentDiscoveryEngine, AgentSelection
from crewai_agent_system.utils.agent_registry import AgentRegistryManager

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of execution step"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    """A single step in the execution plan"""
    step_id: int
    agent_id: str
    agent_name: str
    role: str
    capabilities: List[str]
    tools: List[str]
    status: ExecutionStatus = ExecutionStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def duration_ms(self) -> Optional[int]:
        """Get execution duration in milliseconds"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None


@dataclass
class ExecutionPlan:
    """Complete execution plan for processing a query"""
    query: str
    query_type: str
    classification: str
    steps: List[ExecutionStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def add_step(self, agent_id: str, agent_name: str, role: str,
                 capabilities: List[str], tools: List[str]) -> ExecutionStep:
        """Add a step to the execution plan"""
        step = ExecutionStep(
            step_id=len(self.steps),
            agent_id=agent_id,
            agent_name=agent_name,
            role=role,
            capabilities=capabilities,
            tools=tools
        )
        self.steps.append(step)
        return step

    def get_step(self, step_id: int) -> Optional[ExecutionStep]:
        """Get a specific step"""
        if 0 <= step_id < len(self.steps):
            return self.steps[step_id]
        return None

    def status(self) -> str:
        """Get overall execution status"""
        if not self.steps:
            return "empty"
        if self.completed_at:
            return "completed"
        if self.started_at:
            return "running"
        return "pending"

    def success_count(self) -> int:
        """Count successful steps"""
        return sum(1 for step in self.steps if step.status == ExecutionStatus.SUCCESS)

    def failure_count(self) -> int:
        """Count failed steps"""
        return sum(1 for step in self.steps if step.status == ExecutionStatus.FAILED)

    def total_duration_ms(self) -> Optional[int]:
        """Get total execution duration"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None


class AgentOrchestrator:
    """
    Orchestrates multi-agent execution for query processing.

    Coordinates agent discovery, execution planning, and tool calling.
    """

    def __init__(self, registry: AgentRegistryManager, discovery_engine: AgentDiscoveryEngine):
        """
        Initialize the orchestrator.

        Args:
            registry: AgentRegistryManager for agent information
            discovery_engine: AgentDiscoveryEngine for discovering agents
        """
        self.registry = registry
        self.discovery_engine = discovery_engine
        self.execution_plans: Dict[str, ExecutionPlan] = {}

    def create_execution_plan(self, parsed_query: ParsedQuery) -> ExecutionPlan:
        """
        Create an execution plan for a parsed query.

        Args:
            parsed_query: ParsedQuery object with query analysis

        Returns:
            ExecutionPlan with ordered steps
        """
        # Create the plan
        plan = ExecutionPlan(
            query=parsed_query.original_query,
            query_type=parsed_query.query_type.value,
            classification=parsed_query.classification.value
        )

        # Get the optimal workflow for this query
        workflow = self.discovery_engine.discover_workflow(parsed_query)

        # Add steps to the plan
        for agent_id in workflow:
            agent = self.registry.get_agent(agent_id)
            if agent and agent.status == "active":
                plan.add_step(
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    role=agent.role,
                    capabilities=agent.capabilities,
                    tools=agent.tools
                )

        # Store plan
        plan_id = f"plan_{int(plan.created_at.timestamp())}"
        self.execution_plans[plan_id] = plan

        return plan

    def build_agent_team(self, parsed_query: ParsedQuery) -> List[AgentSelection]:
        """
        Build an optimized team of agents for the query.

        Args:
            parsed_query: ParsedQuery object

        Returns:
            List of selected agents ranked by relevance
        """
        # Discover agents for the query
        selections = self.discovery_engine.discover_agents(parsed_query)

        # Filter to top matching agents
        top_agents = selections[:3]  # Use top 3 agents

        return top_agents

    def get_agent_responsibilities(self, agent_id: str) -> Dict[str, Any]:
        """
        Get the responsibilities and tools for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Dictionary with agent info and responsibilities
        """
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return {}

        # Get tools information
        tools_info = []
        for tool_id in agent.tools:
            # In a real system, would look up tool details from registry
            tools_info.append({
                "tool_id": tool_id,
                "agent_id": agent_id
            })

        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "role": agent.role,
            "description": agent.description,
            "status": agent.status,
            "capabilities": agent.capabilities,
            "tools": tools_info,
            "performance_metrics": agent.performance_metrics
        }

    def get_execution_summary(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Get a summary of the execution plan.

        Args:
            plan: ExecutionPlan object

        Returns:
            Dictionary with plan summary
        """
        return {
            "query": plan.query,
            "query_type": plan.query_type,
            "classification": plan.classification,
            "status": plan.status(),
            "total_steps": len(plan.steps),
            "successful_steps": plan.success_count(),
            "failed_steps": plan.failure_count(),
            "duration_ms": plan.total_duration_ms(),
            "created_at": plan.created_at.isoformat(),
            "started_at": plan.started_at.isoformat() if plan.started_at else None,
            "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
            "steps": [
                {
                    "step_id": step.step_id,
                    "agent_name": step.agent_name,
                    "agent_role": step.role,
                    "status": step.status.value,
                    "duration_ms": step.duration_ms(),
                    "error": step.error
                }
                for step in plan.steps
            ]
        }

    def print_execution_plan(self, plan: ExecutionPlan):
        """Print a human-readable execution plan"""
        print("\n" + "="*80)
        print("EXECUTION PLAN")
        print("="*80)
        print(f"\nQuery: {plan.query}")
        print(f"Type: {plan.query_type} | Classification: {plan.classification}")

        print("\n" + "-"*80)
        print("EXECUTION STEPS")
        print("-"*80)

        for step in plan.steps:
            status_icon = {
                ExecutionStatus.PENDING: "⏳",
                ExecutionStatus.RUNNING: "⚙️",
                ExecutionStatus.SUCCESS: "✅",
                ExecutionStatus.FAILED: "❌",
                ExecutionStatus.SKIPPED: "⊘",
            }.get(step.status, "?")

            print(f"\n{status_icon} Step {step.step_id + 1}: {step.agent_name}")
            print(f"   Role: {step.role}")
            if step.capabilities:
                print(f"   Capabilities: {', '.join(step.capabilities[:2])}")
            if step.duration_ms():
                print(f"   Duration: {step.duration_ms()}ms")
            if step.error:
                print(f"   Error: {step.error}")

        print("\n" + "="*80)

    def get_tool_execution_order(self, plan: ExecutionPlan) -> List[Dict[str, Any]]:
        """
        Get the order of tool execution across all agents.

        Args:
            plan: ExecutionPlan

        Returns:
            List of tools to execute in order
        """
        tool_order = []
        for step in plan.steps:
            for tool_id in step.tools:
                tool_order.append({
                    "tool_id": tool_id,
                    "agent_id": step.agent_id,
                    "agent_name": step.agent_name,
                    "step_id": step.step_id
                })
        return tool_order

    def print_agent_team(self, selections: List[AgentSelection]):
        """Print the selected agent team"""
        print("\n" + "="*80)
        print("SELECTED AGENT TEAM")
        print("="*80)

        for i, selection in enumerate(selections, 1):
            print(f"\n{i}. {selection.agent_name}")
            print(f"   ID: {selection.agent_id}")
            print(f"   Role: {selection.role}")
            print(f"   Match Score: {selection.match_score:.0%}")
            print(f"   Capabilities: {', '.join(selection.available_capabilities)}")
            if selection.tools:
                print(f"   Tools: {', '.join(selection.tools[:3])}" +
                      (f" +{len(selection.tools)-3}" if len(selection.tools) > 3 else ""))
            if selection.reasoning:
                print(f"   Reasoning: {selection.reasoning}")

        print("\n" + "="*80)


def get_agent_orchestrator(registry: AgentRegistryManager,
                          discovery_engine: AgentDiscoveryEngine) -> AgentOrchestrator:
    """
    Get or create an agent orchestrator.

    Args:
        registry: AgentRegistryManager instance
        discovery_engine: AgentDiscoveryEngine instance

    Returns:
        AgentOrchestrator instance
    """
    return AgentOrchestrator(registry, discovery_engine)


if __name__ == "__main__":
    # Test the orchestrator
    from crewai_agent_system.utils.query_parser import IntelligentQueryParser

    parser = IntelligentQueryParser()
    registry = AgentRegistryManager("bolt://localhost:7687", "neo4j", "siemensenergy")
    discovery = AgentDiscoveryEngine(registry)
    orchestrator = AgentOrchestrator(registry, discovery)

    # Test query
    query = "How many HVDC projects do we have in 2024?"
    parsed = parser.parse(query)

    # Create execution plan
    plan = orchestrator.create_execution_plan(parsed)
    orchestrator.print_execution_plan(plan)

    # Build agent team
    team = orchestrator.build_agent_team(parsed)
    orchestrator.print_agent_team(team)

    # Get tool execution order
    tools = orchestrator.get_tool_execution_order(plan)
    print("\nTool Execution Order:")
    for tool in tools:
        print(f"  - {tool['tool_id']} (Agent: {tool['agent_name']})")

    registry.close()
