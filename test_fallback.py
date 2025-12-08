#!/usr/bin/env python3
"""Test if fallback counting logic is working"""

import re

# The answer from Ollama
answer = "I'm sorry, but I don't have any of the reference chunks for Germany projects from 2022 to review, so I can't determine how many projects were completed that year. If you can provide the relevant chunks, I'll be happy to count them for you."

# Test the pattern
zeroProjectsPattern = r"(?:0|zero|no)\s+(?:unique\s+)?(?:germany|france|uk|china|india|usa)?\s*projects?"
containsZero = bool(re.search(zeroProjectsPattern, answer, re.IGNORECASE))

print(f"Answer: {answer[:100]}...")
print(f"Pattern: {zeroProjectsPattern}")
print(f"Matches 'zero projects' pattern: {containsZero}")

# Check for other patterns that indicate no projects
noDataPatterns = [
    r"don't have.*chunks",
    r"can't determine",
    r"no.*reference chunks",
    r"provide.*relevant chunks"
]

for pattern in noDataPatterns:
    if re.search(pattern, answer, re.IGNORECASE):
        print(f"✓ Matches pattern: {pattern}")

# Updated pattern to catch "don't have chunks" responses
betterPattern = r"(?:don't have|can't determine|no.*reference chunks|0|zero|no)\s+(?:.*)?(?:projects|chunks)"
matchesBetter = bool(re.search(betterPattern, answer, re.IGNORECASE))
print(f"\nBetter pattern matches: {matchesBetter}")