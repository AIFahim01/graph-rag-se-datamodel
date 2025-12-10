#!/usr/bin/env python3
"""
Comprehensive Test Suite for CrewAI Multi-Agent System

Tests all components:
1. Query Parser
2. Agent Registry
3. Agent Discovery
4. Agent Orchestrator
5. Response Formatter
6. Complete System Integration
"""

import json
import sys
from typing import Dict, Any

# Import all components
from crewai_agent_system.utils import (
    IntelligentQueryParser,
    get_agent_registry,
    AgentDiscoveryEngine,
    AgentOrchestrator,
    IntelligentResponseFormatter,
)
from crewai_agent_system.crewai_system import CrewAIQuerySystem


class TestRunner:
    """Helper class to run and report test results"""

    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    def test(self, name: str, condition: bool, details: str = ""):
        """Run a single test"""
        self.tests_run += 1
        status = "✅ PASS" if condition else "❌ FAIL"
        self.test_results.append({
            "name": name,
            "passed": condition,
            "details": details
        })
        if condition:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
        print(f"  {status}: {name}" + (f" - {details}" if details else ""))

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print(f"TEST SUMMARY: {self.tests_passed}/{self.tests_run} passed")
        print("="*80)
        if self.tests_failed > 0:
            print(f"❌ {self.tests_failed} test(s) failed")
        else:
            print("✅ All tests passed!")
        print("="*80)


def test_query_parser():
    """Test the Intelligent Query Parser"""
    print("\n" + "="*80)
    print("TEST 1: INTELLIGENT QUERY PARSER")
    print("="*80)

    runner = TestRunner()
    parser = IntelligentQueryParser()

    test_queries = [
        {
            "query": "How many HVDC projects do we have in 2024?",
            "expected_type": "count",
            "expected_classification": "quantitative",
            "expected_tech": ["HVDC"],
            "expected_year": [2024],
        },
        {
            "query": "List all SynCon projects in Germany",
            "expected_type": "list",
            "expected_classification": "qualitative",
            "expected_tech": ["SynCon"],
            "expected_country": ["Germany"],
        },
        {
            "query": "What AI and grid-related projects are there?",
            "expected_type": "list",
            "expected_classification": "qualitative",
            "expected_semantic": True,
        },
        {
            "query": "Give me TenneT projects in Netherlands",
            "expected_type": "list",
            "expected_classification": "qualitative",
            "expected_company": ["TenneT"],
            "expected_country": ["Netherlands"],
        },
    ]

    for i, test_case in enumerate(test_queries, 1):
        print(f"\n  Test {i}: {test_case['query']}")
        parsed = parser.parse(test_case["query"])

        runner.test(
            f"Query type detection",
            parsed.query_type.value == test_case["expected_type"],
            f"Got {parsed.query_type.value}"
        )

        runner.test(
            f"Classification",
            parsed.classification.value == test_case["expected_classification"],
            f"Got {parsed.classification.value}"
        )

        if "expected_tech" in test_case:
            runner.test(
                f"Technology extraction",
                parsed.technologies == test_case["expected_tech"],
                f"Got {parsed.technologies}"
            )

        if "expected_year" in test_case:
            runner.test(
                f"Year extraction",
                parsed.years == test_case["expected_year"],
                f"Got {parsed.years}"
            )

        if "expected_country" in test_case:
            runner.test(
                f"Country extraction",
                parsed.countries == test_case["expected_country"],
                f"Got {parsed.countries}"
            )

        if "expected_company" in test_case:
            runner.test(
                f"Company extraction",
                parsed.companies == test_case["expected_company"],
                f"Got {parsed.companies}"
            )

        if "expected_semantic" in test_case:
            runner.test(
                f"Semantic search requirement",
                parsed.requires_semantic == test_case["expected_semantic"],
                f"Got {parsed.requires_semantic}"
            )

        runner.test(
            f"Primary tools recommended",
            len(parsed.primary_tools) > 0,
            f"Tools: {parsed.primary_tools}"
        )

    runner.print_summary()
    return runner


