#!/usr/bin/env python3
"""
Enhanced Text-to-Cypher GraphRAG with Entity Pre-Retrieval
Based on research: Neo4j Text2Cypher, LangChain, Microsoft GraphRAG

Features:
1. Entity Pre-Retrieval (full-text search before Cypher generation)
2. Enhanced Schema with sample data from actual graph
3. Few-Shot Learning (5 example question→Cypher pairs)
4. Self-Healing (retry on errors)
5. Vector search for context
"""

import sys
import json
import argparse
import re
from pathlib import Path
import requests
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


class SmartCypherGraphRAG:
    """Enhanced GraphRAG with entity-aware Cypher generation"""

    def __init__(self, ollama_model="mistral", ollama_url="http://localhost:11434"):
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

        # Get enhanced schema with samples
        self.enhanced_schema = self.build_enhanced_schema()

        # Few-shot examples
        self.few_shot_examples = self.build_few_shot_examples()

    def build_enhanced_schema(self):
        """Build enhanced schema with sample data from actual graph"""
        with self.neo4j_driver.session() as session:
            # Get node labels and counts
            labels_result = session.run("""
                MATCH (n)
                WITH labels(n)[0] as label, count(n) as count
                RETURN label, count
                ORDER BY count DESC
            """)
            labels_info = {record['label']: record['count'] for record in labels_result}

            # Get relationship types and counts
            rels_result = session.run("""
                MATCH ()-[r]->()
                WITH type(r) as relType, count(r) as count
                RETURN relType, count
                ORDER BY count DESC
            """)
            rels_info = {record['relType']: record['count'] for record in rels_result}

            # Get top entities (clean ones)
            top_entities = session.run("""
                MATCH (e:Entity)
                WHERE e.mentions > 5
                  AND NOT e.name CONTAINS '</s'
                  AND NOT e.name CONTAINS '<obj>'
                  AND size(e.name) > 2
                RETURN e.name as name, e.mentions as mentions
                ORDER BY e.mentions DESC
                LIMIT 20
            """)
            entity_samples = [f"{record['name']} ({record['mentions']} mentions)"
                            for record in top_entities]

            # Get sample projects
            sample_projects = session.run("""
                MATCH (p:Project)
                RETURN p.name as name
                ORDER BY p.name
                LIMIT 10
            """)
            project_samples = [record['name'] for record in sample_projects]

        schema = {
            'labels': labels_info,
            'relationships': rels_info,
            'entity_samples': entity_samples,
            'project_samples': project_samples
        }

        return schema

    def build_few_shot_examples(self):
        """Build few-shot learning examples for common question types"""
        examples = [
            {
                "question": "How many projects mention HVDC?",
                "cypher": """MATCH (p:Project)
WHERE toLower(p.name) CONTAINS 'hvdc'
RETURN count(p) as total"""
            },
            {
                "question": "What are all the VSC projects?",
                "cypher": """MATCH (p:Project)
WHERE toLower(p.name) CONTAINS 'vsc'
RETURN p.name as project_name
ORDER BY project_name"""
            },
            {
                "question": "How many projects does TenneT have?",
                "cypher": """MATCH (p:Project)
WHERE toLower(p.name) CONTAINS 'tennet'
RETURN count(p) as total"""
            },
            {
                "question": "What entities are related to HVDC?",
                "cypher": """MATCH (e:Entity)-[:RELATED]-(related:Entity)
WHERE toLower(e.name) CONTAINS 'hvdc'
RETURN DISTINCT related.name as entity
LIMIT 10"""
            },
            {
                "question": "What are the most mentioned entities?",
                "cypher": """MATCH (e:Entity)
WHERE e.mentions > 10
RETURN e.name as entity, e.mentions as mentions
ORDER BY mentions DESC
LIMIT 10"""
            }
        ]
        return examples

    def extract_key_terms(self, question: str):
        """Extract potential entities/companies/technologies from question"""
        # Clean and tokenize
        terms = []

        # Technical acronyms (2-6 uppercase letters)
        acronyms = re.findall(r'\b[A-Z]{2,6}\b', question)
        terms.extend(acronyms)

        # Capitalized words (potential company names)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', question)
        terms.extend(capitalized)

        # Known power system terms
        power_terms = ['hvdc', 'vsc', 'lcc', 'statcom', 'syncon', 'protection',
                      'converter', 'grid', 'transformer', 'breaker', 'mmc']
        for term in power_terms:
            if term.lower() in question.lower():
                terms.append(term.upper())

        # Geographic terms
        geo_terms = ['germany', 'german', 'netherlands', 'dutch', 'saudi',
                    'india', 'france', 'uk', 'spain', 'norway']
        for term in geo_terms:
            if term.lower() in question.lower():
                terms.append(term.title())

        # Remove duplicates and empty strings
        terms = list(set([t for t in terms if len(t) > 1]))

        return terms

    def entity_pre_retrieval(self, terms: list):
        """Pre-retrieve matching entities/projects from Neo4j using full-text search"""
        matches = {
            'entities': [],
            'projects': []
        }

        with self.neo4j_driver.session() as session:
            for term in terms:
                # Search entities with fuzzy matching
                try:
                    entity_results = session.run("""
                        CALL db.index.fulltext.queryNodes('entity_fulltext', $term + '~')
                        YIELD node, score
                        WHERE score > 1.0
                          AND NOT node.name CONTAINS '</s'
                          AND NOT node.name CONTAINS '<obj>'
                        RETURN node.name as name, score
                        ORDER BY score DESC
                        LIMIT 5
                    """, term=term)

                    for record in entity_results:
                        matches['entities'].append({
                            'name': record['name'],
                            'score': record['score'],
                            'search_term': term
                        })
                except Exception as e:
                    # Full-text index might not be ready
                    pass

                # Search projects with fuzzy matching
                try:
                    project_results = session.run("""
                        CALL db.index.fulltext.queryNodes('project_fulltext', $term + '~')
                        YIELD node, score
                        WHERE score > 1.0
                        RETURN node.name as name, score
                        ORDER BY score DESC
                        LIMIT 5
                    """, term=term)

                    for record in project_results:
                        matches['projects'].append({
                            'name': record['name'],
                            'score': record['score'],
                            'search_term': term
                        })
                except Exception as e:
                    pass

        # Deduplicate and sort by score
        if matches['entities']:
            seen = set()
            unique_entities = []
            for e in sorted(matches['entities'], key=lambda x: x['score'], reverse=True):
                if e['name'] not in seen:
                    unique_entities.append(e)
                    seen.add(e['name'])
            matches['entities'] = unique_entities[:10]

        if matches['projects']:
            seen = set()
            unique_projects = []
            for p in sorted(matches['projects'], key=lambda x: x['score'], reverse=True):
                if p['name'] not in seen:
                    unique_projects.append(p)
                    seen.add(p['name'])
            matches['projects'] = unique_projects[:10]

        return matches

    def ask_ollama(self, prompt: str, temperature=0.2):
        """Query local Ollama model"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_p": 0.9
                    }
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                return f"❌ Ollama error: {response.status_code}"

        except requests.exceptions.ConnectionError:
            return "❌ Cannot connect to Ollama. Make sure Ollama is running"
        except Exception as e:
            return f"❌ Error: {e}"

    def generate_cypher_with_context(self, question: str, matches: dict):
        """Generate Cypher query with entity pre-retrieval context"""

        # Build few-shot examples section
        few_shot_text = "\n\nFEW-SHOT EXAMPLES:\n"
        for i, example in enumerate(self.few_shot_examples, 1):
            few_shot_text += f"\nExample {i}:\n"
            few_shot_text += f"Question: {example['question']}\n"
            few_shot_text += f"Cypher:\n{example['cypher']}\n"

        # Build pre-retrieved entities section
        context_text = "\n\nPRE-RETRIEVED MATCHES FROM YOUR GRAPH:\n"
        if matches['entities']:
            context_text += "\nEntities found:\n"
            for e in matches['entities'][:5]:
                context_text += f"  - '{e['name']}' (search term: {e['search_term']}, score: {e['score']:.2f})\n"
        if matches['projects']:
            context_text += "\nProjects found:\n"
            for p in matches['projects'][:5]:
                context_text += f"  - '{p['name']}' (search term: {p['search_term']}, score: {p['score']:.2f})\n"

        if not matches['entities'] and not matches['projects']:
            context_text += "  (No exact matches found - use CONTAINS for partial matching)\n"

        # Build schema section
        schema_text = f"""
