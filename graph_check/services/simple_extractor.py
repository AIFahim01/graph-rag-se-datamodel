"""
Simple Entity Extractor (Fallback - no ReLiK required)
Uses basic pattern matching to extract entities and relations
"""

import json
import time
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
from collections import defaultdict, Counter
import re


class SimpleExtractor:
    """Simple entity extraction without ReLiK dependency"""

    def __init__(self):
        """Initialize simple extractor"""
        print(f"🤖 Initializing Simple Extractor (no ReLiK required)...")
        print(f"   Using basic pattern matching")

    def extract_from_chunk(self, chunk: Dict) -> Dict:
        """
        Extract entities and relations from a single chunk using patterns

        Args:
            chunk: Chunk dictionary with 'text' field

        Returns:
            Dictionary with extracted entities and relations
        """
        text = chunk.get('text', '')
        chunk_id = chunk.get('chunk_id', 'unknown')
        project_type = chunk.get('project_type', 'unknown')
        project_id = chunk.get('project_id', 'unknown')

        entities = []
        relations = []

        # Extract simple entities based on patterns
        # Numbers with units
        voltage_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(kV|MW|MVA|Hz)', text, re.IGNORECASE)
        for value, unit in voltage_matches:
            entities.append({
                'text': f"{value} {unit}",
                'label': 'Measurement',
                'start': 0,
                'end': 0
            })

        # Project-specific entities
        if project_type != 'unknown':
            entities.append({
                'text': project_type,
                'label': 'ProjectType',
                'start': 0,
                'end': 0
            })

        if project_id != 'unknown':
            entities.append({
                'text': project_id,
                'label': 'ProjectID',
                'start': 0,
                'end': 0
            })

        # Create simple relations
        if len(entities) >= 2:
            relations.append({
                'subject': entities[0]['text'],
                'relation': 'belongs_to',
                'object': project_id,
                'confidence': 1.0
            })

        return {
            'chunk_id': chunk_id,
            'project_id': project_id,
            'project_type': project_type,
            'entities': entities,
            'relations': relations,
            'text_length': len(text)
        }

    def process_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Process multiple chunks

        Args:
            chunks: List of chunk dictionaries

        Returns:
            List of extraction results
        """
        print(f"\n🔍 Extracting entities from {len(chunks)} chunks...")
        print(f"   Using simple pattern matching")

        results = []
        start_time = time.time()

        for chunk in tqdm(chunks, desc="Extracting"):
            result = self.extract_from_chunk(chunk)
            results.append(result)

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
