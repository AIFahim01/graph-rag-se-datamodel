"""
ReLiK Entity and Relationship Extractor
"""

import json
import time
import torch
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
from collections import defaultdict, Counter


class RelikExtractor:
    """Extract entities and relationships using ReLiK"""

    def __init__(self, model_name: str = "relik-ie/relik-relation-extraction-small",
                 batch_size: int = 8, use_gpu: bool = True):
        """
        Initialize ReLiK extractor

        Args:
            model_name: HuggingFace model name
            batch_size: Batch size for processing
            use_gpu: Use GPU if available
        """
        print(f"🤖 Initializing ReLiK Extractor...")
        print(f"   Model: {model_name}")

        from relik import Relik

        # Setup device
        self.device = self._setup_gpu(use_gpu)
        self.batch_size = batch_size

        # Load model
        print(f"📥 Loading ReLiK model...")
        self.model = Relik.from_pretrained(model_name)
        print(f"✅ Model loaded on {self.device}")

    def _setup_gpu(self, use_gpu: bool) -> str:
        """Setup GPU if available"""
        if not use_gpu or not torch.cuda.is_available():
            return "cpu"

        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"🎮 GPU: {gpu_name} ({gpu_memory:.2f} GB)")
        torch.cuda.empty_cache()
        return "cuda"

    def extract_from_chunk(self, chunk: Dict) -> Dict:
        """
        Extract entities and relations from a single chunk

        Args:
            chunk: Chunk dictionary with 'text' field

        Returns:
            Dictionary with extracted entities and relations
        """
        text = chunk.get('text', '')
        chunk_id = chunk.get('chunk_id', 'unknown')

        # Truncate if too long
        if len(text) > 3000:
            text = text[:3000]

        try:
            # Run ReLiK extraction
            with torch.cuda.amp.autocast(enabled=(self.device == "cuda")):
                result = self.model(text)

            entities = []
            relations = []

            # Extract entities
            if hasattr(result, 'entities'):
                for entity in result.entities:
                    entities.append({
                        'text': entity.text.strip(),
                        'label': getattr(entity, 'label', 'Entity'),
                        'start': getattr(entity, 'start', 0),
                        'end': getattr(entity, 'end', 0)
                    })

            # Extract relations (triplets)
            if hasattr(result, 'triplets'):
                for triplet in result.triplets:
                    relations.append({
                        'subject': triplet.subject.text.strip(),
                        'relation': triplet.label,
                        'object': triplet.object.text.strip(),
                        'confidence': getattr(triplet, 'confidence', 1.0)
                    })

            return {
                'chunk_id': chunk_id,
                'project_id': chunk.get('project_id', 'unknown'),
                'project_type': chunk.get('project_type', 'unknown'),
                'entities': entities,
                'relations': relations,
                'text_length': len(text)
            }

        except Exception as e:
            print(f"⚠️  Error processing chunk {chunk_id}: {e}")
            return {
                'chunk_id': chunk_id,
                'entities': [],
                'relations': [],
                'error': str(e)
            }

    def process_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Process multiple chunks

        Args:
            chunks: List of chunk dictionaries

        Returns:
            List of extraction results
        """
        print(f"\n🔍 Extracting entities and relations from {len(chunks)} chunks...")
        print(f"   Device: {self.device}")
        print(f"   Batch size: {self.batch_size}")

        results = []
        start_time = time.time()

        for chunk in tqdm(chunks, desc="Extracting"):
            result = self.extract_from_chunk(chunk)
            results.append(result)

            # Clear GPU cache periodically
            if self.device == "cuda" and len(results) % 50 == 0:
                torch.cuda.empty_cache()

        elapsed_time = time.time() - start_time

        # Statistics
        total_entities = sum(len(r['entities']) for r in results)
        total_relations = sum(len(r['relations']) for r in results)

        print(f"\n✅ Extraction complete!")
        print(f"   Time: {elapsed_time:.1f} seconds")
        print(f"   Speed: {len(chunks)/elapsed_time:.2f} chunks/sec")
        print(f"   Entities: {total_entities}")
        print(f"   Relations: {total_relations}")

        return results

    def build_knowledge_graph(self, extraction_results: List[Dict]) -> Dict:
        """
        Build knowledge graph from extraction results

        Args:
            extraction_results: List of extraction results

        Returns:
            Knowledge graph dictionary
        """
        print(f"\n📊 Building knowledge graph...")

        entity_index = defaultdict(list)
        relation_type_stats = Counter()
        project_stats = defaultdict(lambda: {
            'chunks': 0,
            'entities': 0,
            'relations': 0
        })

        for result in extraction_results:
            project_type = result.get('project_type', 'unknown')
            project_stats[project_type]['chunks'] += 1

            # Index entities
            for entity in result['entities']:
                entity_text = entity['text']
                entity_index[entity_text].append(result['chunk_id'])
                project_stats[project_type]['entities'] += 1

            # Count relation types
            for relation in result['relations']:
                relation_type_stats[relation['relation']] += 1
                project_stats[project_type]['relations'] += 1

        # Build graph
        knowledge_graph = {
            'metadata': {
                'total_chunks': len(extraction_results),
                'total_entities': sum(len(r['entities']) for r in extraction_results),
                'unique_entities': len(entity_index),
                'total_relations': sum(len(r['relations']) for r in extraction_results),
                'unique_relation_types': len(relation_type_stats)
            },
            'statistics': {
                'relation_types': dict(relation_type_stats.most_common(20)),
                'projects': dict(project_stats)
            },
            'entity_index': dict(entity_index),
            'extraction_results': extraction_results
        }

        print(f"✅ Knowledge graph built!")
        print(f"   Unique entities: {knowledge_graph['metadata']['unique_entities']}")
        print(f"   Total relations: {knowledge_graph['metadata']['total_relations']}")

        return knowledge_graph

    def save_knowledge_graph(self, kg: Dict, output_file: Path):
        """Save knowledge graph to JSON"""
        print(f"\n💾 Saving knowledge graph to: {output_file}")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(kg, f, indent=2, ensure_ascii=False)

        print(f"✅ Knowledge graph saved!")


def main():
    """Test the extractor"""
    from config import CHUNKS_FILE, KNOWLEDGE_GRAPH_FILE, RELIK_MODEL, BATCH_SIZE, USE_GPU

    # Load chunks
    print(f"📄 Loading chunks from: {CHUNKS_FILE}")
    with open(CHUNKS_FILE, 'r') as f:
        chunks = json.load(f)

    # Sample mode for testing
    chunks = chunks[:10]
    print(f"🧪 Testing with {len(chunks)} chunks")

    # Extract
    extractor = RelikExtractor(
        model_name=RELIK_MODEL,
        batch_size=BATCH_SIZE,
        use_gpu=USE_GPU
    )

    results = extractor.process_chunks(chunks)
    kg = extractor.build_knowledge_graph(results)
    extractor.save_knowledge_graph(kg, KNOWLEDGE_GRAPH_FILE)


if __name__ == "__main__":
    main()
