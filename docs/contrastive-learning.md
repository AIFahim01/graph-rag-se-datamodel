# Contrastive Learning for Document Embeddings

## What is Contrastive Learning?

Contrastive learning is a training method that teaches models by showing examples of what's similar and what's different, rather than requiring explicit category labels.

## Core Concept

**Traditional Supervised Learning**:
```
Input: "The voltage rating is 690V"
Label: Category = "Electrical"

Problem: Requires manual labeling
```

**Contrastive Learning**:
```
Positive Pair: "690V rating" ↔ "Circuit breaker for 690V" (SIMILAR)
Negative Pair: "690V rating" ↔ "Training schedule" (DIFFERENT)

Model learns: What makes things similar/different
```

## Training from Document Structure

### Why No Q&A Generation?

Our approach uses document structure as training signal:

**Positive Pairs (Similar)**:
- Adjacent chunks in same PDF (90-95% confidence)
- Same section chunks (75-85% confidence)
- Cross-PDF chunks sharing technical terms (65-75% confidence)

**Negative Pairs (Different)**:
- Chunks from different PDFs (in-batch negatives)
- Automatically generated during training

### Training Pair Examples

```
POSITIVE:
Chunk A (Page 5): "Voltage specifications include..."
Chunk B (Page 5): "...690V AC three-phase power..."
→ Adjacent in document → Similar

NEGATIVE:
Chunk A (electrical_spec.pdf): "690V specifications..."
Chunk C (training_manual.pdf): "Employee procedures..."
→ Different documents → Different
```

## Multiple Negatives Ranking Loss (MNRL)

### Why MNRL?

- Uses in-batch negatives (free negatives from batch)
- More efficient than triplet loss
- State-of-the-art for retrieval tasks

### How It Works

```
Batch of 32 pairs:
Q1 → D1 (correct)
Q2 → D2 (correct)
...
Q32 → D32 (correct)

For Q1:
- Positive: D1
- Negatives: D2, D3, ..., D32 (other docs in batch)

Loss = -log(exp(sim(Q1,D1)) / Σexp(sim(Q1,Di)))

Goal: Rank D1 highest for Q1
```

## Label Noise Tolerance

### Expected Noise

20-30% of auto-generated pairs may be incorrect:
- Adjacent chunks crossing section boundaries
- False positives from shared common words
- Cross-PDF mismatches

### Why It's OK

Models learn from consistent signals:
- Correct pairs: 70-80% (consistent pattern)
- Wrong pairs: 20-30% (random noise)
- Over thousands of steps: Correct pattern dominates

**Research**: Models proven to tolerate 30-40% label noise

## Research Foundation

### SimCSE (Princeton NLP, 2021)

**Paper**: https://arxiv.org/abs/2104.08821

**Key Finding**: Unsupervised contrastive learning with only dropout noise achieves competitive results

**Relevance**: Proves structure-based training works

### BGE Models (BAAI, 2023)

**GitHub**: https://github.com/FlagOpen/FlagEmbedding

**Method**: RetroMAE pre-training + contrastive fine-tuning

**Relevance**: Our base model, state-of-the-art results

### E5 Embeddings (Microsoft, 2022)

**Paper**: https://arxiv.org/abs/2212.03533

**Method**: Weak supervision from document structure (title-body, anchor-link)

**Relevance**: Validates using document structure for training

## Implementation

See `src/training/` for complete implementation:
- `pair_generator.py` - Structure-based pair generation
- `trainer.py` - Contrastive learning with MNRL

## Further Reading

- [Contrastive Representation Learning](https://lilianweng.github.io/posts/2021-05-31-contrastive/) by Lilian Weng
- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [MTEB Benchmark](https://huggingface.co/spaces/mteb/leaderboard)
