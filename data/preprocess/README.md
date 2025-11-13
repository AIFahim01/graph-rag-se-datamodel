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

All commands should be run from the `data/preprocess` directory. First, navigate there from the project root:

```bash
cd data/preprocess
```

### Setup & Run

- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

  Optional (CUDA GPU):
  ```bash
  pip3 install -U torch torchvision --index-url https://download.pytorch.org/whl/cu128
  ```
  By default, torch installs CPU builds. Use the above only if you have a CUDA supported GPU.
  Check this page to get the desired url for pytorch with CUDA 12.8 https://pytorch.org/get-started/locally/

- Run preprocessing:
  ```bash
  python preprocess.py <input_folder> <output_folder>
  ```
  *Paths can be relative or absolute and work across OSes.*

## Dependency Management

This section is for contributors who need to add or update dependencies.

-   **Add Pip Package:**
    ```bash
    pip install <package>
    pip list --not-required --format=freeze > requirements.txt
    ```

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
