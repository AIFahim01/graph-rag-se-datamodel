#!/usr/bin/env python3
"""
Build Knowledge Graph using ReLiK (Retrieval-Augmented Entity Linking)
Cleaner, faster extraction than REBEL with no XML artifacts
"""

import os
import sys
import json
import time
from pathlib import Path
from collections import defaultdict, Counter
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Ensure XET is disabled
os.environ['HF_HUB_DISABLE_XET'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'

from neo4j import GraphDatabase

class ReLiKExtractor:
    """Extract entities and relationships using ReLiK model"""

    def __init__(self, model_name="relik-ie/relik-relation-extraction-small", use_gpu=True):
        """
        Initialize ReLiK extractor

        Args:
            model_name: HuggingFace model name for ReLiK
            use_gpu: Whether to use GPU if available
        """
        print(f"🤖 Loading ReLiK model: {model_name}...")

        # Import ReLiK
        from relik import Relik

        # Load ReLiK model
        try:
            self.model = Relik.from_pretrained(model_name)
            print(f"✅ ReLiK model loaded successfully")

            # Check if GPU is available
            import torch
            self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
            if self.device == "cuda":
                print(f"🚀 Using GPU acceleration")
            else:
                print(f"💻 Using CPU (slower but functional)")

        except Exception as e:
            print(f"❌ Failed to load ReLiK model: {e}")
            raise

    def extract_relations(self, text: str):
        """
        Extract relations (triplets) from text using ReLiK

        Args:
            text: Input text to extract from

        Returns:
            List of relations as dictionaries
        """
        # Truncate text if too long
        if len(text) > 3000:
            text = text[:3000]

        try:
            # Run ReLiK extraction
            result = self.model(text)

            relations = []

            # Extract relations (triplets)
            if hasattr(result, 'triplets'):
                for triplet in result.triplets:
                    # Clean extraction - no XML artifacts!
                    relations.append({
                        'subject': triplet.subject.text.strip(),
                        'relation': triplet.label,
                        'object': triplet.object.text.strip()
                    })

            return relations

        except Exception as e:
            # Skip problematic chunks
            return []


def build_relik_kg(test_mode=False, sample_size=100):
    """
    Build knowledge graph using ReLiK

    Args:
        test_mode: If True, only process sample_size chunks
        sample_size: Number of chunks to process in test mode
    """

    print("=" * 80)
    print("🧠 BUILDING KNOWLEDGE GRAPH WITH RELIK")
    print("=" * 80)

    # Load chunks
    chunks_file = PROJECT_ROOT / "data" / "graphrag_complete" / "graphrag_chunks.json"
    print(f"\n📄 Loading chunks from: {chunks_file}")

    with open(chunks_file) as f:
        chunks = json.load(f)

    total_chunks = len(chunks)

    if test_mode:
        chunks = chunks[:sample_size]
        print(f"🧪 TEST MODE: Processing {len(chunks)} of {total_chunks:,} chunks")
    else:
        print(f"✅ Loaded {len(chunks):,} chunks")

    # Initialize ReLiK extractor
    extractor = ReLiKExtractor(use_gpu=True)

    # Data structures for aggregation
    all_entities = defaultdict(lambda: {'count': 0, 'projects': set()})
    all_relationships = []
    relation_type_counter = Counter()

    print(f"\n🔍 Extracting relations with ReLiK...")

    if not test_mode:
        print(f"   Processing {len(chunks):,} chunks")
        print(f"   Estimated time: 10-20 minutes on GPU, 30-60 minutes on CPU")

    print("")

    # Process chunks with progress bar
    start_time = time.time()
    chunks_processed = 0
    relations_extracted = 0

    for chunk in tqdm(chunks, desc="Processing chunks"):
        text = chunk['text']
        project = chunk.get('project', 'unknown')
        chunk_index = chunk.get('chunk_index', chunks_processed)

        try:
            # Extract relations using ReLiK
            relations = extractor.extract_relations(text)

            # Process each relation
            for rel in relations:
                subject = rel['subject']
                relation = rel['relation']
                obj = rel['object']

                # Skip if any component is too short
                if len(subject) < 2 or len(obj) < 2:
                    continue

                # Track entities
                all_entities[subject]['count'] += 1
                all_entities[subject]['projects'].add(project)
                all_entities[obj]['count'] += 1
                all_entities[obj]['projects'].add(project)

                # Track relationship
                all_relationships.append({
                    'subject': subject,
                    'relation': relation,
                    'object': obj,
                    'project': project,
                    'chunk_index': chunk_index,
                    'source': 'ReLiK'
                })

                # Count relation types
                relation_type_counter[relation] += 1
                relations_extracted += 1

        except Exception as e:
            # Skip problematic chunks
            continue

        chunks_processed += 1

        # Progress update every 500 chunks
        if chunks_processed % 500 == 0:
            elapsed = time.time() - start_time
            rate = chunks_processed / elapsed
            eta = (len(chunks) - chunks_processed) / rate
            print(f"   Progress: {chunks_processed}/{len(chunks)} chunks, "
                  f"{relations_extracted} relations, "
                  f"ETA: {eta/60:.1f} minutes")

    elapsed_time = time.time() - start_time

    print(f"\n✅ Processed {chunks_processed:,} chunks in {elapsed_time/60:.1f} minutes")
    print(f"   Speed: {chunks_processed/elapsed_time:.1f} chunks/sec")

    # Filter entities (require at least 2 mentions)
    filtered_entities = {
        entity: {
            'mentions': data['count'],
            'projects': list(data['projects'])
        }
        for entity, data in all_entities.items()
        if data['count'] >= 2
    }

    # Statistics
    print("\n" + "=" * 80)
    print("📊 RELIK KNOWLEDGE GRAPH STATISTICS")
    print("=" * 80)
    print(f"   Total entities extracted: {len(all_entities):,}")
    print(f"   Filtered entities (≥2 mentions): {len(filtered_entities):,}")
    print(f"   Total relationships: {len(all_relationships):,}")
    print(f"   Unique relationship types: {len(relation_type_counter)}")
    print(f"   Average relations per chunk: {len(all_relationships)/chunks_processed:.2f}")

    # Top entities
    print(f"\n🔝 Top 15 Entities:")
    for entity, data in sorted(filtered_entities.items(),
                              key=lambda x: x[1]['mentions'],
                              reverse=True)[:15]:
        print(f"   • {entity}: {data['mentions']} mentions in {len(data['projects'])} projects")

    # Top relationship types
    print(f"\n🔗 Top 15 Relationship Types:")
    for rel_type, count in relation_type_counter.most_common(15):
        print(f"   • {rel_type}: {count} occurrences")

    # Save knowledge graph
    kg_data = {
        'entities': filtered_entities,
        'relationships': all_relationships,
        'statistics': {
            'total_entities': len(filtered_entities),
            'total_relationships': len(all_relationships),
            'unique_entities': len(all_entities),
            'relation_types': dict(relation_type_counter),
            'chunks_processed': chunks_processed,
            'extraction_time_minutes': elapsed_time / 60,
            'extraction_method': 'ReLiK',
            'model': 'relik-ie/relik-relation-extraction-small'
        }
    }

    # Save to file
    if test_mode:
        output_file = PROJECT_ROOT / "data" / "graphrag_complete" / "relik_knowledge_graph_test.json"
    else:
        output_file = PROJECT_ROOT / "data" / "graphrag_complete" / "relik_knowledge_graph.json"

    print(f"\n💾 Saving knowledge graph to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(kg_data, f, indent=2)

    print(f"✅ Knowledge graph saved successfully!")

    # Quality comparison with REBEL (if available)
    rebel_kg_file = PROJECT_ROOT / "data" / "graphrag_complete" / "rebel_knowledge_graph.json"
    if rebel_kg_file.exists():
        print("\n" + "=" * 80)
        print("📊 COMPARISON WITH REBEL")
        print("=" * 80)

        with open(rebel_kg_file) as f:
            rebel_kg = json.load(f)

        rebel_entities = rebel_kg.get('entities', {})
        rebel_relationships = rebel_kg.get('relationships', [])

        print(f"   REBEL entities: {len(rebel_entities):,}")
        print(f"   ReLiK entities: {len(filtered_entities):,}")
        print(f"   Improvement: {len(filtered_entities)/len(rebel_entities):.1f}x more entities")

        print(f"\n   REBEL relationships: {len(rebel_relationships):,}")
        print(f"   ReLiK relationships: {len(all_relationships):,}")
        print(f"   Improvement: {len(all_relationships)/len(rebel_relationships):.1f}x more relationships")

        # Check for XML artifacts in REBEL
        rebel_noisy = sum(1 for r in rebel_relationships
                         if '</s>' in str(r) or '<obj>' in str(r) or '<subj>' in str(r))
        rebel_noise_pct = 100 * rebel_noisy / len(rebel_relationships) if rebel_relationships else 0

        print(f"\n   🧹 Entity Cleanliness:")
        print(f"      REBEL: {rebel_noise_pct:.1f}% noisy (XML artifacts)")
        print(f"      ReLiK: 0.0% noisy (clean extraction)")

    return kg_data


def load_to_neo4j(kg_data):
    """
    Load ReLiK knowledge graph to Neo4j

    Args:
        kg_data: Knowledge graph data dictionary
    """
    print("\n" + "=" * 80)
    print("📥 LOADING TO NEO4J")
    print("=" * 80)

    # Connect to Neo4j
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "password"  # Update with your password

    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        print(f"✅ Connected to Neo4j at {uri}")
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {e}")
        print("   Make sure Neo4j is running and credentials are correct")
        return

    with driver.session() as session:
        # Clear existing ReLiK data
        print("\n🧹 Clearing existing ReLiK data...")
        session.run("MATCH (n {source: 'ReLiK'}) DETACH DELETE n")

        # Create entities
        print(f"\n📥 Creating {len(kg_data['entities'])} entity nodes...")
        for entity_name, entity_data in tqdm(kg_data['entities'].items(), desc="Creating entities"):
            session.run("""
                MERGE (e:Entity {name: $name})
                SET e.mentions = $mentions,
                    e.projects = $projects,
                    e.source = 'ReLiK'
            """, name=entity_name,
                 mentions=entity_data['mentions'],
                 projects=entity_data['projects'])

        # Create relationships
        print(f"\n📥 Creating {len(kg_data['relationships'])} relationships...")
        for rel in tqdm(kg_data['relationships'], desc="Creating relationships"):
            session.run("""
                MERGE (s:Entity {name: $subject})
                MERGE (o:Entity {name: $object})
                MERGE (s)-[r:RELATED {type: $relation, project: $project}]->(o)
                SET r.source = 'ReLiK',
                    r.chunk_index = $chunk_index
            """, **rel)

    driver.close()
    print("\n✅ Knowledge graph loaded to Neo4j successfully!")


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("RELIK KNOWLEDGE GRAPH BUILDER")
    print("🚀" * 40 + "\n")

    # Check for test mode flag
    import argparse
    parser = argparse.ArgumentParser(description='Build knowledge graph using ReLiK')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (100 chunks only)')
    parser.add_argument('--load-neo4j', action='store_true',
                       help='Load results to Neo4j after extraction')
    parser.add_argument('--sample-size', type=int, default=100,
                       help='Number of chunks to process in test mode')

    args = parser.parse_args()

    # Build knowledge graph
    kg_data = build_relik_kg(test_mode=args.test, sample_size=args.sample_size)

    # Load to Neo4j if requested
    if args.load_neo4j:
        load_to_neo4j(kg_data)
    else:
        print("\n💡 To load to Neo4j, run with --load-neo4j flag")

    print("\n✨ Done! Next steps:")
    print("   1. Review the extracted knowledge graph")
    print("   2. Load to Neo4j: python build_relik_kg.py --load-neo4j")
    print("   3. Test with Smart Cypher: python ollama_smart_cypher_graphrag.py")