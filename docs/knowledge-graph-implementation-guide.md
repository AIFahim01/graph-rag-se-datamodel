# Knowledge Graph Implementation Guide for PDF Vector Search Service

## Executive Summary

This guide outlines how to integrate Neo4j Knowledge Graph capabilities into your existing PDF extraction and vector search service. The integration will complement your current ChromaDB vector search with structured relationship-based querying.

---

## 1. Current Architecture Analysis

### Existing Components
- ✅ **PDF Processing**: Text, table, and image extraction
- ✅ **Vector Search**: ChromaDB with embeddings
- ✅ **Chunking**: Text splitting for semantic search
- ✅ **Multi-environment**: Dev/Staging/Production setup

### Gap Analysis
- ❌ **Structured Relationships**: No entity-relationship mapping
- ❌ **Graph Queries**: Cannot traverse document relationships
- ❌ **Entity Linking**: Entities across documents not connected
- ❌ **Knowledge Organization**: Flat document structure

---

## 2. Knowledge Graph Integration Strategy

### Hybrid Architecture: Vector + Graph

```
┌─────────────────────────────────────────────────────────────┐
│                    PDF Document Input                        │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────────┐
│  Text Extractor │    │   PDF Metadata      │
│   (Existing)    │    │   (Existing)        │
└────────┬────────┘    └──────────┬──────────┘
         │                        │
         │            ┌───────────┴──────────┐
         │            │                      │
         ▼            ▼                      ▼
┌─────────────┐  ┌──────────────┐  ┌────────────────┐
│   Chunks    │  │   Entities   │  │ Relationships  │
│ (ChromaDB)  │  │  (Neo4j KG)  │  │   (Neo4j KG)   │
└─────────────┘  └──────────────┘  └────────────────┘
         │            │                      │
         └────────────┴──────────────────────┘
                     │
                     ▼
         ┌──────────────────────┐
         │   Unified Query API  │
         │ - Vector Search      │
         │ - Graph Traversal    │
         │ - Hybrid Results     │
         └──────────────────────┘
```

### Benefits of This Approach

1. **Vector Search** (ChromaDB): Semantic similarity, fuzzy matching
2. **Graph Search** (Neo4j): Precise relationships, entity connections
3. **Hybrid Queries**: "Find documents similar to X that are connected to entity Y"

---

## 3. Neo4j GraphRAG Pipeline Design

### 3.1 Schema Design for Your Domain

Based on typical document processing use cases:

