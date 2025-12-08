#!/usr/bin/env python3
"""Test the chat API directly to debug Germany counting"""

import requests
import json

# Test query
query = "In 2022 how many Germany project we have done?"

# Call the chat API
response = requests.post(
    "http://localhost:3000/api/chat",
    json={
        "query": query,
        "history": [],
        "topK": 10  # Get more chunks
    }
)

if response.status_code == 200:
    data = response.json()

    print(f"Query: {query}")
    print("-" * 60)
    print(f"Answer: {data.get('answer', 'No answer')}")
    print("-" * 60)
    print("Results found:")

    # Extract unique 2022 projects
    projects_2022 = set()
    for result in data.get('results', []):
        if result.get('year') == 2022:
            project_id = result.get('project_id')
            if project_id:
                projects_2022.add(project_id)
                print(f"  - {project_id} (Year: 2022, Customer: {result.get('customer', 'N/A')})")

    print(f"\nTotal unique 2022 projects found: {len(projects_2022)}")
    print(f"Projects: {sorted(projects_2022)}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)