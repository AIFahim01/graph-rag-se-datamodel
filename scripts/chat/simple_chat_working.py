#!/usr/bin/env python3
"""
Simple Working Chat for HDVC/SYNCON Documents
Uses direct file access to avoid ChromaDB version issues
"""

import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
import os
import numpy as np

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from openai import AzureOpenAI
    print("✅ OpenAI library available")
except ImportError:
    print("❌ OpenAI library not available")
    sys.exit(1)

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def simple_text_search(query: str, chunks: list, top_k: int = 5):
    """Simple text-based search as fallback"""
    query_words = set(query.lower().split())

    scored_chunks = []
    for chunk in chunks:
        text_words = set(chunk['text'].lower().split())

        # Simple word overlap score
        overlap = len(query_words.intersection(text_words))
        if overlap > 0:
            score = overlap / len(query_words)
            scored_chunks.append((score, chunk))

    # Sort by score and return top k
    scored_chunks.sort(reverse=True, key=lambda x: x[0])

    results = []
    for score, chunk in scored_chunks[:top_k]:
        results.append({
            'text': chunk['text'],
            'project': chunk.get('project', 'unknown'),
            'source': chunk.get('source', 'unknown'),
            'page': chunk.get('page', 0),
            'vector_score': score,
            'source_type': 'text_search'
        })

    return results

def ask_question_simple(question: str, chunks: list):
    """Ask question using simple search + Azure OpenAI"""

    print("\n" + "=" * 80)
    print(f"❓ QUESTION: {question}")
    print("=" * 80)

    # Simple search
    print("\n🔍 Searching HDVC/SYNCON documents...")

    results = simple_text_search(question, chunks, top_k=5)

    if not results:
        print("❌ No relevant documents found")
        return

    print(f"✓ Found {len(results)} relevant chunks")

    # Show sources
    print("\n📚 Sources:")
    for i, result in enumerate(results, 1):
        score = result.get('vector_score', 0)
        print(f"\n{i}. Score: {score:.3f}")
        print(f"   Project: {result['project']}")
        print(f"   Source: {result['source']}")
        print(f"   Text: {result['text'][:150]}...")

    # Generate answer with Azure OpenAI
    print("\n🤖 Generating answer with Azure OpenAI...")

    try:
        # Initialize Azure OpenAI
        client = AzureOpenAI(
            api_key=os.getenv('AZURE_API_KEY'),
            api_version=os.getenv('AZURE_API_VERSION'),
            azure_endpoint=os.getenv('AZURE_API_BASE')
        )

        # Build context
        context_text = "\n\n".join([
            f"[Source {i+1}] Project: {result['project']}, Document: {result['source']}\n{result['text']}"
            for i, result in enumerate(results)
        ])

        # Create prompt
        prompt = f"""Based on the following context from HDVC and SYNCON technical documents, please answer the question.

CONTEXT:
{context_text}

QUESTION: {question}

ANSWER (cite sources using [Source N] format):"""

        # Call GPT-4.1
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a technical expert assistant specializing in HVDC and SYNCON power systems. Answer questions based on the provided technical documentation and always cite your sources."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )

        answer = response.choices[0].message.content

        # Display answer
        print("\n" + "🎯" * 80)
        print("AI ANSWER (GPT-4.1):")
        print("🎯" * 80)
        print(answer)
        print("\n" + "📖" * 80)
        print("SOURCES:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['project']} - {result['source']}")
        print("📖" * 80)

    except Exception as e:
        print(f"❌ Azure OpenAI error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Simple HDVC/SYNCON Chat")
    parser.add_argument('--query', type=str, help='Question to ask')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--deployment', type=str, default='gpt-4.1', help='Deployment name')

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("🚀 SIMPLE HDVC/SYNCON CHAT SYSTEM")
    print("=" * 80)

    # Load processed chunks
    chunks_file = PROJECT_ROOT / "data" / "graphrag_complete" / "graphrag_chunks.json"

    if not chunks_file.exists():
        print(f"❌ Chunks file not found: {chunks_file}")
        return False

    print(f"📦 Loading chunks from {chunks_file}")

    with open(chunks_file) as f:
        chunks = json.load(f)

    print(f"✅ Loaded {len(chunks):,} document chunks")
    print(f"📊 Categories: {set(chunk.get('category', 'unknown') for chunk in chunks[:100])}")

    if args.query:
        ask_question_simple(args.query, chunks)
    elif args.interactive:
        print("\n📝 Interactive mode - ask questions about HDVC/SYNCON documents!")
        print("Type 'exit' to quit.\n")

        while True:
            try:
                question = input("❓ Your question: ").strip()
                if not question or question.lower() in ['exit', 'quit']:
                    print("👋 Goodbye!")
                    break
                ask_question_simple(question, chunks)
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
    else:
        print("\n⚠️  Use --query 'your question' or --interactive")

if __name__ == "__main__":
    main()