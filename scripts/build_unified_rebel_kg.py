"""
Build Unified Knowledge Graph - Process ALL Chunks Together

Instead of processing each project separately, this processes ALL chunks
from ALL projects together, allowing REBEL to potentially find
cross-project entity relationships directly.

Approach:
1. Extract chunks from ALL projects simultaneously
2. Feed all chunks to REBEL together
3. Track which chunk/project each triplet comes from
4. Find entities that appear in multiple projects
5. Create direct project-to-project connections based on shared entities
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from collections import defaultdict
from tqdm.auto import tqdm
from loguru import logger

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from processing import PDFExtractor, DocumentChunker


def extract_triplets(text: str) -> List[Dict[str, str]]:
    """Parse REBEL model output and extract relation triplets"""
    triplets = []
    relation, subject, object_ = '', '', ''
    text = text.strip()
    current = 'x'

    for token in text.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split():
        if token == "<triplet>":
            current = 't'
            if relation != '':
                triplets.append({
                    'head': subject.strip(),
                    'type': relation.strip(),
                    'tail': object_.strip()
                })
                relation = ''
            subject = ''
        elif token == "<subj>":
            current = 's'
            if relation != '':
                triplets.append({
                    'head': subject.strip(),
                    'type': relation.strip(),
                    'tail': object_.strip()
                })
            object_ = ''
        elif token == "<obj>":
            current = 'o'
            relation = ''
        else:
            if current == 't':
                subject += ' ' + token
            elif current == 's':
                object_ += ' ' + token
            elif current == 'o':
                relation += ' ' + token

    if subject != '' and relation != '' and object_ != '':
        triplets.append({
            'head': subject.strip(),
            'type': relation.strip(),
            'tail': object_.strip()
        })

    return triplets


class UnifiedREBELProcessor:
    """Process all project chunks together to find cross-project relationships"""

    def __init__(self, model_name: str = "Babelscape/rebel-large"):
        logger.info(f"Loading REBEL model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        logger.info(f"Model loaded on device: {self.device}")

        self.gen_kwargs = {
            "max_length": 256,
            "length_penalty": 0,
            "num_beams": 3,
            "num_return_sequences": 1,
        }

        self.pdf_extractor = PDFExtractor()
        self.chunker = DocumentChunker(chunk_size=400, overlap=40)

    def extract_all_chunks_from_all_projects(self, projects_dir: Path) -> List[Dict]:
        """
        Extract chunks from ALL projects together

        Returns:
            List of chunks with project metadata
        """
        all_chunks = []
        project_dirs = [p for p in projects_dir.iterdir() if p.is_dir()]

        logger.info(f"Extracting chunks from {len(project_dirs)} projects...")

        for project_dir in project_dirs:
            project_name = project_dir.name
            pdf_files = list(project_dir.glob("*.pdf"))

            logger.info(f"  Processing {project_name}: {len(pdf_files)} PDFs")

            for pdf_file in pdf_files:
                try:
                    # Extract pages
                    pages = self.pdf_extractor.extract(str(pdf_file))

                    # Chunk pages
                    chunks = self.chunker.chunk_pages(pages)

                    # Add project metadata to each chunk
                    for chunk in chunks:
                        chunk['project'] = project_name
                        chunk['source_pdf'] = pdf_file.name
                        chunk['source_path'] = str(pdf_file)
                        all_chunks.append(chunk)

                except Exception as e:
                    logger.error(f"Failed to process {pdf_file.name}: {e}")

        logger.info(f"✓ Extracted {len(all_chunks)} total chunks from all projects")
        return all_chunks

    def process_chunks_with_rebel(self, chunks: List[Dict], batch_size: int = 4) -> List[Dict]:
        """
        Process all chunks through REBEL

        Args:
            chunks: All chunks from all projects
            batch_size: Batch size for processing

        Returns:
            List of triplets with full metadata
        """
        all_triplets = []

        logger.info(f"Processing {len(chunks)} chunks through REBEL...")

        for i in tqdm(range(0, len(chunks), batch_size), desc="Processing batches"):
            batch_chunks = chunks[i:i + batch_size]
            batch_texts = [c['text'] for c in batch_chunks]

            # Tokenize and generate
            model_inputs = self.tokenizer(
                batch_texts,
                max_length=512,
                padding=True,
                truncation=True,
                return_tensors='pt'
            )
            model_inputs = {k: v.to(self.device) for k, v in model_inputs.items()}

            generated_tokens = self.model.generate(
                model_inputs["input_ids"],
                attention_mask=model_inputs["attention_mask"],
                **self.gen_kwargs
            )

            decoded_preds = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=False)

            # Extract triplets with metadata
            for idx, sentence in enumerate(decoded_preds):
                chunk_data = batch_chunks[idx]
                triplet_dicts = extract_triplets(sentence)

                for t in triplet_dicts:
                    all_triplets.append({
                        'head': t['head'],
                        'relation': t['type'],
                        'tail': t['tail'],
                        'project': chunk_data['project'],
                        'source_pdf': chunk_data['source_pdf'],
                        'page_number': chunk_data['page'],
                        'chunk_id': chunk_data['chunk_id'],
                        'source_text': chunk_data['text'][:200] + '...'
                    })

        logger.info(f"✓ Extracted {len(all_triplets)} total triplets")
        return all_triplets

    def find_cross_project_connections(self, triplets: List[Dict]) -> Dict:
        """
        Find entities that appear in multiple projects and create connections

        Args:
            triplets: All triplets from all projects

        Returns:
            Cross-project analysis results
        """
        # Track entities by project
        entity_to_projects = defaultdict(set)
        entity_to_triplets = defaultdict(list)

        for triplet in triplets:
            entity_to_projects[triplet['head']].add(triplet['project'])
            entity_to_projects[triplet['tail']].add(triplet['project'])
            entity_to_triplets[triplet['head']].append(triplet)
            entity_to_triplets[triplet['tail']].append(triplet)

        # Find cross-project entities
        cross_project_entities = {
            entity: list(projects)
            for entity, projects in entity_to_projects.items()
            if len(projects) > 1
        }

        # Create project-to-project connections based on shared entities
        project_connections = defaultdict(lambda: {
            'shared_entities': set(),
            'shared_triplets': []
        })

        for entity, projects in cross_project_entities.items():
            # For each pair of projects sharing this entity
            projects_list = list(projects)
            for i, proj1 in enumerate(projects_list):
                for proj2 in projects_list[i+1:]:
                    pair = tuple(sorted([proj1, proj2]))
                    project_connections[pair]['shared_entities'].add(entity)

                    # Find triplets involving this entity from both projects
                    for triplet in entity_to_triplets[entity]:
                        if triplet['project'] in [proj1, proj2]:
                            project_connections[pair]['shared_triplets'].append(triplet)

        # Convert to list format
        connections = []
        for pair, data in project_connections.items():
            connections.append({
                'project1': pair[0],
                'project2': pair[1],
                'shared_entities': list(data['shared_entities']),
                'num_shared_entities': len(data['shared_entities']),
                'shared_triplets': data['shared_triplets']
            })

        return {
            'cross_project_entities': cross_project_entities,
            'project_connections': connections
        }

    def build_unified_kg(self, projects_dir: Path, output_dir: Path, batch_size: int = 4):
        """Build unified knowledge graph from all projects processed together"""

        # Extract all chunks from all projects
        all_chunks = self.extract_all_chunks_from_all_projects(projects_dir)

        # Process through REBEL
        all_triplets = self.process_chunks_with_rebel(all_chunks, batch_size)

        # Find cross-project connections
        cross_project_analysis = self.find_cross_project_connections(all_triplets)

        # Prepare results
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_chunks': len(all_chunks),
            'total_triplets': len(all_triplets),
            'num_cross_project_entities': len(cross_project_analysis['cross_project_entities']),
            'cross_project_entities': cross_project_analysis['cross_project_entities'],
            'project_connections': cross_project_analysis['project_connections'],
            'all_triplets': all_triplets
        }

        # Save
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / 'unified_rebel_cross_project.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Unified cross-project KG saved to: {output_file}")

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Build unified KG by processing all chunks together"
    )
    parser.add_argument(
        '--datasets-dir',
        type=str,
        default='./datasets',
        help='Path to datasets directory'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=4,
        help='Batch size for processing'
    )

    args = parser.parse_args()

    datasets_dir = Path(args.datasets_dir)
    projects_dir = datasets_dir / 'projects'
    output_dir = datasets_dir / 'knowledge_graphs'

    if not projects_dir.exists():
        print(f"❌ Projects directory not found: {projects_dir}")
        return

    print("\n" + "=" * 80)
    print("UNIFIED REBEL PROCESSOR - ALL CHUNKS TOGETHER")
    print("=" * 80)

    try:
        processor = UnifiedREBELProcessor()
        results = processor.build_unified_kg(projects_dir, output_dir, args.batch_size)

        print(f"\n{'─' * 80}")
        print("RESULTS")
        print(f"{'─' * 80}")
        print(f"Total chunks processed:       {results['total_chunks']}")
        print(f"Total triplets extracted:     {results['total_triplets']}")
        print(f"Cross-project entities:       {results['num_cross_project_entities']}")

        if results['cross_project_entities']:
            print(f"\n{'─' * 80}")
            print("CROSS-PROJECT ENTITIES (Shared Across Projects)")
            print(f"{'─' * 80}")
            for entity, projects in results['cross_project_entities'].items():
                print(f"  {entity:40s} → {', '.join(projects)}")

        if results['project_connections']:
            print(f"\n{'─' * 80}")
            print("PROJECT-TO-PROJECT CONNECTIONS")
            print(f"{'─' * 80}")
            for conn in results['project_connections']:
                print(f"\n  {conn['project1']} ↔ {conn['project2']}")
                print(f"    Shared entities: {conn['num_shared_entities']}")
                print(f"    Entities: {', '.join(conn['shared_entities'][:5])}")

        print(f"\n{'=' * 80}")
        print("✓ Unified cross-project KG saved to:")
        print(f"  {output_dir / 'unified_rebel_cross_project.json'}")
        print(f"{'=' * 80}\n")

    except Exception as e:
        logger.error(f"Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
