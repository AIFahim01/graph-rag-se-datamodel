"""
Contrastive learning trainer for custom embeddings
"""

from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
from typing import List, Dict
from loguru import logger


class ContrastiveTrainer:
    """
    Train custom embedding model using contrastive learning

    Uses Multiple Negatives Ranking Loss (MNRL) with structure-based
    training pairs from documents.
    """

    def __init__(self, base_model: str = "BAAI/bge-large-en-v1.5"):
        """
        Initialize trainer

        Args:
            base_model: Pre-trained model to fine-tune
        """
        self.base_model_name = base_model
        self.model = None
        self.logger = logger

    def train(
        self,
        training_pairs: List[Dict],
        output_path: str,
        epochs: int = 3,
        batch_size: int = 32,
        learning_rate: float = 2e-5,
        warmup_steps: int = 100
    ) -> SentenceTransformer:
        """
        Train custom embedding model with contrastive learning

        Args:
            training_pairs: List of pair dicts from TrainingPairGenerator
            output_path: Where to save trained model
            epochs: Number of training epochs
            batch_size: Batch size per GPU
            learning_rate: Learning rate
            warmup_steps: Warmup steps

        Returns:
            Trained SentenceTransformer model
        """
        self.logger.info(f"Loading base model: {self.base_model_name}")
        self.model = SentenceTransformer(self.base_model_name)

        # Prepare training examples
        train_examples = []
        for pair in training_pairs:
            example = InputExample(
                texts=[pair['chunk_a']['text'], pair['chunk_b']['text']],
                label=1.0  # Positive pair
            )
            train_examples.append(example)

        # Split train/validation (90/10)
        split_idx = int(0.9 * len(train_examples))
        train_data = train_examples[:split_idx]
        val_data = train_examples[split_idx:]

        self.logger.info(f"Training: {len(train_data)} pairs, Validation: {len(val_data)} pairs")

        # Create data loader
        train_dataloader = DataLoader(train_data, shuffle=True, batch_size=batch_size)

        # Define loss (MNRL - Multiple Negatives Ranking Loss)
        train_loss = losses.MultipleNegativesRankingLoss(self.model)

        # Create evaluator
        from sentence_transformers import evaluation
        evaluator = evaluation.EmbeddingSimilarityEvaluator(
            sentences1=[ex.texts[0] for ex in val_data[:1000]],
            sentences2=[ex.texts[1] for ex in val_data[:1000]],
            scores=[1.0] * min(1000, len(val_data)),
            name="validation"
        )

        # Train
        self.logger.info("Starting training...")
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            evaluator=evaluator,
            epochs=epochs,
            warmup_steps=warmup_steps,
            output_path=output_path,
            show_progress_bar=True,
            evaluation_steps=500,
            save_best_model=True
        )

        self.logger.info(f"Training complete! Model saved to {output_path}")
        return self.model