def test_agent_registry():
    """Test the Agent Registry with Neo4j"""
    print("\n" + "="*80)
    print("TEST 2: AGENT REGISTRY (Neo4j)")
    print("="*80)

    runner = TestRunner()
    registry = get_agent_registry()

    # Test getting agents
    print("\n  Testing agent retrieval...")
    agents = registry.get_all_agents()
    runner.test("Get all agents", len(agents) > 0, f"Found {len(agents)} agents")

    expected_agent_ids = [
        "agent_query_analyst",
        "agent_search_specialist",
        "agent_graph_navigator",
        "agent_analytics_aggregator",
        "agent_response_synthesizer",
    ]

    agent_ids = [a.agent_id for a in agents]
    for expected_id in expected_agent_ids:
        runner.test(
            f"Agent exists: {expected_id}",
            expected_id in agent_ids,
            ""
        )

    # Test getting specific agent
    print("\n  Testing agent details...")
    search_specialist = registry.get_agent("agent_search_specialist")
    runner.test(
        "Get specific agent",
        search_specialist is not None,
        f"Got {search_specialist.name if search_specialist else 'None'}"
    )

    if search_specialist:
        runner.test(
            f"Agent has capabilities",
            len(search_specialist.capabilities) > 0,
            f"Capabilities: {search_specialist.capabilities}"
        )

        runner.test(
            f"Agent has tools",
            len(search_specialist.tools) > 0,
            f"Tools: {search_specialist.tools}"
        )

    # Test getting tools
    print("\n  Testing tool retrieval...")
    tools = registry.get_all_tools()
    runner.test("Get all tools", len(tools) > 0, f"Found {len(tools)} tools")

    # Test getting capabilities
    print("\n  Testing capability retrieval...")
    capabilities = registry.get_all_capabilities()
    runner.test("Get all capabilities", len(capabilities) > 0, f"Found {len(capabilities)} capabilities")

    # Test registry stats
    print("\n  Testing registry statistics...")
    stats = registry.get_agent_stats()
    runner.test(
        "Get registry stats",
        stats.get("agent_count", 0) > 0,
        f"Agents: {stats.get('agent_count', 0)}, Tools: {stats.get('tool_count', 0)}, Capabilities: {stats.get('capability_count', 0)}"
    )

    registry.close()
    runner.print_summary()
    return runner


def test_agent_discovery():
    """Test the Agent Discovery Engine"""
    print("\n" + "="*80)
    print("TEST 3: AGENT DISCOVERY ENGINE")
    print("="*80)

    runner = TestRunner()
    parser = IntelligentQueryParser()
    registry = get_agent_registry()
    discovery = AgentDiscoveryEngine(registry)

    test_queries = [
        "How many HVDC projects do we have in 2024?",
        "List all SynCon projects in Germany",
        "What AI and grid-related projects are there?",
        "Give me TenneT projects",
    ]

    for query in test_queries:
        print(f"\n  Testing: {query}")
        parsed = parser.parse(query)
        selections = discovery.discover_agents(parsed)

        runner.test(
            "Agents discovered",
            len(selections) > 0,
            f"Found {len(selections)} agents"
        )

        if selections:
            top_agent = selections[0]
            runner.test(
                f"Top agent has match score",
                0 <= top_agent.match_score <= 1.0,
                f"Score: {top_agent.match_score:.0%}"
            )

            runner.test(
                f"Agent has reasoning",
                len(top_agent.reasoning) > 0,
                f"Reasoning: {top_agent.reasoning[:50]}..."
            )

    # Test workflow generation
    print(f"\n  Testing workflow generation...")
    parsed = parser.parse("How many projects?")
    workflow = discovery.discover_workflow(parsed)
    runner.test(
        "Workflow generated",
        len(workflow) > 0,
        f"Workflow: {workflow}"
    )

    registry.close()
    runner.print_summary()
    return runner


