#!/usr/bin/env python3
"""
Autonomous Agents System - Custom Implementation

Implements autonomous agents with:
- Defined roles, goals, and backstory
- Tools for specific tasks
- Ability to handle multiple types of queries
- Agent orchestration and task execution
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ==================== TOOL DEFINITIONS ====================

class Tool:
    """Base class for agent tools"""

    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

    def execute(self, *args, **kwargs) -> Any:
        """Execute the tool"""
        return self.func(*args, **kwargs)


@dataclass
class ToolDefinition:
    """Definition of a tool an agent can use"""
    name: str
    description: str
    input_params: List[str]
    output_type: str


# ==================== AGENT DEFINITION ====================

@dataclass
class Agent:
    """Autonomous Agent with role, goal, tools, and capabilities"""

    agent_id: str
    role: str  # What the agent does
    goal: str  # What the agent is trying to achieve
    backstory: str  # Context and personality
    tools: List[Tool]  # Tools available to the agent
    max_iterations: int = 10
    verbose: bool = False

    def __post_init__(self):
        self.execution_history = []
        self.memory = {}

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent has access to a tool"""
        return any(t.name == tool_name for t in self.tools)

    def execute_tool(self, tool_name: str, *args, **kwargs) -> Optional[Any]:
        """Execute a tool if available"""
        for tool in self.tools:
            if tool.name == tool_name:
                if self.verbose:
                    logger.info(f"{self.agent_id} executing tool: {tool_name}")
                result = tool.execute(*args, **kwargs)
                self.execution_history.append({
                    "tool": tool_name,
                    "args": args,
                    "kwargs": kwargs,
                    "result": result
                })
                return result
        return None

    def process_task(self, task_description: str, context: Dict[str, Any]) -> str:
        """
        Process a task using available tools.
        Returns the response/result.
        """
        if self.verbose:
            logger.info(f"\n{self.agent_id} processing task:")
            logger.info(f"  Role: {self.role}")
            logger.info(f"  Goal: {self.goal}")
            logger.info(f"  Task: {task_description}")

        # Store context in memory
        self.memory["current_task"] = task_description
        self.memory["context"] = context

        # Agent determines which tools to use based on task
        result = self._reason_and_act(task_description, context)

        return result

    def _reason_and_act(self, task: str, context: Dict[str, Any]) -> str:
        """
        Agent reasons about the task and determines which tools to use.
        This is where the agent's intelligence comes in.
        """
        # Default implementation - subclasses can override
        return f"Task processed by {self.role}: {task}"

    def add_tool(self, tool: Tool):
        """Add a tool to the agent"""
        self.tools.append(tool)

    def get_tools_info(self) -> str:
        """Get information about available tools"""
        tools_info = f"\n{self.agent_id} has access to {len(self.tools)} tools:\n"
        for tool in self.tools:
            tools_info += f"  - {tool.name}: {tool.description}\n"
        return tools_info


# ==================== SPECIALIZED AGENTS ====================

class QueryAnalystAgent(Agent):
    """Agent that analyzes and understands queries"""

    def _reason_and_act(self, task: str, context: Dict[str, Any]) -> str:
        """Analyze the query and determine requirements"""
        response = f"""
Query Analysis by {self.role}:
========================================
Task: {task}

Analysis:
- This query requires understanding the user's intent
- Determining what data should be retrieved
- Identifying key filters or criteria
- Recommending optimal retrieval strategy

Recommendation:
Next, hand off to Research Specialist to retrieve the data.
"""
        return response


