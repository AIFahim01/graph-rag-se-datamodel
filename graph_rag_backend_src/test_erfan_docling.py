#!/usr/bin/env python3
"""
Test Erfan's Docling PDF extraction on 1 sample PDF
"""

import sys
from pathlib import Path

# Add preprocess processors to path
sys.path.insert(0, str(Path(__file__).parent / "data" / "preprocess"))

from processors import DocumentProcessor

print("=" * 80)
print("TESTING ERFAN'S DOCLING PDF EXTRACTION")
print("=" * 80)

# Test on 1 sample PDF
test_pdf = Path("data/pdfs/hdvc/GC25_002_HVDC_SE_RnD_POD/1_Contract_documents/GC25_002_HVDC_SE_RnD_POD_Offer_signed.pdf")

if not test_pdf.exists():
    print(f"❌ Test PDF not found: {test_pdf}")
    sys.exit(1)

print(f"\n📄 Test PDF: {test_pdf.name}")
print(f"   Size: {test_pdf.stat().st_size / 1024:.1f} KB")

# Process with Docling
processor = DocumentProcessor()

print(f"\n🔄 Processing with Docling...")
content, success = processor.process_file(test_pdf)

if success:
    print(f"\n✅ SUCCESS!")
    print(f"   Extracted {len(content):,} characters")
    print(f"   Lines: {len(content.splitlines())}")

    # Show first 1000 chars
    print(f"\n📝 First 1000 characters of extracted content:")
    print("=" * 80)
    print(content[:1000])
    print("=" * 80)

    # Save full output for inspection
    output_file = Path("test_erfan_output.md")
    output_file.write_text(content)
    print(f"\n💾 Full output saved to: {output_file}")
    print(f"   You can review the complete extraction")

else:
    print(f"\n❌ FAILED to extract PDF content")
    print(f"   Error: {content}")

sys.exit(0 if success else 1)
