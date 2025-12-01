#!/usr/bin/env python3
"""Test Ollama directly with Germany project counting"""

import requests
import json

# Simple test prompt with clear Germany projects
prompt = """
*** LOCATION QUERY RESULTS FOR: GERMANY ***
These chunks are ALL from GERMANY-related projects (vector search already filtered for GERMANY):

SUMMARY OF UNIQUE PROJECTS BY YEAR:
- 2022: 4 project(s) - GC22_046, GC22_070, GC22_082, GC22_085

DETAILED CHUNKS:

Chunk 1 (relevance: 85%)
[PROJECT: GC22_046] [YEAR: 2022] [CUSTOMER: H2Clip] [TECHNOLOGY: Other]
Content: H2Clip hydrogen project in Germany with German text Wasserstofftechnologien

Chunk 2 (relevance: 83%)
[PROJECT: GC22_070] [YEAR: 2022] [CUSTOMER: STEAG] [TECHNOLOGY: BESS]
Content: STEAG battery energy storage system project in Germany

Chunk 3 (relevance: 81%)
[PROJECT: GC22_082] [YEAR: 2022] [CUSTOMER: NEOM] [TECHNOLOGY: Other]
Content: NEOM project with German connections

Chunk 4 (relevance: 80%)
[PROJECT: GC22_085] [YEAR: 2022] [CUSTOMER: NeuConnect] [TECHNOLOGY: HVDC]
Content: NeuConnect UK-Germany interconnector project

User question:
In 2022 how many Germany project we have done?

Instructions for your answer:
IMPORTANT: For location queries (Germany, France, UK, etc.):
- The vector search has ALREADY filtered for location relevance
- ALL chunks shown above ARE from that location's projects - trust this completely!
- Simply count the unique project IDs that match the year

COUNTING INSTRUCTIONS:
- Each chunk has [PROJECT: GC22_XXX] [YEAR: 2022] format
- If you see [PROJECT: GC22_046] [YEAR: 2022], this IS a Germany project from 2022
- Count EVERY unique project ID, don't look for "Germany" in text - the search already did that
- Example answer: "Based on the provided chunks, there are 4 Germany projects from 2022: GC22_046, GC22_070, GC22_082, GC22_085"

Answer:"""

# Test with different models
models = ["gpt-oss:120b", "qwen3:14b", "gpt-oss:20b"]

for model in models:
    print(f"\nTesting with model: {model}")
    print("=" * 60)

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1  # Low temperature for consistent answers
            },
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            answer = data.get('response', 'No response')
            print(f"Answer: {answer[:500]}")

            # Check if answer contains correct count
            if "4" in answer and "GC22_046" in answer:
                print("✅ Model correctly identified 4 Germany projects!")
            else:
                print("❌ Model failed to identify correct count")
        else:
            print(f"Error: {response.status_code}")

    except Exception as e:
        print(f"Error testing {model}: {e}")