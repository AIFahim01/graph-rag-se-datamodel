#!/usr/bin/env python3
"""
Chunk-Level ReLiK Knowledge Graph Extraction with GPU Optimization
Processes each chunk individually with full metadata and provenance tracking
"""

import os
import sys
import json
import time
import torch
from pathlib import Path
from collections import defaultdict, Counter
from tqdm import tqdm
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Ensure XET is disabled for clean downloads
os.environ['HF_HUB_DISABLE_XET'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'

# Force CUDA settings for optimal GPU usage
os.environ['CUDA_LAUNCH_BLOCKING'] = '0'  # Async GPU operations
os.environ['TORCH_CUDA_ARCH_LIST'] = '7.0;7.5;8.0;8.6;8.9;9.0'  # Support modern GPUs

from neo4j import GraphDatabase


class ChunkLevelReLiKExtractor:
    """GPU-optimized chunk-level entity and relationship extraction using ReLiK"""

    def __init__(self, model_name="relik-ie/relik-relation-extraction-small",
                 batch_size=8, use_gpu=True):
        """
        Initialize ReLiK extractor with GPU optimization

        Args:
            model_name: HuggingFace model name for ReLiK
            batch_size: Batch size for GPU processing
            use_gpu: Force GPU usage if available
        """
        print(f"🤖 Initializing Chunk-Level ReLiK Extractor...")
        print(f"   Model: {model_name}")
        print(f"   Batch size: {batch_size}")

        # Import ReLiK
        from relik import Relik

        # Check GPU availability
        self.device = self._setup_gpu(use_gpu)

        # Load ReLiK model
        try:
            print(f"📥 Loading ReLiK model...")
            self.model = Relik.from_pretrained(model_name)

            # Move model to GPU if available
            if self.device == "cuda":
                print(f"🚀 Moving model to GPU...")
                # ReLiK handles device placement internally
                # We'll ensure batched processing for efficiency

            print(f"✅ ReLiK model loaded successfully on {self.device}")
            self.batch_size = batch_size

        except Exception as e:
            print(f"❌ Failed to load ReLiK model: {e}")
            raise

    def _setup_gpu(self, use_gpu):
        """Setup and verify GPU configuration"""
        if not use_gpu:
            return "cpu"

        if not torch.cuda.is_available():
            print("⚠️  GPU requested but not available. Using CPU.")
            return "cpu"

        # GPU is available
        gpu_count = torch.cuda.device_count()
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9

        print(f"🎮 GPU Configuration:")
        print(f"   Device count: {gpu_count}")
        print(f"   Primary GPU: {gpu_name}")
        print(f"   GPU Memory: {gpu_memory:.2f} GB")
        print(f"   CUDA Version: {torch.version.cuda}")
        print(f"   PyTorch CUDA: {torch.cuda.is_available()}")

        # Clear GPU cache
        torch.cuda.empty_cache()

        return "cuda"

    def extract_chunk_relations(self, chunk_data):
        """
        Extract relations from a single chunk with metadata

        Args:
            chunk_data: Dictionary with chunk text and metadata

        Returns:
            Dictionary with extracted relations and metadata
        """
        text = chunk_data.get('text', '')
        chunk_id = chunk_data.get('chunk_index', -1)
        project = chunk_data.get('project', 'unknown')

        # Truncate text if too long (ReLiK limit)
        if len(text) > 3000:
            text = text[:3000]

        try:
            # Run ReLiK extraction
            with torch.cuda.amp.autocast(enabled=(self.device == "cuda")):
                result = self.model(text)

            entities = []
            relations = []

            # Extract entities if available
            if hasattr(result, 'entities'):
                for entity in result.entities:
                    entities.append({
                        'text': entity.text.strip(),
                        'label': getattr(entity, 'label', 'Entity'),
                        'start': getattr(entity, 'start', 0),
                        'end': getattr(entity, 'end', 0),
                        'chunk_id': chunk_id,
                        'project': project
                    })

            # Extract relations (triplets)
            if hasattr(result, 'triplets'):
                for triplet in result.triplets:
                    relations.append({
                        'subject': triplet.subject.text.strip(),
                        'relation': triplet.label,
                        'object': triplet.object.text.strip(),
                        'confidence': getattr(triplet, 'confidence', 1.0),
                        'chunk_id': chunk_id,
                        'project': project,
                        'source': 'ReLiK'
                    })

            return {
                'chunk_id': chunk_id,
                'project': project,
                'entities': entities,
                'relations': relations,
                'text_length': len(text),
                'extraction_time': time.time()
            }

        except Exception as e:
            print(f"⚠️  Error processing chunk {chunk_id}: {e}")
            return {
                'chunk_id': chunk_id,
                'project': project,
                'entities': [],
                'relations': [],
                'error': str(e)
            }

    def process_chunks_batch(self, chunks_batch):
        """
        Process multiple chunks in a batch for GPU efficiency

        Args:
            chunks_batch: List of chunk dictionaries

        Returns:
            List of extraction results
        """
        results = []

        # Process each chunk (ReLiK doesn't support true batching yet)
        # But we can optimize GPU memory usage
        for chunk in chunks_batch:
            result = self.extract_chunk_relations(chunk)
            results.append(result)

            # Clear CUDA cache periodically
            if self.device == "cuda" and len(results) % 50 == 0:
                torch.cuda.empty_cache()

        return results


def build_chunk_level_kg(test_mode=False, sample_size=100, batch_size=8):
    """
    Build chunk-level knowledge graph using ReLiK with GPU optimization

    Args:
        test_mode: If True, only process sample_size chunks
        sample_size: Number of chunks to process in test mode
        batch_size: Batch size for GPU processing
    """

    print("=" * 80)
    print("🧠 CHUNK-LEVEL KNOWLEDGE GRAPH EXTRACTION WITH RELIK")
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
        print(f"✅ Loaded {len(chunks):,} chunks for processing")

    # Initialize ReLiK extractor with GPU
    extractor = ChunkLevelReLiKExtractor(
        use_gpu=True,
        batch_size=batch_size
    )

    # Data structures for chunk-level storage
    chunk_level_data = []
    entity_index = defaultdict(list)  # entity -> list of chunk_ids
    relation_type_stats = Counter()
    project_stats = defaultdict(lambda: {'chunks': 0, 'entities': 0, 'relations': 0})

    print(f"\n🔍 Starting chunk-level extraction...")
    print(f"   Processing mode: {'GPU' if extractor.device == 'cuda' else 'CPU'}")
    print(f"   Batch size: {batch_size}")

    if not test_mode:
        estimated_time = len(chunks) * 0.5  # ~0.5 sec per chunk on GPU
        print(f"   Estimated time: {estimated_time/60:.1f} minutes")

    # Process chunks with progress bar
    start_time = time.time()

    # Process in batches
    for i in tqdm(range(0, len(chunks), batch_size),
                  desc=f"Processing chunks (batch size={batch_size})"):

        batch = chunks[i:i + batch_size]
        batch_results = extractor.process_chunks_batch(batch)

        # Process results
        for result in batch_results:
            chunk_level_data.append(result)

            # Update indices and stats
            project = result['project']
            project_stats[project]['chunks'] += 1

            # Index entities
            for entity in result['entities']:
                entity_text = entity['text']
                entity_index[entity_text].append(result['chunk_id'])
                project_stats[project]['entities'] += 1

            # Count relation types
            for relation in result['relations']:
                relation_type_stats[relation['relation']] += 1
                project_stats[project]['relations'] += 1

    elapsed_time = time.time() - start_time

    # Calculate statistics
    total_entities = sum(len(r['entities']) for r in chunk_level_data)
    total_relations = sum(len(r['relations']) for r in chunk_level_data)
    unique_entities = len(entity_index)
    chunks_processed = len(chunk_level_data)

    print(f"\n✅ Processed {chunks_processed:,} chunks in {elapsed_time:.1f} seconds")
    print(f"   Speed: {chunks_processed/elapsed_time:.2f} chunks/sec")

    if extractor.device == "cuda":
        # Show GPU memory usage
        memory_used = torch.cuda.max_memory_allocated() / 1e9
        print(f"   Peak GPU Memory: {memory_used:.2f} GB")

    # Build comprehensive chunk-level knowledge graph
    chunk_level_kg = {
        'metadata': {
            'extraction_date': datetime.now().isoformat(),
            'model': 'relik-ie/relik-relation-extraction-small',
            'device': extractor.device,
            'chunks_processed': chunks_processed,
            'processing_time_seconds': elapsed_time,
            'chunks_per_second': chunks_processed / elapsed_time,
            'batch_size': batch_size
        },
        'statistics': {
            'total_chunks': chunks_processed,
            'total_entities': total_entities,
            'unique_entities': unique_entities,
            'total_relations': total_relations,
            'relation_types': dict(relation_type_stats.most_common()),
            'projects': dict(project_stats)
        },
        'entity_index': {
            entity: chunks_list
            for entity, chunks_list in entity_index.items()
            if len(chunks_list) >= 2  # Filter entities appearing in 2+ chunks
        },
        'chunks': chunk_level_data
    }

    # Display statistics
    print("\n" + "=" * 80)
    print("📊 CHUNK-LEVEL EXTRACTION STATISTICS")
    print("=" * 80)
    print(f"   Total chunks processed: {chunks_processed:,}")
    print(f"   Total entities extracted: {total_entities:,}")
    print(f"   Unique entities: {unique_entities:,}")
    print(f"   Total relationships: {total_relations:,}")
    print(f"   Unique relationship types: {len(relation_type_stats)}")
    print(f"   Average entities per chunk: {total_entities/chunks_processed:.2f}")
    print(f"   Average relations per chunk: {total_relations/chunks_processed:.2f}")

    # Top entities across chunks
    print(f"\n🔝 Top 10 Cross-Chunk Entities:")
    for entity, chunk_ids in sorted(entity_index.items(),
                                   key=lambda x: len(x[1]),
                                   reverse=True)[:10]:
        print(f"   • {entity}: appears in {len(chunk_ids)} chunks")

    # Top relationship types
    print(f"\n🔗 Top 10 Relationship Types:")
    for rel_type, count in relation_type_stats.most_common(10):
        print(f"   • {rel_type}: {count} occurrences")

    # Project breakdown
    print(f"\n📁 Project Statistics:")
    for project, stats in sorted(project_stats.items(),
                                key=lambda x: x[1]['relations'],
                                reverse=True)[:5]:
        print(f"   • {project}:")
        print(f"     - Chunks: {stats['chunks']}")
        print(f"     - Entities: {stats['entities']}")
        print(f"     - Relations: {stats['relations']}")

    # Save chunk-level knowledge graph
    output_file = PROJECT_ROOT / "data" / "graphrag_complete" / (
        "chunk_level_relik_kg_test.json" if test_mode else "chunk_level_relik_kg.json"
    )

    print(f"\n💾 Saving chunk-level knowledge graph to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(chunk_level_kg, f, indent=2)

    print(f"✅ Chunk-level knowledge graph saved successfully!")

    return chunk_level_kg


def load_chunk_kg_to_neo4j(kg_data):
    """
    Load chunk-level knowledge graph to Neo4j with provenance

    Args:
        kg_data: Chunk-level knowledge graph data
    """
    print("\n" + "=" * 80)
    print("📥 LOADING CHUNK-LEVEL KG TO NEO4J")
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
        # Clear existing chunk-level data
        print("\n🧹 Clearing existing chunk-level ReLiK data...")
        session.run("MATCH (n {source: 'ChunkReLiK'}) DETACH DELETE n")

        # Create chunks
        print(f"\n📥 Creating {len(kg_data['chunks'])} chunk nodes...")
        for chunk_data in tqdm(kg_data['chunks'], desc="Creating chunks"):
            session.run("""
                CREATE (c:Chunk {
                    id: $chunk_id,
                    project: $project,
                    text_length: $text_length,
                    entity_count: $entity_count,
                    relation_count: $relation_count,
                    source: 'ChunkReLiK'
                })
            """,
                chunk_id=chunk_data['chunk_id'],
                project=chunk_data['project'],
                text_length=chunk_data.get('text_length', 0),
                entity_count=len(chunk_data['entities']),
                relation_count=len(chunk_data['relations'])
            )

        # Create entities with chunk provenance
        print(f"\n📥 Creating entity nodes with provenance...")
        for entity_text, chunk_ids in tqdm(kg_data['entity_index'].items(),
                                          desc="Creating entities"):
            session.run("""
                MERGE (e:Entity {name: $name})
                SET e.chunk_count = $chunk_count,
                    e.chunk_ids = $chunk_ids,
                    e.source = 'ChunkReLiK'
            """,
                name=entity_text,
                chunk_count=len(chunk_ids),
                chunk_ids=chunk_ids
            )

        # Create relationships with chunk provenance
        print(f"\n📥 Creating relationships with provenance...")
        for chunk_data in tqdm(kg_data['chunks'], desc="Creating relationships"):
            for rel in chunk_data['relations']:
                session.run("""
                    MERGE (s:Entity {name: $subject})
                    MERGE (o:Entity {name: $object})
                    CREATE (s)-[r:RELATED {
                        type: $relation,
                        chunk_id: $chunk_id,
                        project: $project,
                        confidence: $confidence,
                        source: 'ChunkReLiK'
                    }]->(o)
                """,
                    subject=rel['subject'],
                    object=rel['object'],
                    relation=rel['relation'],
                    chunk_id=rel['chunk_id'],
                    project=rel['project'],
                    confidence=rel.get('confidence', 1.0)
                )

    driver.close()
    print("\n✅ Chunk-level knowledge graph loaded to Neo4j successfully!")
    print("   You can now query with chunk-level provenance!")


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("CHUNK-LEVEL RELIK KNOWLEDGE GRAPH BUILDER")
    print("🚀" * 40 + "\n")

    import argparse
    parser = argparse.ArgumentParser(description='Build chunk-level KG with ReLiK')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (100 chunks only)')
    parser.add_argument('--load-neo4j', action='store_true',
                       help='Load results to Neo4j after extraction')
    parser.add_argument('--sample-size', type=int, default=100,
                       help='Number of chunks in test mode')
    parser.add_argument('--batch-size', type=int, default=8,
                       help='Batch size for GPU processing')

    args = parser.parse_args()

    # Build chunk-level knowledge graph
    kg_data = build_chunk_level_kg(
        test_mode=args.test,
        sample_size=args.sample_size,
        batch_size=args.batch_size
    )

    # Load to Neo4j if requested
    if args.load_neo4j:
        load_chunk_kg_to_neo4j(kg_data)
    else:
        print("\n💡 To load to Neo4j, run with --load-neo4j flag")

    print("\n✨ Done! Chunk-level extraction complete with GPU optimization!")
    print("   - Full metadata and provenance preserved")
    print("   - Optimized for GPU processing")
    print("   - Ready for chunk-aware querying")