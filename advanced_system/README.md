# Advanced Multi-Agent System with Dynamic Tool Creation

## Overview

This system uses **4 specialized agents** with **dynamic tool creation** and **Open Interpreter** for autonomous code execution.

### Architecture

```
User Query
    ↓
┌─────────────────────────────────────────────┐
│  ORCHESTRATOR (orchestrator.py)              │
└─────────────────────────────────────────────┘
    ↓
┌─ PHASE 1: PLANNER ────────────┐
│ • Analyzes requirements        │
│ • Plans approach              │
│ • Identifies tools needed     │
└───────────────────────────────┘
    ↓
┌─ PHASE 2: REQUIREMENTS ENGINEER ────────────┐
│ • Documents requirements                     │
│ • Specifies parameters                      │
│ • Defines expected outputs                  │
└──────────────────────────────────────────────┘
    ↓
┌─ PHASE 3: CODER (with Open Interpreter) ────────────┐
│ • Writes Python code                                 │
│ • Creates Cypher queries                            │
│ • Tests code with Open Interpreter                 │
│ • Saves tools to generated_tools/                   │
└──────────────────────────────────────────────────────┘
    ↓
┌─ PHASE 4: VALIDATOR ────────────┐
│ • Tests tools                   │
│ • Validates results             │
│ • Checks error handling         │
│ • Approves or rejects          │
└─────────────────────────────────┘
    ↓
Generated Tools
(stored in generated_tools/ folder)
```

## Directory Structure

```
advanced_system/
├── __init__.py                 # Module initialization
├── README.md                   # This file
├── orchestrator.py             # Main orchestration system
│
├── tools_factory/
│   ├── __init__.py
│   └── tool_manager.py         # Creates, stores, loads tools
│
├── agents/
│   ├── __init__.py
│   ├── planner_agent.py        # Planning agent
│   ├── requirements_agent.py    # Requirements engineering agent
│   ├── coder_agent.py          # Tool coding agent
│   └── validator_agent.py      # Validation agent
│
├── generated_tools/            # 📁 Dynamically created tools stored here
│   └── __init__.py
│
└── open_interpreter_integration/
    ├── __init__.py
    └── interpreter_manager.py   # Open Interpreter wrapper
```

## Usage

### Basic Execution

```bash
cd /mnt/c/Users/User/PycharmProjects/graph-rag-se-datamodel
python3 advanced_system/orchestrator.py
```

### Process a Custom Query

```python
from advanced_system.orchestrator import AdvancedMultiAgentOrchestrator

# Initialize
orchestrator = AdvancedMultiAgentOrchestrator()

# Process query
result = orchestrator.process_query(
    "Create tools to count HVDC projects and list all projects by technology"
)

# Display results
orchestrator.display_results(result)

# View available tools
orchestrator.show_available_tools()
```

## How It Works

### 1. Planner Agent
- **Role**: Strategic Planner
- **Job**: Analyzes query and creates execution plan
- **Output**: Detailed plan with approach and requirements

### 2. Requirements Engineer Agent
- **Role**: Requirements Specialist
- **Job**: Documents exact requirements and specifications
- **Output**: Formal requirements specification

### 3. Coder Agent
- **Role**: Tool Developer (with Open Interpreter)
- **Job**: Writes Python code and Cypher queries
- **Tools**: Has access to Open Interpreter for testing
- **Output**: Production-ready tool code

### 4. Validator Agent
- **Role**: Quality Assurance
- **Job**: Tests tools and validates results
- **Tools**: Has access to Open Interpreter for validation
- **Output**: Approval/rejection with reasoning

## Features

✅ **4 Specialized Agents** - Each with specific expertise
✅ **Dynamic Tool Creation** - Tools created on-demand and stored
✅ **Open Interpreter Integration** - Agents can execute and test code
✅ **Automatic Tool Loading** - Generated tools auto-loaded at startup
✅ **Tool Management** - Create, load, delete, list tools
✅ **Sequential Processing** - Agents work in logical order
✅ **Error Handling** - Fallback execution when needed
✅ **Comprehensive Logging** - Full visibility into system operation

## Generated Tools

