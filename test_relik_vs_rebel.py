#!/usr/bin/env python3
"""
Test ReLiK vs REBEL for Entity Extraction
Compares speed, accuracy, and entity quality
"""

import sys
import json
import time
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print("\n" + "=" * 80)
print("RELIK vs REBEL COMPARISON TEST")
print("=" * 80)

# Load chunks
chunks_file = PROJECT_ROOT / "data" / "graphrag_complete" / "graphrag_chunks.json"
print(f"\n📄 Loading chunks from: {chunks_file}")

with open(chunks_file) as f:
    all_chunks = json.load(f)

print(f"✅ Loaded {len(all_chunks):,} chunks")

# Select sample chunks for testing (from first project)
sample_size = 50
test_chunks = all_chunks[:sample_size]

print(f"\n🧪 Testing with {sample_size} sample chunks")
print(f"   Sample from: {test_chunks[0].get('project', 'unknown')}")

# =============================================================================
# TEST 1: REBEL Extraction (Current Method)
# =============================================================================

print("\n" + "=" * 80)
print("TEST 1: REBEL EXTRACTION")
print("=" * 80)

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    print("\n📥 Loading REBEL model...")
    rebel_tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
    rebel_model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    rebel_model.to(device)
    print(f"✅ REBEL model loaded on {device}")

    rebel_entities = []
    rebel_triplets = []

    print(f"\n⏱️  Starting REBEL extraction on {sample_size} chunks...")
    rebel_start = time.time()

    for i, chunk in enumerate(test_chunks[:10], 1):  # Test on first 10 chunks
        text = chunk['text'][:512]  # Limit to 512 chars

        inputs = rebel_tokenizer(text, return_tensors="pt", padding=True,
                                truncation=True, max_length=512).to(device)

        with torch.no_grad():
            outputs = rebel_model.generate(inputs['input_ids'], max_length=256,
                                         num_beams=3, early_stopping=True)

        decoded = rebel_tokenizer.batch_decode(outputs, skip_special_tokens=False)[0]

        # Parse triplets (simplified)
        if '<triplet>' in decoded:
            triplets = decoded.split('<triplet>')
            for triplet in triplets[1:]:
                parts = triplet.split('<subj>')
                if len(parts) > 1:
                    rebel_triplets.append(triplet.strip())

        if i % 5 == 0:
            print(f"   Processed {i}/10 chunks...")

    rebel_time = time.time() - rebel_start

    print(f"\n✅ REBEL Results:")
    print(f"   ⏱️  Time: {rebel_time:.2f} seconds")
    print(f"   📊 Triplets extracted: {len(rebel_triplets)}")
    print(f"   ⚡ Speed: {len(rebel_triplets)/rebel_time:.2f} triplets/sec")

    print(f"\n   Sample triplets:")
    for triplet in rebel_triplets[:5]:
        print(f"      - {triplet[:100]}...")

    rebel_success = True

except Exception as e:
    print(f"❌ REBEL extraction failed: {e}")
    rebel_success = False
    rebel_time = 0
    rebel_triplets = []

# =============================================================================
# TEST 2: RELIK Extraction (New Method)
# =============================================================================

print("\n" + "=" * 80)
print("TEST 2: RELIK EXTRACTION")
print("=" * 80)

try:
    from relik import Relik
    import os

    # Ensure XET is disabled
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'

    print("\n📥 Loading ReLiK model...")
    print("   Using relation extraction model (proven to work)")

    # Load ReLiK relation extraction model that we confirmed works
    relik_model = Relik.from_pretrained("relik-ie/relik-relation-extraction-small")
    print("✅ ReLiK model loaded")

    relik_entities = []
    relik_relations = []

    print(f"\n⏱️  Starting ReLiK extraction on {sample_size} chunks...")
    relik_start = time.time()

    for i, chunk in enumerate(test_chunks[:10], 1):  # Test on first 10 chunks
        text = chunk['text'][:512]  # Limit to 512 chars

        # Extract entities and relations
        result = relik_model(text)

        # Collect entities
        if hasattr(result, 'entities'):
            for entity in result.entities:
                relik_entities.append({
                    'text': entity.text,
                    'label': entity.label if hasattr(entity, 'label') else 'Unknown',
                    'start': entity.start if hasattr(entity, 'start') else 0,
                    'end': entity.end if hasattr(entity, 'end') else 0
                })

        # Collect relations
        if hasattr(result, 'triplets'):
            for triplet in result.triplets:
                relik_relations.append({
                    'subject': triplet.subject.text,
                    'relation': triplet.label,
                    'object': triplet.object.text
                })

        if i % 5 == 0:
            print(f"   Processed {i}/10 chunks...")

    relik_time = time.time() - relik_start

    print(f"\n✅ ReLiK Results:")
    print(f"   ⏱️  Time: {relik_time:.2f} seconds")
    print(f"   📊 Entities extracted: {len(relik_entities)}")
    print(f"   📊 Relations extracted: {len(relik_relations)}")
    print(f"   ⚡ Speed: {len(relik_entities)/relik_time:.2f} entities/sec")

    print(f"\n   Sample entities:")
    for entity in relik_entities[:10]:
        print(f"      - {entity['text']} ({entity['label']})")

    if relik_relations:
        print(f"\n   Sample relations:")
        for rel in relik_relations[:5]:
            print(f"      - {rel['subject']} → {rel['relation']} → {rel['object']}")

    relik_success = True

