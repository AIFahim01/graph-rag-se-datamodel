# CrewAI Autonomous Agents Implementation Guide

## Overview

This guide shows how to implement autonomous agents using the **CrewAI framework** with proper agent definitions, tools, and multi-query handling as per the official CrewAI documentation.

---

## What We've Implemented

### ✅ File: `crewai_agent_system/crewai_implementation.py`

**Features:**
- ✅ 3 Autonomous Agents with roles, goals, and backstory
- ✅ 6 Database Tools with `@tool` decorator
- ✅ Sequential Multi-Agent Process
- ✅ Task definitions for different query types
- ✅ Real Neo4j database integration

**Agents:**
1. **Query Analyzer Agent**
   - Role: Query Analysis
   - Goal: Understand and classify user queries
   - Tools: None (decision-making)

2. **Research Specialist Agent**
   - Role: Data Retrieval
   - Goal: Retrieve project data using tools
   - Tools: 5 database tools

3. **Response Synthesizer Agent**
   - Role: Response Generation
   - Goal: Create comprehensive answers
   - Tools: None (synthesis)

**Tools (with @tool decorator):**
1. `count_projects_tool` - Count projects by technology and year
2. `list_projects_tool` - List all projects with filters
3. `search_location_tool` - Search by country
4. `search_company_tool` - Search by company
5. `semantic_search_tool` - Semantic search (optional)
6. `stats_tool` - Database statistics

---

## How to Use

### Setup Requirements

```bash
# Install CrewAI
pip install crewai crewai-tools

# Set up LLM (choose one option)

# Option 1: OpenAI API
export OPENAI_API_KEY="your-api-key-here"

# Option 2: Use Ollama locally (if installed)
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="gpt-oss:120b"

# Option 3: Use LiteLLM with other providers
pip install litellm
```

### Basic Usage

```python
from crewai_agent_system.crewai_implementation import CrewAIProjectAnalysis

# Initialize the system
system = CrewAIProjectAnalysis()

# Process queries
result = system.process_query("How many HVDC projects do we have?")
print(result)

# Process different query types
result = system.process_query("List all SynCon projects")
result = system.process_query("Show me TenneT projects")

# Clean up
system.close()
```

### Output Structure

```python
{
    "query": "User's query",
    "parsed_query": {
        "type": "count|list|search",
        "classification": "quantitative|qualitative",
        "technologies": [...],
        "countries": [...],
        "companies": [...]
    },
    "agent_analysis": {
        "agent": "Query Analyzer",
        "result": "Analysis result"
    },
    "agent_research": {
        "agent": "Research Specialist",
        "tools_available": 6,
        "result": "Research result"
    },
    "agent_synthesis": {
        "agent": "Response Synthesizer",
        "result": "Final response"
    }
}
```

---

## Agent Definitions (Following CrewAI Documentation)

### Agent 1: Query Analyzer

```python
query_analyzer = Agent(
    role="Query Analyzer",
    goal="Understand and classify user queries to determine optimal data retrieval strategy",
    backstory="""You are an expert at understanding natural language queries about projects.
You excel at identifying:
- What the user is looking for (count, list, search)
- What filters should be applied (technology, location, company)
- What data sources to access (database, vector search)
You provide clear analysis and recommendations.""",
    verbose=True,
    allow_delegation=True,
)
```

### Agent 2: Research Specialist

```python
researcher = Agent(
    role="Research Specialist",
    goal="Retrieve and analyze project data from the database based on various criteria",
    backstory="""You are an expert researcher with deep knowledge of the project database.
You are skilled at:
- Counting projects by technology and year
- Listing projects with detailed information
- Searching by location and company
- Finding projects semantically
You use the available tools effectively to answer any project-related question.""",
    tools=[
        count_projects_tool,
        list_projects_tool,
        search_location_tool,
        search_company_tool,
        semantic_search_tool,
        stats_tool,
    ],
    verbose=True,
    allow_delegation=False,
)
```

### Agent 3: Response Synthesizer

