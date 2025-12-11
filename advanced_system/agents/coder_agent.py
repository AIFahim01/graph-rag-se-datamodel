#!/usr/bin/env python3
"""
Coder Agent - Implements plans with tools and code execution
Supports Open Interpreter for autonomous code execution
"""

from crewai import Agent
import logging

logger = logging.getLogger(__name__)


def create_coder_agent(llm=None):
    """
    Create an Implementation Expert agent for executing plans.

    This agent:
    - Writes Python code and Cypher queries
    - Executes code using Open Interpreter
    - Handles errors and edge cases
    - Documents implementation progress
    - Provides detailed results

    Args:
        llm: Optional LLM instance (uses default if not provided)

    Returns:
        Agent: Configured coder agent
    """
    return Agent(
        role="Implementation Expert",
        goal=(
            "Execute approved plans by writing clean, efficient Python code and queries. "
            "Use available tools to run code, query databases, and produce results. "
            "Document all progress and deliver complete, working implementations."
        ),
        backstory=(
            "You are an expert software engineer and data developer with deep expertise in:\n"
            "- Writing clean, production-ready Python code\n"
            "- Creating optimized Cypher queries for Neo4j\n"
            "- Using Open Interpreter to execute code autonomously\n"
            "- Handling errors gracefully\n"
            "- Following best practices and standards\n"
            "- Testing and validating implementations\n\n"
            "You excel at turning detailed plans into working implementations. "
            "You use available tools to execute code and verify results. "
            "You provide clear documentation of your work."
        ),
        verbose=False,
        llm=llm
    )
