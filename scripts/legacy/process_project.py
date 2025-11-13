"""
Process project-organized PDF documents

Extracts text and creates chunks from project folders.
Simple flat structure - all PDFs directly in project folder.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from loguru import logger

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from processing import PDFExtractor, DocumentChunker


class ProjectProcessor:
    """Process multi-document projects"""

    def __init__(self):
        self.extractor = PDFExtractor()
        self.chunker = DocumentChunker(chunk_size=1000, overlap=200)
        self.logger = logger

    def get_project_folders(self, datasets_dir: Path) -> List[Path]:
        """Get all project folders"""
        projects_dir = datasets_dir / "projects"
        return [p for p in projects_dir.iterdir() if p.is_dir()]

    def get_pdfs(self, project_dir: Path) -> List[Path]:
        """Get all PDFs in project folder"""
        return list(project_dir.glob("*.pdf"))

    def process_project(self, project_dir: Path, output_dir: Path) -> Dict:
        """
        Process all PDFs in a project

        Args:
            project_dir: Path to project folder
            output_dir: Path to save outputs

        Returns:
            Processing results and statistics
        """
        project_name = project_dir.name
        self.logger.info(f"Processing project: {project_name}")

        # Get PDFs
        pdf_files = self.get_pdfs(project_dir)

        if not pdf_files:
            self.logger.warning(f"No PDFs found in {project_name}")
            return None

        # Process PDFs
        all_chunks = []
        total_pages = 0
        failed_pdfs = []

        self.logger.info(f"  Found {len(pdf_files)} PDF files")

        for pdf_file in pdf_files:
            try:
                # Extract
                pages = self.extractor.extract(str(pdf_file))
                total_pages += len(pages)

                # Chunk
                chunks = self.chunker.chunk_pages(pages)

                # Add project metadata
                for chunk in chunks:
                    chunk["project"] = project_name

                all_chunks.extend(chunks)
                self.logger.info(f"    ✓ {pdf_file.name}: {len(pages)} pages, {len(chunks)} chunks")

            except Exception as e:
                self.logger.error(f"    ✗ {pdf_file.name}: {e}")
                failed_pdfs.append(pdf_file.name)

        # Create stats
        stats = {
            "project_name": project_name,
            "total_pdfs": len(pdf_files),
            "successful_pdfs": len(pdf_files) - len(failed_pdfs),
            "failed_pdfs": failed_pdfs,
            "total_pages": total_pages,
            "total_chunks": len(all_chunks),
            "timestamp": datetime.now().isoformat()
        }

        # Save outputs
        project_output = output_dir / project_name
        project_output.mkdir(parents=True, exist_ok=True)

        # Save chunks
        chunks_file = project_output / "chunks.json"
        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, indent=2, ensure_ascii=False)

        # Save metadata
        metadata_file = project_output / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)

        self.logger.info(f"  ✓ Processed {stats['total_chunks']} chunks from {stats['successful_pdfs']} PDFs")
        self.logger.info(f"  ✓ Saved to {project_output}")

        return stats


def main():
    parser = argparse.ArgumentParser(
        description="Process project-organized PDF documents"
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Project name to process (e.g., project_001)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all projects"
    )
    parser.add_argument(
        "--datasets-dir",
        type=str,
        default="./datasets",
        help="Path to datasets directory (default: ./datasets)"
    )

    args = parser.parse_args()

    # Setup paths
    datasets_dir = Path(args.datasets_dir)
    projects_dir = datasets_dir / "projects"
    output_dir = datasets_dir / "processed"

    if not projects_dir.exists():
        print(f"❌ Projects directory not found: {projects_dir}")
        print(f"   Please create dataset structure first")
        return

    # Setup logging
    logger.add(
        datasets_dir / "processing.log",
        format="{time} {level} {message}",
        level="INFO"
    )

    print("\n" + "=" * 80)
    print("PROJECT DOCUMENT PROCESSOR")
    print("=" * 80)

    processor = ProjectProcessor()

    # Determine which projects to process
    if args.all:
        project_dirs = processor.get_project_folders(datasets_dir)
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
    all_stats = []
    for project_dir in project_dirs:
        print(f"\n{'─' * 80}")
        print(f"Processing: {project_dir.name}")
        print(f"{'─' * 80}")

        stats = processor.process_project(project_dir, output_dir)

        if stats:
            all_stats.append(stats)

            # Display stats
            print(f"\n  Project: {stats['project_name']}")
            print(f"  PDFs:    {stats['successful_pdfs']}/{stats['total_pdfs']} successful")
            if stats['failed_pdfs']:
                print(f"  Failed:  {', '.join(stats['failed_pdfs'])}")
            print(f"  Pages:   {stats['total_pages']}")
            print(f"  Chunks:  {stats['total_chunks']}")

    # Summary
    if all_stats:
        print(f"\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        total_projects = len(all_stats)
        total_pdfs = sum(s['total_pdfs'] for s in all_stats)
        successful_pdfs = sum(s['successful_pdfs'] for s in all_stats)
        total_pages = sum(s['total_pages'] for s in all_stats)
        total_chunks = sum(s['total_chunks'] for s in all_stats)

        print(f"Projects:       {total_projects}")
        print(f"PDFs:           {successful_pdfs}/{total_pdfs} successful")
        print(f"Pages:          {total_pages}")
        print(f"Chunks:         {total_chunks}")
        print(f"\n✓ Outputs saved to: {output_dir}")
        print("=" * 80)
    else:
        print("\n❌ No projects processed")


if __name__ == "__main__":
    main()
