#!/usr/bin/env python3
"""
TRUE GraphRAG Chat - Uses BOTH Vector Database AND Knowledge Graph

This implements real GraphRAG by:
1. Vector search in document chunks
2. Entity extraction from query
3. Graph traversal to find related entities
4. Graph-enhanced context for better answers
"""

import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
import os
import re

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from openai import AzureOpenAI
    from neo4j import GraphDatabase
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    sys.exit(1)

class TrueGraphRAG:
    """True GraphRAG implementation using both vector and graph search"""

    def __init__(self):
        # Load chunks
        chunks_file = PROJECT_ROOT / "data" / "graphrag_complete" / "graphrag_chunks.json"
        with open(chunks_file) as f:
            self.chunks = json.load(f)

        print(f"✅ Loaded {len(self.chunks):,} document chunks")

        # Connect to Neo4j
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )
        print("✅ Connected to Neo4j knowledge graph")

        # Initialize Azure OpenAI
        self.openai_client = AzureOpenAI(
            api_key=os.getenv('AZURE_API_KEY'),
            api_version=os.getenv('AZURE_API_VERSION'),
            azure_endpoint=os.getenv('AZURE_API_BASE')
        )
        print("✅ Connected to Azure OpenAI")

    def extract_entities_from_query(self, query: str):
        """Extract potential entities from the query"""
        entities = set()

        # Technical acronyms
        acronyms = re.findall(r'\b[A-Z][A-Z0-9]{2,6}\b', query)
        entities.update(acronyms)

        # Project codes
        project_codes = re.findall(r'\bGC25?_\d{3}\b', query, re.IGNORECASE)
        entities.update(project_codes)

        # Multi-word technical terms
        words = query.split()
        for i in range(len(words)):
            # Two-word phrases
            if i < len(words) - 1:
                phrase = f"{words[i]} {words[i+1]}"
                if words[i][0].isupper() or words[i].lower() in ['protection', 'system', 'converter']:
                    entities.add(phrase)

        # Common power system terms
        power_terms = [
            'HVDC', 'VSC', 'LCC', 'STATCOM', 'SynCon', 'protection', 'converter',
            'grid', 'power', 'voltage', 'current', 'frequency', 'transformer',
            'breaker', 'relay', 'monitoring', 'control', 'stability'
        ]

        for term in power_terms:
            if term.lower() in query.lower():
                entities.add(term)

        return list(entities)

    def graph_search(self, entities: list):
        """Search knowledge graph for related entities and relationships"""
        graph_context = []

        with self.neo4j_driver.session() as session:
            for entity in entities:
                try:
                    # Find direct relationships
                    result = session.run("""
                        MATCH (e:Entity)-[r]->(related:Entity)
                        WHERE e.name CONTAINS $entity OR $entity CONTAINS e.name
                        RETURN e.name as entity, type(r) as relationship, related.name as related_entity
                        LIMIT 10
                    """, entity=entity)

                    for record in result:
                        graph_context.append({
                            'entity': record['entity'],
                            'relationship': record['relationship'],
                            'related_entity': record['related_entity'],
                            'source_type': 'graph',
                            'text': f"{record['entity']} {record['relationship']} {record['related_entity']}"
                        })

                    # Find entities in same projects
                    result = session.run("""
                        MATCH (p:Project)-[:MENTIONS]->(e:Entity)
                        MATCH (p)-[:MENTIONS]->(other:Entity)
                        WHERE e.name CONTAINS $entity OR $entity CONTAINS e.name
                        AND other.name <> e.name
                        RETURN p.name as project, e.name as entity, other.name as related_entity
                        LIMIT 5
                    """, entity=entity)

                    for record in result:
                        graph_context.append({
                            'project': record['project'],
                            'entity': record['entity'],
                            'related_entity': record['related_entity'],
                            'source_type': 'graph',
                            'text': f"In project {record['project']}: {record['entity']} is related to {record['related_entity']}"
                        })

                except Exception as e:
                    print(f"⚠️  Graph search failed for '{entity}': {e}")

        return graph_context

    def vector_search(self, query: str, top_k: int = 5):
        """Text-based vector search in chunks"""
        query_words = set(query.lower().split())
        scored_chunks = []

        for chunk in self.chunks:
            text_words = set(chunk['text'].lower().split())
            overlap = len(query_words.intersection(text_words))

            if overlap > 0:
                # Enhanced scoring
                score = overlap / len(query_words)

                # Boost score for technical documents
                if chunk.get('document_type') == 'technical':
                    score *= 1.2

                # Boost score for protection-related content
                if 'protection' in chunk['text'].lower():
                    score *= 1.3

                scored_chunks.append((score, chunk))

        scored_chunks.sort(reverse=True, key=lambda x: x[0])

        results = []
        for score, chunk in scored_chunks[:top_k]:
            results.append({
                'text': chunk['text'],
                'project': chunk.get('project', 'unknown'),
                'source': chunk.get('source', 'unknown'),
                'page': chunk.get('page', 0),
                'category': chunk.get('category', 'unknown'),
                'vector_score': score,
                'source_type': 'vector'
            })

        return results

    def hybrid_retrieve(self, query: str, top_k: int = 5):
        """True hybrid retrieval: Vector + Graph"""

        print("🔍 Performing hybrid search (Vector + Graph)...")

        # Step 1: Vector search
        print("  📊 Vector search in document chunks...")
        vector_results = self.vector_search(query, top_k)

        # Step 2: Extract entities from query
        print("  🧠 Extracting entities from query...")
        entities = self.extract_entities_from_query(query)
        print(f"     Found entities: {entities[:5]}")

        # Step 3: Graph search
        print("  🕸️  Knowledge graph traversal...")
        graph_results = self.graph_search(entities)
        print(f"     Found {len(graph_results)} graph relationships")

        # Step 4: Combine results
        print("  🔄 Fusing vector and graph results...")

        # Enhanced context with graph relationships
        enhanced_context = vector_results.copy()

        # Add graph insights to context
        if graph_results:
            graph_summary = "Knowledge Graph Insights:\n"
            for graph_item in graph_results[:3]:
                graph_summary += f"• {graph_item['text']}\n"

            enhanced_context.append({
                'text': graph_summary,
                'project': 'Knowledge Graph',
                'source': 'Entity Relationships',
                'page': 0,
                'source_type': 'graph',
                'vector_score': 0.8
            })

        return enhanced_context, graph_results

    def ask_question(self, question: str):
        """Ask question using true hybrid GraphRAG"""

        print("\n" + "🎯" * 80)
        print(f"❓ QUESTION: {question}")
        print("🎯" * 80)

        # Hybrid retrieval
        context, graph_insights = self.hybrid_retrieve(question, top_k=4)

        print(f"\n✅ Retrieved {len(context)} context pieces")

        # Show sources
        print("\n📚 Sources (Vector + Graph):")
        for i, result in enumerate(context, 1):
            score = result.get('vector_score', 0)
            source_type = result.get('source_type', 'unknown')
            print(f"\n{i}. [{source_type.upper()}] Score: {score:.3f}")
            print(f"   Project: {result['project']}")
            print(f"   Source: {result['source']}")
            if result.get('category'):
                print(f"   Category: {result['category'].upper()}")
            print(f"   Text: {result['text'][:200]}...")

        # Generate enhanced answer
        print(f"\n🤖 Generating GraphRAG answer with GPT-4.1...")

        # Build enhanced prompt with graph context
        context_text = "\n\n".join([
            f"[Source {i+1} - {result.get('source_type', 'vector').upper()}] "
            f"Project: {result['project']}, Document: {result['source']}\n{result['text']}"
            for i, result in enumerate(context)
        ])

        prompt = f"""You are an expert in HVDC and SYNCON power systems. Answer the question using the provided context from technical documents AND knowledge graph relationships.

The context includes both document excerpts (VECTOR) and entity relationships (GRAPH) from a knowledge graph.

CONTEXT:
{context_text}

QUESTION: {question}

Provide a comprehensive technical answer that:
1. Uses information from both document excerpts AND graph relationships
2. Cites sources using [Source N] format
3. Explains the technical concepts clearly
4. Shows how different projects/entities are related

ANSWER:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a technical expert in HVDC and SYNCON systems. Use both document content and knowledge graph relationships to provide comprehensive answers."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.2
            )

            answer = response.choices[0].message.content

            print("\n" + "🚀" * 80)
            print("TRUE GRAPHRAG ANSWER (Vector + Graph + GPT-4.1):")
            print("🚀" * 80)
            print(answer)

            # Show graph insights
            if graph_insights:
                print(f"\n🕸️  Knowledge Graph Insights:")
                for insight in graph_insights[:5]:
                    print(f"   • {insight['text']}")

            print("\n" + "📖" * 80)
            print("SOURCES:")
            for i, result in enumerate(context, 1):
                source_type = result.get('source_type', 'unknown')
                print(f"{i}. [{source_type.upper()}] {result['project']} - {result['source']}")
            print("📖" * 80)

        except Exception as e:
            print(f"❌ Azure OpenAI error: {e}")

def main():
    parser = argparse.ArgumentParser(description="True GraphRAG Chat")
    parser.add_argument('--query', type=str, help='Question to ask')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--deployment', type=str, default='gpt-4.1', help='Deployment')

    args = parser.parse_args()

    print("\n" + "🚀" * 80)
    print("TRUE GRAPHRAG SYSTEM - VECTOR DATABASE + KNOWLEDGE GRAPH")
    print("🚀" * 80)

    try:
        # Initialize true GraphRAG
        graphrag = TrueGraphRAG()

        if args.query:
            graphrag.ask_question(args.query)
        elif args.interactive:
            print("\n🎯 Interactive GraphRAG Chat - Ask about HDVC/SYNCON!")
            print("Type 'exit' to quit.\n")

            while True:
                try:
                    question = input("❓ Your question: ").strip()
                    if not question or question.lower() in ['exit', 'quit']:
                        print("👋 Goodbye!")
                        break
                    graphrag.ask_question(question)
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
        else:
            print("\n💡 Usage examples:")
            print("python true_graphrag_chat.py --query 'What protection systems connect to HVDC converters?' --deployment gpt-4.1")
            print("python true_graphrag_chat.py --interactive")

        # Close Neo4j connection
        graphrag.neo4j_driver.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()