GRAPH SCHEMA:
- Node Labels: {', '.join(self.enhanced_schema['labels'].keys())}
- Relationship Types: {', '.join(self.enhanced_schema['relationships'].keys())}

Node Properties:
- Entity: name (string), mentions (int), num_projects (int)
- Project: name (string)

Top Entities in Graph (examples):
{chr(10).join(f"  - {e}" for e in self.enhanced_schema['entity_samples'][:10])}

Sample Projects:
{chr(10).join(f"  - {p}" for p in self.enhanced_schema['project_samples'][:5])}
"""

        prompt = f"""You are a Neo4j Cypher query expert. Generate a Cypher query to answer the user's question.

{schema_text}
{context_text}
{few_shot_text}

IMPORTANT RULES:
1. Use MATCH, WHERE, RETURN syntax
2. Use toLower() and CONTAINS for text matching: WHERE toLower(p.name) CONTAINS 'text'
3. For counting: RETURN count(x) as total
4. For listing: RETURN x.name as name ORDER BY name
5. Use the PRE-RETRIEVED MATCHES above - these are ACTUAL entities/projects from the graph
6. Handle spelling variations with CONTAINS (e.g., 'tennet', 'TenneT', 'TENNET' all match)
7. For company names, technology types, or countries, search in Project.name
8. Return ONLY valid Cypher, no explanations

