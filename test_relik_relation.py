#!/usr/bin/env python3
"""Test ReLiK relation extraction model"""

import os
import sys

# Ensure hf-xet is not interfering
os.environ['HF_HUB_DISABLE_XET'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'

print("=" * 80)
print("TESTING RELIK RELATION EXTRACTION MODEL")
print("=" * 80)

try:
    print("\n🔄 Attempting to load ReLiK relation extraction model...")
    print("   Model: relik-ie/relik-relation-extraction-small")
    print("   This model is specifically designed for relation extraction")
    print("   This may take a few minutes on first download...")

    from relik import Relik

    # Try the relation extraction model
    model = Relik.from_pretrained("relik-ie/relik-relation-extraction-small")

    print("\n✅ SUCCESS! ReLiK relation extraction model loaded!")

    # Test on sample HVDC text
    test_text = """
    The HVDC converter station at TenneT's facility uses modular multilevel
    converter (MMC) technology. The system operates at 500 kV DC voltage
    and connects Germany to the Netherlands through submarine cables.
    """

    print("\n🧪 Testing extraction on HVDC text:")
    print(f"   Text: {test_text[:100].strip()}...")

    result = model(test_text)

    print(f"\n📊 Extraction results:")

    # Check entities
    if hasattr(result, 'entities'):
        print(f"\n   Entities found: {len(result.entities)}")
        for i, entity in enumerate(result.entities[:10], 1):  # Show first 10
            entity_text = entity.text if hasattr(entity, 'text') else str(entity)
            entity_label = entity.label if hasattr(entity, 'label') else 'Unknown'
            print(f"      {i}. {entity_text} ({entity_label})")

    # Check relations/triplets
    if hasattr(result, 'triplets'):
        print(f"\n   Relations found: {len(result.triplets)}")
        for i, triplet in enumerate(result.triplets[:10], 1):  # Show first 10
            if hasattr(triplet, 'subject'):
                subj = triplet.subject.text if hasattr(triplet.subject, 'text') else str(triplet.subject)
                rel = triplet.label if hasattr(triplet, 'label') else 'related_to'
                obj = triplet.object.text if hasattr(triplet.object, 'text') else str(triplet.object)
                print(f"      {i}. ({subj}) --[{rel}]--> ({obj})")

    print("\n🎉 ReLiK relation extraction is ready for production use!")
    print("\n📝 Next steps:")
    print("   1. Run full comparison: python test_relik_vs_rebel.py")
    print("   2. Build KG: python build_relik_kg.py")

    sys.exit(0)

except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("   Please install: pip install relik")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ FAILED to load ReLiK model")
    print(f"   Error: {e}")
    print(f"   Error type: {type(e).__name__}")

    # Check if it's a network/download error
    if "connection" in str(e).lower() or "timeout" in str(e).lower():
        print("\n⚠️  Network connection error. Try again or use manual download.")
    elif "404" in str(e) or "not found" in str(e).lower():
        print("\n⚠️  Model not found. Check model name or try a different model.")
    else:
        print("\n⚠️  Unknown error. Trying alternative approaches...")

    print("\n📝 Alternative models to try:")
    print("   1. relik-ie/relik-cie-small (closed information extraction)")
    print("   2. sapienzanlp/relik-reader-deberta-v3-base-aida (reader only)")
    print("   3. Manual download with git-lfs")

    sys.exit(1)