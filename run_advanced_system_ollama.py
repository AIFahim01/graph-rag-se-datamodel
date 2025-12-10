#!/usr/bin/env python3
"""
Main entry point for Advanced Multi-Agent System with Ollama LLM

Run Ollama first:
  ollama serve

Then in another terminal:
  python3 run_advanced_system_ollama.py
"""

import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Ollama configuration
from advanced_system.ollama_config import OllamaConfig

print("\n" + "="*100)
print("ADVANCED MULTI-AGENT SYSTEM WITH OLLAMA LLM")
print("="*100 + "\n")

# Check Ollama connection
print("1️⃣  Checking Ollama connection...")
if not OllamaConfig.check_ollama_connection():
    print("\n⚠️  Ollama is not running!")
    print("\nTo use Ollama, you need to:")
    print("  1. Install Ollama from https://ollama.ai")
    print("  2. In one terminal, start the server: ollama serve")
    print("  3. In another terminal, pull a model: ollama pull mistral")
    print("  4. Then run this script: python3 run_advanced_system_ollama.py")
    print("\nAvailable models:")
    OllamaConfig.list_available_models()
    sys.exit(1)

print("\n2️⃣  Setting up Ollama configuration...")
OllamaConfig.setup_environment()

# Now configure CrewAI to use Ollama
print("3️⃣  Configuring CrewAI for Ollama...")

from crewai import Agent, Task, Crew, Process, LLM

# Create Ollama LLM instance
ollama_url = OllamaConfig.get_ollama_url()
ollama_model = OllamaConfig.get_model()

print(f"  • Ollama URL: {ollama_url}")
print(f"  • Model: {ollama_model}")

# Create LLM instance for Ollama
ollama_llm = LLM(
    model=f"ollama/{ollama_model}",
    base_url=ollama_url,
)

print(f"  ✓ Ollama LLM configured\n")

# Import agents and orchestrator
from advanced_system.agents.planner_agent import PlannerAgent
from advanced_system.agents.requirements_agent import RequirementsAgent
from advanced_system.agents.coder_agent import CoderAgent
from advanced_system.agents.validator_agent import ValidatorAgent
from advanced_system.tools_factory.tool_manager import get_tool_manager

print("4️⃣  Initializing agents with Ollama LLM...")

# Initialize agents with Ollama LLM
planner = Agent(
    role="Planning Expert",
    goal="Plan the approach to solve data retrieval tasks",
    backstory="You are a strategic planner expert",
    verbose=False,
    llm=ollama_llm,
)

requirements_engineer = Agent(
    role="Requirements Engineer",
    goal="Document and refine data retrieval requirements",
    backstory="You are a requirements engineering expert",
    verbose=False,
    llm=ollama_llm,
)

coder = Agent(
    role="Tool Coder",
    goal="Write and create tools for data retrieval",
    backstory="You are an expert Python and Cypher developer",
    verbose=False,
    llm=ollama_llm,
)

validator = Agent(
    role="Quality Validator",
    goal="Validate that tools work correctly",
    backstory="You are a quality assurance expert",
    verbose=False,
    llm=ollama_llm,
)

print("✓ All 4 agents initialized with Ollama LLM\n")

# Create crew
print("5️⃣  Creating multi-agent crew...")
crew = Crew(
    agents=[planner, requirements_engineer, coder, validator],
    process=Process.sequential,
    verbose=True,
)
print("✓ Crew created\n")

# Test queries
print("="*100)
print("EXECUTING TEST QUERIES (Pure 4-Phase Pipeline with Ollama)")
print("="*100 + "\n")

test_queries = [
    "Create a tool to count HVDC projects in the Neo4j database",
    "Create a tool to list all projects with their technology",
]

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*100}")
    print(f"TEST QUERY {i}")
    print(f"{'='*100}")
    print(f"Query: {query}\n")

    try:
        # Create tasks
        task1 = Task(
            description=f"Analyze and plan the approach for: {query}",
            expected_output="Comprehensive execution plan",
            agent=planner,
        )

        task2 = Task(
            description=f"Document requirements for: {query}",
            expected_output="Complete requirements specification",
            agent=requirements_engineer,
        )

        task3 = Task(
            description=f"Create tools for: {query}",
            expected_output="Production-ready tool code",
            agent=coder,
        )

        task4 = Task(
            description=f"Validate the solution for: {query}",
            expected_output="Validation report",
            agent=validator,
        )

        # Store tasks in crew
        crew.tasks = [task1, task2, task3, task4]

        # Execute crew
        print("🚀 Executing 4-phase pipeline with Ollama LLM...")
        result = crew.kickoff(inputs={"task": query})
        print(f"\n✅ Result:\n{result}\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*100)
print("✅ Advanced Multi-Agent System with Ollama Ready!")
print("="*100 + "\n")

print("Summary:")
print(f"  • Ollama URL: {ollama_url}")
print(f"  • Model: {ollama_model}")
print(f"  • Agents: 4 specialized agents")
print(f"  • Process: Sequential 4-phase pipeline")
print(f"  • Status: ✅ Working with Local Ollama LLM\n")
