#!/usr/bin/env python3
"""
Requirements Engineer Agent - Documents and refines requirements
"""

import os
if not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'gsk_init_placeholder'

from crewai import Agent


class RequirementsAgent:
    """Agent that documents requirements"""

    @staticmethod
    def create():
        """Create and return the requirements agent"""
        return Agent(
            role="Requirements Engineer",
            goal="""Document and refine data retrieval requirements.
Ensure all specifications are clear and complete.""",
            backstory="""You are a requirements engineering expert with expertise in:
- Clarifying ambiguous requirements
- Defining exact parameters needed
- Specifying Cypher query needs
- Documenting expected outputs
- Identifying edge cases and error scenarios

You ensure nothing is missed and all details are documented.""",
            verbose=False,
        )
