# Data Preprocessing Pipeline

Simple preprocessing pipeline for converting offer documents to Markdown format.

## Structure

```
data/preprocess/
├── preprocess.py             # Entry point, handles CLI arguments
├── orchestrator.py           # Main orchestrator
├── console_watcher.py        # Console progress and logging
├── requirements.txt          # Python dependencies
├── logs/                     # Log files
└── processors/
    ├── __init__.py
    ├── file_filter.py        # File filtering
    ├── document_processor.py # Document processing
    └── output_manager.py     # Output management
```

## Components

### FileFilter
- Scans folders recursively for supported files (.pdf)
- Returns a list of file paths

### DocumentProcessor
- Processes individual PDF files to Markdown using the `docling` library
- Extracts text, images, and tables from documents

### OutputManager
- Saves processed files, including Markdown content, images, and metadata
- Tracks processed files to avoid duplicates

## Usage

All commands should be run from the `data/preprocess` directory. First, navigate there from the project root:

```bash
cd data/preprocess
```

### Setup & Run

- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

- Run preprocessing:
  ```bash
  python preprocess.py -i <input_folder> -o <output_folder>
  ```
  *Paths can be relative or absolute.*

## Dependency Management

This section is for contributors who need to add or update dependencies.

-   **Add Pip Package:**
    Manually add the new dependency to `requirements.txt`.

-   **Sync Environment:**
    ```bash
    pip install -r requirements.txt
    ```

**Guidelines:**
- Keep dependencies in `requirements.txt` under version control.
- Use a consistent Python version across OSes (3.10+).

## Output Structure

```
output_folder/
├── document1/
│   ├── document1 - full_content.md
│   ├── document1 - metadata.json
│   ├── document1 - page 1.md
│   ├── pictures/
│   │   └── document1 - picture 1.png
│   └── tables/
│       └── document1 - table 1.png
└── processed_files.json
```

## Features

- Memory efficient processing
- Simple error handling
- Duplicate detection
- Configurable logging
- Minimal dependencies
- Self-explanatory code

Ready for integration with Docling and DeepSeek-OCR libraries.