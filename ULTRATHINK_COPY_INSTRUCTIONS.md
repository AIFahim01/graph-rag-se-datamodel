# HDVC & SYNCON Subset Copy Instructions

## Overview
This process will copy files from `G:\ultrathink` containing HDVC or SYNCON content from the last year into organized directories for GraphRAG processing.

## Prerequisites
- G: drive must be accessible
- Python installed on Windows
- ultrathink folder exists at `G:\ultrathink`

## Files Created
- `copy_ultrathink_subset.py` - Main copy script
- `run_copy_ultrathink.bat` - Windows batch file to run the script
- Directory structure created at `data/pdfs/`:
  - `hdvc/` - Files containing HDVC content
  - `syncon/` - Files containing SYNCON content
  - `mixed/` - Files containing both HDVC and SYNCON

## How to Run

### Option 1: Double-click the batch file
1. Navigate to the project directory in Windows Explorer
2. Double-click `run_copy_ultrathink.bat`
3. Wait for the process to complete

### Option 2: Run from Command Prompt
```cmd
cd "C:\Users\z0051yym\Desktop\test_bp_code\knowledge_graph_vector_GC_Data\graph-rag-se-datamodel"
run_copy_ultrathink.bat
```

### Option 3: Run Python script directly
```cmd
cd "C:\Users\z0051yym\Desktop\test_bp_code\knowledge_graph_vector_GC_Data\graph-rag-se-datamodel"
python copy_ultrathink_subset.py
```

## What the Script Does

1. **Scans G:\ultrathink recursively** for supported files (.pdf, .docx, .png, .jpg, .jpeg)
2. **Filters by date** - Only copies files modified within the last year
3. **Categorizes by keywords**:
   - Files with "hdvc" in filename/path → `data/pdfs/hdvc/`
   - Files with "syncon" in filename/path → `data/pdfs/syncon/`
   - Files with both → `data/pdfs/mixed/`
4. **Preserves folder structure** in destination directories
5. **Creates manifest** - `data/pdfs/copy_manifest.json` with detailed results

## Expected Output

```
data/pdfs/
├── hdvc/
│   ├── [original folder structure preserved]
│   └── [HDVC-related files]
├── syncon/
│   ├── [original folder structure preserved]
│   └── [SYNCON-related files]
├── mixed/
│   ├── [files containing both keywords]
│   └── [original folder structure preserved]
└── copy_manifest.json (detailed results)
```

## Troubleshooting

### Error: G:\ultrathink not found
- Check that G: drive is connected and accessible
- Verify `G:\ultrathink` folder exists
- Try accessing `G:\ultrathink` in Windows Explorer first

### Error: Python not found
- Install Python from python.org
- Restart Command Prompt after installation
- Ensure Python is added to Windows PATH

### No files copied
- Check if files in `G:\ultrathink` contain "hdvc" or "syncon" in filename/path
- Verify files are from the last year (script filters by modification date)
- Check `copy_manifest.json` for details

## Next Steps

After successful copy:
1. Verify files were copied to `data/pdfs/` directories
2. Review `copy_manifest.json` for copy statistics
3. Run the GraphRAG preprocessing pipeline on the subset
4. Train embeddings and build knowledge graph from HDVC/SYNCON data

The copied files will be ready for the GraphRAG pipeline to process into embeddings and knowledge graphs.