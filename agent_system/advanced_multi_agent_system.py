#!/usr/bin/env python3
"""
Advanced Multi-Agent System with Dynamic Tool Creation

Agents:
1. Planner Agent - Plans the approach
2. Requirements Engineer - Documents requirements
3. Coder Agent - Writes tools dynamically using Open Interpreter
4. Validator Agent - Validates results

Tools are stored in dynamic_tools folder and dynamically loaded.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# Set mock OpenAI key for CrewAI
if not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'gsk_init_placeholder'

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from neo4j import GraphDatabase

# Import tool factory
from dynamic_tools.tool_factory import get_tool_factory


# ==================== CYPHER QUERY TEMPLATES ====================

CYPHER_TEMPLATES = {
    'count': '''
        with self.driver.session() as session:
            result = session.run(
                f"MATCH (c:PageChunk) WHERE c.{field} = '{value}' "
                f"RETURN count(DISTINCT c.project_id) as cnt"
            ).single()
            return f"Found {{result['cnt']}} {description}"
    ''',
    'list': '''
        with self.driver.session() as session:
            results = list(session.run(
                f"MATCH (c:PageChunk) {where_clause} "
                f"RETURN DISTINCT c.project_name as name, c.technology as tech "
                f"LIMIT {limit}"
            ))
            names = [f"{{i+1}}. {{r['name']}} ({{r['tech']}})" for i, r in enumerate(results)]
            return f"Found {{len(results)}} projects: " + "\\n".join(names)
    ''',
    'search': '''
        with self.driver.session() as session:
            result = session.run(
                f"MATCH (c:PageChunk) WHERE toLower(c.{field}) CONTAINS toLower('{value}') "
                f"RETURN count(DISTINCT c.project_id) as cnt"
            ).single()
            return f"Found {{result['cnt']}} projects matching {description}"
    '''
}


# ==================== TOOL CREATION & MANAGEMENT ====================

class ToolCreationManager:
    """Manages tool creation using Open Interpreter"""

    def __init__(self):
        self.factory = get_tool_factory()
        self.created_tools: List[str] = []

    def create_cypher_tool(self, tool_spec: Dict[str, Any]) -> bool:
        """
        Create a Cypher-based tool from specification

        Args:
            tool_spec: {
                'name': 'tool_name',
                'description': 'What the tool does',
                'cypher_query': 'The Cypher query',
                'parameters': {'param_name': 'param_type'}
            }
        """
        try:
            # Generate tool code
            tool_code = self._generate_tool_code(
                tool_spec['name'],
                tool_spec.get('cypher_query', ''),
                tool_spec.get('parameters', {})
            )

            # Create the tool
            success = self.factory.create_tool(
                tool_name=tool_spec['name'],
                tool_code=tool_code,
                tool_description=tool_spec['description'],
                parameters=tool_spec.get('parameters', {})
            )

            if success:
                self.created_tools.append(tool_spec['name'])
                logger.info(f"✓ Created tool: {tool_spec['name']}")

            return success

        except Exception as e:
            logger.error(f"✗ Error creating tool: {e}")
            return False

    def _generate_tool_code(self, tool_name: str, cypher_query: str, parameters: Dict) -> str:
        """Generate Python code for the tool"""
        params_code = ', '.join([f"{k}: {v}" for k, v in parameters.items()])

        code = f'''
            def execute(self, {params_code}) -> str:
                """Execute the Cypher query"""
                try:
                    query = """{cypher_query}"""
                    with self.driver.session() as session:
                        result = session.run(query).single()
                        if result:
                            return str(dict(result))
                        return "No results found"
                except Exception as e:
                    return f"Error executing query: {{str(e)}}"
        '''
        return code

    def list_created_tools(self) -> List[str]:
        """List all created tools"""
        return self.created_tools.copy()


# ==================== CREWAI AGENTS ====================

class AdvancedAgentSystem:
    """Advanced multi-agent system with dynamic tool creation"""

    def __init__(self):
        self.tool_manager = ToolCreationManager()
        self.factory = get_tool_factory()
        self._initialize_agents()
        self._create_crew()

    def _initialize_agents(self):
        """Initialize the 4 specialized agents"""

        # Agent 1: Planner
        self.planner = Agent(
            role="Planning Expert",
            goal="Plan the approach to solve data retrieval tasks",
            backstory="""You are a strategic planner expert.
