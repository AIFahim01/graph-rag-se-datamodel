"""
Flexible Neo4j Vector Store - Supports Custom Node Labels
Extended version for testing new vectorization alongside old data
"""

import time
from typing import List, Dict, Optional
import numpy as np
from neo4j import GraphDatabase
from loguru import logger


class Neo4jVectorStoreFlexible:
    """Neo4j vector storage with configurable node labels"""

    def __init__(self, uri: str = "bolt://localhost:7687", auth=None,
                 node_label: str = "Chunk"):
        """
        Initialize Neo4j vector store with custom node label

        Args:
            uri: Neo4j connection URI
            auth: Authentication tuple (username, password) or None
            node_label: Custom node label (default: "Chunk")
        """
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.node_label = node_label
        logger.info(f"Connected to Neo4j at {uri} with label '{node_label}'")

    def close(self):
        """Close driver connection"""
        self.driver.close()

    def create_vector_index(self, index_name: str = "chunk_embeddings",
                           dimensions: int = 1024):
        """
        Create vector index for similarity search

        Args:
            index_name: Name of the vector index
            dimensions: Embedding dimensions (1024 for BGE-large)
        """
        with self.driver.session() as session:
            # Drop if exists
            try:
                session.run(f"DROP INDEX {index_name} IF EXISTS")
            except:
                pass

            # Create vector index with configurable label
            session.run(f"""
                CREATE VECTOR INDEX {index_name}
                FOR (c:{self.node_label})
                ON (c.embedding)
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {dimensions},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
            """)

            logger.info(f"Created vector index: {index_name} for label '{self.node_label}'")

            # Wait for index to be online
            max_wait = 60
            for i in range(max_wait):
                time.sleep(1)
                result = session.run(f"""
                    SHOW INDEXES
                    YIELD name, state
                    WHERE name = '{index_name}'
                    RETURN state
                """)
                record = result.single()
                if record and record['state'] == 'ONLINE':
                    logger.info(f"Vector index online (took {i+1}s)")
                    return True

            logger.warning("Vector index creation timeout")
            return False

    def create_metadata_indexes(self):
        """Create indexes on metadata fields for fast filtering"""
        with self.driver.session() as session:
            # Create indexes with custom label
            session.run(f"CREATE INDEX {self.node_label.lower()}_project IF NOT EXISTS FOR (c:{self.node_label}) ON (c.project_id)")
            session.run(f"CREATE INDEX {self.node_label.lower()}_customer IF NOT EXISTS FOR (c:{self.node_label}) ON (c.customer_normalized)")
            session.run(f"CREATE INDEX {self.node_label.lower()}_category IF NOT EXISTS FOR (c:{self.node_label}) ON (c.category)")
            session.run(f"CREATE INDEX {self.node_label.lower()}_technology IF NOT EXISTS FOR (c:{self.node_label}) ON (c.technology)")

            logger.info(f"Created metadata indexes for label '{self.node_label}'")

    def store_chunk_batch(self, chunks: List[Dict], embeddings: np.ndarray):
        """
        Store batch of chunks with embeddings and metadata

        Args:
            chunks: List of chunk dictionaries with metadata
            embeddings: Numpy array of embeddings (shape: [n, 1024])
        """
        with self.driver.session() as session:
            for chunk, embedding in zip(chunks, embeddings):
                # Build properties dynamically
                properties = {
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'embedding': embedding.tolist(),

                    # Core metadata
                    'project_id': chunk.get('project_id', 'Unknown'),
                    'project_name': chunk.get('project_name', 'Unknown'),
                    'customer': chunk.get('customer', 'Unknown'),
                    'customer_normalized': chunk.get('customer_normalized', 'unknown'),
                    'category': chunk.get('category', 'unknown'),
                    'technology': chunk.get('technology', 'Unknown'),
                    'document_type': chunk.get('document_type', 'other'),

                    # Document info
                    'source_file': chunk.get('source_file', 'Unknown'),
                    'page': chunk.get('page', 0),
                    'page_file': chunk.get('page_file', ''),

                    # From metadata.json
                    'file_name': chunk.get('file_name', ''),
                    'file_path': chunk.get('file_path', ''),
                    'extracted_at': chunk.get('extracted_at', ''),
                    'total_pages': chunk.get('total_pages', 0),
                    'total_images': chunk.get('total_images', 0),
                    'total_tables': chunk.get('total_tables', 0),

                    # Page image path
                    'page_image_relative': chunk.get('page_image_relative', ''),
                }

                # Create query with dynamic label
                session.run(f"""
                    CREATE (c:{self.node_label} $props)
                """, props=properties)

        logger.info(f"Stored {len(chunks)} chunks with label '{self.node_label}'")

    def vector_search(self, query_embedding: np.ndarray, top_k: int = 5,
                     filters: Optional[Dict] = None, index_name: str = "chunk_embeddings") -> List[Dict]:
        """
        Perform vector similarity search with optional metadata filters

        Args:
            query_embedding: Query vector (1024-dim)
            top_k: Number of results
            filters: Optional metadata filters
            index_name: Vector index to use

        Returns:
            List of matching chunks with scores
        """
        with self.driver.session() as session:
            # Build WHERE clause for filters
            where_clauses = []
            if filters:
                if 'customer' in filters:
                    where_clauses.append(f"node.customer_normalized = '{filters['customer'].lower()}'")
                if 'category' in filters:
                    where_clauses.append(f"node.category = '{filters['category']}'")
                if 'project_id' in filters:
                    where_clauses.append(f"node.project_id = '{filters['project_id']}'")

            where_clause = " AND ".join(where_clauses) if where_clauses else "true"

            # Query with configurable index
            result = session.run(f"""
                CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
                YIELD node, score
                WHERE {where_clause}
                RETURN node.chunk_id AS chunk_id,
                       node.text AS text,
                       node.project_id AS project_id,
                       node.project_name AS project_name,
                       node.customer AS customer,
                       node.category AS category,
                       node.technology AS technology,
                       node.document_type AS document_type,
                       node.source_file AS source_file,
                       node.page AS page,
                       node.file_name AS file_name,
                       node.total_pages AS total_pages,
                       node.total_images AS total_images,
                       node.total_tables AS total_tables,
                       node.page_image_relative AS page_image_relative,
                       score
                ORDER BY score DESC
            """,
                index_name=index_name,
                top_k=top_k,
                query_embedding=query_embedding.tolist()
            )

            results = []
            for record in result:
                results.append({
                    'chunk_id': record['chunk_id'],
                    'text': record['text'],
                    'project_id': record['project_id'],
                    'project_name': record['project_name'],
                    'customer': record['customer'],
                    'category': record['category'],
                    'technology': record['technology'],
                    'document_type': record['document_type'],
                    'source_file': record['source_file'],
                    'page': record['page'],
                    'file_name': record['file_name'],
                    'total_pages': record['total_pages'],
                    'total_images': record['total_images'],
                    'total_tables': record['total_tables'],
                    'page_image_relative': record['page_image_relative'],
                    'score': float(record['score'])
                })

            return results

    def clear_all_chunks(self):
        """Delete all chunks with this label"""
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH (c:{self.node_label})
                DELETE c
            """)
            logger.info(f"Cleared all nodes with label '{self.node_label}'")

    def count_chunks(self) -> int:
        """Count total chunks with this label"""
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH (c:{self.node_label})
                RETURN count(c) AS count
            """)
            record = result.single()
            return record['count'] if record else 0