QUESTION: {question}

Generate ONLY the Cypher query (no markdown, no explanation):"""

        print(f"\n🤖 Asking {self.ollama_model} to generate Cypher...")
        cypher = self.ask_ollama(prompt, temperature=0.1)

        # Clean up response
        cypher = cypher.strip()

        # Remove markdown code blocks
        if '```' in cypher:
            match = re.search(r'```(?:cypher)?\s*(.*?)\s*```', cypher, re.DOTALL)
            if match:
                cypher = match.group(1).strip()

        # Extract just the query
        lines = []
        for line in cypher.split('\n'):
            line = line.strip()
            if line and not line.startswith('//') and not line.lower().startswith(('explanation', 'note', 'this query')):
                lines.append(line)

        cypher = '\n'.join(lines)

        return cypher

    def execute_cypher(self, cypher: str, retry_on_error=True):
        """Execute Cypher query with self-healing retry"""
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(cypher)
                records = [dict(record) for record in result]
                return records, None
        except Exception as e:
            error_msg = str(e)

            if retry_on_error:
                print(f"⚠️  Query failed: {error_msg}")
                print("🔄 Attempting self-healing retry...")

                # Ask LLM to fix the query
                fix_prompt = f"""The following Cypher query failed with an error. Fix the query.

FAILED QUERY:
{cypher}

ERROR:
{error_msg}

