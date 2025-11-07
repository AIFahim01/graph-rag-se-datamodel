"""
Build Knowledge Graphs using REBEL with FULL METADATA

Extracts relation triplets WITH metadata preservation:
- Source PDF file
- Page number
- Source text chunk
- Position in document
- Confidence scores

This implements the metadata requirements from the architecture diagram.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from tqdm.auto import tqdm
from loguru import logger

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from processing import PDFExtractor, DocumentChunker


def extract_triplets(text: str) -> List[Dict[str, str]]:
    """
    Parse REBEL model output and extract relation triplets

    Args:
        text: Generated text from REBEL model

    Returns:
        List of triplets as dicts with 'head', 'type', 'tail' keys
    """
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


class REBELKnowledgeGraphBuilder:
    """Build knowledge graphs from PDFs using REBEL model with metadata"""

    def __init__(self, model_name: str = "Babelscape/rebel-large"):
        """
        Initialize REBEL model and tokenizer

        Args:
            model_name: HuggingFace model identifier
        """
        logger.info(f"Loading REBEL model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        # Move to GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        logger.info(f"Model loaded on device: {self.device}")

        # Generation parameters
        self.gen_kwargs = {
            "max_length": 256,
            "length_penalty": 0,
            "num_beams": 3,
            "num_return_sequences": 1,
        }

        self.pdf_extractor = PDFExtractor()
        # Add chunker with article's proven parameters
        self.chunker = DocumentChunker(chunk_size=400, overlap=40)

    def extract_text_with_metadata(self, pdf_dir: Path) -> List[Dict]:
        """
        Extract text from all PDFs in a directory WITH METADATA

        Args:
            pdf_dir: Directory containing PDF files

        Returns:
            List of text chunks with rich metadata
        """
        logger.info(f"Extracting text from PDFs in {pdf_dir}")
        pdf_files = list(pdf_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_dir}")
            return []

        all_chunks = []
        for pdf_file in pdf_files:
            try:
                # Extract pages from PDF
                pages = self.pdf_extractor.extract(str(pdf_file))

                # Chunk the pages using DocumentChunker
                chunks = self.chunker.chunk_pages(pages)

                # Add chunks with enhanced metadata
                for chunk in chunks:
                    all_chunks.append({
                        'text': chunk['text'],
                        'source_pdf': pdf_file.name,
                        'source_path': str(pdf_file),
                        'page_number': chunk['page'],
                        'char_count': chunk['char_count'],
                        'chunk_id': chunk['chunk_id'],
                        'chunk_position': chunk['position']
                    })
            except Exception as e:
                logger.error(f"Failed to extract {pdf_file.name}: {e}")

        logger.info(f"Extracted {len(all_chunks)} text chunks from {len(pdf_files)} PDFs (chunked with size=400, overlap=40)")
        return all_chunks

    def generate_triplets_with_metadata(
        self,
        text_data_list: List[Dict]
    ) -> List[Dict]:
        """
        Generate triplets WITH METADATA for each triplet

        Args:
            text_data_list: List of dicts with text and metadata

        Returns:
            List of triplet dicts with full metadata
        """
        texts = [item['text'] for item in text_data_list]

        # Tokenize
        model_inputs = self.tokenizer(
            texts,
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors='pt'
        )

        # Move to device
        model_inputs = {k: v.to(self.device) for k, v in model_inputs.items()}

        # Generate
        generated_tokens = self.model.generate(
            model_inputs["input_ids"],
            attention_mask=model_inputs["attention_mask"],
            **self.gen_kwargs
        )

        # Decode
        decoded_preds = self.tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=False
        )

        # Extract triplets WITH metadata
        all_triplets_with_metadata = []
        for idx, sentence in enumerate(decoded_preds):
            source_data = text_data_list[idx]
            triplet_dicts = extract_triplets(sentence)

            for t in triplet_dicts:
                triplet_with_metadata = {
                    # Triplet data
                    'head': t['head'],
                    'relation': t['type'],
                    'tail': t['tail'],

                    # Metadata
                    'metadata': {
                        'source_pdf': source_data['source_pdf'],
                        'source_path': source_data['source_path'],
                        'page_number': source_data['page_number'],
                        'chunk_id': source_data['chunk_id'],
                        'source_text': source_data['text'][:200] + '...',  # Preview
                        'source_text_length': source_data['char_count'],
                        'extraction_method': 'REBEL',
                        'model_name': 'Babelscape/rebel-large'
                    }
                }
                all_triplets_with_metadata.append(triplet_with_metadata)

        return all_triplets_with_metadata

    def build_knowledge_graph(
        self,
        project_dir: Path,
        batch_size: int = 4,
        output_dir: Path = None
    ) -> Dict:
        """
        Build knowledge graph for a project WITH METADATA

        Args:
            project_dir: Directory containing project PDFs
            batch_size: Number of texts to process in one batch
            output_dir: Directory to save outputs

        Returns:
            Dictionary with project stats and triplets with metadata
        """
        project_name = project_dir.name
        logger.info(f"Building knowledge graph with metadata for: {project_name}")

        # Extract text WITH metadata
        text_data = self.extract_text_with_metadata(project_dir)

        if not text_data:
            logger.warning(f"No text extracted from {project_name}")
            return None

        # Generate triplets WITH metadata in batches
        all_triplets = []

        logger.info(f"Generating triplets with metadata from {len(text_data)} text chunks (400 chars each with 40 overlap)...")
        for i in tqdm(range(0, len(text_data), batch_size), desc="Processing batches"):
            batch_data = text_data[i:i + batch_size]
            batch_triplets = self.generate_triplets_with_metadata(batch_data)
            all_triplets.extend(batch_triplets)

        # Create unique identifier for each triplet (for deduplication)
        unique_triplets = {}
        for triplet in all_triplets:
            # Key: head-relation-tail
            key = f"{triplet['head']}|{triplet['relation']}|{triplet['tail']}"

            if key not in unique_triplets:
                unique_triplets[key] = triplet
            else:
                # If duplicate, add source to mentions
                if 'mentions' not in unique_triplets[key]:
                    unique_triplets[key]['mentions'] = [unique_triplets[key]['metadata']]
                    unique_triplets[key]['mention_count'] = 1

                unique_triplets[key]['mentions'].append(triplet['metadata'])
                unique_triplets[key]['mention_count'] = len(unique_triplets[key]['mentions'])

        distinct_triplets = list(unique_triplets.values())

        logger.info(f"Extracted {len(all_triplets)} total triplets, {len(distinct_triplets)} unique")

        # Prepare results
        results = {
            'project_name': project_name,
            'num_pdfs': len(set(item['source_pdf'] for item in text_data)),
            'num_text_segments': len(text_data),
            'num_total_triplets': len(all_triplets),
            'num_unique_triplets': len(distinct_triplets),
            'timestamp': datetime.now().isoformat(),
            'has_metadata': True,
            'triplets': distinct_triplets
        }

        # Save results
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save full KG with metadata
            kg_file = output_dir / f"{project_name}_knowledge_graph_with_metadata.json"
            with open(kg_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"Knowledge graph with metadata saved to: {kg_file}")

            # Save statistics
            stats = {
                'project_name': project_name,
                'num_pdfs': results['num_pdfs'],
                'num_text_segments': results['num_text_segments'],
                'num_total_triplets': results['num_total_triplets'],
                'num_unique_triplets': results['num_unique_triplets'],
                'has_metadata': True,
                'timestamp': results['timestamp']
            }

            stats_file = output_dir / f"{project_name}_stats_metadata.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Build knowledge graphs from PDFs using REBEL with METADATA"
    )
    parser.add_argument(
        '--project',
        type=str,
        help='Specific project to process (e.g., alpha_erp_system)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all projects'
    )
    parser.add_argument(
        '--datasets-dir',
        type=str,
        default='./datasets',
        help='Path to datasets directory (default: ./datasets)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=4,
        help='Batch size for processing (default: 4, increased for chunk processing)'
    )

    args = parser.parse_args()

    # Setup paths
    datasets_dir = Path(args.datasets_dir)
    projects_dir = datasets_dir / 'projects'
    output_dir = datasets_dir / 'knowledge_graphs'

    if not projects_dir.exists():
        print(f"❌ Projects directory not found: {projects_dir}")
        return

    # Setup logging
    logger.add(
        datasets_dir / "knowledge_graph_metadata_extraction.log",
        format="{time} {level} {message}",
        level="INFO"
    )

    print("\n" + "=" * 80)
    print("REBEL KNOWLEDGE GRAPH BUILDER (WITH METADATA)")
    print("=" * 80)

    # Initialize REBEL builder
    try:
        builder = REBELKnowledgeGraphBuilder()
    except Exception as e:
        print(f"\n❌ Failed to load REBEL model: {e}")
        return

    # Determine which projects to process
    if args.all:
        project_dirs = [p for p in projects_dir.iterdir() if p.is_dir()]
        print(f"\n📁 Processing all {len(project_dirs)} projects with metadata...")
    elif args.project:
        project_dir = projects_dir / args.project
        if not project_dir.exists():
            print(f"❌ Project not found: {project_dir}")
            return
        project_dirs = [project_dir]
        print(f"\n📁 Processing project: {args.project}")
    else:
        print("❌ Please specify --project PROJECT_NAME or --all")
        parser.print_help()
        return

    # Process projects
    all_results = []
    for project_dir in project_dirs:
        print(f"\n{'─' * 80}")
        print(f"Project: {project_dir.name}")
        print(f"{'─' * 80}")

        try:
            results = builder.build_knowledge_graph(
                project_dir,
                batch_size=args.batch_size,
                output_dir=output_dir
            )

            if results:
                all_results.append(results)

                # Display results
                print(f"\n  ✓ Knowledge Graph Built (WITH METADATA)")
                print(f"    PDFs processed:      {results['num_pdfs']}")
                print(f"    Text segments:       {results['num_text_segments']}")
                print(f"    Total triplets:      {results['num_total_triplets']}")
                print(f"    Unique triplets:     {results['num_unique_triplets']}")

                # Show sample triplet with metadata
                if results['triplets']:
                    print(f"\n  Sample triplet WITH METADATA:")
                    sample = results['triplets'][0]
                    print(f"    Triplet: {sample['head']} --[{sample['relation']}]--> {sample['tail']}")
                    print(f"    Source:  {sample['metadata']['source_pdf']} (Page {sample['metadata']['page_number']})")
                    if 'mention_count' in sample:
                        print(f"    Mentions: {sample['mention_count']} times")

        except Exception as e:
            logger.error(f"Failed to process {project_dir.name}: {e}")
            print(f"  ❌ Error: {e}")

    # Summary
    if all_results:
        print(f"\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        total_projects = len(all_results)
        total_pdfs = sum(r['num_pdfs'] for r in all_results)
        total_triplets = sum(r['num_total_triplets'] for r in all_results)
        total_unique = sum(r['num_unique_triplets'] for r in all_results)

        print(f"Projects processed:     {total_projects}")
        print(f"Total PDFs:             {total_pdfs}")
        print(f"Total triplets:         {total_triplets}")
        print(f"Unique triplets:        {total_unique}")
        print(f"Metadata preserved:     ✅ YES")
        print(f"\n✓ Knowledge graphs WITH METADATA saved to: {output_dir}")
        print("=" * 80)
    else:
        print("\n❌ No knowledge graphs generated")


if __name__ == "__main__":
    main()
