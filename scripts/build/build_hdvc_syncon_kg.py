#!/usr/bin/env python3
"""
Build Knowledge Graph from HDVC/SYNCON Documents

Extract entities and relationships from the actual technical documents
and load them into Neo4j for true GraphRAG functionality
"""

import sys
import json
import re
from pathlib import Path
from collections import defaultdict, Counter

# Add src to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from neo4j import GraphDatabase

class HDVCSYNCONEntityExtractor:
    """Extract entities and relationships from HDVC/SYNCON technical documents"""

    def __init__(self):
        # HDVC/SYNCON specific technical terms
        self.technical_entities = {
            'HVDC', 'VSC', 'LCC', 'STATCOM', 'SynCon', 'Synchronous Condenser',
            'Converter Station', 'Grid Code', 'Power System', 'Protection System',
            'Circuit Breaker', 'Transformer', 'GIS', 'Substation', 'Offshore',
            'Reactive Power', 'Power Quality', 'Harmonic Analysis', 'Load Flow',
            'Short Circuit', 'Stability', 'Black Start', 'Grid Connection',
            'Frequency Control', 'Voltage Control', 'Protection Relay',
            'Overcurrent Protection', 'Differential Protection', 'Distance Protection',
            'Thermal Overload', 'DC Protection', 'AC Protection', 'Earthing',
            'Lightning Protection', 'Surge Arrester', 'Filter', 'Capacitor',
            'Reactor', 'Valve Group', 'Thyristor Valve', 'IGBT', 'Cooling System',
            'Control System', 'SCADA', 'Communication System', 'Fiber Optic',
            'DC Cable', 'AC Cable', 'Overhead Line', 'Underground Cable',
            'Grid Integration', 'Grid Studies', 'System Studies', 'EMT Studies',
            'Fault Analysis', 'Contingency Analysis', 'Dynamic Studies'
        }

        # Company names from documents
        self.companies = {
            'Siemens Energy', 'Siemens', 'ABB', 'General Electric', 'GE',
            'Hitachi Energy', 'Schneider Electric', 'National Grid',
            'RTE', 'TenneT', 'Elia', 'TransnetBW', 'Amprion', 'Statnett'
        }

        # Voltage/power levels
        self.technical_values = re.compile(r'\d+\.?\d*\s?(kV|MW|GW|MVA|Hz|kA|A|Ω|%)')

        # Project codes
        self.project_codes = re.compile(r'\bGC25?_\d{3}[_A-Za-z0-9]*\b')

    def extract_entities(self, text: str, project_name: str):
        """Extract entities from text chunk"""
        entities = set()

        # Add known technical terms
        text_upper = text.upper()
        for term in self.technical_entities:
            if term.upper() in text_upper:
                entities.add(term)

        # Add company names
        for company in self.companies:
            if company in text:
                entities.add(company)

        # Add technical values
        values = self.technical_values.findall(text)
        for value in values:
            cleaned_value = value.replace(' ', '').strip()
            if cleaned_value:
                entities.add(cleaned_value)

        # Add project codes
        project_codes = self.project_codes.findall(text)
        entities.update(project_codes)

        # Add the project itself as an entity
        entities.add(project_name)

        # Extract multi-word technical phrases
        words = text.split()
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if any(tech_word in phrase.upper() for tech_word in ['PROTECTION', 'SYSTEM', 'CONTROL', 'STATION']):
                if len(phrase) > 5:
                    entities.add(phrase.title())

        return entities

    def extract_relationships(self, text: str, entities: list):
        """Extract relationships between entities in text"""
        relationships = []
        text_lower = text.lower()

        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if entity1 == entity2:
                    continue

                # Both entities must be in the text
                if entity1.lower() not in text_lower or entity2.lower() not in text_lower:
                    continue

                # Determine relationship type based on context
                if 'protection' in text_lower and 'system' in text_lower:
                    if 'protection' in entity1.lower() or 'protection' in entity2.lower():
                        relationships.append((entity1, 'protects', entity2))
                elif 'connection' in text_lower or 'connected' in text_lower:
                    relationships.append((entity1, 'connected_to', entity2))
                elif 'part of' in text_lower or 'component' in text_lower:
                    relationships.append((entity1, 'part_of', entity2))
                elif 'supply' in text_lower or 'supplier' in text_lower:
                    if entity1 in self.companies:
                        relationships.append((entity1, 'supplies', entity2))
                elif 'requirement' in text_lower or 'specification' in text_lower:
                    relationships.append((entity1, 'requires', entity2))
                else:
                    relationships.append((entity1, 'related_to', entity2))

        return relationships[:3]  # Limit to avoid noise


