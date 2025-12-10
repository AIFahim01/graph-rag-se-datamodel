#!/usr/bin/env python3
"""
Open Interpreter Manager - Provides autonomous code execution
Allows agents to write and execute code dynamically
"""

import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class InterpreterManager:
    """Manages Open Interpreter for autonomous code execution"""

    def __init__(self):
        self.interpreter = None
        self._initialize_interpreter()

    def _initialize_interpreter(self):
        """Initialize Open Interpreter"""
        try:
            import interpreter
            self.interpreter = interpreter

            # Configure interpreter
            self.interpreter.auto_run = False  # Require approval before execution
            self.interpreter.chat.display_markdown = True

            logger.info("✓ Open Interpreter initialized")
        except ImportError:
            logger.warning("⚠ Open Interpreter not installed. Install with: pip install open-interpreter")
            self.interpreter = None
        except Exception as e:
            logger.error(f"✗ Error initializing Open Interpreter: {e}")
            self.interpreter = None

    def is_available(self) -> bool:
        """Check if Open Interpreter is available"""
        return self.interpreter is not None

    def execute_code(self, code: str, language: str = "python") -> str:
        """
        Execute code using Open Interpreter

        Args:
            code: Code to execute
            language: Programming language (python, bash, etc.)

        Returns:
            Execution result as string
        """
        if not self.is_available():
            logger.warning("Open Interpreter not available")
            return "Error: Open Interpreter not available"

        try:
            prompt = f"""Execute this {language} code and return the output:

```{language}
{code}
```

Return only the output/result, no explanations."""

            result = self.interpreter.chat(prompt)
            return str(result)

        except Exception as e:
            logger.error(f"Error executing code: {e}")
            return f"Error: {str(e)}"

    def write_and_execute_tool(self, tool_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write and execute a tool specification

        Args:
            tool_spec: {
                'name': 'tool_name',
                'description': 'What it does',
                'code': 'Python code',
                'test_code': 'Test code to validate'
            }

        Returns:
            Result with success status and output
        """
        result = {
            'tool_name': tool_spec.get('name', 'unknown'),
            'success': False,
            'output': None,
            'error': None
        }

        if not self.is_available():
            result['error'] = 'Open Interpreter not available'
            return result

        try:
            # Execute the tool code
            output = self.execute_code(tool_spec.get('code', ''))
            result['output'] = output
            result['success'] = True

            # Run test code if provided
            if tool_spec.get('test_code'):
                test_output = self.execute_code(tool_spec['test_code'])
                result['test_output'] = test_output

            logger.info(f"✓ Tool {tool_spec['name']} executed successfully")
            return result

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"✗ Error executing tool: {e}")
            return result

    def validate_cypher_query(self, cypher_query: str) -> Dict[str, Any]:
        """
        Validate a Cypher query using Open Interpreter

        Args:
            cypher_query: The Cypher query to validate

        Returns:
            Validation result
        """
        validation_code = f'''
from neo4j import GraphDatabase

try:
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "siemensenergy"))
    with driver.session() as session:
        result = session.run("""{cypher_query}""")
        records = list(result)
        print(f"Valid query. Records returned: {{len(records)}}")
        if records:
            print(f"First record: {{dict(records[0])}}")
except Exception as e:
    print(f"Invalid query: {{e}}")
finally:
    driver.close()
'''

        result = {
            'query': cypher_query,
            'valid': False,
            'output': None
        }

        try:
            output = self.execute_code(validation_code)
            result['output'] = output
            result['valid'] = 'Valid query' in output

            return result

        except Exception as e:
            result['output'] = str(e)
            return result

    def generate_cypher_query(self, requirement: str) -> str:
        """
        Generate a Cypher query from natural language requirement

        Args:
            requirement: Natural language description of the query

        Returns:
            Generated Cypher query
        """
        if not self.is_available():
            return ""

        prompt = f"""Generate a Cypher query for Neo4j to: {requirement}

Database structure:
- Node: PageChunk (has properties: project_id, project_name, technology, year, text)

Return ONLY the Cypher query, nothing else."""

        try:
            result = self.interpreter.chat(prompt)
            return str(result).strip()
        except Exception as e:
            logger.error(f"Error generating Cypher query: {e}")
            return ""


# Global instance
_interpreter_manager_instance = None


def get_interpreter_manager() -> InterpreterManager:
    """Get or create global interpreter manager instance"""
    global _interpreter_manager_instance
    if _interpreter_manager_instance is None:
        _interpreter_manager_instance = InterpreterManager()
    return _interpreter_manager_instance
