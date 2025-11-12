#!/usr/bin/env python3
"""
GraphRAG Chat with LOCAL OLLAMA MODEL
Uses vector database + knowledge graph + local Ollama LLM
No cloud API needed - 100% local and private!
"""

import sys
import json
import argparse
from pathlib import Path
import os
import re
import requests

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from neo4j import GraphDatabase
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    sys.exit(1)

class OllamaGraphRAG:
    """GraphRAG with local Ollama model"""

    def __init__(self, ollama_model="llama3", ollama_url="http://localhost:11434"):
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

        # Ollama configuration
        self.ollama_model = ollama_model
        self.ollama_url = ollama_url
        print(f"✅ Using local Ollama model: {ollama_model}")

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
                score = overlap / len(query_words)

                # Boost technical documents
                if chunk.get('document_type') == 'technical':
                    score *= 1.2

                # Boost protection-related content
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

    def ask_ollama(self, prompt: str):
        """Query local Ollama model"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.9
                    }
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                return f"❌ Ollama error: {response.status_code} - {response.text}"

        except requests.exceptions.ConnectionError:
            return "❌ Cannot connect to Ollama. Make sure Ollama is running (ollama serve)"
        except Exception as e:
            return f"❌ Error: {e}"

    def ask_question(self, question: str):
        """Ask question using hybrid GraphRAG with local Ollama"""

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

        # Generate answer with Ollama
        print(f"\n🤖 Generating answer with local Ollama ({self.ollama_model})...")

        # Build prompt
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

        answer = self.ask_ollama(prompt)

        print("\n" + "🚀" * 80)
        print(f"LOCAL OLLAMA GRAPHRAG ANSWER ({self.ollama_model}):")
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


def main():
    parser = argparse.ArgumentParser(description="GraphRAG Chat with Local Ollama")
    parser.add_argument('--query', type=str, help='Question to ask')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--model', type=str, default='llama3',
                       help='Ollama model (llama3, mistral, phi3, etc.)')
    parser.add_argument('--url', type=str, default='http://localhost:11434',
                       help='Ollama server URL')

    args = parser.parse_args()

    print("\n" + "🚀" * 80)
    print("LOCAL OLLAMA GRAPHRAG SYSTEM")
    print("Vector Database + Knowledge Graph + Local LLM")
    print("🚀" * 80)

    try:
        # Initialize GraphRAG with Ollama
        graphrag = OllamaGraphRAG(ollama_model=args.model, ollama_url=args.url)

        if args.query:
            graphrag.ask_question(args.query)
        elif args.interactive:
            print("\n🎯 Interactive Ollama GraphRAG Chat - Ask about HDVC/SYNCON!")
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
            print("# Interactive mode with Llama 3")
            print("python ollama_graphrag_chat.py --interactive --model llama3")
            print("\n# Single query with Mistral")
            print("python ollama_graphrag_chat.py --query 'What protection systems connect to HVDC?' --model mistral")
            print("\n# Available models: llama3, llama3.1, mistral, phi3, gemma2, qwen2.5, etc.")
            print("\nFirst install Ollama: https://ollama.com")
            print("Then: ollama pull llama3")

        # Close Neo4j connection
        graphrag.neo4j_driver.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
