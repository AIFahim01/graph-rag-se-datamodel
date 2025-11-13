"""
Vector Generation using Sentence Transformers

Generates embeddings for chunks and entities using pre-trained models.
"""

import numpy as np
from pathlib import Path
from typing import List, Dict, Union
from loguru import logger
from sentence_transformers import SentenceTransformer


class VectorGenerator:
    """Generate vector embeddings for text chunks and entities"""

    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5"):
        """
        Initialize vector generator

        Args:
            model_name: HuggingFace model name or path to custom model
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")

    def embed_chunks(self, chunks: List[Dict]) -> np.ndarray:
        """
        Generate embeddings for text chunks

        Args:
            chunks: List of chunk dicts with 'text' key

        Returns:
            numpy array of shape (n_chunks, embedding_dim)
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")

        texts = [chunk['text'] for chunk in chunks]

        # Generate embeddings in batch
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )

        logger.info(f"✓ Generated embeddings: shape {embeddings.shape}")
        return embeddings

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for list of texts

        Args:
            texts: List of text strings

        Returns:
            numpy array of embeddings
        """
        logger.info(f"Generating embeddings for {len(texts)} texts...")

        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32,
            normalize_embeddings=True
        )

        logger.info(f"✓ Generated embeddings: shape {embeddings.shape}")
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query

        Args:
            query: Query text

        Returns:
            1D numpy array of embedding
        """
        embedding = self.model.encode(
            query,
            normalize_embeddings=True
        )

        return embedding

    def save_embeddings(
        self,
        embeddings: np.ndarray,
        output_path: Union[str, Path],
        metadata: Dict = None
    ):
        """
        Save embeddings to file

        Args:
            embeddings: numpy array
            output_path: Path to save .npy file
            metadata: Optional metadata dict to save alongside
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save embeddings
        np.save(output_path, embeddings)
        logger.info(f"✓ Saved embeddings to: {output_path}")

        # Save metadata if provided
        if metadata:
            import json
            metadata_path = output_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"✓ Saved metadata to: {metadata_path}")

    def load_embeddings(self, path: Union[str, Path]) -> np.ndarray:
        """Load embeddings from file"""
        embeddings = np.load(path)
        logger.info(f"✓ Loaded embeddings: shape {embeddings.shape}")
        return embeddings
