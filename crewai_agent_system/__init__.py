"""
CrewAI Agent System - Intelligent Multi-Agent Query Processing

This package provides a fully autonomous CrewAI-based multi-agent system
with Agent-as-Graph pattern for dynamic discovery and composition.

Components:
- agents: CrewAI agent definitions with specialized roles
- tools: Tool implementations for query execution
- utils: Helper modules (query parser, response formatter, etc.)
"""

from crewai_agent_system.utils.query_parser import (
    IntelligentQueryParser,
    ParsedQuery,
    QueryType,
    QueryClassification,
    DataRequirement,
    analyze_query_for_agents,
)

__all__ = [
    'IntelligentQueryParser',
    'ParsedQuery',
    'QueryType',
    'QueryClassification',
    'DataRequirement',
    'analyze_query_for_agents',
]

__version__ = '0.1.0'
