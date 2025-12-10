#!/usr/bin/env python3
"""
Validator Agent - Validates tools and results
"""

import os
if not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'gsk_init_placeholder'

from crewai import Agent


class ValidatorAgent:
    """Agent that validates tools and results"""

    @staticmethod
    def create(tools=None):
        """Create and return the validator agent"""
        return Agent(
            role="Quality Validator",
            goal="""Validate that tools work correctly and return accurate results.
Ensure reliability and data accuracy.""",
            backstory="""You are a quality assurance expert with expertise in:
- Testing tools thoroughly
- Verifying result accuracy
- Checking error handling
- Validating data completeness
- Identifying potential issues
- Ensuring production readiness

You ensure only quality, reliable tools are approved for use.
You can use Open Interpreter to test and validate code.""",
            verbose=False,
        )