```python
# app/services/knowledge_graph/schema.py

NODE_TYPES = [
    # Core document entities
    {
        "label": "Document",
        "description": "A processed PDF document",
        "properties": [
            {"name": "doc_id", "type": "STRING", "required": True},
            {"name": "filename", "type": "STRING", "required": True},
            {"name": "extraction_method", "type": "STRING"},
            {"name": "processed_date", "type": "DATE"},
            {"name": "total_pages", "type": "INTEGER"}
        ]
    },
    # Text chunks (linked to vector DB)
    {
        "label": "Chunk",
        "description": "A text chunk from a document",
        "properties": [
            {"name": "chunk_id", "type": "STRING", "required": True},
            {"name": "text", "type": "STRING", "required": True},
            {"name": "page_number", "type": "INTEGER"},
            {"name": "chunk_index", "type": "INTEGER"},
            {"name": "embedding_id", "type": "STRING"}  # Links to ChromaDB
        ]
    },
    # Entities extracted from content
    {
        "label": "Person",
        "description": "A person mentioned in documents",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "role", "type": "STRING"},
            {"name": "organization", "type": "STRING"}
        ]
    },
    {
        "label": "Organization",
        "description": "An organization mentioned in documents",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "type", "type": "STRING"},
            {"name": "industry", "type": "STRING"}
        ]
    },
    {
        "label": "Concept",
        "description": "Key concepts or topics",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "category", "type": "STRING"},
            {"name": "description", "type": "STRING"}
        ]
    },
    {
        "label": "Date",
        "description": "Important dates mentioned",
        "properties": [
            {"name": "value", "type": "DATE", "required": True},
            {"name": "context", "type": "STRING"}
        ]
    },
    {
        "label": "Location",
        "description": "Geographic locations",
        "properties": [
            {"name": "name", "type": "STRING", "required": True},
            {"name": "country", "type": "STRING"},
            {"name": "coordinates", "type": "STRING"}
        ]
    }
]

RELATIONSHIP_TYPES = [
    # Document structure
    {"label": "CONTAINS_CHUNK", "description": "Document contains chunk"},
    {"label": "NEXT_CHUNK", "description": "Sequential chunk relationship"},

    # Entity relationships
    {"label": "MENTIONS", "description": "Chunk mentions entity"},
    {"label": "EXTRACTED_FROM", "description": "Entity extracted from chunk"},

    # Entity-to-entity relationships
    {"label": "WORKS_FOR", "description": "Person works for organization"},
    {"label": "LOCATED_IN", "description": "Entity located in location"},
    {"label": "RELATED_TO", "description": "General relationship between concepts"},
    {"label": "OCCURRED_ON", "description": "Event occurred on date"},

    # Cross-document relationships
    {"label": "REFERENCES", "description": "Document references another document"},
    {"label": "SIMILAR_TO", "description": "Documents are similar"}
]

PATTERNS = [
    # Document structure
    ("Document", "CONTAINS_CHUNK", "Chunk"),
    ("Chunk", "NEXT_CHUNK", "Chunk"),

    # Entity extraction
    ("Chunk", "MENTIONS", "Person"),
    ("Chunk", "MENTIONS", "Organization"),
    ("Chunk", "MENTIONS", "Concept"),
    ("Chunk", "MENTIONS", "Location"),
    ("Person", "EXTRACTED_FROM", "Chunk"),
    ("Organization", "EXTRACTED_FROM", "Chunk"),

    # Entity relationships
    ("Person", "WORKS_FOR", "Organization"),
    ("Person", "LOCATED_IN", "Location"),
    ("Organization", "LOCATED_IN", "Location"),
    ("Concept", "RELATED_TO", "Concept"),
    ("Person", "RELATED_TO", "Concept"),

    # Document relationships
    ("Document", "REFERENCES", "Document"),
    ("Document", "SIMILAR_TO", "Document")
]
```

### 3.2 Pipeline Configuration

Create a configuration file for the KG builder:

```yaml
# config/kg_pipeline_config.yaml

version_: 1
template_: SimpleKGPipeline

# Neo4j Configuration
neo4j_config:
  params_:
    uri:
      resolver_: ENV
      var_: NEO4J_URI
    user: neo4j
    password:
      resolver_: ENV
      var_: NEO4J_PASSWORD
    database: neo4j

# LLM Configuration (using Azure OpenAI from your setup)
llm_config:
  class_: AzureOpenAILLM
  params_:
    api_key:
      resolver_: ENV
      var_: AZURE_API_KEY
    azure_endpoint:
      resolver_: ENV
      var_: AZURE_API_BASE
    api_version:
      resolver_: ENV
      var_: AZURE_API_VERSION
    model_name: gpt-4o  # or your preferred model
    model_params:
      temperature: 0
      max_tokens: 2000
      response_format:
        type: json_object

# Embedder Configuration (reuse your existing OpenAI setup)
embedder_config:
  class_: OpenAIEmbeddings
  params_:
    api_key:
      resolver_: ENV
      var_: OPENAI_API_KEY
    model: text-embedding-ada-002

# Pipeline Settings
from_pdf: false  # We already extract text
perform_entity_resolution: true
neo4j_database: documents_kg

# Error handling
on_error: IGNORE  # Continue processing even if some chunks fail

# Schema (loaded from Python module)
schema:
  node_types: []  # Will be loaded from schema.py
  relationship_types: []
  patterns: []

# Text splitter configuration (match your existing setup)
text_splitter:
  class_: text_splitters.FixedSizeSplitter
  params_:
    chunk_size: 1000
    chunk_overlap: 200

# Lexical graph configuration
lexical_graph_config:
  chunk_node_label: Chunk
  document_node_label: Document
  chunk_to_document_relationship_type: PART_OF
  next_chunk_relationship_type: NEXT_CHUNK
```