```python
synthesizer = Agent(
    role="Response Synthesizer",
    goal="Synthesize project data into clear, comprehensive, well-structured answers",
    backstory="""You are an expert communicator who excels at:
- Summarizing project information clearly
- Formatting data in easy-to-understand ways
- Providing context and insights
- Highlighting key findings
You create responses that directly answer the user's question with all relevant details.""",
    verbose=True,
    allow_delegation=False,
)
```

---

## Tool Definitions (Following CrewAI @tool Decorator)

### Tool Example: Count Projects

```python
@tool("Count Projects by Technology")
def count_projects_tool(self, technology: str, year: Optional[int] = None) -> str:
    """
    Count projects by technology and optional year.

    Args:
        technology: Technology type (HVDC, SynCon, SVC/STATCOM, Other)
        year: Optional year to filter

    Returns:
        Count of projects and sample names
    """
    # Implementation executes Neo4j query
    # Returns formatted result
```

### Tool Example: List Projects

```python
@tool("List All Projects")
def list_projects_tool(self, technology: Optional[str] = None, limit: int = 500) -> str:
    """
    List all projects, optionally filtered by technology.

    Args:
        technology: Optional technology filter
        limit: Maximum projects to return

    Returns:
        List of matching projects with all details
    """
    # Implementation executes Neo4j query
    # Returns complete list of projects
```

---

## Task Definitions

Tasks define what the crew should do. Example:

```python
analyze_task = Task(
    description="""Analyze this query and determine the best approach:
"{user_query}"

Identify:
1. What the user is looking for
2. What type of query it is (count, list, search)
3. What tools should be used
4. What results should be returned""",
    expected_output="Clear analysis of the query and recommended approach",
    agent=query_analyzer,
)

research_task = Task(
    description="""Based on the analysis, retrieve all relevant project data:
"{user_query}"

Use the appropriate tools to get comprehensive results.
Provide ALL matching projects, not just samples.""",
    expected_output="Complete list of all projects matching the query",
    agent=researcher,
)

synthesis_task = Task(
    description="""Create a final response:
"{user_query}"

Make sure to:
1. Directly answer the question
2. Include ALL relevant projects
3. Format clearly for the user
4. Provide insights if relevant""",
    expected_output="Professional, well-structured final answer",
    agent=synthesizer,
)
```

---

## Crew Setup (Sequential Process)

```python
crew = Crew(
    agents=[
        query_analyzer,
        researcher,
        synthesizer
    ],
    process=Process.sequential,
    verbose=True,
)

# Execute the crew
result = crew.kickoff(inputs={"task": user_query})
```

---

## Process Flow

```
User Query
    ↓
[1] Query Analyzer Agent
    ├─ Analyzes query intent
    ├─ Classifies query type
    └─ Determines required tools
    ↓
[2] Research Specialist Agent
    ├─ Executes analysis
    ├─ Calls appropriate tools
    ├─ Executes Neo4j queries
    └─ Compiles results
    ↓
[3] Response Synthesizer Agent
    ├─ Reviews findings
    ├─ Formats response
    └─ Creates final answer
    ↓
Final Response to User
```

---

## Multiple Query Types

The system automatically handles different query types:

### Count Queries
```
User: "How many HVDC projects do we have in 2024?"
→ Triggers: count_projects_tool
→ Response: "There are 14 HVDC projects in 2024..."
```

### List Queries
```
User: "List all SynCon projects"
→ Triggers: list_projects_tool
→ Response: "Found 35 SynCon projects:
   1. SynCon_Project1 (Tech: SynCon, Year: 2021)
   2. SynCon_Project2 (Tech: SynCon, Year: 2021)
   ..."
```

### Search Queries
```
User: "Projects in Germany"
→ Triggers: search_location_tool
→ Response: "Found 312 projects in Germany..."
```

### Company Queries
```
User: "TenneT projects"
→ Triggers: search_company_tool
→ Response: "Found 45 TenneT projects..."
```

---

## Running the System

### Option 1: With OpenAI API

```bash
export OPENAI_API_KEY="sk-..."
python3 -c "
from crewai_agent_system.crewai_implementation import CrewAIProjectAnalysis
system = CrewAIProjectAnalysis()
result = system.process_query('How many HVDC projects?')
print(result)
system.close()
"
```

