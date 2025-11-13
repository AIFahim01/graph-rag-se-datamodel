#!/usr/bin/env python3
"""
Build Knowledge Graph using REBEL (Relation Extraction By End-to-end Language generation)

REBEL is a state-of-the-art transformer model that extracts entities and relationships
from text using sequence-to-sequence generation.
"""

import sys
import json
import torch
from pathlib import Path
from collections import defaultdict, Counter
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from neo4j import GraphDatabase

class REBELExtractor:
    """Extract entities and relationships using REBEL model"""

    def __init__(self, use_gpu=True):
        print("🤖 Loading REBEL model...")

        # Load REBEL model
        model_name = "Babelscape/rebel-large"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        # Use GPU if available
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

        print(f"✅ REBEL model loaded on {self.device.upper()}")

    def extract_triplets(self, text: str, max_length=512):
        """Extract (subject, relation, object) triplets using REBEL"""

        # Truncate text if too long
        if len(text) > 3000:
            text = text[:3000]

        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length
        ).to(self.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                inputs['input_ids'],
                max_length=256,
                num_beams=3,
                num_return_sequences=1,
                early_stopping=True
            )

        # Decode
        decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=False)[0]

        # Parse triplets from REBEL output
        triplets = self._parse_rebel_output(decoded)

        return triplets

    def _parse_rebel_output(self, text: str):
        """Parse REBEL model output into triplets"""
        triplets = []

        # REBEL outputs format: <triplet> subject <subj> relation <obj> object <triplet>
        parts = text.split('<triplet>')

        for part in parts:
            if '<subj>' in part and '<obj>' in part:
                try:
                    # Extract subject
                    subj_start = part.find('<subj>') + 6
                    subj_end = part.find('</subj>')
                    subject = part[subj_start:subj_end].strip()

                    # Extract relation
                    rel_start = subj_end + 7  # Skip </subj>
                    rel_end = part.find('<obj>')
                    relation = part[rel_start:rel_end].strip()

                    # Extract object
                    obj_start = rel_end + 5
                    obj_end = part.find('</obj>')
                    obj = part[obj_start:obj_end].strip()

                    if subject and relation and obj:
                        # Clean up special tokens
                        subject = subject.replace('<s>', '').replace('</s>', '').strip()
                        relation = relation.replace('<s>', '').replace('</s>', '').strip()
                        obj = obj.replace('<s>', '').replace('</s>', '').strip()

                        triplets.append({
                            'subject': subject,
                            'relation': relation,
                            'object': obj
                        })
                except Exception as e:
                    continue

        return triplets


