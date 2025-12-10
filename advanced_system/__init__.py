"""
Advanced Multi-Agent System with Dynamic Tool Creation

This system provides:
1. Planner Agent - Plans the approach
2. Requirements Engineer - Documents requirements
3. Coder Agent - Writes tools (with Open Interpreter support)
4. Validator Agent - Validates results

Tools are dynamically created and stored in generated_tools/ folder.
Open Interpreter enables autonomous code execution.

Structure:
├── tools_factory/        - Tool creation and management
├── agents/              - Individual agent implementations
├── generated_tools/     - Dynamically created tools
├── open_interpreter_integration/ - Code execution engine
└── orchestrator.py      - Main orchestration system
"""
