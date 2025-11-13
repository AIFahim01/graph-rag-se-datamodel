#!/usr/bin/env python3
"""Test ReLiK model download after removing hf-xet"""

import os
import sys

# Ensure hf-xet is not interfering
os.environ['HF_HUB_DISABLE_XET'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'

print("=" * 80)
print("TESTING RELIK MODEL DOWNLOAD")
print("=" * 80)

try:
    print("\n🔄 Attempting to load ReLiK model...")
    print("   Model: sapienzanlp/relik-entity-linking-small")
    print("   This may take a few minutes on first download...")

    from relik import Relik

    # Try to load the model
    model = Relik.from_pretrained("sapienzanlp/relik-entity-linking-small")

    print("\n✅ SUCCESS! ReLiK model loaded successfully!")

    # Test on sample text
    test_text = "TenneT operates HVDC links between Germany and Netherlands. The converter stations use VSC technology."

    print("\n🧪 Testing extraction on sample text:")
    print(f"   Text: {test_text[:80]}...")

    result = model(test_text)

    # Check what's in the result
    print(f"\n📊 Extraction results:")
    if hasattr(result, 'entities'):
        print(f"   Entities found: {len(result.entities)}")
        for entity in result.entities[:5]:  # Show first 5
            print(f"      - {entity.text if hasattr(entity, 'text') else entity}")

    if hasattr(result, 'triplets'):
        print(f"   Relations found: {len(result.triplets)}")
        for triplet in result.triplets[:5]:  # Show first 5
            if hasattr(triplet, 'subject'):
                print(f"      - {triplet.subject.text} -> {triplet.label} -> {triplet.object.text}")

    print("\n🎉 ReLiK is ready for production use!")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ FAILED to load ReLiK model")
    print(f"   Error: {e}")
    print(f"\n   Error type: {type(e).__name__}")

    # Check if it's an XET error
    if "XET" in str(e) or "cas-bridge" in str(e):
        print("\n⚠️  This is an XET download error. Try manual download approach.")

    print("\n📝 Next steps:")
    print("   1. Try manual download with git-lfs")
    print("   2. Or try a different model: relik-ie/relik-relation-extraction-small")

    sys.exit(1)