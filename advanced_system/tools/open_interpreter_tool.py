"""
Open Interpreter Tool for CrewAI
Enables autonomous code execution and file operations
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import logging
import os

logger = logging.getLogger(__name__)

try:
    from interpreter import interpreter
    INTERPRETER_AVAILABLE = True
except ImportError:
    INTERPRETER_AVAILABLE = False
    logger.warning("Open Interpreter not installed. Install with: pip install open-interpreter")


class OpenInterpreterToolInput(BaseModel):
    """Input schema for OpenInterpreterTool"""
    command: str = Field(
        ...,
        description="Natural language command, Python code, or CLI command to execute"
    )


class OpenInterpreterTool(BaseTool):
    """
    A tool that uses Open Interpreter to execute code and CLI commands
    through natural language instructions.

    Enables agents to:
    - Write and execute Python code
    - Read and write files
    - Run system commands
    - Interact with databases
    - Perform data analysis
    """
    name: str = "OpenInterpreterTool"
    description: str = (
        "Execute code, commands, and file operations using Open Interpreter. "
        "Accepts natural language commands or Python code snippets. "
        "Useful for file operations, data analysis, and autonomous execution."
    )
    args_schema: Type[BaseModel] = OpenInterpreterToolInput

    def __init__(self, auto_run: bool = True, offline: bool = False, **kwargs):
        """
        Initialize Open Interpreter Tool.

        Args:
            auto_run: Automatically run generated code (default: True for full autonomy)
            offline: Use offline mode (default: False)
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        if not INTERPRETER_AVAILABLE:
            self.available = False
            logger.error("Open Interpreter is not installed")
            return

        # Configure interpreter for autonomy
        interpreter.auto_run = auto_run
        interpreter.offline = offline
        interpreter.verbose = False
        interpreter.conversation_history = True

        # Try to detect and use available LLM
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('AZURE_API_KEY')
        if not api_key:
            logger.warning("No API key found for interpreter LLM")

        self.available = True
        logger.info(f"Open Interpreter initialized (auto_run={auto_run})")

    def _run(self, command: str) -> str:
        """
        Execute a command using Open Interpreter.

        Args:
            command: Natural language command, Python code, or CLI command

        Returns:
            String representation of the execution result
        """
        if not INTERPRETER_AVAILABLE or not self.available:
            return "ERROR: Open Interpreter is not available. Install with: pip install open-interpreter"

        try:
            logger.info(f"Executing: {command[:100]}...")
            result = interpreter.chat(command, display=False)

            # Format result
            if isinstance(result, list):
                output_parts = []
                for msg in result:
                    if isinstance(msg, dict) and msg.get('content'):
                        output_parts.append(msg['content'])
                return "\n".join(output_parts) if output_parts else "Executed successfully"

            return str(result) if result else "Executed successfully"

        except Exception as e:
            logger.error(f"Execution error: {str(e)}")
            return f"ERROR: {str(e)}"
