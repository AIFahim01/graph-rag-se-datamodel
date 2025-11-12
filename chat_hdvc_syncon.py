#!/usr/bin/env python3
"""
HDVC/SYNCON GraphRAG Chat - Works with Persistent ChromaDB

Modified version that works with our local setup:
- Uses persistent ChromaDB (not server mode)
- Connects to our existing vector database
- Works with Azure OpenAI GPT-4.1
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from embeddings import VectorGenerator
from qa.azure_qa import AzureQASystem
import chromadb

def vector_search(query: str, vector_generator, collection, top_k: int = 5):
    """Perform vector search in our persistent ChromaDB"""

    # Generate query embedding
    query_embedding = vector_generator.embed_query(query)

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )

    # Format results
    formatted = []
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        formatted.append({
            'text': doc,
            'project': metadata.get('project', 'unknown'),
            'source': metadata.get('source', 'unknown'),
            'page': metadata.get('page', 0),
            'vector_score': 1 - distance,
            'source_type': 'vector',
            'rank': i + 1
        })

    return formatted

def ask_question(question: str, vector_generator, collection, qa_system, top_k: int = 5):
    """Ask a question and get answer"""

    print("\n" + "=" * 80)
    print(f"❓ QUESTION: {question}")
    print("=" * 80)

    # Vector search
    print("\n🔍 Searching HDVC/SYNCON documents...")

    results = vector_search(question, vector_generator, collection, top_k)

    print(f"✓ Found {len(results)} relevant chunks")

    # Show sources
    print("\n📚 Sources:")
    for i, result in enumerate(results, 1):
        score = result.get('vector_score', 0)
        print(f"\n{i}. [VECTOR] Score: {score:.3f}")
        print(f"   Project: {result.get('project', 'unknown')}")
        print(f"   Source: {result.get('source', 'unknown')}")
        print(f"   Text: {result['text'][:150]}...")

    # Generate answer
    print("\n🤖 Generating answer with GPT-4.1...")

    answer_data = qa_system.answer(question, results)

    # Display answer
    print("\n" + "=" * 80)
    print("🎯 AI ANSWER:")
    print("=" * 80)
    print(answer_data['answer'])
    print("\n" + "=" * 80)

    # Show citations
    print("\n📖 Citations:")
    for i, source in enumerate(answer_data['sources'], 1):
        print(f"{i}. {source['project']} - {source['document'][:60]}...")

    print("\n" + "=" * 80)

def interactive_mode(vector_generator, collection, qa_system):
    """Interactive chat mode"""

    print("\n" + "=" * 80)
    print("🚀 HDVC/SYNCON GRAPHRAG CHAT")
    print("=" * 80)
    print("\nAsk technical questions about your HDVC and SYNCON documents!")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            question = input("❓ Your question: ").strip()

            if not question:
                continue

            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break

            ask_question(question, vector_generator, collection, qa_system)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="HDVC/SYNCON GraphRAG Chat"
    )
    parser.add_argument(
        '--query',
        type=str,
        help='Single question to ask'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Start interactive chat mode'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of results to retrieve (default: 5)'
    )
    parser.add_argument(
        '--deployment',
        type=str,
        default='gpt-4',
        help='Azure OpenAI deployment name (default: gpt-4)'
    )

    args = parser.parse_args()

    # Initialize system
    print("\n" + "=" * 80)
    print("🚀 INITIALIZING HDVC/SYNCON GRAPHRAG SYSTEM")
    print("=" * 80)

    try:
        print("\n📦 Loading components...")

        # BGE Vector Generator
        print("  1. BGE embedding model...")
        vector_generator = VectorGenerator(model_name="BAAI/bge-large-en-v1.5")

        # ChromaDB (persistent mode)
        print("  2. ChromaDB vector database...")
        output_dir = PROJECT_ROOT / "data" / "graphrag_complete"
        chroma_client = chromadb.PersistentClient(path=str(output_dir / "chroma_db"))
        collection = chroma_client.get_collection("graphrag_chunks")
        print(f"     ✓ Loaded {collection.count():,} document chunks")

        # Azure OpenAI
        print(f"  3. Azure OpenAI (deployment: {args.deployment})...")
        qa_system = AzureQASystem(
            api_key=os.getenv('AZURE_API_KEY'),
            api_base=os.getenv('AZURE_API_BASE'),
            api_version=os.getenv('AZURE_API_VERSION'),
            deployment=args.deployment
        )

        print("\n✅ System ready!")

        # Run query or interactive mode
        if args.query:
            ask_question(args.query, vector_generator, collection, qa_system, args.top_k)
        elif args.interactive:
            interactive_mode(vector_generator, collection, qa_system)
        else:
            print("\n⚠️  Please provide --query or --interactive")
            print("\nExamples:")
            print('  python chat_hdvc_syncon.py --query "What HVDC protection systems are mentioned?"')
            print('  python chat_hdvc_syncon.py --interactive')

    except Exception as e:
        print(f"\n❌ Error initializing system: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    main()