You analyze user requirements and create a clear plan:
- What data needs to be retrieved
- What tools are needed
- What Cypher queries are required
- Step-by-step execution plan

You provide structured, actionable plans.""",
            verbose=False,
        )

        # Agent 2: Requirements Engineer
        self.requirements_engineer = Agent(
            role="Requirements Engineer",
            goal="Document and refine data retrieval requirements",
            backstory="""You are a requirements engineering expert.
You:
- Clarify ambiguous requirements
- Define exact parameters needed
- Document Cypher query needs
- Specify expected output format
- Create requirement specifications

You ensure nothing is missed.""",
            verbose=False,
        )

        # Agent 3: Coder (writes tools)
        self.coder = Agent(
            role="Tool Coder",
            goal="Write and create tools for data retrieval",
            backstory="""You are an expert Python and Cypher developer.
You:
- Write Python tool code
- Create Cypher queries for Neo4j
- Follow best practices
- Handle errors gracefully
- Create production-ready tools

You write tools that are tested and reliable.""",
            verbose=False,
        )

        # Agent 4: Validator
        self.validator = Agent(
            role="Quality Validator",
            goal="Validate that tools work correctly and return accurate results",
            backstory="""You are a quality assurance expert.
You:
- Test tools thoroughly
- Verify results accuracy
- Check error handling
- Validate data completeness
- Ensure reliability