def build_kg_from_chunks():
    """Build knowledge graph from HDVC/SYNCON chunks"""

    print("🧠 Building Knowledge Graph from HDVC/SYNCON Documents...")
    print("=" * 70)

    # Load chunks
    chunks_file = PROJECT_ROOT / "data" / "graphrag_complete" / "graphrag_chunks.json"
    with open(chunks_file) as f:
        chunks = json.load(f)

    print(f"📄 Processing {len(chunks):,} chunks...")

    # Extract entities and relationships
    extractor = HDVCSYNCONEntityExtractor()
    all_entities = defaultdict(int)
    all_relationships = defaultdict(int)
    project_entities = defaultdict(set)

    for i, chunk in enumerate(chunks):
        if i % 1000 == 0:
            print(f"  Progress: {i:,}/{len(chunks):,} chunks processed")

        text = chunk['text']
        project = chunk['project']

        # Extract entities
        entities = extractor.extract_entities(text, project)
        for entity in entities:
            all_entities[entity] += 1
            project_entities[project].add(entity)

        # Extract relationships
        entity_list = list(entities)
        relationships = extractor.extract_relationships(text, entity_list)
        for rel in relationships:
            rel_key = f"{rel[0]}|{rel[1]}|{rel[2]}"
            all_relationships[rel_key] += 1

    # Filter entities (keep those mentioned at least 3 times)
    filtered_entities = {entity: count for entity, count in all_entities.items() if count >= 3}

    print(f"\n📊 Knowledge Graph Statistics:")
    print(f"   Raw entities extracted: {len(all_entities):,}")
    print(f"   Filtered entities (≥3 mentions): {len(filtered_entities):,}")
    print(f"   Raw relationships: {len(all_relationships):,}")
    print(f"   Projects: {len(project_entities):,}")

    # Build structured knowledge graph
    kg_data = {
        'entities': {},
        'triplets': {
            'within_project': [],
            'project_level': []
        },
        'project_names': list(project_entities.keys()),
        'num_projects': len(project_entities),
        'num_total_entities': len(filtered_entities),
        'creation_date': '2025-11-10'
    }

    # Add entities with metadata
    for entity, count in filtered_entities.items():
        projects_with_entity = [proj for proj, entities in project_entities.items() if entity in entities]

        kg_data['entities'][entity] = {
            'total_mentions': count,
            'project_count': len(projects_with_entity),
            'projects': projects_with_entity
        }

    # Add relationships
    for rel_key, count in all_relationships.items():
        if count >= 2:  # Keep relationships mentioned at least twice
            head, relation, tail = rel_key.split('|')
            if head in filtered_entities and tail in filtered_entities:
                # Find project for this relationship
                for project, entities in project_entities.items():
                    if head in entities and tail in entities:
                        kg_data['triplets']['within_project'].append({
                            'head': head,
                            'relation': relation,
                            'tail': tail,
                            'project': project,
                            'count': count
                        })
                        break

    # Add project-entity connections
    for project, entities in project_entities.items():
        for entity in entities:
            if entity in filtered_entities and entity != project:
                kg_data['triplets']['project_level'].append({
                    'type': 'project_to_entity',
                    'head': project,
                    'tail': entity,
                    'relation': 'mentions'
                })

    kg_data['num_total_triplets'] = len(kg_data['triplets']['within_project'])

    # Save knowledge graph
    kg_file = PROJECT_ROOT / "data" / "graphrag_complete" / "hdvc_syncon_knowledge_graph.json"
    with open(kg_file, 'w') as f:
        json.dump(kg_data, f, indent=2)

    print(f"\n💾 Knowledge graph saved to: {kg_file}")
    print(f"📊 Final stats:")
    print(f"   • Entities: {len(kg_data['entities'])}")
    print(f"   • Relationships: {kg_data['num_total_triplets']}")
    print(f"   • Projects: {kg_data['num_projects']}")

    # Show sample entities
    sample_entities = list(kg_data['entities'].keys())[:10]
    print(f"\n🔍 Sample HDVC/SYNCON entities:")
    for entity in sample_entities:
        count = kg_data['entities'][entity]['total_mentions']
        projects = kg_data['entities'][entity]['project_count']
        print(f"   • {entity} (mentioned {count} times across {projects} projects)")

    return kg_data