Tools created by the Coder Agent are automatically:
1. **Saved** to `generated_tools/` folder
2. **Documented** with metadata
3. **Loaded** at system startup
4. **Provided** to agents for use

### Tool Structure

Each generated tool is a Python module with:
```python
def tool_name(**kwargs) -> str:
    """
    Tool description
    Parameters: {...}
    """
    # Implementation
    return result
```

## Open Interpreter Integration

The Coder and Validator agents have access to **Open Interpreter** for:
- ✅ Writing and testing Python code
- ✅ Creating and validating Cypher queries
- ✅ Running test suites
- ✅ Debugging code issues

### Installation (Optional)

```bash
pip install open-interpreter
```

If not installed, the system falls back to standard execution.

## Example Queries

```
1. "Create a tool to count HVDC projects"
   → Coder writes Python tool + Cypher query
   → Validator tests with sample data
   → Tool saved to generated_tools/

2. "Create tools to search projects by location"
   → Planner designs approach
   → Requirements engineer specifies parameters
   → Coder writes location search tool
   → Validator tests accuracy

3. "Create tools to list projects by technology"
   → Each agent contributes expertise
   → Tools created with proper error handling
   → Results saved for reuse
```

## Tool Manager API

```python
from advanced_system.tools_factory.tool_manager import get_tool_manager

manager = get_tool_manager()

# Create a tool
manager.create_tool(
    tool_name='my_tool',
    tool_code='...',
    tool_description='What it does',
    parameters={'param1': 'type1'},
    cypher_query='...'
)

# Get a tool
tool = manager.get_tool('my_tool')

# List all tools
tools = manager.list_tools()

# Get tools for agents
agent_tools = manager.get_all_tools_list()

# Delete a tool
manager.delete_tool('my_tool')
```

## Open Interpreter API

```python
from advanced_system.open_interpreter_integration.interpreter_manager import get_interpreter_manager

interpreter = get_interpreter_manager()

# Check if available
if interpreter.is_available():
    # Execute code
    result = interpreter.execute_code(code, language='python')

    # Validate Cypher query
    validation = interpreter.validate_cypher_query(query)

    # Generate Cypher query
    query = interpreter.generate_cypher_query("Count HVDC projects")
```

## Key Advantages

1. **Separation of Concerns** - Each agent has specific responsibility
2. **Dynamic Tools** - Tools created as needed, not predefined
3. **Open Interpreter** - Autonomous code execution and testing
4. **Tool Reusability** - Created tools available for all future queries
5. **Scalability** - Can handle complex, multi-step requirements
6. **Quality Assurance** - Validation phase ensures reliability
7. **Flexibility** - Easy to extend with new agents or tools

## Troubleshooting

### Open Interpreter Not Available
```
⚠ Open Interpreter not installed
Solution: pip install open-interpreter
```

### Tools Not Loading
```
Ensure generated_tools/ directory exists and is writable
Check permissions: ls -la advanced_system/generated_tools/
```

### Agent Initialization Fails
```
Check OPENAI_API_KEY or mock key is set
Verify Neo4j connection is available
```

## Advanced Usage

### Custom Agent Integration

```python
from advanced_system.agents.custom_agent import CustomAgent
orchestrator.add_agent(CustomAgent.create())
```

### Tool Pipeline

```python
# Chain multiple tools
orchestrator.create_tool_pipeline([
    'count_hvdc',
    'list_projects',
    'search_location'
])
```

### Batch Processing

```python
queries = [
    "Create HVDC counter",
    "Create project lister",
    "Create location searcher"
]

for query in queries:
    result = orchestrator.process_query(query)
```

## Performance Notes

- **First execution**: ~5-10 seconds (agent initialization)
- **Subsequent executions**: ~2-5 seconds
- **Tool creation**: ~1-2 seconds per tool
- **Validation**: ~1-2 seconds per tool

## Support

For issues or questions:
1. Check logs: `orchestrator.py` uses Python logging
2. Verify Neo4j connection: `bolt://localhost:7687`
3. Check Open Interpreter installation
4. Review tool syntax in `generated_tools/`

---

**Status**: Production Ready ✅
**Framework**: CrewAI 1.7.0
**Database**: Neo4j with 370 projects
