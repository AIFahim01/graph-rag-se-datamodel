# Preprocessing Pipeline - Integration Notes

## What This Is

A modular document preprocessing pipeline extracted from feature/document-preprocessing-pipeline branch.

**Purpose:** Convert documents (PDF, DOCX, images) to Markdown format before feeding into the main GraphRAG pipeline.

## Current Status

**Architecture:** ✅ Well-designed, modular
**Implementation:** ⚠️ INCOMPLETE - Has placeholders

### Implemented:
- ✅ File filtering (scans for .pdf, .docx, .png, .jpg, .jpeg)
- ✅ Document routing by file type
- ✅ Output management with folder structure
- ✅ Processing metrics tracking (time, count, files)
- ✅ Duplicate detection via JSON state file
- ✅ Clean separation of concerns

### TODO - Needs Implementation:
- ❌ PDF processing (placeholder for Docling integration)
- ❌ DOCX processing (placeholder for Docling integration)
- ❌ Image OCR (placeholder for DeepSeek-OCR integration)

## Integration with Main Pipeline

This preprocessing step can be inserted BEFORE the existing GraphRAG pipeline:

```
Current Pipeline:
PDFs → scripts/process_project.py → chunks → embeddings → ChromaDB/Neo4j → chat

With Preprocessing:
PDFs → data/preprocess/preprocess.py → Markdown → scripts/process_project.py → ...
```

## Next Steps to Complete

1. **Install Docling:**
   ```bash
   pip install docling  # For PDF/DOCX processing
   ```

2. **Implement PDF Processor:**
   - Replace TODO in `processors/document_processor.py`
   - Use Docling to extract structured content
   - Convert to Markdown format

3. **Implement DOCX Processor:**
   - Similar to PDF processing
   - Docling supports DOCX natively

4. **Implement Image OCR:**
   - Install DeepSeek-OCR or similar
   - Extract text from images
   - Convert to Markdown

5. **Integrate with Existing Pipeline:**
   - Modify `scripts/process_project.py` to accept Markdown input
   - Or convert Markdown back to text for chunking

## Usage (When Complete)

```bash
cd data/preprocess

# Process documents to Markdown
python preprocess.py /path/to/input /path/to/output

# Then feed to main pipeline
cd ../..
python scripts/process_project.py --all
```

## Benefits

- **Cleaner text extraction** via Docling (better than PyMuPDF)
- **Format preservation** (headings, lists, tables)
- **OCR support** for scanned documents/images
- **Modular design** easy to extend
- **Metrics tracking** for monitoring

## Note

This preprocessing pipeline is **optional**. The existing PyMuPDF-based extraction in `src/processing/pdf_extractor.py` works fine for text-based PDFs. Use this preprocessing when you need:
- Better structure preservation
- OCR for scanned documents
- DOCX support
- Image text extraction
