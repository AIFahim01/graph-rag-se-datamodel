"""
Hybrid GraphRAG Chat - Terminal Interface

Run from command line to ask questions about your documents.
Uses:
1. ChromaDB for vector search
2. Neo4j for graph traversal
3. Azure OpenAI for answer generation

Usage:
    python scripts/chat_graphrag.py --query "What database technologies are used?"
    python scripts/chat_graphrag.py --interactive
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from storage.chroma_store import ChromaVectorStore
from storage.neo4j_store import Neo4jGraphStore
from embeddings import VectorGenerator
from retrieval.hybrid_retriever import HybridRetriever
from qa.azure_qa import AzureQASystem


def ask_question(question: str, retriever: HybridRetriever, qa_system: AzureQASystem, top_k: int = 5):
    """Ask a question and get answer"""

    print("\n" + "=" * 80)
    print(f"❓ QUESTION: {question}")
    print("=" * 80)

    # Step 1: Hybrid Retrieval
    print("\n🔍 Retrieving relevant information...")
    print("  📊 Searching ChromaDB (vector similarity)...")
    print("  🕸️  Searching Neo4j (graph relationships)...")

    results = retriever.retrieve(question, top_k=top_k)

    print(f"\n✓ Retrieved {len(results)} relevant chunks")

    # Show sources
    print("\n📚 Sources:")
    for i, result in enumerate(results, 1):
        source_type = result.get('source_type', 'unknown')
        score = result.get('final_score', 0)

        print(f"\n{i}. [{source_type.upper()}] Score: {score:.3f}")
        print(f"   Project: {result.get('project', 'unknown')}")
        print(f"   Source: {result.get('source', result.get('entity', 'unknown'))}")

        if 'text' in result:
            print(f"   Text: {result['text'][:150]}...")
        elif 'related_entity' in result:
            print(f"   Related: {result['related_entity']}")

    # Step 2: Generate Answer
    print("\nGenerating answer with Azure OpenAI...")

    answer_data = qa_system.answer(question, results)

    # Display answer
    print("\n" + "=" * 80)
    print("💬 ANSWER:")
    print("=" * 80)
    print(answer_data['answer'])
    print("\n" + "=" * 80)

    # Show citations
    print("\n📖 Citations:")
    for i, source in enumerate(answer_data['sources'], 1):
        print(f"{i}. {source['project']} - {source['document']} (page {source['page']}) [{source['source_type']}]")

    print("\n" + "=" * 80)


def interactive_mode(retriever: HybridRetriever, qa_system: AzureQASystem):
    """Interactive chat mode"""

    print("\n" + "=" * 80)
    print("HYBRID GRAPHRAG CHAT")
    print("=" * 80)
    print("\nAsk questions about your documents!")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            question = input("❓ Your question: ").strip()

            if not question:
                continue

            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break

            ask_question(question, retriever, qa_system)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description="Hybrid GraphRAG Chat - Ask questions about your documents"
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
        default='gpt-35-turbo',
        help='Azure OpenAI deployment name (default: gpt-35-turbo)'
    )

    args = parser.parse_args()

    # Initialize system
    print("\n" + "=" * 80)
    print("🚀 INITIALIZING HYBRID GRAPHRAG SYSTEM")
    print("=" * 80)

    print("\n📦 Loading components...")
    print("  1. ChromaDB (vector search)...")
    vector_store = ChromaVectorStore()

    print("  2. Neo4j (knowledge graph)...")
    graph_store = Neo4jGraphStore()

    print("  3. Embedding model...")
    embedding_gen = VectorGenerator()

    print("  4. Hybrid retriever...")
    retriever = HybridRetriever(vector_store, graph_store, embedding_gen)

    print(f"  5. Azure OpenAI (deployment: {args.deployment})...")
    qa_system = AzureQASystem(deployment=args.deployment)

    print("\n✅ System ready!")

    # Run query or interactive mode
    if args.query:
        ask_question(args.query, retriever, qa_system, args.top_k)
    elif args.interactive:
        interactive_mode(retriever, qa_system)
    else:
        print("\n⚠️  Please provide --query or --interactive")
        print("\nExamples:")
        print('  python scripts/chat_graphrag.py --query "What database technologies are used?"')
        print('  python scripts/chat_graphrag.py --interactive')

    # Cleanup
    graph_store.close()


if __name__ == "__main__":
    main()
