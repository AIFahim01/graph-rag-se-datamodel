#!/usr/bin/env python3
"""
Dynamic Tool Factory - Manages creation, storage, and loading of tools

This factory:
- Creates tools dynamically (written by Coder Agent)
- Stores tools in the tools folder
- Loads tools dynamically at runtime
- Provides tools to agents
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

TOOLS_DIR = Path(__file__).parent.parent / "dynamic_tools"
TOOLS_DIR.mkdir(exist_ok=True)


class ToolFactory:
    """Factory for creating, storing, and loading dynamic tools"""

    def __init__(self):
        self.tools_dir = TOOLS_DIR
        self.tools: Dict[str, Callable] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        self.load_all_tools()

    def create_tool(self,
                    tool_name: str,
                    tool_code: str,
                    tool_description: str,
                    parameters: Dict[str, str]) -> bool:
        """
        Create a new tool and save it to the tools folder.

        Args:
            tool_name: Name of the tool
            tool_code: Python code for the tool (function)
            tool_description: Description of what the tool does
            parameters: Dict of parameter names and types

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create tool file
            tool_file = self.tools_dir / f"{tool_name}.py"

            # Wrap the tool code with proper imports and structure
            wrapped_code = f'''"""
Tool: {tool_name}
Description: {tool_description}
Parameters: {json.dumps(parameters)}
"""

from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)

class {tool_name.upper()}:
    """Auto-generated tool for {tool_description}"""

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def execute(self, **kwargs) -> str:
        """Execute the tool with provided parameters"""
        try:
{tool_code}
        except Exception as e:
            logger.error(f"Tool execution error: {{e}}")
            return f"Error: {{str(e)}}"

    def close(self):
        if self.driver:
            self.driver.close()


# Function wrapper for CrewAI compatibility
def {tool_name}(**kwargs):
    """
    {tool_description}

    Parameters: {json.dumps(parameters)}
    """
    tool_instance = {tool_name.upper()}()
    result = tool_instance.execute(**kwargs)
    tool_instance.close()
    return result
'''

            # Write to file
            with open(tool_file, 'w') as f:
                f.write(wrapped_code)

            # Save metadata
            self.tool_metadata[tool_name] = {
                'description': tool_description,
                'parameters': parameters,
                'file': str(tool_file),
            }

            logger.info(f"✓ Tool created: {tool_name}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to create tool {tool_name}: {e}")
            return False

    def load_all_tools(self) -> None:
        """Load all tools from the tools directory"""
        try:
            tool_files = list(self.tools_dir.glob("*.py"))
            tool_files = [f for f in tool_files if f.name != "__init__.py"]

            for tool_file in tool_files:
                self._load_tool(tool_file)

            logger.info(f"✓ Loaded {len(self.tools)} tools from {self.tools_dir}")
        except Exception as e:
            logger.error(f"✗ Error loading tools: {e}")

    def _load_tool(self, tool_file: Path) -> bool:
        """Load a single tool from a Python file"""
        try:
            tool_name = tool_file.stem
            spec = importlib.util.spec_from_file_location(tool_name, tool_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get the tool function
            if hasattr(module, tool_name):
                self.tools[tool_name] = getattr(module, tool_name)
                logger.info(f"  ✓ Loaded: {tool_name}")
                return True
            else:
                logger.warning(f"  ✗ Tool function {tool_name} not found in {tool_file}")
                return False

        except Exception as e:
            logger.error(f"  ✗ Error loading {tool_file}: {e}")
            return False

    def get_tool(self, tool_name: str) -> Optional[Callable]:
        """Get a tool by name"""
        return self.tools.get(tool_name)

    def get_all_tools(self) -> Dict[str, Callable]:
        """Get all loaded tools"""
        return self.tools.copy()

    def get_all_tools_for_agent(self) -> List[Callable]:
        """Get all tools as a list for agent use"""
        return list(self.tools.values())

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a tool"""
        return self.tool_metadata.get(tool_name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools with metadata"""
        result = []
        for tool_name, metadata in self.tool_metadata.items():
            result.append({
                'name': tool_name,
                'description': metadata['description'],
                'parameters': metadata['parameters'],
            })
        return result

    def delete_tool(self, tool_name: str) -> bool:
        """Delete a tool"""
        try:
            tool_file = self.tools_dir / f"{tool_name}.py"
            if tool_file.exists():
                tool_file.unlink()
                if tool_name in self.tools:
                    del self.tools[tool_name]
                if tool_name in self.tool_metadata:
                    del self.tool_metadata[tool_name]
                logger.info(f"✓ Tool deleted: {tool_name}")
                return True
            else:
                logger.warning(f"✗ Tool file not found: {tool_file}")
                return False
        except Exception as e:
            logger.error(f"✗ Error deleting tool: {e}")
            return False

    def get_tools_summary(self) -> str:
        """Get a summary of all available tools"""
        if not self.tools:
            return "No tools available"

        summary = f"Available Tools ({len(self.tools)}):\n"
        for tool_name, metadata in self.tool_metadata.items():
            summary += f"\n  • {tool_name}\n"
            summary += f"    Description: {metadata['description']}\n"
            summary += f"    Parameters: {metadata['parameters']}\n"

        return summary


# Global tool factory instance
_factory_instance = None


def get_tool_factory() -> ToolFactory:
    """Get or create the global tool factory instance"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ToolFactory()
    return _factory_instance
