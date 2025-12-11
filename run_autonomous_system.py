#!/usr/bin/env python3
"""
FULLY AUTONOMOUS SYSTEM WITH ITERATIVE PLANNING AND EXECUTION

This system provides complete autonomy with:
- Iterative planning with validator feedback loop
- Iterative execution with validator feedback loop
- Approval-based system (no manual intervention needed)
- Open Interpreter for code execution
- Full autonomy: agents refine work until approved

Setup:
1. Set environment variable (if using specific LLM):
   export OPENAI_API_KEY='your_key' (or AZURE_API_KEY for Azure)

2. Run the system:
   python3 run_autonomous_system.py

The system will automatically:
1. Create a comprehensive plan for your objective
2. Get validator feedback (if not approved)
3. Refine plan iteratively (up to 5 times)
4. Implement approved plan
5. Get validator feedback on implementation
6. Refine implementation iteratively (up to 5 times)
7. Deliver final approved implementation
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import autonomous system
from advanced_system.autonomous_orchestrator import AutonomousOrchestrator
from crewai import LLM


def setup_llm():
    """
    Setup LLM for the system.

    Supports:
    - OpenAI (via OPENAI_API_KEY)
    - Azure OpenAI (via AZURE_API_KEY)
    - Ollama (via OLLAMA_URL)
    - Any LiteLLM provider
    """

    # Check for OpenAI
    if os.getenv('OPENAI_API_KEY'):
        logger.info("Using OpenAI API")
        return LLM(model="gpt-4-turbo")

    # Check for Azure OpenAI
    if os.getenv('AZURE_API_KEY'):
        logger.info("Using Azure OpenAI")
        return LLM(
            model="azure/gpt-4",
            api_key=os.getenv('AZURE_API_KEY'),
            api_base=os.getenv('AZURE_API_BASE'),
            api_version=os.getenv('AZURE_API_VERSION')
        )

    # Check for Ollama
    if os.getenv('OLLAMA_URL'):
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        ollama_model = os.getenv('OLLAMA_MODEL', 'mistral')
        logger.info(f"Using Ollama at {ollama_url} with model {ollama_model}")
        return LLM(
            model=f"ollama/{ollama_model}",
            base_url=ollama_url
        )

    # Default: Try OpenAI, will fail if no key
    logger.info("No LLM configured. Trying OpenAI (set OPENAI_API_KEY if needed)")
    return None


def main():
    """Main entry point for autonomous system."""

    print("\n" + "=" * 100)
    print("FULLY AUTONOMOUS SYSTEM WITH ITERATIVE PLANNING & EXECUTION")
    print("=" * 100)
    print()
    print("This system provides complete autonomy:")
    print("✅ Iterative Planning: Plan → Validate → Refine until approved")
    print("✅ Iterative Execution: Implement → Validate → Refine until approved")
    print("✅ Approval-Based: No manual intervention needed")
    print("✅ Open Interpreter: Can execute code autonomously")
    print()
    print("=" * 100)
    print()

    # Example task: Working with Neo4j data
    user_objective = (
        "Create a tool to count HVDC projects in the Neo4j database. "
        "The tool should query the database, count projects by type, and provide statistics."
    )

    user_data = (
        "Neo4j database with project data. "
        "Schema: Project nodes with properties including type, name, location, voltage_level"
    )

    domain_context = (
        "Working with Neo4j Cypher queries for graph database operations. "
        "Need to connect to database and execute queries to retrieve and analyze project data."
    )

    print(f"OBJECTIVE:\n{user_objective}\n")
    print(f"DATA:\n{user_data}\n")
    print(f"CONTEXT:\n{domain_context}\n")
    print("=" * 100 + "\n")

    try:
        # Setup LLM
        llm = setup_llm()

        # Create orchestrator
        print("Initializing Autonomous Orchestrator...\n")
        orchestrator = AutonomousOrchestrator(
            max_planning_iterations=5,
            max_execution_iterations=5,
            llm=llm
        )

        # Run autonomous pipeline
        print("Starting autonomous pipeline execution...\n")
        results = orchestrator.run(
            user_objective=user_objective,
            user_data=user_data,
            domain_context=domain_context
        )

        # Display results
        print("\n" + "=" * 100)
        print("PIPELINE RESULTS")
        print("=" * 100)

        print(f"\n✅ SUCCESS: {results['success']}")
        print(f"⏱️  Duration: {results['duration_seconds']:.2f} seconds")
        print(f"📋 Phases Completed: {', '.join(results['phases_completed'])}")

        if results.get('final_plan'):
            print("\n" + "─" * 100)
            print("FINAL APPROVED PLAN:")
            print("─" * 100)
            plan_preview = results['final_plan'][:500] + "..." if len(results['final_plan']) > 500 else results['final_plan']
            print(plan_preview)

        if results.get('final_implementation'):
            print("\n" + "─" * 100)
            print("FINAL APPROVED IMPLEMENTATION:")
            print("─" * 100)
            impl_preview = results['final_implementation'][:500] + "..." if len(results['final_implementation']) > 500 else results['final_implementation']
            print(impl_preview)

        if results.get('error'):
            print(f"\n❌ ERROR: {results['error']}")

        print("\n" + "=" * 100)

    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise

    print("\nThank you for using the Autonomous System")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