def build_rebel_kg():
    """Build knowledge graph using REBEL"""

    print("=" * 80)
    print("🧠 BUILDING KNOWLEDGE GRAPH WITH REBEL")
    print("=" * 80)

    # Load chunks
    chunks_file = PROJECT_ROOT / "data" / "graphrag_complete" / "graphrag_chunks.json"
    print(f"\n📄 Loading chunks from: {chunks_file}")

    with open(chunks_file) as f:
        chunks = json.load(f)

    print(f"✅ Loaded {len(chunks):,} chunks\n")

    # Initialize REBEL extractor
    extractor = REBELExtractor(use_gpu=True)

    # Extract entities and relationships
    all_entities = defaultdict(int)
    all_relationships = []
    project_entities = defaultdict(set)

    print("🔍 Extracting entities and relationships with REBEL...")
    print(f"   Processing chunks (this may take 10-30 minutes with GPU)...\n")

    # Process in batches for better performance
    batch_size = 10
    processed = 0

    for i in tqdm(range(0, len(chunks), batch_size), desc="Processing batches"):
        batch_chunks = chunks[i:i+batch_size]

        for chunk in batch_chunks:
            text = chunk['text']
            project = chunk['project']

            try:
                # Extract triplets with REBEL
                triplets = extractor.extract_triplets(text)

                # Process triplets
                for triplet in triplets:
                    subject = triplet['subject']
                    relation = triplet['relation']
                    obj = triplet['object']

                    # Add entities
                    all_entities[subject] += 1
                    all_entities[obj] += 1

                    # Track project entities
                    project_entities[project].add(subject)
                    project_entities[project].add(obj)

                    # Add relationship
                    all_relationships.append({
                        'subject': subject,
                        'relation': relation,
                        'object': obj,
                        'project': project,
                        'source': 'REBEL'
                    })

                processed += 1

            except Exception as e:
                print(f"⚠️  Error processing chunk {i}: {e}")
                continue

    print(f"\n✅ Processed {processed:,} chunks with REBEL\n")

    # Filter entities (keep those mentioned at least 2 times)
    filtered_entities = {entity: count for entity, count in all_entities.items() if count >= 2}

    # Count relationship types
    relation_types = Counter([r['relation'] for r in all_relationships])

    print("=" * 80)
    print("📊 REBEL KNOWLEDGE GRAPH STATISTICS")
    print("=" * 80)
    print(f"   Total entities extracted: {len(all_entities):,}")
    print(f"   Filtered entities (≥2 mentions): {len(filtered_entities):,}")
    print(f"   Total relationships: {len(all_relationships):,}")
    print(f"   Unique relationship types: {len(relation_types)}")
    print(f"   Projects analyzed: {len(project_entities)}")

    print(f"\n🔝 Top 10 Entities:")
    for entity, count in sorted(filtered_entities.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   • {entity}: {count} mentions")

    print(f"\n🔗 Top 10 Relationship Types:")
    for rel_type, count in relation_types.most_common(10):
        print(f"   • {rel_type}: {count} occurrences")

    # Save knowledge graph
    kg_data = {
        'entities': {
            entity: {
                'mentions': count,
                'projects': [p for p, entities in project_entities.items() if entity in entities]
            }
            for entity, count in filtered_entities.items()
        },
        'relationships': all_relationships,
        'statistics': {
            'total_entities': len(filtered_entities),
            'total_relationships': len(all_relationships),
            'num_projects': len(project_entities),
            'relation_types': dict(relation_types),
            'extraction_method': 'REBEL-large',
            'model': 'Babelscape/rebel-large'
        },
        'projects': list(project_entities.keys())
    }

    # Save to file
    output_file = PROJECT_ROOT / "data" / "graphrag_complete" / "rebel_knowledge_graph.json"
    with open(output_file, 'w') as f:
        json.dump(kg_data, f, indent=2)

    print(f"\n💾 Saved knowledge graph to: {output_file}")

    return kg_data


def load_rebel_kg_to_neo4j(kg_data):
    """Load REBEL knowledge graph into Neo4j"""

    print("\n" + "=" * 80)
    print("📦 LOADING REBEL KNOWLEDGE GRAPH TO NEO4J")
    print("=" * 80)

    # Connect to Neo4j
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "password")
    )

    with driver.session() as session:
        # Clear existing graph
        print("\n🧹 Clearing existing knowledge graph...")
        session.run("MATCH (n) DETACH DELETE n")

        # Create constraints
        print("📋 Creating constraints...")
        session.run("CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")
        session.run("CREATE CONSTRAINT project_name IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE")

        # Load entities
        print(f"\n📥 Loading {len(kg_data['entities'])} entities...")
        for entity, data in tqdm(kg_data['entities'].items(), desc="Entities"):
            session.run("""
                MERGE (e:Entity {name: $name})
                SET e.mentions = $mentions,
                    e.num_projects = $num_projects
            """, name=entity, mentions=data['mentions'], num_projects=len(data['projects']))

        # Load projects
        print(f"\n📥 Loading {len(kg_data['projects'])} projects...")
        for project in tqdm(kg_data['projects'], desc="Projects"):
            session.run("""
                MERGE (p:Project {name: $name})
            """, name=project)

        # Load relationships
        print(f"\n📥 Loading {len(kg_data['relationships'])} relationships...")
        for rel in tqdm(kg_data['relationships'], desc="Relationships"):
            # Create relationship between entities
            session.run("""
                MATCH (s:Entity {name: $subject})
                MATCH (o:Entity {name: $object})
                MERGE (s)-[r:RELATED {type: $relation}]->(o)
                SET r.source = 'REBEL'
            """, subject=rel['subject'], object=rel['object'], relation=rel['relation'])

            # Connect entities to projects
            session.run("""
                MATCH (p:Project {name: $project})
                MATCH (e:Entity {name: $entity})
                MERGE (p)-[:MENTIONS]->(e)
            """, project=rel['project'], entity=rel['subject'])

            session.run("""
                MATCH (p:Project {name: $project})
                MATCH (e:Entity {name: $entity})
                MERGE (p)-[:MENTIONS]->(e)
            """, project=rel['project'], entity=rel['object'])

    driver.close()

    print("\n✅ REBEL knowledge graph loaded to Neo4j successfully!")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("REBEL KNOWLEDGE GRAPH BUILDER")
    print("Using State-of-the-Art NLP for Entity & Relationship Extraction")
    print("🚀" * 40 + "\n")

    # Build knowledge graph with REBEL
    kg_data = build_rebel_kg()

    # Load to Neo4j
    load_rebel_kg_to_neo4j(kg_data)

    print("\n✨ Done! Your GraphRAG system now uses REBEL-extracted knowledge graph!")
    print("\nTest it with:")
    print("python true_graphrag_chat.py --interactive")
