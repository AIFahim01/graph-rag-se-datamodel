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

1.  **Create Conda Environment:**
    ```bash
    conda env create -f environment.yml
    ```

2.  **Activate Environment:**
    ```bash
    conda activate <env_name>
    ```
    *(Use the name defined in `environment.yml`, e.g., `env12`)*

3.  **Install Pip Packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run Preprocessing:**
    ```bash
    python preprocess.py <input_folder> <output_folder>
    ```
    *Note: `<input_folder>` and `<output_folder>` paths can be relative to the current directory or absolute.*

## Dependency Management

This section is for contributors who need to add or update dependencies.

-   **Add Conda Package:**
    ```bash
    conda install <package>
    ```
    Then, regenerate the `environment.yml` file:
    ```bash
    # Windows
    conda env export --from-history > environment.yml
    # Linux/macOS
    conda env export --from-history > environment.yml
    ```

-   **Add Pip Package:**
    ```bash
    pip install <package>
    pip freeze > requirements.txt
    ```

-   **Sync Local Environment:**
    To apply updates from the YAML and requirements files:
    ```bash
    conda env update -f environment.yml --prune
    pip install -r requirements.txt
    ```

**Guidelines:**
- Do not commit the `prefix:` line in `environment.yml` to ensure it remains portable.
- Always activate the Conda environment before running scripts or managing packages.

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