---

## 4. Implementation Roadmap

### Phase 1: Setup & Infrastructure (Week 1)

#### 1.1 Add Dependencies

```bash
# Add to requirements-dev.txt
neo4j==5.14.0
neo4j-graphrag==0.2.0
```

#### 1.2 Update Docker Compose

```yaml
# Add to docker-compose.yml

  neo4j:
    image: neo4j:5.14.0
    container_name: neo4j-kg
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-password}
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_dbms_security_procedures_unrestricted: apoc.*,gds.*
      NEO4J_dbms_memory_heap_max__size: 2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    networks:
      - app_network
    profiles:
      - dev
      - stage
      - prod
      - all

volumes:
  neo4j_data:
  neo4j_logs:
```

#### 1.3 Environment Variables

```bash
# Add to .env
NEO4J_URI=bolt://neo4j:7687
NEO4J_PASSWORD=your_secure_password
NEO4J_DATABASE=documents_kg
```

#### 1.4 Update Configuration

```python
# Add to app/config.py

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "documents_kg")

# Knowledge Graph Configuration
KG_ENABLED = os.getenv("KG_ENABLED", "true").lower() == "true"
KG_ENTITY_RESOLUTION = os.getenv("KG_ENTITY_RESOLUTION", "true").lower() == "true"
KG_SCHEMA_PATH = BASE_DIR / "config" / "kg_schema.json"
```

### Phase 2: Core Integration (Week 2)

#### 2.1 Create KG Service Module

```python
# app/services/knowledge_graph/__init__.py

from .kg_builder import KnowledgeGraphBuilder
from .kg_query import KnowledgeGraphQuery
from .schema import NODE_TYPES, RELATIONSHIP_TYPES, PATTERNS

__all__ = [
    "KnowledgeGraphBuilder",
    "KnowledgeGraphQuery",
    "NODE_TYPES",
    "RELATIONSHIP_TYPES",
    "PATTERNS"
]
```

#### 2.2 KG Builder Service