except Exception as e:
    print(f"❌ ReLiK extraction failed: {e}")
    import traceback
    traceback.print_exc()
    relik_success = False
    relik_time = 0
    relik_entities = []
    relik_relations = []

# =============================================================================
# COMPARISON RESULTS
# =============================================================================

print("\n" + "=" * 80)
print("COMPARISON RESULTS")
print("=" * 80)

if rebel_success and relik_success:
    speedup = rebel_time / relik_time if relik_time > 0 else 0

    print(f"\n⚡ Speed Comparison:")
    print(f"   REBEL:  {rebel_time:.2f} seconds")
    print(f"   ReLiK:  {relik_time:.2f} seconds")
    print(f"   Speedup: {speedup:.1f}x faster with ReLiK")

    print(f"\n📊 Extraction Quality:")
    print(f"   REBEL triplets: {len(rebel_triplets)}")
    print(f"   ReLiK entities: {len(relik_entities)}")
    print(f"   ReLiK relations: {len(relik_relations)}")

    # Entity cleanliness check
    rebel_noisy = sum(1 for t in rebel_triplets if '</s' in t or '<obj>' in t)
    relik_noisy = sum(1 for e in relik_entities if '</s' in e['text'] or '<obj>' in e['text'])

    print(f"\n🧹 Entity Cleanliness:")
    print(f"   REBEL noisy entities: {rebel_noisy}/{len(rebel_triplets)} ({100*rebel_noisy/len(rebel_triplets) if rebel_triplets else 0:.1f}%)")
    print(f"   ReLiK noisy entities: {relik_noisy}/{len(relik_entities)} ({100*relik_noisy/len(relik_entities) if relik_entities else 0:.1f}%)")

    # Recommendation
    print(f"\n🎯 RECOMMENDATION:")
    if speedup > 5 and relik_noisy < rebel_noisy:
        print(f"   ✅ ReLiK is {speedup:.1f}x faster with cleaner entities!")
        print(f"   ✅ Recommended: Switch to ReLiK for production")
    elif speedup > 5:
        print(f"   ⚠️  ReLiK is {speedup:.1f}x faster but check entity quality")
    else:
        print(f"   ⚠️  Results are mixed, manual review recommended")

elif relik_success:
    print(f"\n✅ ReLiK extraction successful!")
    print(f"   Extracted {len(relik_entities)} entities in {relik_time:.2f}s")
    print(f"\n   🎯 RECOMMENDATION: ReLiK is working, proceed with full extraction")

else:
    print(f"\n❌ Both methods failed or ReLiK not available")
    print(f"   Check dependencies and GPU availability")

# =============================================================================
# SAVE RESULTS
# =============================================================================

results = {
    'test_date': '2025-11-11',
    'sample_size': 10,
    'rebel': {
        'success': rebel_success,
        'time': rebel_time,
        'triplets': len(rebel_triplets),
        'sample': rebel_triplets[:5] if rebel_triplets else []
    },
    'relik': {
        'success': relik_success,
        'time': relik_time,
        'entities': len(relik_entities),
        'relations': len(relik_relations),
        'sample_entities': relik_entities[:10] if relik_entities else [],
        'sample_relations': relik_relations[:5] if relik_relations else []
    }
}

output_file = PROJECT_ROOT / "test_results_relik_vs_rebel.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved to: {output_file}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