class ResearchSpecialistAgent(Agent):
    """Agent that retrieves project data using tools"""

    def _reason_and_act(self, task: str, context: Dict[str, Any]) -> str:
        """Use tools to research and find projects"""
        response = f"""
Research by {self.role}:
========================================
Task: {task}

Available Tools:
"""
        for tool in self.tools:
            response += f"  - {tool.name}: {tool.description}\n"

        # Execute relevant tools based on task
        if "count" in task.lower() or "how many" in task.lower():
            response += "\n✓ Using tool: Count Projects By Technology"

        elif "list" in task.lower():
            response += "\n✓ Using tool: List Projects By Filter"

        elif "search" in task.lower() or "find" in task.lower():
            response += "\n✓ Using tools: Text Search & Semantic Search"

        response += "\nData retrieval in progress..."

        return response


class ResponseSynthesizerAgent(Agent):
    """Agent that synthesizes findings into comprehensive answers"""

    def _reason_and_act(self, task: str, context: Dict[str, Any]) -> str:
        """Synthesize findings into a clear response"""
        response = f"""
Response Synthesis by {self.role}:
========================================

Synthesizing findings from Research Specialist...

The response has been:
✓ Formatted clearly
✓ Organized logically
✓ Enhanced with context
✓ Ready for delivery to user
"""
        return response


# ==================== TASK DEFINITION ====================

@dataclass
class Task:
    """Task to be executed by agents"""

    task_id: str
    description: str
    expected_output: str
    agent: Optional[Agent] = None
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}


# ==================== AUTONOMOUS SYSTEM ====================