```python
# app/services/knowledge_graph/kg_builder.py

from typing import Dict, List, Optional
from pathlib import Path
import neo4j
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm import AzureOpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings

from app.config import (
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE,
    AZURE_API_KEY, AZURE_API_BASE, AZURE_API_VERSION,
    OPENAI_API_KEY
)
from app.utils.logging import get_logger
from .schema import NODE_TYPES, RELATIONSHIP_TYPES, PATTERNS


class KnowledgeGraphBuilder:
    """Builds Knowledge Graph from extracted PDF content."""

    def __init__(self):
        self.logger = get_logger("KGBuilder")

        # Initialize Neo4j driver
        self.driver = neo4j.GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

        # Initialize LLM
        self.llm = AzureOpenAILLM(
            api_key=AZURE_API_KEY,
            azure_endpoint=AZURE_API_BASE,
            api_version=AZURE_API_VERSION,
            model_name="gpt-4o",
            model_params={
                "temperature": 0,
                "max_tokens": 2000,
                "response_format": {"type": "json_object"}
            }
        )

        # Initialize embedder
        self.embedder = OpenAIEmbeddings(
            api_key=OPENAI_API_KEY,
            model="text-embedding-ada-002"
        )

        # Initialize KG Pipeline
        self.kg_pipeline = SimpleKGPipeline(
            llm=self.llm,
            driver=self.driver,
            embedder=self.embedder,
            from_pdf=False,  # We provide extracted text
            neo4j_database=NEO4J_DATABASE,
            schema={
                "node_types": NODE_TYPES,
                "relationship_types": RELATIONSHIP_TYPES,
                "patterns": PATTERNS
            },
            perform_entity_resolution=True,
            on_error="IGNORE"
        )

    async def build_from_extraction(
        self,
        extraction_result: Dict,
        project_name: Optional[str] = None
    ) -> Dict:
        """
        Build knowledge graph from PDF extraction results.

        Args:
            extraction_result: Result from PDFExtractor.process_pdf()
            project_name: Optional project categorization

        Returns:
            Dictionary with KG build statistics
        """
        try:
            doc_id = extraction_result['doc_id']
            file_name = extraction_result['file_name']

            # Extract text from results
            text_content = self._extract_text_content(extraction_result)

            if not text_content:
                self.logger.warning(f"No text content found in {file_name}")
                return {"status": "skipped", "reason": "no_text"}

            self.logger.info(f"Building KG for {file_name} ({len(text_content)} chars)")

            # Run KG pipeline
            await self.kg_pipeline.run_async(text=text_content)

            # Add document metadata node
            await self._add_document_metadata(
                doc_id, file_name, extraction_result, project_name
            )

            # Link chunks to vector DB embeddings
            await self._link_to_vector_db(doc_id, extraction_result)

            return {
                "status": "success",
                "doc_id": doc_id,
                "file_name": file_name,
                "text_length": len(text_content)
            }

        except Exception as e:
            self.logger.error(f"KG build failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _extract_text_content(self, extraction_result: Dict) -> str:
        """Extract combined text from extraction results."""
        content_parts = []

        # Extract text elements
        for text_elem in extraction_result.get('content', {}).get('text', []):
            if hasattr(text_elem, 'content'):
                content_parts.append(str(text_elem.content))

        # Extract table text
        for table_elem in extraction_result.get('content', {}).get('tables', []):
            if hasattr(table_elem, 'content'):
                content_parts.append(f"[TABLE] {str(table_elem.content)}")

        return "\n\n".join(content_parts)

    async def _add_document_metadata(
        self,
        doc_id: str,
        file_name: str,
        extraction_result: Dict,
        project_name: Optional[str]
    ):
        """Add document metadata node to graph."""
        query = """
        MERGE (d:Document {doc_id: $doc_id})
        SET d.filename = $file_name,
            d.extraction_method = $method,
            d.processed_date = datetime(),
            d.project_name = $project_name,
            d.total_pages = $total_pages,
            d.text_elements = $text_count,
            d.table_elements = $table_count,
            d.image_elements = $image_count
        """

        stats = extraction_result.get('stats', {})

        async with self.driver.session(database=NEO4J_DATABASE) as session:
            await session.run(query, {
                "doc_id": doc_id,
                "file_name": file_name,
                "method": extraction_result.get('extraction_method'),
                "project_name": project_name,
                "total_pages": stats.get('total_pages', 0),
                "text_count": stats.get('text_elements', 0),
                "table_count": stats.get('table_elements', 0),
                "image_count": stats.get('image_elements', 0)
            })

    async def _link_to_vector_db(self, doc_id: str, extraction_result: Dict):
        """Create links between KG chunks and ChromaDB embeddings."""
        # This creates a bridge between your vector DB and knowledge graph
        # Implementation depends on how you store chunk IDs in ChromaDB
        pass

    def close(self):
        """Close Neo4j driver."""
        if self.driver:
            self.driver.close()
```

#### 2.3 KG Query Service