def test_agent_orchestrator():
    """Test the Agent Orchestrator"""
    print("\n" + "="*80)
    print("TEST 4: AGENT ORCHESTRATOR")
    print("="*80)

    runner = TestRunner()
    parser = IntelligentQueryParser()
    registry = get_agent_registry()
    discovery = AgentDiscoveryEngine(registry)
    orchestrator = AgentOrchestrator(registry, discovery)

    test_query = "How many HVDC projects in 2024?"
    print(f"\n  Testing: {test_query}")

    parsed = parser.parse(test_query)

    # Test execution plan creation
    plan = orchestrator.create_execution_plan(parsed)
    runner.test(
        "Execution plan created",
        plan is not None,
        f"Steps: {len(plan.steps)}"
    )

    runner.test(
        "Plan has steps",
        len(plan.steps) > 0,
        f"Found {len(plan.steps)} steps"
    )

    if plan.steps:
        step = plan.steps[0]
        runner.test(
            "Step has agent",
            len(step.agent_id) > 0,
            f"Agent: {step.agent_name}"
        )

        runner.test(
            "Step has status",
            step.status.value in ["pending", "running", "success", "failed", "skipped"],
            f"Status: {step.status.value}"
        )

    # Test agent team building
    team = orchestrator.build_agent_team(parsed)
    runner.test(
        "Agent team built",
        len(team) > 0,
        f"Team size: {len(team)}"
    )

    # Test tool execution order
    tools = orchestrator.get_tool_execution_order(plan)
    runner.test(
        "Tool execution order generated",
        len(tools) > 0,
        f"Tools: {len(tools)}"
    )

    # Test execution summary
    summary = orchestrator.get_execution_summary(plan)
    runner.test(
        "Execution summary generated",
        "status" in summary and "steps" in summary,
        f"Status: {summary.get('status')}"
    )

    registry.close()
    runner.print_summary()
    return runner


def test_response_formatter():
    """Test the Response Formatter"""
    print("\n" + "="*80)
    print("TEST 5: RESPONSE FORMATTER")
    print("="*80)

    runner = TestRunner()
    parser = IntelligentQueryParser()
    formatter = IntelligentResponseFormatter()

    test_cases = [
        {
            "query": "How many HVDC projects in 2024?",
            "data": {
                "total_count": 12,
                "breakdown": {
                    "by_technology": {"HVDC": 12},
                    "by_year": {"2024": 12}
                }
            },
            "expected_answer_type": "count",
        },
        {
            "query": "List SynCon projects",
            "data": {
                "total": 5,
                "projects": [
                    {"project_id": "P1", "project_name": "Project 1", "technology": "SynCon", "year": 2024},
                    {"project_id": "P2", "project_name": "Project 2", "technology": "SynCon", "year": 2023},
                ]
            },
            "expected_answer_type": "list",
        },
        {
            "query": "Statistics on projects by technology",
            "data": {
                "total_count": 50,
                "statistics": {
                    "by_technology": {"HVDC": 30, "SynCon": 20},
                    "by_year": {"2024": 25, "2023": 25}
                }
            },
            "expected_answer_type": "statistics",
        },
    ]

    for test_case in test_cases:
        print(f"\n  Testing: {test_case['query']}")
        parsed = parser.parse(test_case["query"])

        response = formatter.format_response(
            parsed,
            test_case["data"],
            confidence=0.95
        )

        runner.test(
            "Response formatted",
            response is not None,
            ""
        )

        runner.test(
            "Response has answer",
            len(response.answer) > 0,
            f"Answer length: {len(response.answer)}"
        )

        runner.test(
            "Answer type matches",
            response.answer_type == test_case["expected_answer_type"],
            f"Got {response.answer_type}"
        )

        runner.test(
            "Confidence set",
            0 <= response.confidence <= 1.0,
            f"Confidence: {response.confidence:.0%}"
        )

        # Test JSON conversion
        json_response = formatter.format_for_json(response)
        runner.test(
            "JSON conversion",
            json.loads(json.dumps(json_response)) is not None,
            ""
        )

    runner.print_summary()
    return runner


