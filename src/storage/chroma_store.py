"""
ChromaDB Storage Layer

Stores chunk embeddings in ChromaDB with metadata.
"""

import os
from typing import List, Dict
from loguru import logger
import chromadb
from chromadb.config import Settings


class ChromaVectorStore:
    """ChromaDB storage for vector embeddings"""

    def __init__(self, host: str = None, port: int = None, token: str = None):
        """
        Initialize ChromaDB client

        Args:
            host: ChromaDB host (from .env if None)
            port: ChromaDB port (from .env if None)
            token: Auth token (from .env if None)
        """
        # Use local ChromaDB on port 8002 (Docker container)
        self.host = host or os.getenv('CHROMADB_HOST', 'localhost')
        self.port = port or int(os.getenv('CHROMADB_PORT', '8002'))
        self.token = token or os.getenv('CHROMADB_TOKEN', '')

        logger.info(f"Connecting to ChromaDB at {self.host}:{self.port}")

        # Connect to ChromaDB
        if self.token:
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                headers={"Authorization": f"Bearer {self.token}"}
            )
        else:
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port
            )

        logger.info("✓ Connected to ChromaDB")

    def create_collection(self, collection_name: str):
        """Create or get collection"""
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"GraphRAG collection for {collection_name}"}
            )
            logger.info(f"✓ Collection '{collection_name}' ready")
            return collection
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    def insert_chunks(
        self,
        collection_name: str,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ):
        """
        Insert chunks with embeddings into collection

        Args:
            collection_name: Name of collection
            chunks: List of chunk dicts
            embeddings: List of embedding vectors
        """
        collection = self.create_collection(collection_name)

        # Prepare data for insertion (use embedding_index for truly unique IDs)
        ids = [f"{chunk.get('project', 'unknown')}_{chunk.get('source', 'doc')}_{chunk.get('embedding_index', idx)}"
               for idx, chunk in enumerate(chunks)]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [
            {
                'project': chunk.get('project', 'unknown'),
                'source': chunk.get('source', ''),
                'page': chunk.get('page', 0),
                'source_path': chunk.get('source_path', '')
            }
            for chunk in chunks
        ]

        # Insert
        logger.info(f"Inserting {len(chunks)} chunks into '{collection_name}'...")
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        logger.info(f"✓ Inserted {len(chunks)} chunks")

    def query(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 5
    ) -> Dict:
        """
        Query collection for similar chunks

        Args:
            collection_name: Collection to query
            query_embedding: Query vector
            n_results: Number of results

        Returns:
            Dict with results
        """
        collection = self.client.get_collection(collection_name)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        logger.info(f"✓ Retrieved {len(results['ids'][0])} results")
        return results
