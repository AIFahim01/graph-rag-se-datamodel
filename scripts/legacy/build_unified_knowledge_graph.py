"""
Build Unified Knowledge Graph Across Projects

Creates a unified knowledge graph that includes:
1. Cross-project entity linking
2. Project-level relationships
3. Multi-collection structure
4. Community detection across projects

This implements the multi-collection architecture shown in the diagram.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from loguru import logger

import networkx as nx

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


class UnifiedKnowledgeGraphBuilder:
    """Build unified knowledge graph across multiple projects"""

    def __init__(self, kg_dir: Path):
        """
        Initialize unified KG builder

        Args:
            kg_dir: Directory containing individual project KGs
        """
        self.kg_dir = Path(kg_dir)
        self.logger = logger

        # Data structures for unified graph
        self.projects = {}
        self.entities = defaultdict(lambda: {
            "type": "Entity",
            "projects": set(),
            "mentions": []
        })
        self.all_triplets = []
        self.entity_to_projects = defaultdict(set)

    def load_project_knowledge_graphs(self) -> Dict:
        """Load all project knowledge graphs (prefer metadata version)"""
        # Try to load metadata-enriched version first
        kg_files = list(self.kg_dir.glob("*_knowledge_graph_with_metadata.json"))

        if not kg_files:
            # Fallback to non-metadata version
            kg_files = list(self.kg_dir.glob("*_knowledge_graph.json"))
            kg_files = [f for f in kg_files if 'unified' not in f.name and 'with_metadata' not in f.name]

        if not kg_files:
            self.logger.error(f"No knowledge graph files found in {self.kg_dir}")
            return {}

        self.logger.info(f"Loading {len(kg_files)} project knowledge graphs...")

        for kg_file in kg_files:
            with open(kg_file, 'r', encoding='utf-8') as f:
                kg_data = json.load(f)
                project_name = kg_data['project_name']
                self.projects[project_name] = kg_data
                self.logger.info(f"  Loaded {project_name}: {kg_data['num_unique_triplets']} triplets")

        return self.projects

    def extract_entities_with_projects(self):
        """Extract all entities and track which projects they appear in"""
        self.logger.info("Extracting entities across all projects...")

        for project_name, kg_data in self.projects.items():
            for triplet in kg_data['triplets']:
                head = triplet['head']
                tail = triplet['tail']
                relation = triplet['relation']

                # Track head entity
                self.entities[head]['projects'].add(project_name)
                self.entities[head]['mentions'].append({
                    'project': project_name,
                    'role': 'head',
                    'relation': relation
                })
                self.entity_to_projects[head].add(project_name)

                # Track tail entity
                self.entities[tail]['projects'].add(project_name)
                self.entities[tail]['mentions'].append({
                    'project': project_name,
                    'role': 'tail',
                    'relation': relation
                })
                self.entity_to_projects[tail].add(project_name)

                # Store triplet with project info
                triplet_with_project = triplet.copy()
                triplet_with_project['project'] = project_name
                self.all_triplets.append(triplet_with_project)

        # Convert sets to lists for JSON serialization
        for entity in self.entities:
            self.entities[entity]['projects'] = list(self.entities[entity]['projects'])
            self.entities[entity]['project_count'] = len(self.entities[entity]['projects'])
            self.entities[entity]['total_mentions'] = len(self.entities[entity]['mentions'])

        self.logger.info(f"  Found {len(self.entities)} unique entities across all projects")

    def find_cross_project_entities(self) -> List[Dict]:
        """Find entities that appear in multiple projects"""
        cross_project = []

        for entity, data in self.entities.items():
            if data['project_count'] > 1:
                cross_project.append({
                    'entity': entity,
                    'projects': data['projects'],
                    'project_count': data['project_count'],
                    'total_mentions': data['total_mentions']
                })

        # Sort by project count (most shared first)
        cross_project.sort(key=lambda x: x['project_count'], reverse=True)

        self.logger.info(f"  Found {len(cross_project)} entities appearing in multiple projects")

        return cross_project

    def create_project_level_triplets(self) -> List[Dict]:
        """Create triplets at project level (project-to-entity, project-to-project)"""
        project_triplets = []

        # Project-to-Entity relationships
        for entity, data in self.entities.items():
            for project in data['projects']:
                project_triplets.append({
                    'head': project,
                    'relation': 'mentions_entity',
                    'tail': entity,
                    'type': 'project_to_entity'
                })

        # Project-to-Project relationships (based on shared entities)
        projects_list = list(self.projects.keys())
        for i, proj1 in enumerate(projects_list):
            for proj2 in projects_list[i+1:]:
                # Find shared entities
                entities_proj1 = {e for e, d in self.entities.items() if proj1 in d['projects']}
                entities_proj2 = {e for e, d in self.entities.items() if proj2 in d['projects']}
                shared = entities_proj1.intersection(entities_proj2)

                if shared:
                    project_triplets.append({
                        'head': proj1,
                        'relation': 'shares_entities_with',
                        'tail': proj2,
                        'type': 'project_to_project',
                        'shared_entities': list(shared),
                        'shared_count': len(shared)
                    })

        self.logger.info(f"  Created {len(project_triplets)} project-level relationships")

        return project_triplets

    def build_unified_graph(self) -> nx.DiGraph:
        """Build NetworkX graph with all projects combined"""
        G = nx.DiGraph()

        # Add project nodes
        for project_name, kg_data in self.projects.items():
            G.add_node(project_name,
                      type='Project',
                      num_pdfs=kg_data['num_pdfs'],
                      num_triplets=kg_data['num_unique_triplets'])

        # Add entity nodes and within-project edges
        for triplet in self.all_triplets:
            G.add_node(triplet['head'], type='Entity')
            G.add_node(triplet['tail'], type='Entity')
            G.add_edge(triplet['head'], triplet['tail'],
                      relation=triplet['relation'],
                      project=triplet['project'])

        # Add project-to-entity edges
        for entity, data in self.entities.items():
            for project in data['projects']:
                G.add_edge(project, entity, relation='mentions', type='project_to_entity')

        self.logger.info(f"  Unified graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        return G

    def detect_communities(self, G: nx.DiGraph) -> Dict:
        """Detect communities in the unified graph"""
        try:
            # Convert to undirected for community detection
            G_undirected = G.to_undirected()

            # Use Louvain method for community detection
            import community as community_louvain
            communities = community_louvain.best_partition(G_undirected)

            # Group by community
            community_groups = defaultdict(list)
            for node, comm_id in communities.items():
                community_groups[comm_id].append(node)

            self.logger.info(f"  Detected {len(community_groups)} communities")

            return {
                'num_communities': len(community_groups),
                'communities': {k: v for k, v in community_groups.items()}
            }
        except ImportError:
            self.logger.warning("python-louvain not installed, skipping community detection")
            return {'num_communities': 0, 'communities': {}}

    def build_and_save_unified_kg(self, output_file: Path):
        """Build and save complete unified knowledge graph"""
        self.logger.info("Building unified knowledge graph...")

        # Load all projects
        self.load_project_knowledge_graphs()

        # Extract and link entities
        self.extract_entities_with_projects()

        # Find cross-project entities
        cross_project_entities = self.find_cross_project_entities()

        # Create project-level relationships
        project_triplets = self.create_project_level_triplets()

        # Build unified graph
        unified_graph = self.build_unified_graph()

        # Detect communities
        communities = self.detect_communities(unified_graph)

        # Prepare unified KG data
        unified_kg = {
            'timestamp': datetime.now().isoformat(),
            'num_projects': len(self.projects),
            'project_names': list(self.projects.keys()),

            # Entity statistics
            'num_total_entities': len(self.entities),
            'num_cross_project_entities': len(cross_project_entities),

            # Triplet statistics
            'num_within_project_triplets': len(self.all_triplets),
            'num_project_level_triplets': len(project_triplets),
            'num_total_triplets': len(self.all_triplets) + len(project_triplets),

            # Graph statistics
            'graph_nodes': unified_graph.number_of_nodes(),
            'graph_edges': unified_graph.number_of_edges(),

            # Communities
            'communities': communities,

            # Detailed data
            'projects': {name: {
                'num_pdfs': data['num_pdfs'],
                'num_triplets': data['num_unique_triplets'],
                'timestamp': data['timestamp']
            } for name, data in self.projects.items()},

            'entities': dict(self.entities),
            'cross_project_entities': cross_project_entities,

            'triplets': {
                'within_project': self.all_triplets,
                'project_level': project_triplets
            }
        }

        # Save unified KG
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unified_kg, f, indent=2, ensure_ascii=False, default=str)

        self.logger.info(f"✓ Unified knowledge graph saved to: {output_file}")

        return unified_kg


def main():
    parser = argparse.ArgumentParser(
        description="Build unified knowledge graph across all projects"
    )
    parser.add_argument(
        '--datasets-dir',
        type=str,
        default='./datasets',
        help='Path to datasets directory (default: ./datasets)'
    )

    args = parser.parse_args()

    # Setup paths
    datasets_dir = Path(args.datasets_dir)
    kg_dir = datasets_dir / 'knowledge_graphs'
    output_file = kg_dir / 'unified_knowledge_graph.json'

    if not kg_dir.exists():
        print(f"❌ Knowledge graphs directory not found: {kg_dir}")
        print("   Run build_knowledge_graph_rebel.py first")
        return

    # Setup logging
    logger.add(
        datasets_dir / "unified_kg_build.log",
        format="{time} {level} {message}",
        level="INFO"
    )

    print("\n" + "=" * 80)
    print("UNIFIED KNOWLEDGE GRAPH BUILDER")
    print("=" * 80)

    try:
        # Build unified KG
        builder = UnifiedKnowledgeGraphBuilder(kg_dir)
        unified_kg = builder.build_and_save_unified_kg(output_file)

        # Display results
        print(f"\n✓ Unified Knowledge Graph Created!")
        print(f"\n{'─' * 80}")
        print("STATISTICS")
        print(f"{'─' * 80}")
        print(f"Projects:                    {unified_kg['num_projects']}")
        print(f"  {', '.join(unified_kg['project_names'])}")
        print(f"\nEntities:")
        print(f"  Total unique entities:     {unified_kg['num_total_entities']}")
        print(f"  Cross-project entities:    {unified_kg['num_cross_project_entities']}")
        print(f"\nTriplets:")
        print(f"  Within-project:            {unified_kg['num_within_project_triplets']}")
        print(f"  Project-level:             {unified_kg['num_project_level_triplets']}")
        print(f"  Total:                     {unified_kg['num_total_triplets']}")
        print(f"\nGraph:")
        print(f"  Nodes:                     {unified_kg['graph_nodes']}")
        print(f"  Edges:                     {unified_kg['graph_edges']}")
        print(f"  Communities:               {unified_kg['communities']['num_communities']}")

        # Show cross-project entities
        if unified_kg['cross_project_entities']:
            print(f"\n{'─' * 80}")
            print("TOP CROSS-PROJECT ENTITIES")
            print(f"{'─' * 80}")
            for entity_data in unified_kg['cross_project_entities'][:10]:
                projects_str = ', '.join(entity_data['projects'])
                print(f"  {entity_data['entity']:40s} : {projects_str}")

        print(f"\n{'=' * 80}")
        print(f"✓ Saved to: {output_file}")
        print(f"{'=' * 80}\n")

    except Exception as e:
        logger.error(f"Failed to build unified KG: {e}")
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
