#!/usr/bin/env python3
"""
Main entry point for Advanced Multi-Agent System
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_system.orchestrator import AdvancedMultiAgentOrchestrator

if __name__ == "__main__":
    try:
        # Initialize orchestrator
        orchestrator = AdvancedMultiAgentOrchestrator()

        # Show status
        print("\n" + "="*100)
        print("SYSTEM STATUS")
        print("="*100)
        orchestrator.show_interpreter_status()
        orchestrator.show_available_tools()

        # Process test queries
        print("\n" + "="*100)
        print("PROCESSING TEST QUERIES")
        print("="*100)

        test_queries = [
            "Create a tool to count HVDC projects in the Neo4j database",
            "Create a tool to list all projects with their technology",
            "Create a tool to search projects in Germany",
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*100}")
            print(f"TEST QUERY {i}/{len(test_queries)}")
            print(f"{'='*100}")
            result = orchestrator.process_query(query)
            orchestrator.display_results(result)

        print("\n" + "="*100)
        print("✅ Advanced Multi-Agent System Ready!")
        print("="*100 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