```python
# app/services/knowledge_graph/kg_query.py

from typing import Dict, List, Optional
import neo4j
from app.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
from app.utils.logging import get_logger


class KnowledgeGraphQuery:
    """Query service for Knowledge Graph."""

    def __init__(self):
        self.logger = get_logger("KGQuery")
        self.driver = neo4j.GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    async def find_entities(
        self,
        entity_type: str,
        project_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Find entities of a specific type."""
        query = f"""
        MATCH (e:{entity_type})
        WHERE $project_name IS NULL OR
              EXISTS((e)<-[:MENTIONS]-(:Chunk)<-[:CONTAINS_CHUNK]-(:Document {{project_name: $project_name}}))
        RETURN e
        LIMIT $limit
        """

        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query, {
                "project_name": project_name,
                "limit": limit
            })
            return [dict(record["e"]) async for record in result]

    async def find_entity_relationships(
        self,
        entity_name: str,
        relationship_type: Optional[str] = None
    ) -> List[Dict]:
        """Find relationships for an entity."""
        if relationship_type:
            query = """
            MATCH (e)-[r:$rel_type]-(related)
            WHERE e.name = $entity_name
            RETURN type(r) as relationship, related
            """
        else:
            query = """
            MATCH (e)-[r]-(related)
            WHERE e.name = $entity_name
            RETURN type(r) as relationship, related
            """

        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query, {
                "entity_name": entity_name,
                "rel_type": relationship_type
            })
            return [dict(record) async for record in result]

    async def find_document_entities(
        self,
        doc_id: str
    ) -> Dict[str, List[Dict]]:
        """Get all entities extracted from a document."""
        query = """
        MATCH (d:Document {doc_id: $doc_id})-[:CONTAINS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e)
        RETURN labels(e)[0] as entity_type, collect(DISTINCT e) as entities
        """

        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query, {"doc_id": doc_id})
            entities_by_type = {}
            async for record in result:
                entity_type = record["entity_type"]
                entities_by_type[entity_type] = [
                    dict(e) for e in record["entities"]
                ]
            return entities_by_type

    async def find_related_documents(
        self,
        doc_id: str,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """Find documents related through shared entities."""
        if relationship_types:
            rel_filter = f"[:{':'.join(relationship_types)}]"
        else:
            rel_filter = ""

        query = f"""
        MATCH (d1:Document {{doc_id: $doc_id}})-[:CONTAINS_CHUNK]->(:Chunk)-[:MENTIONS]->(e)
              <-[:MENTIONS]-(:Chunk)<-[:CONTAINS_CHUNK]-(d2:Document)
        WHERE d1 <> d2
        RETURN DISTINCT d2, count(DISTINCT e) as shared_entities
        ORDER BY shared_entities DESC
        LIMIT 10
        """

        async with self.driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query, {"doc_id": doc_id})
            return [
                {
                    "document": dict(record["d2"]),
                    "shared_entities": record["shared_entities"]
                }
                async for record in result
            ]

    async def hybrid_search(
        self,
        vector_results: List[Dict],
        entity_filter: Optional[str] = None,
        relationship_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Enhance vector search results with graph context.

        Args:
            vector_results: Results from ChromaDB vector search
            entity_filter: Filter by entity name
            relationship_filter: Filter by relationship type
        """
        # Combine vector similarity with graph traversal
        # This is where the real power of hybrid search comes in
        pass

    def close(self):
        """Close Neo4j driver."""
        if self.driver:
            self.driver.close()
```

### Phase 3: API Integration (Week 3)

#### 3.1 Add KG Routes

```python
# app/routes/kg_routes.py

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.services.knowledge_graph.kg_builder import KnowledgeGraphBuilder
from app.services.knowledge_graph.kg_query import KnowledgeGraphQuery
from app.utils.logging import get_logger

router = APIRouter(prefix="/kg", tags=["Knowledge Graph"])
logger = get_logger("KGRoutes")


class EntityQueryRequest(BaseModel):
    entity_type: str
    project_name: Optional[str] = None
    limit: int = 10


class RelationshipQueryRequest(BaseModel):
    entity_name: str
    relationship_type: Optional[str] = None


@router.post("/build/{doc_id}")
async def build_knowledge_graph(
    doc_id: str,
    project_name: Optional[str] = None
):
    """Build knowledge graph for a processed document."""
    kg_builder = KnowledgeGraphBuilder()

    try:
        # Get extraction results (you'll need to retrieve this from your storage)
        # extraction_result = get_extraction_result(doc_id)

        # result = await kg_builder.build_from_extraction(
        #     extraction_result,
        #     project_name
        # )

        return {"status": "success", "doc_id": doc_id}

    finally:
        kg_builder.close()


@router.post("/entities/search")
async def search_entities(request: EntityQueryRequest):
    """Search for entities in the knowledge graph."""
    kg_query = KnowledgeGraphQuery()

    try:
        entities = await kg_query.find_entities(
            entity_type=request.entity_type,
            project_name=request.project_name,
            limit=request.limit
        )

        return {
            "entity_type": request.entity_type,
            "count": len(entities),
            "entities": entities
        }

    finally:
        kg_query.close()


@router.post("/relationships/search")
async def search_relationships(request: RelationshipQueryRequest):
    """Search for entity relationships."""
    kg_query = KnowledgeGraphQuery()

    try:
        relationships = await kg_query.find_entity_relationships(
            entity_name=request.entity_name,
            relationship_type=request.relationship_type
        )

        return {
            "entity_name": request.entity_name,
            "count": len(relationships),
            "relationships": relationships
        }

    finally:
        kg_query.close()


@router.get("/documents/{doc_id}/entities")
async def get_document_entities(doc_id: str):
    """Get all entities extracted from a document."""
    kg_query = KnowledgeGraphQuery()

    try:
        entities = await kg_query.find_document_entities(doc_id)

        return {
            "doc_id": doc_id,
            "entities_by_type": entities
        }

    finally:
        kg_query.close()


@router.get("/documents/{doc_id}/related")
async def get_related_documents(doc_id: str):
    """Find documents related through shared entities."""
    kg_query = KnowledgeGraphQuery()

    try:
        related_docs = await kg_query.find_related_documents(doc_id)

        return {
            "doc_id": doc_id,
            "related_documents": related_docs
        }

    finally:
        kg_query.close()
```