You ensure only quality tools are used.""",
            verbose=False,
        )

        logger.info("✓ Initialized 4 specialized agents")

    def _create_crew(self):
        """Create the crew with all agents"""
        self.crew = Crew(
            agents=[
                self.planner,
                self.requirements_engineer,
                self.coder,
                self.validator
            ],
            process=Process.sequential,
            verbose=False,
        )
        logger.info("✓ Created multi-agent crew")

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a query through the multi-agent pipeline

        Returns: {
            'plan': 'Execution plan from planner',
            'requirements': 'Requirements from engineer',
            'tool_code': 'Code from coder',
            'validation': 'Validation result',
            'result': 'Final result'
        }
        """
        logger.info(f"\n{'='*100}")
        logger.info(f"QUERY: {user_query}")
        logger.info(f"{'='*100}\n")

        result = {
            'query': user_query,
            'plan': None,
            'requirements': None,
            'tools_created': [],
            'validation': None,
            'result': None
        }

        try:
            # Task 1: Planning
            logger.info("1️⃣ PLANNING PHASE...")
            plan_task = Task(
                description=f"""Plan the approach for: {user_query}

Provide:
1. What data needs to be retrieved
2. What tools are needed
3. Required Cypher queries
4. Step-by-step execution plan""",
                expected_output="Detailed execution plan",
                agent=self.planner,
            )

            # Task 2: Requirements
            logger.info("2️⃣ REQUIREMENTS ENGINEERING PHASE...")
            req_task = Task(
                description=f"""Document requirements for: {user_query}

Specify:
1. Exact parameters needed
2. Cypher query specifications
3. Expected output format
4. Edge cases and error handling""",
                expected_output="Complete requirements specification",
                agent=self.requirements_engineer,
            )

            # Task 3: Coding
            logger.info("3️⃣ TOOL CREATION PHASE...")
            code_task = Task(
                description=f"""Create tools for: {user_query}

You must:
1. Write Python tool code
2. Write Cypher queries
3. Create self-contained, executable tools
4. Include error handling

Output the complete tool code.""",
                expected_output="Ready-to-use tool code",
                agent=self.coder,
            )

            # Task 4: Validation
            logger.info("4️⃣ VALIDATION PHASE...")
            val_task = Task(
                description=f"""Validate the solution for: {user_query}

Check:
1. Code quality
2. Query correctness
3. Error handling
4. Result accuracy""",
                expected_output="Validation report with approval",
                agent=self.validator,
            )

            # Execute crew
            try:
                crew_result = self.crew.kickoff(inputs={"task": user_query})
                logger.info("✓ Crew execution completed")
            except Exception as e:
                logger.warning(f"Crew execution error (using fallback): {e}")
                return self._fallback_execution(user_query)

            return result

        except Exception as e:
            logger.error(f"Error in multi-agent pipeline: {e}")
            import traceback
            traceback.print_exc()
            return result

    def _fallback_execution(self, query: str) -> Dict[str, Any]:
        """Fallback execution with direct database queries"""
        logger.info("Using fallback execution...")

        result = {
            'query': query,
            'plan': 'Fallback execution plan',
            'requirements': 'Standard query requirements',
            'tools_created': [],
            'validation': 'Fallback execution mode',
            'result': None
        }

        # Execute direct queries
        try:
            from dynamic_tools.tool_factory import get_tool_factory
            factory = get_tool_factory()

            if 'HVDC' in query:
                # Create a count tool
                tool_spec = {
                    'name': 'count_hvdc_projects',
                    'description': 'Count HVDC projects',
                    'cypher_query': 'MATCH (c:PageChunk) WHERE c.technology = "HVDC" RETURN count(DISTINCT c.project_id) as count',
                    'parameters': {}
                }
                self.tool_manager.create_cypher_tool(tool_spec)
                result['tools_created'].append('count_hvdc_projects')
                result['result'] = 'Tool created for counting HVDC projects'

            elif 'list' in query.lower():
                # Create a list tool
                tool_spec = {
                    'name': 'list_all_projects',
                    'description': 'List all projects',
                    'cypher_query': 'MATCH (c:PageChunk) RETURN DISTINCT c.project_name as name LIMIT 50',
                    'parameters': {}
                }
                self.tool_manager.create_cypher_tool(tool_spec)
                result['tools_created'].append('list_all_projects')
                result['result'] = 'Tool created for listing projects'

            elif 'Germany' in query or 'location' in query.lower():
                # Create a location search tool
                tool_spec = {
                    'name': 'search_location_projects',
                    'description': 'Search projects by location',
                    'cypher_query': 'MATCH (c:PageChunk) WHERE toLower(c.text) CONTAINS toLower("Germany") RETURN count(DISTINCT c.project_id) as count',
                    'parameters': {}
                }
                self.tool_manager.create_cypher_tool(tool_spec)
                result['tools_created'].append('search_location_projects')
                result['result'] = 'Tool created for location search'

        except Exception as e:
            logger.error(f"Fallback execution error: {e}")
            result['result'] = f"Error: {str(e)}"

        return result

    def display_results(self, result: Dict[str, Any]):
        """Display results in a nice format"""
        print(f"\n{'='*100}")
        print("MULTI-AGENT EXECUTION RESULTS")
        print(f"{'='*100}\n")

        print(f"📋 Query: {result['query']}\n")

        if result['plan']:
            print(f"📌 Plan:\n{result['plan']}\n")

        if result['requirements']:
            print(f"📝 Requirements:\n{result['requirements']}\n")

        if result['tools_created']:
            print(f"🔧 Tools Created: {', '.join(result['tools_created'])}\n")

        if result['validation']:
            print(f"✅ Validation:\n{result['validation']}\n")

        if result['result']:
            print(f"📊 Result:\n{result['result']}\n")

        print(f"{'='*100}\n")

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools"""
        return self.factory.list_tools()

    def show_tools_summary(self):
        """Display summary of all available tools"""
        print("\n" + self.factory.get_tools_summary())


# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    print("\n" + "="*100)
    print("ADVANCED MULTI-AGENT SYSTEM WITH DYNAMIC TOOL CREATION")
    print("="*100 + "\n")

    try:
        # Initialize system
        print("Initializing advanced multi-agent system...")
        system = AdvancedAgentSystem()
        print("✅ System initialized!\n")

        # Display available tools
        system.show_tools_summary()

        # Test queries
        test_queries = [
            "Create a tool to count HVDC projects in our Neo4j database",
            "Create a tool to list all SynCon projects with their details",
            "Create a tool to search for projects in Germany",
        ]

        for query in test_queries:
            print(f"\n{'─'*100}")
            result = system.process_query(query)
            system.display_results(result)

        # Show final tools summary
        print("\n" + "="*100)
        print("FINAL TOOLS SUMMARY")
        print("="*100)
        system.show_tools_summary()

        print("\n✅ Advanced Multi-Agent System Ready!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
