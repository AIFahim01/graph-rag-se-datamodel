#!/usr/bin/env python3
"""Debug what context is sent to Ollama"""

import requests
import json

# Call the chat API with debug flag
response = requests.post(
    "http://localhost:3000/api/chat",
    json={
        "query": "In 2022 how many Germany project we have done?",
        "history": [],
        "topK": 5
    },
    timeout=30
)

if response.status_code == 200:
    data = response.json()

    print("Results returned:")
    print("=" * 60)

    # Check what results were returned
    for i, result in enumerate(data.get('results', [])[:3]):
        print(f"\nResult {i+1}:")
        print(f"  Project ID: {result.get('project_id')}")
        print(f"  Year: {result.get('year')}")
        print(f"  Customer: {result.get('customer')}")
        print(f"  Has content: {'Yes' if result.get('content') or result.get('text') else 'No'}")

    # Check the answer
    answer = data.get('answer', 'No answer')
    print("\n" + "=" * 60)
    print("Ollama's answer:")
    print(answer[:300])

    # Check for fallback activation
    if "**Correction:" in answer:
        print("\n✅ Fallback correction was applied!")
    else:
        print("\n❌ Fallback correction was NOT applied")

else:
    print(f"Error: {response.status_code}")
    print(response.text[:500])