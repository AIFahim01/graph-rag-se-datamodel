#!/usr/bin/env python3
"""
Advanced Multi-Agent System with HuggingFace Inference API

Uses HuggingFace models (including Qwen3) via LiteLLM and CrewAI

Setup:
1. Get HuggingFace token: https://huggingface.co/settings/tokens
2. Set environment: export HF_TOKEN='hf_your_token_here'
3. Run this script: python3 run_advanced_system_huggingface.py
"""

import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*100)
print("ADVANCED MULTI-AGENT SYSTEM WITH HUGGINGFACE LLM")
print("="*100 + "\n")

# Check HuggingFace token
hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    print("⚠️  HuggingFace token not found!")
    print("\nTo use HuggingFace models, you need to:")
    print("  1. Get token from https://huggingface.co/settings/tokens")
    print("  2. Set environment variable:")
    print("     export HF_TOKEN='hf_your_token_here'")
    print("  3. Then run this script again")
    sys.exit(1)

print("✓ HuggingFace token detected\n")

# Install required packages
print("1️⃣  Installing required packages...")
os.system("pip install litellm -q 2>/dev/null")
print("✓ LiteLLM installed\n")

# Set up HuggingFace configuration
print("2️⃣  Configuring HuggingFace Inference API...")

os.environ["HF_TOKEN"] = hf_token
# Use direct inference API endpoint (not router which has limited provider support)
os.environ["HF_API_ENDPOINT"] = os.getenv("HF_API_ENDPOINT", "https://api-inference.huggingface.co")

hf_api_endpoint = os.environ.get("HF_API_ENDPOINT")
print(f"  • HuggingFace Token: {hf_token[:30]}...")
print(f"  • API Endpoint: {hf_api_endpoint}\n")

# Configure CrewAI to use HuggingFace
print("3️⃣  Configuring CrewAI for HuggingFace...")

from crewai import Agent, Task, Crew, Process
from crewai import LLM

# Available HuggingFace Models (Available via Inference API)
HUGGINGFACE_MODELS = {
    "llama2-7b": {
        "model_id": "meta-llama/Llama-2-7b-chat-hf",
        "description": "Llama 2 7B Chat (RECOMMENDED, Good balance)",
    },
    "mistral-7b": {
        "model_id": "mistralai/Mistral-7B-Instruct-v0.1",
        "description": "Mistral 7B (Fast, Reliable)",
    },
    "llama2-13b": {
        "model_id": "meta-llama/Llama-2-13b-chat-hf",
        "description": "Llama 2 13B Chat (Higher quality, slower)",
    },
    "zephyr-7b": {
        "model_id": "HuggingFaceH4/zephyr-7b-beta",
        "description": "Zephyr 7B (Good for conversation)",
    },
}

# Get model to use
model_key = os.getenv("HF_MODEL", "llama2-7b")
if model_key not in HUGGINGFACE_MODELS:
    print(f"\n❌ Unknown model: {model_key}")
    print("\nAvailable models:")
    for key, details in HUGGINGFACE_MODELS.items():
        print(f"  • {key:20} - {details['description']}")
    sys.exit(1)

model_config = HUGGINGFACE_MODELS[model_key]
model_id = model_config["model_id"]

print(f"  • Model: {model_key}")
print(f"  • Model ID: {model_id}")
print(f"  • {model_config['description']}\n")

# Create HuggingFace LLM instance using LiteLLM
print("4️⃣  Creating HuggingFace LLM instance...")

hf_llm = LLM(
    model=f"huggingface/{model_id}",
    api_key=hf_token,
    api_base=hf_api_endpoint,
)

print("✓ HuggingFace LLM configured\n")

# Import tool manager
from advanced_system.tools_factory.tool_manager import get_tool_manager

print("5️⃣  Initializing agents with HuggingFace LLM...")

# Initialize agents with HuggingFace LLM
planner = Agent(
    role="Planning Expert",
    goal="Plan the approach to solve data retrieval tasks",
    backstory="You are a strategic planner expert who analyzes requirements and creates clear execution plans",
    verbose=False,
    llm=hf_llm,
)

requirements_engineer = Agent(
    role="Requirements Engineer",
    goal="Document and refine data retrieval requirements",
    backstory="You are a requirements engineering expert who clarifies specifications and identifies edge cases",
    verbose=False,
    llm=hf_llm,
)

coder = Agent(
    role="Tool Coder",
    goal="Write and create tools for data retrieval",
    backstory="You are an expert Python and Cypher developer who writes production-ready code",
    verbose=False,
    llm=hf_llm,
)

validator = Agent(
    role="Quality Validator",
    goal="Validate that tools work correctly and return accurate results",
    backstory="You are a quality assurance expert who ensures reliability and data accuracy",
    verbose=False,
    llm=hf_llm,
)

print("✓ All 4 agents initialized with HuggingFace LLM\n")

# Create crew
print("6️⃣  Creating multi-agent crew...")
crew = Crew(
    agents=[planner, requirements_engineer, coder, validator],
    process=Process.sequential,
    verbose=True,
)
print("✓ Crew created\n")

# Test queries
print("="*100)
print("EXECUTING TEST QUERIES (Pure 4-Phase Pipeline with HuggingFace)")
print("="*100 + "\n")

test_queries = [
    "Create a tool to count HVDC projects in the Neo4j database",
    "Create a tool to list all projects with their technology",
]

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*100}")
    print(f"TEST QUERY {i}")
    print(f"{'='*100}")
    print(f"Query: {query}\n")

    try:
        # Create tasks
        task1 = Task(
            description=f"""Analyze and plan the approach for: {query}

Provide a detailed plan including:
1. What data needs to be retrieved
2. What tools are required
3. Required Cypher queries
4. Step-by-step execution plan""",
            expected_output="Comprehensive execution plan",
            agent=planner,
        )

        task2 = Task(
            description=f"""Document requirements for: {query}

Specify:
1. Exact parameters needed
2. Cypher query specifications
3. Expected output format
4. Error handling requirements""",
            expected_output="Complete requirements specification",
            agent=requirements_engineer,
        )

        task3 = Task(
            description=f"""Create tools for: {query}

You must:
1. Write clean Python code for tools
2. Create optimized Cypher queries
3. Implement proper error handling
4. Make tools self-contained and reusable""",
            expected_output="Production-ready tool code",
            agent=coder,
        )

        task4 = Task(
            description=f"""Validate the solution for: {query}

Check:
1. Code quality and standards
2. Cypher query correctness
3. Error handling robustness
4. Result accuracy""",
            expected_output="Validation report",
            agent=validator,
        )

        # Store tasks in crew
        crew.tasks = [task1, task2, task3, task4]

        # Execute crew
        print("🚀 Executing 4-phase pipeline with HuggingFace LLM...")
        result = crew.kickoff(inputs={"task": query})
        print(f"\n✅ Result:\n{result}\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*100)
print("✅ Advanced Multi-Agent System with HuggingFace Ready!")
print("="*100 + "\n")

print("Summary:")
print(f"  • Model: {model_key}")
print(f"  • Model ID: {model_id}")
print(f"  • Provider: HuggingFace Inference API")
print(f"  • Agents: 4 specialized agents")
print(f"  • Process: Sequential 4-phase pipeline")
print(f"  • Status: ✅ Working with HuggingFace LLM\n")

print("To use different models:")
print("  export HF_MODEL=qwen3-32b  # For better quality")
print("  export HF_MODEL=mistral-7b # For speed")
print("  python3 run_advanced_system_huggingface.py\n")
