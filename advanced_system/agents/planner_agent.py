#!/usr/bin/env python3
"""
Planner Agent - Plans the approach to solve queries
"""

import os
if not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'gsk_init_placeholder'

from crewai import Agent


class PlannerAgent:
    """Agent that plans the approach"""

    @staticmethod
    def create():
        """Create and return the planner agent"""
        return Agent(
            role="Planning Expert",
            goal="""Plan the approach to solve data retrieval tasks.
Analyze requirements and create clear execution plans.""",
            backstory="""You are a strategic planner with expertise in:
- Analyzing data retrieval requirements
- Designing Neo4j query approaches
- Planning tool creation strategies
- Creating step-by-step execution plans

You provide structured, actionable plans that guide the entire system.""",
            verbose=False,
        )