def test_complete_system():
    """Test the complete CrewAI System integration"""
    print("\n" + "="*80)
    print("TEST 6: COMPLETE CREWAI SYSTEM INTEGRATION")
    print("="*80)

    runner = TestRunner()

    system = CrewAIQuerySystem()

    test_queries = [
        "How many HVDC projects do we have in 2024?",
        "List all SynCon projects in Germany",
        "What AI and grid-related projects are there?",
        "Give me TenneT projects in Netherlands",
        "How many projects are in India?",
    ]

    for query in test_queries:
        print(f"\n  Testing: {query}")

        try:
            result = system.process_query(query)

            runner.test(
                "Query processed successfully",
                "response" in result,
                ""
            )

            runner.test(
                "Parsed query included",
                "parsed_query" in result,
                f"Type: {result.get('parsed_query', {}).get('type', 'unknown')}"
            )

            runner.test(
                "Execution plan created",
                "execution_plan" in result,
                f"Steps: {result.get('execution_plan', {}).get('total_steps', 0)}"
            )

            runner.test(
                "Agent selections made",
                "agent_selections" in result and len(result["agent_selections"]) > 0,
                f"Selected: {len(result['agent_selections'])} agents"
            )

            if result.get("agent_selections"):
                top_agent = result["agent_selections"][0]
                runner.test(
                    "Top agent has match score",
                    "match_score" in top_agent,
                    f"Score: {top_agent.get('match_score', 'unknown')}"
                )

            runner.test(
                "Response generated",
                "response" in result and "answer" in result["response"],
                f"Answer length: {len(result.get('response', {}).get('answer', ''))}"
            )

            runner.test(
                "Answer has content",
                len(result.get("response", {}).get("answer", "")) > 10,
                f"Content: {result.get('response', {}).get('answer', '')[:50]}..."
            )

        except Exception as e:
            runner.test(
                "Query processing",
                False,
                f"Error: {str(e)}"
            )

    # Test system statistics
    print(f"\n  Testing system statistics...")
    try:
        stats = system.get_system_stats()

        runner.test(
            "System stats retrieved",
            "agents" in stats,
            f"Agents: {stats.get('agents', {}).get('active', 0)}/{stats.get('agents', {}).get('total', 0)}"
        )

        runner.test(
            "Tool count included",
            "tools" in stats and stats["tools"] > 0,
            f"Tools: {stats.get('tools', 0)}"
        )

        runner.test(
            "Capability count included",
            "capabilities" in stats and stats["capabilities"] > 0,
            f"Capabilities: {stats.get('capabilities', 0)}"
        )

    except Exception as e:
        runner.test(
            "System statistics",
            False,
            f"Error: {str(e)}"
        )

    system.close()
    runner.print_summary()
    return runner


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "CREWAI MULTI-AGENT SYSTEM - COMPREHENSIVE TEST SUITE" + " "*12 + "║")
    print("╚" + "="*78 + "╝")

    all_results = []

    # Run all test suites
    all_results.append(test_query_parser())
    all_results.append(test_agent_registry())
    all_results.append(test_agent_discovery())
    all_results.append(test_agent_orchestrator())
    all_results.append(test_response_formatter())
    all_results.append(test_complete_system())

    # Print overall summary
    print("\n" + "="*80)
    print("OVERALL TEST SUMMARY")
    print("="*80)

    total_tests = sum(r.tests_run for r in all_results)
    total_passed = sum(r.tests_passed for r in all_results)
    total_failed = sum(r.tests_failed for r in all_results)

    print(f"\nTotal Tests Run: {total_tests}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"Success Rate: {total_passed/total_tests*100:.1f}%")

    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n⚠️ {total_failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
