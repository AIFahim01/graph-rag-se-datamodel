"""
Markdown File Chunker
Scans GC_2021 folder and creates chunks from .md files
"""

import json
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm


class MarkdownChunker:
    """Chunk markdown files from output copy folder"""

    def __init__(self, data_source: Path, chunk_size: int = 1000,
                 chunk_overlap: int = 200, sample_mode: bool = False):
        """
        Initialize chunker

        Args:
            data_source: Path to GC_2021 folder
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between consecutive chunks
            sample_mode: If True, process only first 100 documents
        """
        self.data_source = Path(data_source)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sample_mode = sample_mode

    def find_markdown_files(self) -> List[Path]:
        """Find all .md files in the data source"""
        print(f"📂 Scanning for markdown files in: {self.data_source}")

        # Find all .md files (excluding full_content.md)
        md_files = []
        for md_file in self.data_source.rglob("*.md"):
            # Skip full_content files, only use individual page files
            if "full_content" not in md_file.name and "page" in md_file.name:
                md_files.append(md_file)

        print(f"✅ Found {len(md_files)} markdown page files")

        if self.sample_mode:
            md_files = md_files[:100]
            print(f"🧪 Sample mode: Processing only {len(md_files)} files")

        return md_files

    def extract_metadata(self, md_file: Path) -> Dict:
        """Extract metadata from file path"""
        parts = md_file.parts

        # Find GC_2021 index
        try:
            gc_index = parts.index("GC_2021")
            project_id = parts[gc_index + 1] if gc_index + 1 < len(parts) else "unknown"
        except ValueError:
            project_id = "unknown"

        # Extract project type
        project_type = "unknown"
        if "HVDC" in project_id.upper():
            project_type = "HVDC"
        elif "SYNCON" in project_id.upper():
            project_type = "SynCon"
        elif "OWF" in project_id.upper():
            project_type = "OWF"
        elif "CCPP" in project_id.upper():
            project_type = "CCPP"

        return {
            "project_id": project_id,
            "project_type": project_type,
            "file_path": str(md_file),
            "file_name": md_file.name
        }

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > self.chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - self.chunk_overlap

        return chunks

    def process_files(self) -> List[Dict]:
        """
        Process all markdown files and create chunks

        Returns:
            List of chunk dictionaries
        """
        md_files = self.find_markdown_files()

        all_chunks = []
        chunk_id_counter = 0

        print(f"\n📄 Processing markdown files and creating chunks...")

        for md_file in tqdm(md_files, desc="Processing files"):
            try:
                # Read markdown content
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Skip empty files
                if not content.strip():
                    continue

                # Extract metadata
                metadata = self.extract_metadata(md_file)

                # Create chunks
                text_chunks = self.chunk_text(content)

                # Create chunk objects
                for chunk_idx, chunk_text in enumerate(text_chunks):
                    chunk = {
                        "chunk_id": f"chunk_{chunk_id_counter}",
                        "text": chunk_text,
                        "char_count": len(chunk_text),
                        "chunk_index": chunk_idx,
                        "total_chunks": len(text_chunks),
                        "source_file": metadata["file_name"],
                        "source_path": metadata["file_path"],
                        "project_id": metadata["project_id"],
                        "project_type": metadata["project_type"]
                    }

                    all_chunks.append(chunk)
                    chunk_id_counter += 1

            except Exception as e:
                print(f"⚠️  Error processing {md_file}: {e}")
                continue

        print(f"\n✅ Created {len(all_chunks)} chunks from {len(md_files)} files")
        return all_chunks

    def save_chunks(self, chunks: List[Dict], output_file: Path):
        """Save chunks to JSON file"""
        print(f"\n💾 Saving chunks to: {output_file}")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved {len(chunks)} chunks successfully!")


def main():
    """Test the chunker"""
    from config import DATA_SOURCE, CHUNKS_FILE, CHUNK_SIZE, CHUNK_OVERLAP, SAMPLE_MODE

    chunker = MarkdownChunker(
        data_source=DATA_SOURCE,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        sample_mode=SAMPLE_MODE
    )

    chunks = chunker.process_files()
    chunker.save_chunks(chunks, CHUNKS_FILE)

    # Print statistics
    print("\n📊 Chunk Statistics:")
    project_types = {}
    for chunk in chunks:
        pt = chunk["project_type"]
        project_types[pt] = project_types.get(pt, 0) + 1

    for project_type, count in sorted(project_types.items()):
        print(f"  • {project_type}: {count} chunks")


if __name__ == "__main__":
    main()
