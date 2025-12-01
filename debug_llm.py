#!/usr/bin/env python3
"""Debug what the LLM is returning for Germany queries"""

from llm_query_generator import LLMQueryGenerator
import json

# Create generator with better model
generator = LLMQueryGenerator(model="qwen3:14b")

# Test query
query = "In 2022 how many Germany project we have done"

print(f"Query: {query}")
print("-" * 40)

# Generate query
result = generator.generate_query(query)

# Print full result
print("Full result:")
print(json.dumps(result, indent=2))