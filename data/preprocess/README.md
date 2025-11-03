# Data Preprocessing Pipeline

Simple preprocessing pipeline for converting offer documents to Markdown format.

## Structure

```
data/preprocess/
├── preprocess.py           # Main orchestrator
└── processors/
    ├── __init__.py
    ├── file_filter.py      # File filtering
    ├── document_processor.py  # Document processing
    └── output_manager.py   # Output management
```

## Components

### FileFilter
- Scans folders for supported files (.pdf, .docx, .png, .jpg, .jpeg)
- Returns file lists and offer folders

### DocumentProcessor  
- Processes individual files to Markdown
- Placeholder implementations for Docling (PDF/DOCX) and DeepSeek-OCR (images)

### OutputManager
- Saves processed files with simple folder structure
- Tracks processed offers to avoid duplicates

## Usage

```bash
python preprocess.py input_folder output_folder
```

## Output Structure

```
output_folder/
├── offer1/
│   ├── document1.md
│   └── document2.md
├── offer2/
│   └── document3.md
└── processed_offers.json
```

## Features

- Memory efficient processing
- Simple error handling
- Duplicate detection
- Minimal dependencies
- Self-explanatory code

Ready for integration with Docling and DeepSeek-OCR libraries.