#### 3.2 Register Routes

```python
# app/main.py (add this)

from app.routes import kg_routes

app.include_router(kg_routes.router, prefix="/api/v1")
```

### Phase 4: Testing & Optimization (Week 4)

#### 4.1 Create Test Suite

```python
# tests/test_kg_integration.py

import pytest
from app.services.knowledge_graph.kg_builder import KnowledgeGraphBuilder
from app.services.knowledge_graph.kg_query import KnowledgeGraphQuery


@pytest.mark.asyncio
async def test_kg_build_from_extraction():
    """Test KG building from extraction results."""
    # Test implementation
    pass


@pytest.mark.asyncio
async def test_entity_search():
    """Test entity search functionality."""
    # Test implementation
    pass


@pytest.mark.asyncio
async def test_relationship_traversal():
    """Test relationship traversal."""
    # Test implementation
    pass
```

---

## 5. Usage Examples

### 5.1 Process PDF with KG

```bash
# Upload and process PDF with KG enabled
curl -X POST http://localhost:8081/api/v1/upload \
  -F "file=@document.pdf" \
  -F "project_name=research_papers" \
  -F "vectorize=true" \
  -F "build_kg=true"
```

### 5.2 Search Entities

```bash
# Find all Person entities
curl -X POST http://localhost:8081/api/v1/kg/entities/search \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "Person",
    "project_name": "research_papers",
    "limit": 10
  }'
```

### 5.3 Find Related Documents

```bash
# Find documents related to a specific document
curl http://localhost:8081/api/v1/kg/documents/{doc_id}/related
```

### 5.4 Hybrid Search (Vector + Graph)

```python
# Combine vector search with graph traversal

# 1. First, do vector search
vector_results = chromadb_client.query(
    collection_name="my_collection",
    query_texts=["machine learning algorithms"],
    n_results=5
)

# 2. Enhance with graph context
kg_query = KnowledgeGraphQuery()
enhanced_results = await kg_query.hybrid_search(
    vector_results=vector_results,
    entity_filter="TensorFlow"  # Only results mentioning TensorFlow
)
```

---

## 6. Advanced Features

### 6.1 Automatic Schema Extraction

Instead of manually defining schema, let LLM extract it:

```python
from neo4j_graphrag.experimental.components.schema import SchemaFromTextExtractor

schema_extractor = SchemaFromTextExtractor(llm=llm)
extracted_schema = await schema_extractor.run(text=sample_text)
extracted_schema.save("config/auto_schema.json")
```

### 6.2 Entity Resolution

Configure different entity resolution strategies:

```python
# Exact match (default)
from neo4j_graphrag.experimental.components.resolver import SinglePropertyExactMatchResolver

# Fuzzy matching
from neo4j_graphrag.experimental.components.resolver import FuzzyMatchResolver
resolver = FuzzyMatchResolver(driver, threshold=0.85)

# Semantic matching
from neo4j_graphrag.experimental.components.resolver import SpaCySemanticMatchResolver
resolver = SpaCySemanticMatchResolver(driver)
```

### 6.3 Custom Prompt Templates

```python
custom_prompt = """
Extract entities and relationships from the following text.
Focus on scientific concepts, researchers, and methodologies.

Text: {text}

Schema: {schema}

Output format: {examples}
"""

extractor = LLMEntityRelationExtractor(
    llm=llm,
    prompt=custom_prompt
)
```

---

## 7. Performance Optimization

### 7.1 Neo4j Indexes

```cypher
-- Create indexes for faster queries
CREATE INDEX doc_id_index FOR (d:Document) ON (d.doc_id);
CREATE INDEX chunk_id_index FOR (c:Chunk) ON (c.chunk_id);
CREATE INDEX person_name_index FOR (p:Person) ON (p.name);
CREATE INDEX org_name_index FOR (o:Organization) ON (o.name);

-- Create full-text indexes
CREATE FULLTEXT INDEX entity_names FOR (e:Person|Organization|Concept) ON EACH [e.name];
```

### 7.2 Batch Processing

```python
# Process multiple documents in batch
async def batch_build_kg(doc_ids: List[str]):
    kg_builder = KnowledgeGraphBuilder()

    results = []
    for doc_id in doc_ids:
        result = await kg_builder.build_from_extraction(...)
        results.append(result)

    kg_builder.close()
    return results
```

### 7.3 Monitoring

```python
# Add monitoring to track KG build performance
from app.utils.logging import get_logger
import time

logger = get_logger("KGMonitoring")

async def monitored_kg_build(extraction_result):
    start_time = time.time()

    result = await kg_builder.build_from_extraction(extraction_result)

    duration = time.time() - start_time
    logger.info(f"KG build took {duration:.2f}s for {result['file_name']}")

    return result
```

---

## 8. Deployment Checklist

- [ ] Neo4j container running and accessible
- [ ] Environment variables configured
- [ ] Schema defined and tested
- [ ] KG pipeline tested with sample PDFs
- [ ] API endpoints tested
- [ ] Indexes created in Neo4j
- [ ] Monitoring and logging configured
- [ ] Error handling implemented
- [ ] Documentation updated
- [ ] Performance benchmarks completed

---

## 9. Troubleshooting

### Common Issues

**1. "Cannot connect to Neo4j"**
- Check `NEO4J_URI` environment variable
- Verify Neo4j container is running: `docker ps | grep neo4j`
- Check network connectivity: `docker network inspect app_network`

**2. "LLM extraction timeout"**
- Increase timeout in LLM config
- Reduce chunk size for processing
- Use smaller/faster model for initial testing

**3. "Entity resolution too slow"**
- Use exact match resolver instead of semantic
- Limit entity resolution to specific types
- Create indexes on entity properties

**4. "Out of memory errors"**
- Increase Neo4j heap size in docker-compose
- Process documents in smaller batches
- Enable streaming for large result sets

---

## 10. Next Steps

1. **Start with Phase 1**: Set up Neo4j infrastructure
2. **Test with Sample Data**: Use 2-3 sample PDFs to validate pipeline
3. **Iterate on Schema**: Refine node/relationship types based on your domain
4. **Integrate with Existing Workflows**: Add KG build to your PDF processing pipeline
5. **Build Advanced Queries**: Create domain-specific graph queries
6. **Monitor Performance**: Track build times and query performance
7. **Scale Up**: Process your full document corpus

---

## Resources

- **Neo4j GraphRAG Docs**: https://neo4j.com/docs/graphrag/
- **Neo4j Browser**: http://localhost:7474 (access your graph visually)
- **Cypher Query Language**: https://neo4j.com/docs/cypher-manual/
- **APOC Procedures**: https://neo4j.com/labs/apoc/

---

**Questions or issues?** Create an issue in your project repository or consult the Neo4j community forums.