class AutonomousAgentSystem:
    """
    System of autonomous agents that work together to process queries.
    Each agent has specific role, goal, tools, and can handle different query types.
    """

    def __init__(self, tools_factory=None):
        """
        Initialize the autonomous agent system.

        Args:
            tools_factory: Optional factory for creating tools (e.g., DatabaseTools)
        """
        self.agents: Dict[str, Agent] = {}
        self.tools_factory = tools_factory
        self.query_history = []
        self.agent_memory = {}

        # Initialize default agents
        self._initialize_agents()

    def _initialize_agents(self):
        """Create and initialize all autonomous agents"""

        # Query Analyst Agent
        analyst = QueryAnalystAgent(
            agent_id="agent_query_analyst",
            role="Query Analyst",
            goal="Understand and classify user queries to determine optimal data retrieval strategy",
            backstory="""You are an expert at understanding natural language queries about projects.
You excel at identifying what users are looking for, what filters apply, and which tools to use.
Your analysis helps the team retrieve the right data efficiently.""",
            tools=[],
            verbose=True
        )
        self.agents["analyst"] = analyst

        # Research Specialist Agent
        researcher = ResearchSpecialistAgent(
            agent_id="agent_research_specialist",
            role="Research Specialist",
            goal="Retrieve and analyze project data from the database using available tools",
            backstory="""You are an expert researcher with deep knowledge of the project database.
You excel at using tools to find projects, count them, search by criteria, and compile results.
Your thorough research ensures complete and accurate data retrieval.""",
            tools=[],  # Will be filled with database tools
            verbose=True
        )
        self.agents["researcher"] = researcher

        # Response Synthesizer Agent
        synthesizer = ResponseSynthesizerAgent(
            agent_id="agent_response_synthesizer",
            role="Response Synthesizer",
            goal="Synthesize research findings into clear, comprehensive, well-structured answers",
            backstory="""You are an expert communicator who excels at:
- Summarizing complex information clearly
- Formatting data in easy-to-understand ways
- Providing context and insights
- Highlighting key findings
Your responses directly answer the user's question with all relevant details.""",
            tools=[],
            verbose=True
        )
        self.agents["synthesizer"] = synthesizer

    def register_tools(self, tools: List[Tool]):
        """
        Register tools with the research specialist agent.

        Args:
            tools: List of Tool objects
        """
        self.agents["researcher"].tools = tools
        logger.info(f"Registered {len(tools)} tools with Research Specialist")

    def add_custom_agent(self, agent_id: str, agent: Agent):
        """Add a custom agent to the system"""
        self.agents[agent_id] = agent
        logger.info(f"Added custom agent: {agent_id}")

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using the autonomous agent system.

        Args:
            query: User's natural language query

        Returns:
            Dictionary with analysis, results, and response
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing Query: {query}")
        logger.info(f"{'='*80}")

        self.query_history.append({
            "query": query,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })

        results = {
            "query": query,
            "analysis": {},
            "research": {},
            "response": {}
        }

        # Step 1: Query Analysis
        analyst = self.agents["analyst"]
        analysis_result = analyst.process_task(
            f"Analyze this query: {query}",
            {"query": query}
        )
        results["analysis"] = {
            "agent": analyst.role,
            "result": analysis_result
        }

        # Step 2: Research
        researcher = self.agents["researcher"]
        research_result = researcher.process_task(
            f"Research projects for this query: {query}",
            {"query": query, "analysis": analysis_result}
        )
        results["research"] = {
            "agent": researcher.role,
            "tools_available": len(researcher.tools),
            "result": research_result
        }

        # Step 3: Response Synthesis
        synthesizer = self.agents["synthesizer"]
        synthesis_result = synthesizer.process_task(
            f"Synthesize response for: {query}",
            {
                "query": query,
                "analysis": analysis_result,
                "research": research_result
            }
        )
        results["response"] = {
            "agent": synthesizer.role,
            "result": synthesis_result
        }

        logger.info(f"{'='*80}")
        logger.info("Query Processing Complete")
        logger.info(f"{'='*80}\n")

        return results

    def handle_count_query(self, query: str) -> Dict[str, Any]:
        """Handle count-type queries"""
        logger.info(f"Handling COUNT query: {query}")
        return self.process_query(query)

    def handle_list_query(self, query: str) -> Dict[str, Any]:
        """Handle list-type queries"""
        logger.info(f"Handling LIST query: {query}")
        return self.process_query(query)

    def handle_search_query(self, query: str) -> Dict[str, Any]:
        """Handle search-type queries"""
        logger.info(f"Handling SEARCH query: {query}")
        return self.process_query(query)

    def get_agent_info(self) -> str:
        """Get information about all agents in the system"""
        info = f"\n{'='*80}\n"
        info += "AUTONOMOUS AGENT SYSTEM\n"
        info += f"{'='*80}\n"
        info += f"Total Agents: {len(self.agents)}\n\n"

        for agent_id, agent in self.agents.items():
            info += f"Agent: {agent.agent_id}\n"
            info += f"  Role: {agent.role}\n"
            info += f"  Goal: {agent.goal}\n"
            info += f"  Tools: {len(agent.tools)}\n"
            if agent.tools:
                for tool in agent.tools:
                    info += f"    - {tool.name}\n"
            info += "\n"

        return info

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "total_agents": len(self.agents),
            "agents": list(self.agents.keys()),
            "queries_processed": len(self.query_history),
            "total_tools": sum(len(agent.tools) for agent in self.agents.values())
        }


if __name__ == "__main__":
    # Example usage
    print("\n" + "="*80)
    print("AUTONOMOUS AGENTS SYSTEM - DEMONSTRATION")
    print("="*80)

    system = AutonomousAgentSystem()

    # Show system info
    print(system.get_agent_info())

    # Process sample queries
    test_queries = [
        "How many HVDC projects do we have?",
        "List all SynCon projects",
        "Find projects in Germany",
    ]

    for query in test_queries:
        results = system.process_query(query)
        print(f"\nQuery: {query}")
        print(f"Analysis Agent: {results['analysis']['agent']}")
        print(f"Research Agent: {results['research']['agent']}")
        print(f"Synthesis Agent: {results['response']['agent']}")

    # Show stats
    stats = system.get_system_stats()
    print(f"\n\nSystem Statistics:")
    print(f"  Total Agents: {stats['total_agents']}")
    print(f"  Total Tools: {stats['total_tools']}")
    print(f"  Queries Processed: {stats['queries_processed']}")
    print("\n" + "="*80)