def load_into_neo4j(kg_data):
    """Load the HDVC/SYNCON knowledge graph into Neo4j"""

    print(f"\n🗄️  Loading HDVC/SYNCON Knowledge Graph into Neo4j...")

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

    with driver.session() as session:
        # Clear existing data
        print("🗑️  Clearing existing data...")
        session.run("MATCH (n) DETACH DELETE n")

        # Create projects
        print("📁 Creating project nodes...")
        for project_name in kg_data['project_names']:
            session.run("""
                MERGE (p:Project {name: $name, type: 'HDVC_SYNCON'})
            """, name=project_name)

        print(f"   ✅ Created {len(kg_data['project_names'])} project nodes")

        # Create entities
        print("🏷️  Creating entity nodes...")
        for entity_name, entity_data in kg_data['entities'].items():
            session.run("""
                MERGE (e:Entity {name: $name})
                SET e.mentions = $mentions,
                    e.project_count = $project_count,
                    e.domain = 'HDVC_SYNCON'
            """,
            name=entity_name,
            mentions=entity_data['total_mentions'],
            project_count=entity_data['project_count'])

        print(f"   ✅ Created {len(kg_data['entities'])} entity nodes")

        # Create relationships
        print("🔗 Creating relationships...")
        for triplet in kg_data['triplets']['within_project']:
            session.run("""
                MATCH (h:Entity {name: $head})
                MATCH (t:Entity {name: $tail})
                MERGE (h)-[r:RELATED {type: $relation, project: $project}]->(t)
            """,
            head=triplet['head'],
            tail=triplet['tail'],
            relation=triplet['relation'],
            project=triplet['project'])

        print(f"   ✅ Created {len(kg_data['triplets']['within_project'])} relationships")

        # Create project-entity connections
        print("📊 Connecting projects to entities...")
        for triplet in kg_data['triplets']['project_level']:
            session.run("""
                MATCH (p:Project {name: $project})
                MATCH (e:Entity {name: $entity})
                MERGE (p)-[:MENTIONS]->(e)
            """,
            project=triplet['head'],
            entity=triplet['tail'])

        print(f"   ✅ Connected projects to entities")

        # Create indexes
        session.run("CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)")
        session.run("CREATE INDEX project_name_idx IF NOT EXISTS FOR (p:Project) ON (p.name)")

    driver.close()
    print(f"✅ HDVC/SYNCON Knowledge Graph loaded into Neo4j!")

def main():
    print("\n🚀 Building HDVC/SYNCON Knowledge Graph for True GraphRAG")
    print("=" * 80)

    # Build KG from chunks
    kg_data = build_kg_from_chunks()

    # Load into Neo4j
    load_into_neo4j(kg_data)

    print(f"\n🎉 SUCCESS! HDVC/SYNCON Knowledge Graph Ready!")
    print(f"🕸️  You now have a domain-specific knowledge graph with:")
    print(f"   • {len(kg_data['entities'])} technical entities")
    print(f"   • {kg_data['num_total_triplets']} relationships")
    print(f"   • {kg_data['num_projects']} HDVC/SYNCON projects")
    print(f"")
    print(f"🚀 Ready for TRUE GraphRAG!")
    print(f"   Use: python true_graphrag_chat.py --interactive")

if __name__ == "__main__":
    main()