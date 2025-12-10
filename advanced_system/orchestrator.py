#!/usr/bin/env python3
"""
Advanced Multi-Agent System Orchestrator

Orchestrates:
1. Planner Agent - Plans approach
2. Requirements Engineer - Documents requirements
3. Coder Agent - Writes tools
4. Validator Agent - Validates results

Tools are stored in generated_tools/ folder and dynamically provided to agents.
"""

import os
import sys
import logging
from typing import Dict, Any, List
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set mock OpenAI key for CrewAI
if not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'gsk_init_placeholder'

from crewai import Crew, Process, Task

# Import agents
from .agents.planner_agent import PlannerAgent
from .agents.requirements_agent import RequirementsAgent
from .agents.coder_agent import CoderAgent
from .agents.validator_agent import ValidatorAgent

# Import tool manager
from .tools_factory.tool_manager import get_tool_manager

# Import Open Interpreter
from .open_interpreter_integration.interpreter_manager import get_interpreter_manager


class AdvancedMultiAgentOrchestrator:
    """Orchestrates the advanced multi-agent system"""

    def __init__(self):
        logger.info("\n" + "="*100)
        logger.info("INITIALIZING ADVANCED MULTI-AGENT SYSTEM")
        logger.info("="*100 + "\n")

        self.tool_manager = get_tool_manager()
        self.interpreter_manager = get_interpreter_manager()

        # Initialize agents
        logger.info("1. Creating Planner Agent...")
        self.planner = PlannerAgent.create()

        logger.info("2. Creating Requirements Engineer...")
        self.requirements_engineer = RequirementsAgent.create()

        logger.info("3. Creating Coder Agent...")
        self.coder = CoderAgent.create()

        logger.info("4. Creating Validator Agent...")
        self.validator = ValidatorAgent.create()

        # Create crew
        logger.info("\n5. Creating multi-agent crew...\n")
        self.crew = Crew(
            agents=[self.planner, self.requirements_engineer, self.coder, self.validator],
            process=Process.sequential,
            verbose=True,  # Enable verbose for full pipeline visibility
        )

        logger.info("✓ Advanced Multi-Agent System initialized!\n")

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a query through the multi-agent pipeline

        Returns: {
            'query': user query,
            'plan': plan from planner,
            'requirements': requirements from engineer,
            'tools_created': list of created tools,
            'validation': validation result,
            'final_result': final result
        }
        """
        logger.info("\n" + "="*100)
        logger.info(f"PROCESSING QUERY: {user_query}")
        logger.info("="*100 + "\n")

        result = {
            'query': user_query,
            'plan': None,
            'requirements': None,
            'tools_created': [],
            'validation': None,
            'final_result': None
        }

        try:
            # Task 1: Planning Phase
            logger.info("📌 PHASE 1: Planning")
            logger.info("-" * 100)
            plan_task = Task(
                description=f"""Analyze and plan the approach for: {user_query}

Provide a detailed plan including:
1. What data needs to be retrieved
2. What tools are required
3. Cypher queries needed
4. Step-by-step execution plan
5. Expected outcomes""",
                expected_output="Comprehensive execution plan",
                agent=self.planner,
            )

            # Task 2: Requirements Phase
            logger.info("\n📝 PHASE 2: Requirements Engineering")
            logger.info("-" * 100)
            req_task = Task(
                description=f"""Document requirements for: {user_query}

Specify:
1. Exact parameters needed
2. Cypher query specifications
3. Expected output format
4. Error handling requirements
5. Edge cases to consider""",
                expected_output="Complete requirements specification",
                agent=self.requirements_engineer,
            )

            # Task 3: Coding Phase
            logger.info("\n💻 PHASE 3: Tool Creation (Coder Agent)")
            logger.info("-" * 100)
            code_task = Task(
                description=f"""Create tools for: {user_query}

You must:
1. Write clean Python code for tools
2. Create optimized Cypher queries
3. Implement proper error handling
4. Make tools self-contained and reusable
5. Include documentation

Use Open Interpreter to test your code.
Return the complete tool code and specifications.""",
                expected_output="Production-ready tool code and specifications",
                agent=self.coder,
            )

            # Task 4: Validation Phase
            logger.info("\n✅ PHASE 4: Validation")
            logger.info("-" * 100)
            val_task = Task(
                description=f"""Validate the solution for: {user_query}

Check:
1. Code quality and standards
2. Cypher query correctness
3. Error handling robustness
4. Result accuracy
5. Performance implications

Use Open Interpreter to test and validate.
Provide approval or rejection with reasoning.""",
                expected_output="Validation report with detailed assessment",
                agent=self.validator,
            )

            # Store tasks in crew and execute
            logger.info("\n🚀 EXECUTING 4-PHASE PIPELINE...")
            logger.info("-" * 100)
            self.crew.tasks = [plan_task, req_task, code_task, val_task]
            crew_result = self.crew.kickoff(inputs={"task": user_query})
            result['final_result'] = str(crew_result) if crew_result else "Execution completed"
            logger.info("\n✓ All 4 phases completed successfully!\n")

            return result

        except Exception as e:
            logger.error(f"✗ Error in multi-agent pipeline: {e}")
            import traceback
            traceback.print_exc()
            return result

    def display_results(self, result: Dict[str, Any]):
        """Display results nicely"""
        print("\n" + "="*100)
        print("MULTI-AGENT EXECUTION RESULTS")
        print("="*100 + "\n")

        print(f"📋 Query: {result['query']}\n")

        if result['plan']:
            print(f"📌 Plan:\n{result['plan'][:200]}...\n")

        if result['requirements']:
            print(f"📝 Requirements:\n{result['requirements'][:200]}...\n")

        if result['tools_created']:
            print(f"🔧 Tools Created: {', '.join(result['tools_created'])}\n")

        if result['validation']:
            print(f"✅ Validation:\n{result['validation'][:200]}...\n")

        if result['final_result']:
            print(f"📊 Final Result:\n{result['final_result'][:300]}...\n")

        print("="*100 + "\n")

    def show_available_tools(self):
        """Display available tools"""
        print("\n" + self.tool_manager.get_tools_summary())

    def show_interpreter_status(self):
        """Display Open Interpreter status"""
        if self.interpreter_manager.is_available():
            print("✓ Open Interpreter: Available (autonomous code execution enabled)")
        else:
            print("⚠ Open Interpreter: Not available (install with: pip install open-interpreter)")


# ==================== MAIN ====================

if __name__ == "__main__":
    try:
        # Initialize orchestrator
        orchestrator = AdvancedMultiAgentOrchestrator()

        # Show status
        orchestrator.show_interpreter_status()
        orchestrator.show_available_tools()

        # Process test queries
        test_queries = [
            "Create a tool to count HVDC projects in the Neo4j database",
            "Create tools to list all projects grouped by technology",
            "Create tools to search projects by location in Germany",
        ]

        for query in test_queries:
            result = orchestrator.process_query(query)
            orchestrator.display_results(result)

        print("\n✅ Advanced Multi-Agent System Ready!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
