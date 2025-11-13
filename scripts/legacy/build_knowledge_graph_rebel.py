"""
Build Knowledge Graphs using REBEL

Extracts relation triplets from PDF documents using the REBEL model
(Relation Extraction By End-to-end Language generation) from Babelscape.

Based on the article:
"Building Knowledge Graphs: REBEL, LlamaIndex, and REBEL + LlamaIndex"
https://medium.com/@zilliz_learn/building-knowledge-graphs-rebel-llamaindex-and-rebel-llamaindex-2ab1c6a5dc4b
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

from processing import PDFExtractor


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
    """Build knowledge graphs from PDFs using REBEL model"""

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

    def extract_text_from_pdfs(self, pdf_dir: Path) -> List[Dict]:
        """
        Extract text from all PDFs in a directory

        Args:
            pdf_dir: Directory containing PDF files

        Returns:
            List of text chunks with metadata
        """
        logger.info(f"Extracting text from PDFs in {pdf_dir}")
        pdf_files = list(pdf_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_dir}")
            return []

        all_texts = []
        for pdf_file in pdf_files:
            try:
                pages = self.pdf_extractor.extract(str(pdf_file))
                for page_data in pages:
                    all_texts.append({
                        'text': page_data['text'],
                        'source': pdf_file.name,
                        'page': page_data['page_number']
                    })
            except Exception as e:
                logger.error(f"Failed to extract {pdf_file.name}: {e}")

        logger.info(f"Extracted {len(all_texts)} text segments from {len(pdf_files)} PDFs")
        return all_texts

    def generate_triplets_batch(self, texts: List[str]) -> List[Tuple[str, str, str]]:
        """
        Generate triplets from a batch of texts

        Args:
            texts: List of text strings

        Returns:
            List of triplets as (head, relation, tail) tuples
        """
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

        # Extract triplets
        all_triplets = []
        for sentence in decoded_preds:
            triplet_dicts = extract_triplets(sentence)
            for t in triplet_dicts:
                all_triplets.append((t['head'], t['type'], t['tail']))

        return all_triplets

    def build_knowledge_graph(
        self,
        project_dir: Path,
        batch_size: int = 2,
        output_dir: Path = None
    ) -> Dict:
        """
        Build knowledge graph for a project

        Args:
            project_dir: Directory containing project PDFs
            batch_size: Number of texts to process in one batch
            output_dir: Directory to save outputs

        Returns:
            Dictionary with project stats and triplets
        """
        project_name = project_dir.name
        logger.info(f"Building knowledge graph for: {project_name}")

        # Extract text from PDFs
        text_data = self.extract_text_from_pdfs(project_dir)

        if not text_data:
            logger.warning(f"No text extracted from {project_name}")
            return None

        # Generate triplets in batches
        all_triplets = []
        texts = [item['text'] for item in text_data]

        logger.info(f"Generating triplets from {len(texts)} text segments...")
        for i in tqdm(range(0, len(texts), batch_size), desc="Processing batches"):
            batch_texts = texts[i:i + batch_size]
            batch_triplets = self.generate_triplets_batch(batch_texts)
            all_triplets.extend(batch_triplets)

        # Remove duplicates
        distinct_triplets = list(set(all_triplets))

        logger.info(f"Extracted {len(all_triplets)} total triplets, {len(distinct_triplets)} unique")

        # Prepare results
        results = {
            'project_name': project_name,
            'num_pdfs': len(set(item['source'] for item in text_data)),
            'num_text_segments': len(text_data),
            'num_total_triplets': len(all_triplets),
            'num_unique_triplets': len(distinct_triplets),
            'timestamp': datetime.now().isoformat(),
            'triplets': [
                {'head': t[0], 'relation': t[1], 'tail': t[2]}
                for t in distinct_triplets
            ]
        }

        # Save results
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save triplets as JSON
            triplets_file = output_dir / f"{project_name}_knowledge_graph.json"
            with open(triplets_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"Knowledge graph saved to: {triplets_file}")

            # Save simple triplet list for graph databases
            simple_triplets = output_dir / f"{project_name}_triplets.json"
            with open(simple_triplets, 'w', encoding='utf-8') as f:
                json.dump(distinct_triplets, f, indent=2, ensure_ascii=False)

            # Save statistics
            stats = {
                'project_name': project_name,
                'num_pdfs': results['num_pdfs'],
                'num_text_segments': results['num_text_segments'],
                'num_total_triplets': results['num_total_triplets'],
                'num_unique_triplets': results['num_unique_triplets'],
                'timestamp': results['timestamp']
            }

            stats_file = output_dir / f"{project_name}_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Build knowledge graphs from PDFs using REBEL"
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
        default=2,
        help='Batch size for processing (default: 2)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='Babelscape/rebel-large',
        help='REBEL model to use (default: Babelscape/rebel-large)'
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
        datasets_dir / "knowledge_graph_extraction.log",
        format="{time} {level} {message}",
        level="INFO"
    )

    print("\n" + "=" * 80)
    print("REBEL KNOWLEDGE GRAPH BUILDER")
    print("=" * 80)

    # Initialize REBEL builder
    try:
        builder = REBELKnowledgeGraphBuilder(model_name=args.model)
    except Exception as e:
        print(f"\n❌ Failed to load REBEL model: {e}")
        print("   Make sure you have transformers and torch installed")
        print("   Run: pip install transformers torch")
        return

    # Determine which projects to process
    if args.all:
        project_dirs = [p for p in projects_dir.iterdir() if p.is_dir()]
        print(f"\n📁 Processing all {len(project_dirs)} projects...")
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
                print(f"\n  ✓ Knowledge Graph Built")
                print(f"    PDFs processed:      {results['num_pdfs']}")
                print(f"    Text segments:       {results['num_text_segments']}")
                print(f"    Total triplets:      {results['num_total_triplets']}")
                print(f"    Unique triplets:     {results['num_unique_triplets']}")

                # Show sample triplets
                if results['triplets']:
                    print(f"\n  Sample triplets:")
                    for triplet in results['triplets'][:5]:
                        print(f"    • {triplet['head']} --[{triplet['relation']}]--> {triplet['tail']}")

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
        print(f"\n✓ Knowledge graphs saved to: {output_dir}")
        print("=" * 80)
    else:
        print("\n❌ No knowledge graphs generated")


if __name__ == "__main__":
    main()
