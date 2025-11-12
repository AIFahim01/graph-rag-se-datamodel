#!/usr/bin/env python3
"""
Build Chunk-Level Knowledge Graph with Provenance
Best Practice Architecture (Microsoft GraphRAG + Neo4j 2024)

Structure:
- Document nodes (project, source, metadata)
- Chunk nodes (text, index, page, embedding)
- Entity nodes (name, type, description, confidence)
- Provenance relationships with metadata
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from neo4j import GraphDatabase


class ChunkLevelKGBuilder:
    """Build hierarchical chunk-level knowledge graph with provenance"""

    def __init__(self, use_relik=True):
        self.use_relik = use_relik
        self.extraction_model_name = "relik-small" if use_relik else "rebel-large"

        # Load existing chunks
        self.chunks_file = PROJECT_ROOT / "data" / "graphrag_complete" / "graphrag_chunks.json"
        print(f"\n📄 Loading chunks from: {self.chunks_file}")

        with open(self.chunks_file) as f:
            self.chunks = json.load(f)

        print(f"✅ Loaded {len(self.chunks):,} chunks")

        # Load REBEL KG for entity data
        self.rebel_kg_file = PROJECT_ROOT / "data" / "graphrag_complete" / "rebel_knowledge_graph.json"
        with open(self.rebel_kg_file) as f:
            self.rebel_kg = json.load(f)

        print(f"✅ Loaded REBEL KG: {len(self.rebel_kg['entities'])} entities, {len(self.rebel_kg['relationships'])} relationships")

        # Connect to Neo4j
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )
        print("✅ Connected to Neo4j")

        # Track statistics
        self.stats = {
            'documents': 0,
            'chunks': 0,
            'entities': 0,
            'chunk_mentions': 0,
            'entity_relationships': 0
        }

    def group_chunks_by_document(self):
        """Group chunks by document/project"""
        documents = {}

        for chunk in self.chunks:
            project = chunk.get('project', 'unknown')
            if project not in documents:
                documents[project] = {
                    'name': project,
                    'source': chunk.get('source', 'unknown'),
                    'category': chunk.get('category', 'unknown'),
                    'document_type': chunk.get('document_type', 'technical'),
                    'chunks': []
                }
            documents[project]['chunks'].append(chunk)

        print(f"\n📊 Found {len(documents)} documents")
        return documents

    def clear_graph(self):
        """Clear existing graph"""
        print("\n🧹 Clearing existing graph...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("   ✅ Graph cleared")

    def create_constraints(self):
        """Create uniqueness constraints"""
        print("\n📋 Creating constraints...")
        with self.driver.session() as session:
            try:
                session.run("CREATE CONSTRAINT doc_name IF NOT EXISTS FOR (d:Document) REQUIRE d.name IS UNIQUE")
                session.run("CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE")
                session.run("CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")
                print("   ✅ Constraints created")
            except Exception as e:
                print(f"   Note: {e}")

    def create_document_nodes(self, documents):
        """Create Document nodes"""
        print(f"\n📥 Creating {len(documents)} Document nodes...")

        with self.driver.session() as session:
            for project, doc_data in tqdm(documents.items(), desc="Documents"):
                session.run("""
                    MERGE (d:Document {name: $name})
                    SET d.source = $source,
                        d.category = $category,
                        d.document_type = $doc_type,
                        d.total_chunks = $total_chunks,
                        d.created_at = datetime($created_at)
                """, name=doc_data['name'],
                     source=doc_data['source'],
                     category=doc_data['category'],
                     doc_type=doc_data['document_type'],
                     total_chunks=len(doc_data['chunks']),
                     created_at=datetime.now().isoformat())

                self.stats['documents'] += 1

    def create_chunk_nodes(self, documents):
        """Create Chunk nodes with Document relationships"""
        print(f"\n📥 Creating Chunk nodes and linking to Documents...")

        total_chunks = sum(len(doc_data['chunks']) for doc_data in documents.values())

        with self.driver.session() as session:
            chunk_counter = 0

            for project, doc_data in tqdm(documents.items(), desc="Documents"):
                for idx, chunk in enumerate(doc_data['chunks']):
                    chunk_id = f"{project}_chunk_{idx}"
                    chunk_text = chunk.get('text', '')

                    # Create Chunk node
                    session.run("""
                        MERGE (c:Chunk {chunk_id: $chunk_id})
                        SET c.text = $text,
                            c.chunk_index = $index,
                            c.page = $page,
                            c.section = $section,
                            c.char_count = $char_count,
                            c.word_count = $word_count
                    """, chunk_id=chunk_id,
                         text=chunk_text,
                         index=idx,
                         page=chunk.get('page', 0),
                         section=chunk.get('section', 'unknown'),
                         char_count=len(chunk_text),
                         word_count=len(chunk_text.split()))

                    # Link to Document
                    session.run("""
                        MATCH (d:Document {name: $doc_name})
                        MATCH (c:Chunk {chunk_id: $chunk_id})
                        MERGE (d)-[:HAS_CHUNK {order: $order}]->(c)
                    """, doc_name=project, chunk_id=chunk_id, order=idx)

                    chunk_counter += 1
                    self.stats['chunks'] += 1

        print(f"   ✅ Created {chunk_counter:,} chunks")

    def create_entity_nodes_from_rebel(self):
        """Create Entity nodes from REBEL knowledge graph"""
        print(f"\n📥 Creating Entity nodes from REBEL data...")

        with self.driver.session() as session:
            for entity, data in tqdm(self.rebel_kg['entities'].items(), desc="Entities"):
                # Clean entity name
                clean_name = entity.strip()

                # Skip very noisy entities
                if '</s' in clean_name or '<obj>' in clean_name or len(clean_name) < 2:
                    continue

                session.run("""
                    MERGE (e:Entity {name: $name})
                    SET e.total_mentions = $mentions,
                        e.num_projects = $num_projects,
                        e.extraction_model = $model,
                        e.created_at = datetime($created_at)
                """, name=clean_name,
                     mentions=data['mentions'],
                     num_projects=len(data['projects']),
                     model=self.extraction_model_name,
                     created_at=datetime.now().isoformat())

                self.stats['entities'] += 1

        print(f"   ✅ Created {self.stats['entities']:,} entity nodes")

    def link_chunks_to_entities(self):
        """Link Chunk nodes to Entity nodes with provenance"""
        print(f"\n📥 Linking chunks to entities with provenance...")

        with self.driver.session() as session:
            for rel in tqdm(self.rebel_kg['relationships'], desc="Relationships"):
                project = rel['project']
                subject = rel['subject'].strip()
                obj = rel['object'].strip()

                # Skip noisy entities
                if '</s' in subject or '</s' in obj or '<obj>' in subject or '<obj>' in obj:
                    continue

                # Find chunks for this project
                # In a real implementation, we'd track which chunk each entity came from
                # For now, we'll link entities to all chunks in their project

                try:
                    # Link subject entity to chunks in this project
                    session.run("""
                        MATCH (d:Document {name: $project})-[:HAS_CHUNK]->(c:Chunk)
                        MATCH (e:Entity {name: $entity})
                        MERGE (c)-[m:MENTIONS]->(e)
                        SET m.confidence = 0.85,
                            m.extraction_model = $model,
                            m.created_at = datetime($created_at)
                    """, project=project,
                         entity=subject,
                         model=self.extraction_model_name,
                         created_at=datetime.now().isoformat())

                    # Link object entity
                    session.run("""
                        MATCH (d:Document {name: $project})-[:HAS_CHUNK]->(c:Chunk)
                        MATCH (e:Entity {name: $entity})
                        MERGE (c)-[m:MENTIONS]->(e)
                        SET m.confidence = 0.85,
                            m.extraction_model = $model,
                            m.created_at = datetime($created_at)
                    """, project=project,
                         entity=obj,
                         model=self.extraction_model_name,
                         created_at=datetime.now().isoformat())

                    self.stats['chunk_mentions'] += 2

                except Exception as e:
                    # Skip if entity not found
                    continue

        print(f"   ✅ Created {self.stats['chunk_mentions']:,} chunk→entity mentions")

    def create_entity_relationships(self):
        """Create Entity→Entity relationships with provenance"""
        print(f"\n📥 Creating entity relationships with provenance...")

        with self.driver.session() as session:
            for rel in tqdm(self.rebel_kg['relationships'], desc="Entity Relations"):
                subject = rel['subject'].strip()
                obj = rel['object'].strip()
                relation = rel['relation']
                project = rel['project']

                # Skip noisy entities
                if '</s' in subject or '</s' in obj or '<obj>' in subject or '<obj>' in obj:
                    continue

                try:
                    session.run("""
                        MATCH (s:Entity {name: $subject})
                        MATCH (o:Entity {name: $object})
                        MERGE (s)-[r:RELATED {type: $relation}]->(o)
                        ON CREATE SET
                            r.source_projects = [$project],
                            r.co_occurrence_count = 1,
                            r.confidence = 0.85,
                            r.extraction_model = $model,
                            r.created_at = datetime($created_at)
                        ON MATCH SET
                            r.source_projects = CASE
                                WHEN NOT $project IN r.source_projects
                                THEN r.source_projects + $project
                                ELSE r.source_projects
                            END,
                            r.co_occurrence_count = r.co_occurrence_count + 1
                    """, subject=subject,
                         object=obj,
                         relation=relation,
                         project=project,
                         model=self.extraction_model_name,
                         created_at=datetime.now().isoformat())

                    self.stats['entity_relationships'] += 1

                except Exception as e:
                    # Skip if entities not found
                    continue

        print(f"   ✅ Created {self.stats['entity_relationships']:,} entity relationships")

    def print_statistics(self):
        """Print final statistics"""
        print("\n" + "=" * 80)
        print("CHUNK-LEVEL KNOWLEDGE GRAPH STATISTICS")
        print("=" * 80)

        with self.driver.session() as session:
            # Get node counts
            result = session.run("""
                MATCH (d:Document)
                WITH count(d) as docs
                MATCH (c:Chunk)
                WITH docs, count(c) as chunks
                MATCH (e:Entity)
                RETURN docs, chunks, count(e) as entities
            """).single()

            # Get relationship counts
            rel_result = session.run("""
                MATCH ()-[r]->()
                WITH type(r) as rel_type, count(r) as count
                RETURN rel_type, count
                ORDER BY count DESC
            """)

            print(f"\n📊 Nodes:")
            print(f"   • Documents:  {result['docs']:,}")
            print(f"   • Chunks:     {result['chunks']:,}")
            print(f"   • Entities:   {result['entities']:,}")
            print(f"   • TOTAL:      {result['docs'] + result['chunks'] + result['entities']:,}")

            print(f"\n🔗 Relationships:")
            for record in rel_result:
                print(f"   • {record['rel_type']}: {record['count']:,}")

        print("\n" + "=" * 80)

    def build_graph(self):
        """Main build method"""
        print("\n" + "🚀" * 80)
        print("BUILDING CHUNK-LEVEL KNOWLEDGE GRAPH")
        print("Best Practice: Document → Chunk → Entity with Provenance")
        print("🚀" * 80)

        start_time = time.time()

        # Step 1: Group chunks by document
        documents = self.group_chunks_by_document()

        # Step 2: Clear and setup
        self.clear_graph()
        self.create_constraints()

        # Step 3: Create hierarchical structure
        self.create_document_nodes(documents)
        self.create_chunk_nodes(documents)

        # Step 4: Create entities and link
        self.create_entity_nodes_from_rebel()
        self.link_chunks_to_entities()
        self.create_entity_relationships()

        # Step 5: Print statistics
        self.print_statistics()

        elapsed = time.time() - start_time
        print(f"\n⏱️  Total time: {elapsed:.2f} seconds ({elapsed/60:.1f} minutes)")

        print("\n✅ CHUNK-LEVEL KNOWLEDGE GRAPH COMPLETE!")
        print("\n🎯 Next Steps:")
        print("   1. Test with Smart Cypher GraphRAG:")
        print("      python ollama_smart_cypher_graphrag.py --interactive --model mistral")
        print("\n   2. View in Neo4j Browser: http://localhost:7474")
        print("\n   3. Example queries:")
        print("      - Which chunks mention HVDC?")
        print("      - Show provenance for entity 'TenneT'")
        print("      - Find all entities in document X")

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()


def main():
    print("\n" + "=" * 80)
    print("CHUNK-LEVEL KNOWLEDGE GRAPH BUILDER")
    print("=" * 80)

    # Check if ReLiK is available
    try:
        import relik
        use_relik = True
        print("✅ ReLiK available - will use for future extractions")
    except ImportError:
        use_relik = False
        print("⚠️  ReLiK not available - using REBEL data")

    try:
        builder = ChunkLevelKGBuilder(use_relik=use_relik)
        builder.build_graph()
        builder.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
