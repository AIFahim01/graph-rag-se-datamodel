"""
Hybrid Retriever - Combines Vector Search + Graph Traversal

Implements multi-level retrieval:
1. Vector search in ChromaDB (semantic similarity)
2. Graph traversal in Neo4j (relationship discovery)
3. Result fusion and ranking
"""

import os
from typing import List, Dict, Tuple
from loguru import logger
import numpy as np


class HybridRetriever:
    """Hybrid retrieval combining vector search and graph traversal"""

    def __init__(self, vector_store, graph_store, embedding_generator):
        """
        Initialize hybrid retriever

        Args:
            vector_store: ChromaVectorStore instance
            graph_store: Neo4jGraphStore instance
            embedding_generator: VectorGenerator instance
        """
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedding_gen = embedding_generator

        # Fusion weights
        self.weights = {
            'vector': 0.6,    # Vector similarity
            'graph': 0.4      # Graph relevance
        }

        logger.info("Hybrid retriever initialized")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        include_graph: bool = True
    ) -> List[Dict]:
        """
        Retrieve relevant chunks using hybrid approach

        Args:
            query: User query
            top_k: Number of results
            include_graph: Whether to include graph traversal

        Returns:
            List of ranked results with scores and sources
        """
        logger.info(f"Retrieving for query: '{query}'")

        # Step 1: Vector search (ChromaDB)
        vector_results = self._vector_search(query, top_k=top_k * 2)

        if not include_graph:
            return vector_results[:top_k]

        # Step 2: Extract entities from query
        query_entities = self._extract_query_entities(query, vector_results)

        # Step 3: Graph traversal (Neo4j)
        graph_results = self._graph_search(query_entities, max_results=top_k)

        # Step 4: Fusion and ranking
        fused_results = self._fuse_results(vector_results, graph_results, top_k)

        logger.info(f"✓ Retrieved {len(fused_results)} results")
        return fused_results

    def _vector_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Vector similarity search in ChromaDB

        Returns:
            List of chunks with similarity scores
        """
        logger.info(f"  Vector search (top {top_k})...")

        # Generate query embedding
        query_embedding = self.embedding_gen.embed_query(query)

        # Search ChromaDB
        results = self.vector_store.query(
            collection_name='graphrag_chunks',
            query_embedding=query_embedding.tolist(),
            n_results=top_k
        )

        # Format results
        formatted = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            formatted.append({
                'text': doc,
                'project': metadata.get('project', 'unknown'),
                'source': metadata.get('source', 'unknown'),
                'page': metadata.get('page', 0),
                'vector_score': 1 - distance,  # Convert distance to similarity
                'source_type': 'vector',
                'rank': i + 1
            })

        logger.info(f"    ✓ Found {len(formatted)} vector results")
        return formatted

    def _extract_query_entities(self, query: str, vector_results: List[Dict]) -> List[str]:
        """Extract potential entities from query and top results"""
        entities = set()

        # Check for date patterns (e.g., "October 29, 2025")
        import re
        date_patterns = [
            r'[A-Z][a-z]+ \d{1,2},? \d{4}',  # October 29, 2025
            r'\d{4}-\d{2}-\d{2}',              # 2025-10-29
            r'\d{1,2}/\d{1,2}/\d{4}'           # 10/29/2025
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                entities.add(match.strip())

        # Extract multi-word capitalized phrases (up to 3 words)
        words = query.split()
        for i in range(len(words)):
            # Single word
            cleaned = words[i].strip('.,;:?()')
            if cleaned and len(cleaned) > 2 and cleaned[0].isupper():
                entities.add(cleaned)

            # Two-word phrases
            if i < len(words) - 1:
                phrase2 = f"{words[i]} {words[i+1]}".strip('.,;:?()')
                if phrase2 and phrase2[0].isupper():
                    entities.add(phrase2)

            # Three-word phrases
            if i < len(words) - 2:
                phrase3 = f"{words[i]} {words[i+1]} {words[i+2]}".strip('.,;:?()')
                if phrase3 and phrase3[0].isupper():
                    entities.add(phrase3)

        # Extract from top vector results
        for result in vector_results[:2]:
            text = result['text']
            text_words = text.split()
            for word in text_words:
                cleaned = word.strip('.,;:()')
                if cleaned and len(cleaned) > 3 and cleaned[0].isupper():
                    entities.add(cleaned)

        # Return prioritized list (longer phrases first)
        entity_list = list(entities)
        entity_list.sort(key=lambda x: len(x.split()), reverse=True)

        return entity_list[:10]  # Top 10 entities

    def _graph_search(self, entities: List[str], max_results: int = 5) -> List[Dict]:
        """
        Search Neo4j graph for related entities

        Args:
            entities: List of entity names to search
            max_results: Maximum results

        Returns:
            List of graph-discovered chunks
        """
        if not entities:
            return []

        logger.info(f"  Graph search for entities: {entities[:3]}...")

        graph_chunks = []

        for entity in entities:
            try:
                # Find neighbors in graph
                neighbors = self.graph_store.query_entity_neighbors(
                    entity_name=entity,
                    max_hops=2
                )

                for neighbor in neighbors[:2]:  # Top 2 neighbors per entity
                    graph_chunks.append({
                        'entity': entity,
                        'related_entity': neighbor['entity'],
                        'distance': neighbor['distance'],
                        'source_type': 'graph',
                        'graph_score': 1.0 / (neighbor['distance'] + 1),  # Closer = higher score
                        'project': 'Knowledge Graph',
                        'source': f"{entity} → {neighbor['entity']}",
                        'page': neighbor['distance'],
                        'text': f"Graph relationship: {entity} is connected to {neighbor['entity']} (distance: {neighbor['distance']} hops)"
                    })

            except Exception as e:
                logger.warning(f"    Graph search failed for '{entity}': {e}")
                continue

        logger.info(f"    ✓ Found {len(graph_chunks)} graph results")
        return graph_chunks[:max_results]

    def _fuse_results(
        self,
        vector_results: List[Dict],
        graph_results: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """
        Fuse and rank results from vector and graph search

        Args:
            vector_results: Results from vector search
            graph_results: Results from graph search
            top_k: Number of final results

        Returns:
            Fused and ranked results
        """
        logger.info("  Fusing results...")

        # Score vector results
        for result in vector_results:
            result['final_score'] = (
                result['vector_score'] * self.weights['vector']
            )

        # Score graph results
        for result in graph_results:
            result['final_score'] = (
                result['graph_score'] * self.weights['graph']
            )

        # Combine and sort
        all_results = vector_results + graph_results
        all_results.sort(key=lambda x: x.get('final_score', 0), reverse=True)

        # Deduplicate and return top k
        seen = set()
        final_results = []

        for result in all_results:
            # Use text or entity as dedup key
            key = result.get('text', result.get('entity', ''))[:100]

            if key not in seen:
                seen.add(key)
                final_results.append(result)

                if len(final_results) >= top_k:
                    break

        logger.info(f"    ✓ Fused to {len(final_results)} final results")
        return final_results
