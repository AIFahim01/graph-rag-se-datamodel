#!/usr/bin/env python3
"""
Tool Manager - Dynamically creates, stores, and manages tools
Stores all tools in generated_tools folder
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional
import logging

logger = logging.getLogger(__name__)

# Generated tools directory
TOOLS_DIR = Path(__file__).parent.parent / "generated_tools"
TOOLS_DIR.mkdir(exist_ok=True)


class ToolManager:
    """Manages dynamic tool creation and loading"""

    def __init__(self):
        self.tools_dir = TOOLS_DIR
        self.tools: Dict[str, Callable] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        self._load_all_tools()

    def create_tool(self,
                    tool_name: str,
                    tool_code: str,
                    tool_description: str,
                    parameters: Dict[str, str],
                    cypher_query: str = "") -> bool:
        """
        Create a new tool and save it

        Args:
            tool_name: Name of the tool
            tool_code: Python code for the tool
            tool_description: Description of what the tool does
            parameters: Parameter specifications
            cypher_query: Optional Cypher query the tool uses

        Returns:
            True if successful
        """
        try:
            tool_file = self.tools_dir / f"{tool_name}.py"

            # Wrap tool code with proper structure
            wrapped_code = f'''"""
Auto-generated Tool: {tool_name}
Description: {tool_description}
Parameters: {json.dumps(parameters)}
Cypher Query: {cypher_query}
"""

from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)


class {tool_name.upper()}Tool:
    """Auto-generated tool class"""

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def execute(self, **kwargs) -> str:
        """Execute the tool"""
        try:
{self._indent_code(tool_code, 12)}
        except Exception as e:
            logger.error(f"Tool error: {{e}}")
            return f"Error: {{str(e)}}"

    def close(self):
        if self.driver:
            self.driver.close()


def {tool_name}(**kwargs) -> str:
    """
    {tool_description}

    Parameters: {json.dumps(parameters)}
    """
    tool = {tool_name.upper()}Tool()
    result = tool.execute(**kwargs)
    tool.close()
    return result
'''

            # Write to file
            with open(tool_file, 'w') as f:
                f.write(wrapped_code)

            # Save metadata
            self.tool_metadata[tool_name] = {
                'description': tool_description,
                'parameters': parameters,
                'cypher_query': cypher_query,
                'file': str(tool_file),
            }

            logger.info(f"✓ Tool created: {tool_name}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to create tool {tool_name}: {e}")
            return False

    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified spaces"""
        indent = " " * spaces
        return "\n".join(indent + line if line.strip() else line for line in code.split("\n"))

    def _load_all_tools(self):
        """Load all tools from generated_tools folder"""
        try:
            tool_files = list(self.tools_dir.glob("*.py"))
            tool_files = [f for f in tool_files if f.name != "__init__.py"]

            for tool_file in tool_files:
                self._load_tool(tool_file)

            if tool_files:
                logger.info(f"✓ Loaded {len(self.tools)} tools")
        except Exception as e:
            logger.error(f"✗ Error loading tools: {e}")

    def _load_tool(self, tool_file: Path) -> bool:
        """Load a single tool from Python file"""
        try:
            tool_name = tool_file.stem
            spec = importlib.util.spec_from_file_location(tool_name, tool_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, tool_name):
                self.tools[tool_name] = getattr(module, tool_name)
                logger.info(f"  ✓ Loaded: {tool_name}")
                return True
            else:
                logger.warning(f"  ✗ Function {tool_name} not found in {tool_file}")
                return False

        except Exception as e:
            logger.error(f"  ✗ Error loading {tool_file}: {e}")
            return False

    def get_tool(self, tool_name: str) -> Optional[Callable]:
        """Get a tool by name"""
        return self.tools.get(tool_name)

    def get_all_tools(self) -> Dict[str, Callable]:
        """Get all tools as dictionary"""
        return self.tools.copy()

    def get_all_tools_list(self) -> List[Callable]:
        """Get all tools as list for agents"""
        return list(self.tools.values())

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools with metadata"""
        result = []
        for name, metadata in self.tool_metadata.items():
            result.append({
                'name': name,
                'description': metadata['description'],
                'parameters': metadata['parameters'],
            })
        return result

    def get_tools_summary(self) -> str:
        """Get summary of all tools"""
        if not self.tools:
            return "No tools available yet"

        summary = f"Available Tools ({len(self.tools)}):\n"
        for name, metadata in self.tool_metadata.items():
            summary += f"\n  • {name}\n"
            summary += f"    Description: {metadata['description']}\n"
            summary += f"    Parameters: {metadata['parameters']}\n"
            if metadata.get('cypher_query'):
                summary += f"    Query: {metadata['cypher_query'][:50]}...\n"

        return summary

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
            return False
        except Exception as e:
            logger.error(f"✗ Error deleting tool: {e}")
            return False


# Global instance
_tool_manager_instance = None


def get_tool_manager() -> ToolManager:
    """Get or create global tool manager instance"""
    global _tool_manager_instance
    if _tool_manager_instance is None:
        _tool_manager_instance = ToolManager()
    return _tool_manager_instance
