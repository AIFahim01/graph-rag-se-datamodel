#!/usr/bin/env python3
"""
Coder Agent - Writes tools dynamically using Open Interpreter
"""

import os
if not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'gsk_init_placeholder'

from crewai import Agent


class CoderAgent:
    """Agent that writes tools using Open Interpreter"""

    @staticmethod
    def create(tools=None):
        """Create and return the coder agent"""
        return Agent(
            role="Tool Coder",
            goal="""Write and create tools for data retrieval.
Generate production-ready Python code and Cypher queries.""",
            backstory="""You are an expert Python and Cypher developer with expertise in:
- Writing clean, production-ready Python code
- Creating optimized Cypher queries for Neo4j
- Implementing proper error handling
- Following best practices
- Creating self-contained, reusable tools

You write tools that are reliable, tested, and ready for production use.
You can use Open Interpreter to execute and test your code.""",
            verbose=False,
        )
