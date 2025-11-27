#!/usr/bin/env python3
"""
Main Script: End-to-End Graph RAG Pipeline
Chunk -> ReLiK -> Neo4j -> LLM Query -> Answer
"""

import sys
import argparse
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from services.markdown_chunker import MarkdownChunker
from services.simple_extractor import SimpleExtractor
from services.neo4j_loader import Neo4jLoader
from services.llm_query_generator import LLMQueryGenerator
from services.query_executor import QueryExecutor

# Check if we should use simple extractor
if USE_SIMPLE_EXTRACTOR:
    RelikExtractor = SimpleExtractor
    RELIK_AVAILABLE = False
    print("⚠️  Using simple extractor (USE_SIMPLE_EXTRACTOR=True in config)")
else:
    try:
        from services.relik_extractor import RelikExtractor
        RELIK_AVAILABLE = True
    except ImportError:
        RelikExtractor = SimpleExtractor
        RELIK_AVAILABLE = False
        print("⚠️  ReLiK not available, using simple extractor")


def run_chunking(sample_mode: bool = False):
    """Step 1: Chunk markdown files"""
    print("\n" + "="*80)
    print("STEP 1: CHUNKING MARKDOWN FILES")
    print("="*80)

    chunker = MarkdownChunker(
        data_source=DATA_SOURCE,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        sample_mode=sample_mode
    )

    chunks = chunker.process_files()
    chunker.save_chunks(chunks, CHUNKS_FILE)

    return chunks


def run_extraction(chunks: list):
    """Step 2: Extract entities and relations with ReLiK"""
    print("\n" + "="*80)
    if RELIK_AVAILABLE:
        print("STEP 2: RELIK ENTITY & RELATION EXTRACTION")
        print("="*80)
        extractor = RelikExtractor(
            model_name=RELIK_MODEL,
            batch_size=BATCH_SIZE,
            use_gpu=USE_GPU
        )
    else:
        print("STEP 2: SIMPLE ENTITY & RELATION EXTRACTION (No ReLiK)")
        print("="*80)
        extractor = RelikExtractor()  # Simple extractor has no params

    results = extractor.process_chunks(chunks)
    kg = extractor.build_knowledge_graph(results)
    extractor.save_knowledge_graph(kg, KNOWLEDGE_GRAPH_FILE)

    return kg


def run_loading(kg: dict):
    """Step 3: Load knowledge graph to Neo4j"""
    print("\n" + "="*80)
    print("STEP 3: LOADING TO NEO4J")
    print("="*80)

    loader = Neo4jLoader(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE
    )

    loader.clear_graph()
    loader.create_indexes()
    loader.load_knowledge_graph(kg)

    stats = loader.get_statistics()
    print(f"\n📊 Final Graph Statistics:")
    print(f"   Nodes: {stats['nodes']}")
    print(f"   Relationships: {stats['relationships']}")

    loader.close()


def run_query_mode():
    """Step 4: Interactive query mode"""
    print("\n" + "="*80)
    print("STEP 4: INTERACTIVE QUERY MODE")
    print("="*80)

    # Initialize components
    query_gen = LLMQueryGenerator(
        ollama_url=OLLAMA_API_URL,
        model=LLM_MODEL
    )

    executor = QueryExecutor(
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
        neo4j_database=NEO4J_DATABASE,
        ollama_url=OLLAMA_API_URL,
        llm_model=LLM_MODEL
    )

    print("\n💬 Ask questions about the knowledge graph!")
    print("   Examples:")
    print("   - How many HVDC projects are there?")
    print("   - How many SynCon projects?")
    print("   - List all project types")
    print("   Type 'exit' to quit\n")

    while True:
        try:
            user_query = input("❓ Your question: ").strip()

            if not user_query or user_query.lower() in ['exit', 'quit', 'q']:
                print("👋 Goodbye!")
                break

            # Generate Cypher query
            cypher_query = query_gen.generate_cypher_with_fallback(user_query)

            # Execute and get answer
            response = executor.answer_question(user_query, cypher_query)

            # Display answer
            print(f"\n✅ Answer: {response['answer']}\n")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

    executor.close()


def main():
    parser = argparse.ArgumentParser(
        description='End-to-End Graph RAG Pipeline'
    )
    parser.add_argument(
        '--mode',
        choices=['full', 'chunk', 'extract', 'load', 'query'],
        default='full',
        help='Pipeline mode: full (all steps), or individual steps'
    )
    parser.add_argument(
        '--sample',
        action='store_true',
        help='Sample mode: process only first 10 documents'
    )
    parser.add_argument(
        '--skip-chunk',
        action='store_true',
        help='Skip chunking (use existing chunks.json)'
    )
    parser.add_argument(
        '--skip-extract',
        action='store_true',
        help='Skip extraction (use existing knowledge_graph.json)'
    )

    args = parser.parse_args()

    print("\n" + "🚀"*40)
    print("GRAPH RAG PIPELINE - END TO END")
    print("🚀"*40)

    try:
        if args.mode == 'full':
            # Full pipeline
            if not args.skip_chunk:
                chunks = run_chunking(sample_mode=args.sample)
            else:
                print(f"\n⏭️  Skipping chunking, loading from: {CHUNKS_FILE}")
                import json
                with open(CHUNKS_FILE, 'r') as f:
                    chunks = json.load(f)

            if not args.skip_extract:
                kg = run_extraction(chunks)
            else:
                print(f"\n⏭️  Skipping extraction, loading from: {KNOWLEDGE_GRAPH_FILE}")
                import json
                with open(KNOWLEDGE_GRAPH_FILE, 'r') as f:
                    kg = json.load(f)

            run_loading(kg)
            run_query_mode()

        elif args.mode == 'chunk':
            run_chunking(sample_mode=args.sample)

        elif args.mode == 'extract':
            import json
            with open(CHUNKS_FILE, 'r') as f:
                chunks = json.load(f)
            run_extraction(chunks)

        elif args.mode == 'load':
            import json
            with open(KNOWLEDGE_GRAPH_FILE, 'r') as f:
                kg = json.load(f)
            run_loading(kg)

        elif args.mode == 'query':
            run_query_mode()

        print("\n✨ Pipeline complete!")

    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
