#!/usr/bin/env python3
"""Test Germany 2022 project counting via chat API"""

import requests
import json
import time

def test_chat_query(query):
    """Test a query through the chat API"""
    url = "http://localhost:3000/api/chat"

    try:
        response = requests.post(
            url,
            json={
                "query": query,
                "history": [],
                "topK": 10
            },
            timeout=30  # 30 second timeout
        )

        if response.status_code == 200:
            data = response.json()

            print(f"Query: {query}")
            print("=" * 60)

            # Print answer
            answer = data.get('answer', 'No answer')
            print(f"Answer:\n{answer[:1500]}")  # First 1500 chars
            print("-" * 60)

            # Count unique projects by year
            projects_by_year = {}
            for r in data.get('results', []):
                year = r.get('year')
                project_id = r.get('project_id')
                if year and project_id:
                    if year not in projects_by_year:
                        projects_by_year[year] = set()
                    projects_by_year[year].add(project_id)

            print("Projects found in search results:")
            for year in sorted(projects_by_year.keys()):
                projects = sorted(projects_by_year[year])
                print(f"  {year}: {len(projects)} projects - {', '.join(projects)}")

            # Check if answer mentions the correct count
            if '2022' in query:
                projects_2022 = projects_by_year.get(2022, set())
                count = len(projects_2022)
                print(f"\nExpected: {count} Germany projects from 2022")
                if str(count) in answer:
                    print("✅ Answer contains correct count!")
                else:
                    print("❌ Answer doesn't contain correct count")

        else:
            print(f"Error: Status {response.status_code}")
            print(response.text[:500])

    except requests.exceptions.Timeout:
        print("Request timed out after 60 seconds")
    except Exception as e:
        print(f"Error: {e}")

# Test the Germany 2022 query
print("Testing Germany 2022 project counting...")
print("=" * 60)
test_chat_query("In 2022 how many Germany project we have done?")