Generate a corrected Cypher query (return ONLY the query, no explanation):"""

                corrected_cypher = self.ask_ollama(fix_prompt, temperature=0.1)

                # Clean up
                corrected_cypher = corrected_cypher.strip()
                if '```' in corrected_cypher:
                    match = re.search(r'```(?:cypher)?\s*(.*?)\s*```', corrected_cypher, re.DOTALL)
                    if match:
                        corrected_cypher = match.group(1).strip()

                print(f"🔧 Corrected query:\n{corrected_cypher}\n")

                # Try again (without retry to avoid infinite loop)
                return self.execute_cypher(corrected_cypher, retry_on_error=False)

            return None, error_msg

    def vector_search(self, query: str, top_k: int = 3):
        """Simple vector search in chunks"""
        query_words = set(query.lower().split())
        scored_chunks = []

        for chunk in self.chunks:
            text_words = set(chunk['text'].lower().split())
            overlap = len(query_words.intersection(text_words))

            if overlap > 0:
                score = overlap / len(query_words)
                scored_chunks.append((score, chunk))

        scored_chunks.sort(reverse=True, key=lambda x: x[0])

        results = []
        for score, chunk in scored_chunks[:top_k]:
            results.append({
                'text': chunk['text'][:300],
                'project': chunk.get('project', 'unknown'),
                'source': chunk.get('source', 'unknown')
            })

        return results

    def ask_question(self, question: str):
        """Answer question using enhanced Text-to-Cypher with entity pre-retrieval"""

        print("\n" + "🎯" * 80)
        print(f"❓ QUESTION: {question}")
        print("🎯" * 80)

        # Step 1: Extract key terms
        print("\n🔍 Step 1: Extracting key terms from question...")
        terms = self.extract_key_terms(question)
        print(f"   Found terms: {terms}")

        # Step 2: Entity pre-retrieval
        print("\n🔍 Step 2: Pre-retrieving matching entities/projects from graph...")
        matches = self.entity_pre_retrieval(terms)
        print(f"   ✅ Found {len(matches['entities'])} entity matches")
        print(f"   ✅ Found {len(matches['projects'])} project matches")

        if matches['entities']:
            print("   Top entities:")
            for e in matches['entities'][:3]:
                print(f"      - {e['name']} (score: {e['score']:.2f})")

        if matches['projects']:
            print("   Top projects:")
            for p in matches['projects'][:3]:
                print(f"      - {p['name'][:60]}... (score: {p['score']:.2f})")

        # Step 3: Generate Cypher with context
        print("\n🔍 Step 3: Generating Cypher query with entity context...")
        cypher = self.generate_cypher_with_context(question, matches)
        print(f"\n📝 Generated Cypher:\n{cypher}\n")

        # Step 4: Execute Cypher
        print("🔍 Step 4: Executing Cypher query...")
        graph_results, error = self.execute_cypher(cypher)

        if graph_results is not None:
            print(f"✅ Query successful: {len(graph_results)} results")
        else:
            print(f"❌ Query failed: {error}")
            graph_results = []

        # Step 5: Vector search for context
        print("\n🔍 Step 5: Vector search for supporting context...")
        vector_results = self.vector_search(question, top_k=3)
        print(f"✅ Retrieved {len(vector_results)} document chunks")

        # Step 6: Generate final answer
        print(f"\n🔍 Step 6: Generating comprehensive answer with {self.ollama_model}...")

        # Build context
        context_parts = []

        if graph_results:
            context_parts.append("KNOWLEDGE GRAPH RESULTS:")
            context_parts.append(f"Query: {cypher}")
            context_parts.append(f"Results: {json.dumps(graph_results, indent=2)}")

        if vector_results:
            context_parts.append("\nDOCUMENT CONTEXT:")
            for i, result in enumerate(vector_results, 1):
                context_parts.append(f"\n[Source {i}] {result['project']}")
                context_parts.append(result['text'])

        context_text = "\n".join(context_parts)

        answer_prompt = f"""You are an expert in HVDC and SYNCON power systems. Answer the question using the provided context.

CONTEXT:
{context_text}

QUESTION: {question}

Provide a clear, concise answer that:
1. Uses the graph query results as primary facts
2. Enhances with document context if relevant
3. States numbers/counts clearly if applicable
4. Handles missing data gracefully

ANSWER:"""

        answer = self.ask_ollama(answer_prompt)

        # Display results
        print("\n" + "🚀" * 80)
        print(f"SMART CYPHER GRAPHRAG ANSWER:")
        print("🚀" * 80)
        print(answer)

        if graph_results:
            print("\n" + "📊" * 80)
            print("GRAPH QUERY RESULTS:")
            print(f"Cypher: {cypher}")
            print(f"\nResults ({len(graph_results)} records):")
            for i, record in enumerate(graph_results[:10], 1):
                print(f"{i}. {record}")
            print("📊" * 80)


def main():
    parser = argparse.ArgumentParser(description="Smart Cypher GraphRAG with Entity Pre-Retrieval")
    parser.add_argument('--query', type=str, help='Question to ask')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--model', type=str, default='mistral',
                       help='Ollama model (llama3, mistral, etc.)')

    args = parser.parse_args()

    print("\n" + "🚀" * 80)
    print("SMART CYPHER GRAPHRAG SYSTEM")
    print("Entity Pre-Retrieval + Few-Shot Learning + Self-Healing")
    print("Based on: Neo4j Text2Cypher, LangChain, Microsoft GraphRAG")
    print("🚀" * 80)

    try:
        graphrag = SmartCypherGraphRAG(ollama_model=args.model)

        if args.query:
            graphrag.ask_question(args.query)
        elif args.interactive:
            print("\n🎯 Interactive Smart Cypher GraphRAG")
            print("Ask questions - I'll search the graph first, then generate queries!")
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
            print("\n💡 Usage:")
            print("python ollama_smart_cypher_graphrag.py --query 'How many projects with TenneT?' --model mistral")
            print("python ollama_smart_cypher_graphrag.py --interactive --model mistral")

        graphrag.neo4j_driver.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