### Option 2: With Ollama (Local LLM)

```bash
# Ensure Ollama is running
ollama serve

# In another terminal
export OLLAMA_BASE_URL="http://localhost:11434"
python3 crewai_agent_system/crewai_with_ollama.py
```

### Option 3: Hybrid Approach

Use the custom autonomous system that doesn't require external LLM:

```bash
python3 crewai_agent_system/crewai_system.py
```

---

## Advanced Features

### Agent Delegation
Enable agents to delegate tasks to other agents:
```python
researcher = Agent(
    role="Research Specialist",
    goal="...",
    allow_delegation=True,  # Can delegate to other agents
)
```

### Agent Memory
Enable agents to remember interactions:
```python
researcher = Agent(
    role="Research Specialist",
    goal="...",
    memory=True,  # Maintains conversation history
)
```

### Custom LLM Configuration
```python
from crewai import Agent

agent = Agent(
    role="Query Analyzer",
    goal="...",
    llm="gpt-4",  # Use specific model
    # or
    llm={
        "model": "custom-model",
        "base_url": "http://custom-url",
        "api_key": "..."
    }
)
```

### Tool Caching
```python
researcher = Agent(
    role="Research Specialist",
    goal="...",
    cache=True,  # Cache tool results
)
```

---

## Key Differences from Traditional Systems

| Feature | Traditional System | CrewAI Agents |
|---------|------------------|---------------|
| **Autonomy** | Follow fixed rules | Agents make decisions |
| **Tools** | Called programmatically | Used autonomously by agents |
| **Query Handling** | Hardcoded logic | Agent reasoning |
| **Multi-Step Tasks** | Sequential code | Agent collaboration |
| **Error Recovery** | Error handling | Agent replanning |
| **Learning** | None | Can improve with feedback |

---

## Troubleshooting

### Issue: OPENAI_API_KEY not found
**Solution**: Set environment variable or use Ollama
```bash
export OPENAI_API_KEY="your-key"
# or use Ollama locally
```

### Issue: LiteLLM not available
**Solution**: Install LiteLLM or use Ollama
```bash
pip install litellm
```

### Issue: Tools not being called
**Solution**: Ensure tools have proper `@tool` decorator and are assigned to agents

### Issue: Slow responses
**Solution**:
- Use faster model
- Reduce tool complexity
- Enable caching
- Use smaller result limits

---

## Files Included

1. **crewai_implementation.py** - Full CrewAI implementation with 3 agents and 6 tools
2. **crewai_with_ollama.py** - CrewAI with Ollama LLM backend
3. **crewai_system.py** - Original working system (no external LLM required)
4. **tool_executor.py** - Real database tool implementations
5. **autonomous_agents.py** - Custom autonomous agent implementation

---

## Next Steps

1. **Set up LLM backend** (OpenAI or Ollama)
2. **Configure agents** with your specific roles and goals
3. **Define tools** specific to your use case
4. **Create tasks** for different query types
5. **Test the system** with various queries
6. **Monitor performance** and adjust as needed

---

## References

- [Official CrewAI Documentation](https://docs.crewai.com)
- [Agent Documentation](https://docs.crewai.com/agents/)
- [Tools Documentation](https://docs.crewai.com/tools/)
- [Tasks Documentation](https://docs.crewai.com/tasks/)
- [Crew Documentation](https://docs.crewai.com/crew/)

---

## Summary

You now have a **complete CrewAI autonomous multi-agent system** with:

✅ **3 Autonomous Agents**
- Query Analyzer
- Research Specialist
- Response Synthesizer

✅ **6 Database Tools**
- Count, List, Search Location, Search Company, Semantic Search, Statistics

✅ **Multiple Query Handling**
- Count queries
- List queries
- Search queries
- Company queries

✅ **Real Database Integration**
- Neo4j for structured queries
- Vector search for semantic matching

✅ **Professional Agent Definitions**
- Following official CrewAI documentation
- Proper roles, goals, and backstory
- Tool assignment and usage

The system is ready for autonomous operation and can handle multiple types of queries with intelligent agent reasoning!
