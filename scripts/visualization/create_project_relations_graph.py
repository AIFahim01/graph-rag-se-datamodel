"""
Create Interactive Graph with Project-to-Project Relationships

Builds an enhanced knowledge graph that shows:
1. How projects relate to each other
2. Technology similarity between projects
3. Shared concepts and patterns
4. Domain clustering

Uses semantic matching to find relationships even when exact entity names differ.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from loguru import logger

from pyvis.network import Network


class ProjectRelationshipGraphBuilder:
    """Build interactive graph focused on project relationships"""

    def __init__(self, kg_dir: Path):
        self.kg_dir = Path(kg_dir)
        self.logger = logger

        # Project colors
        self.project_colors = {
            'alpha_erp_system': '#FF6B6B',
            'beta_cloud_migration': '#4ECDC4',
            'gamma_analytics_platform': '#95E1D3'
        }

        # Technology categories for semantic matching
        self.tech_categories = {
            'database': ['database', 'db', 'sql', 'nosql', 'rds', 'hana', 'postgresql', 'mysql', 'oracle'],
            'cloud': ['cloud', 'aws', 'azure', 'gcp', 'migration', 'kubernetes', 'docker'],
            'analytics': ['analytics', 'data', 'spark', 'kafka', 'ml', 'machine learning', 'tensorflow'],
            'erp': ['erp', 'sap', 's/4hana', 'enterprise', 'resource planning'],
            'integration': ['api', 'rest', 'integration', 'microservices', 'service'],
            'security': ['security', 'encryption', 'authentication', 'authorization']
        }

    def load_projects(self):
        """Load all project knowledge graphs"""
        projects = {}
        kg_files = list(self.kg_dir.glob("*_knowledge_graph_with_metadata.json"))

        if not kg_files:
            kg_files = list(self.kg_dir.glob("*_knowledge_graph.json"))
            kg_files = [f for f in kg_files if 'unified' not in f.name]

        for kg_file in kg_files:
            with open(kg_file, 'r', encoding='utf-8') as f:
                kg_data = json.load(f)
                project_name = kg_data['project_name']
                projects[project_name] = kg_data

        return projects

    def extract_entities_by_project(self, projects):
        """Extract all entities for each project"""
        project_entities = {}

        for project_name, kg_data in projects.items():
            entities = set()
            for triplet in kg_data['triplets']:
                entities.add(triplet['head'].lower())
                entities.add(triplet['tail'].lower())
            project_entities[project_name] = entities

        return project_entities

    def categorize_entities(self, entities):
        """Categorize entities by technology type"""
        categories = defaultdict(list)

        for entity in entities:
            entity_lower = entity.lower()
            for category, keywords in self.tech_categories.items():
                if any(keyword in entity_lower for keyword in keywords):
                    categories[category].append(entity)

        return categories

    def find_project_relationships(self, projects, project_entities):
        """Find relationships between projects"""
        relationships = []
        project_names = list(projects.keys())

        # Categorize entities for each project
        project_categories = {}
        for project, entities in project_entities.items():
            project_categories[project] = self.categorize_entities(entities)

        # Find relationships between each pair of projects
        for i, proj1 in enumerate(project_names):
            for proj2 in project_names[i+1:]:
                # Get categories for both projects
                cat1 = project_categories[proj1]
                cat2 = project_categories[proj2]

                # Find shared technology categories
                shared_categories = set(cat1.keys()).intersection(set(cat2.keys()))

                for category in shared_categories:
                    relationships.append({
                        'source': proj1,
                        'target': proj2,
                        'relation': f'shares_{category}_tech',
                        'category': category,
                        'proj1_entities': cat1[category],
                        'proj2_entities': cat2[category],
                        'strength': len(cat1[category]) + len(cat2[category])
                    })

                # Add general similarity if they share multiple categories
                if len(shared_categories) >= 2:
                    relationships.append({
                        'source': proj1,
                        'target': proj2,
                        'relation': 'similar_tech_stack',
                        'category': 'general',
                        'shared_categories': list(shared_categories),
                        'strength': len(shared_categories) * 2
                    })

        return relationships

    def create_project_focused_graph(self, projects, output_file):
        """Create interactive graph focused on project relationships"""

        # Extract entities
        project_entities = self.extract_entities_by_project(projects)

        # Find project relationships
        project_relationships = self.find_project_relationships(projects, project_entities)

        # Create network
        net = Network(
            height='900px',
            width='100%',
            bgcolor='#f8f9fa',
            font_color='#000000',
            directed=False  # Undirected for project-project relationships
        )

        # Configure for better project-level view
        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 300},
            "barnesHut": {
              "gravitationalConstant": -12000,
              "centralGravity": 0.5,
              "springLength": 250,
              "springConstant": 0.02
            }
          },
          "nodes": {
            "font": {"size": 16}
          },
          "edges": {
            "font": {"size": 14},
            "smooth": {"type": "continuous"}
          }
        }
        """)

        # Add project nodes (LARGE and prominent)
        for project_name, kg_data in projects.items():
            # Count entities
            entities = project_entities[project_name]

            hover_text = f"""
            <b>Project: {project_name.replace('_', ' ').title()}</b><br>
            PDFs: {kg_data['num_pdfs']}<br>
            Entities: {len(entities)}<br>
            Triplets: {kg_data['num_unique_triplets']}<br>
            <hr>
            <i>Click to highlight connections</i>
            """

            net.add_node(
                project_name,
                label=project_name.replace('_', ' ').title(),
                title=hover_text,
                color=self.project_colors.get(project_name, '#95E1D3'),
                size=60,
                shape='box',
                font={'size': 20, 'bold': True},
                borderWidth=3,
                borderWidthSelected=5
            )

        # Aggregate relationships by project pair (FIX: pyvis only keeps first edge)
        aggregated_rels = defaultdict(lambda: {
            'categories': [],
            'all_relations': [],
            'total_strength': 0,
            'entities': {}
        })

        for rel in project_relationships:
            # Create key for project pair (sorted to handle bidirectional)
            pair = tuple(sorted([rel['source'], rel['target']]))

            aggregated_rels[pair]['categories'].append(rel['category'])
            aggregated_rels[pair]['all_relations'].append(rel)
            aggregated_rels[pair]['total_strength'] += rel['strength']

            if 'proj1_entities' in rel:
                if rel['source'] not in aggregated_rels[pair]['entities']:
                    aggregated_rels[pair]['entities'][rel['source']] = []
                aggregated_rels[pair]['entities'][rel['source']].extend(rel['proj1_entities'])

                if rel['target'] not in aggregated_rels[pair]['entities']:
                    aggregated_rels[pair]['entities'][rel['target']] = []
                aggregated_rels[pair]['entities'][rel['target']].extend(rel['proj2_entities'])

        # Add aggregated project-to-project relationships (ONE edge per pair)
        for pair, agg_data in aggregated_rels.items():
            source, target = pair
            categories = [c for c in agg_data['categories'] if c != 'general']
            num_connections = len(categories)

            # Create combined label
            if num_connections == 1:
                label = categories[0].upper()
            elif num_connections == 2:
                label = f"{categories[0].upper()} + {categories[1].upper()}"
            else:
                label = f"{num_connections} CONNECTIONS"

            # Create hover text with ALL relationships
            hover_text = f"""
            <b>{num_connections} Shared Technology Categories</b><br>
            <b>{source.replace('_', ' ').title()}</b> ↔ <b>{target.replace('_', ' ').title()}</b><br>
            <hr>
            """

            for category in categories:
                hover_text += f"<br><b>📌 {category.upper()}</b><br>"
                if source in agg_data['entities'] and target in agg_data['entities']:
                    src_entities = list(set(agg_data['entities'][source]))[:3]
                    tgt_entities = list(set(agg_data['entities'][target]))[:3]
                    hover_text += f"  {source}: {', '.join(src_entities)}<br>"
                    hover_text += f"  {target}: {', '.join(tgt_entities)}<br>"

            # Edge width based on number of connections
            width = min(num_connections * 3, 15)

            net.add_edge(
                source,
                target,
                label=label,
                title=hover_text,
                width=width,
                color={'color': '#FF1493', 'opacity': 0.8},
                font={'size': 16, 'bold': True, 'color': '#FF1493'}
            )

        # Add top entities from each project (smaller nodes)
        for project_name, kg_data in projects.items():
            # Get entity frequency
            entity_freq = defaultdict(int)
            for triplet in kg_data['triplets']:
                entity_freq[triplet['head']] += 1
                entity_freq[triplet['tail']] += 1

            # Add top 5 entities
            top_entities = sorted(entity_freq.items(), key=lambda x: x[1], reverse=True)[:5]

            for entity, freq in top_entities:
                node_id = f"{project_name}::{entity}"

                hover_text = f"""
                <b>{entity}</b><br>
                Project: {project_name.replace('_', ' ').title()}<br>
                Mentions: {freq}<br>
                """

                net.add_node(
                    node_id,
                    label=entity,
                    title=hover_text,
                    color=self.project_colors.get(project_name, '#95E1D3'),
                    size=15 + freq * 3,
                    shape='dot'
                )

                # Connect entity to its project
                net.add_edge(
                    project_name,
                    node_id,
                    color={'color': '#CCCCCC', 'opacity': 0.4},
                    width=1,
                    dashes=True
                )

        # Add legend
        legend_html = f"""
        <div style="position: fixed; top: 10px; right: 10px; background: white; padding: 20px; border: 3px solid #333; border-radius: 10px; font-family: Arial; z-index: 1000; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
            <h2 style="margin-top: 0; border-bottom: 2px solid #333; padding-bottom: 10px;">Project Relationships</h2>

            <h3>Projects</h3>
            <div style="margin-left: 10px;">
                <div><span style="color: {self.project_colors['alpha_erp_system']}; font-size: 20px;">■</span> <b>Alpha ERP System</b></div>
                <div><span style="color: {self.project_colors['beta_cloud_migration']}; font-size: 20px;">■</span> <b>Beta Cloud Migration</b></div>
                <div><span style="color: {self.project_colors['gamma_analytics_platform']}; font-size: 20px;">■</span> <b>Gamma Analytics Platform</b></div>
            </div>

            <h3 style="margin-top: 15px;">Relationships</h3>
            <div style="margin-left: 10px;">
                <div><span style="color: #FF1493; font-size: 18px; font-weight: bold;">━━</span> Project-to-Project (Pink)</div>
                <div><span style="color: #CCCCCC; font-size: 18px;">┄┄</span> Project-to-Entity (Gray)</div>
            </div>

            <h3 style="margin-top: 15px;">Node Size</h3>
            <div style="margin-left: 10px;">
                <div>• Large boxes = Projects</div>
                <div>• Small circles = Top entities</div>
                <div>• Size = Importance/frequency</div>
            </div>

            <hr style="margin: 15px 0;">
            <div><b>Instructions:</b></div>
            <div style="margin-left: 10px; font-size: 12px;">
                <div>• <b>Drag</b> nodes to rearrange</div>
                <div>• <b>Scroll</b> to zoom in/out</div>
                <div>• <b>Hover</b> for details</div>
                <div>• <b>Click</b> to highlight</div>
            </div>

            <div style="margin-top: 15px; padding: 10px; background: #fffacd; border-radius: 5px; font-size: 12px;">
                <b>💡 Tip:</b> Pink lines show how projects are related based on shared technology categories!
            </div>
        </div>
        """

        # Save graph
        net.save_graph(str(output_file))

        # Add legend
        with open(output_file, 'r', encoding='utf-8') as f:
            html = f.read()
        html = html.replace('</body>', f'{legend_html}</body>')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        self.logger.info(f"Project relationship graph saved to: {output_file}")

        return net, project_relationships


def main():
    parser = argparse.ArgumentParser(
        description="Create interactive graph with project-to-project relationships"
    )
    parser.add_argument(
        '--datasets-dir',
        type=str,
        default='./datasets',
        help='Path to datasets directory'
    )

    args = parser.parse_args()

    # Setup paths
    datasets_dir = Path(args.datasets_dir)
    kg_dir = datasets_dir / 'knowledge_graphs'
    output_file = kg_dir / 'project_relationships_interactive.html'

    if not kg_dir.exists():
        print(f"❌ Knowledge graphs directory not found: {kg_dir}")
        return

    print("\n" + "=" * 80)
    print("PROJECT RELATIONSHIP GRAPH BUILDER")
    print("=" * 80)

    try:
        builder = ProjectRelationshipGraphBuilder(kg_dir)

        print("\n📊 Loading knowledge graphs...")
        projects = builder.load_projects()

        if not projects:
            print("❌ No knowledge graphs found")
            return

        print(f"✓ Loaded {len(projects)} projects")

        print("\n🔍 Analyzing project relationships...")
        net, relationships = builder.create_project_focused_graph(projects, output_file)

        # Display results
        print(f"\n{'─' * 80}")
        print("GRAPH STATISTICS")
        print(f"{'─' * 80}")
        print(f"Projects:                   {len(projects)}")
        print(f"Total Nodes:                {len(net.nodes)}")
        print(f"Total Edges:                {len(net.edges)}")
        print(f"Project-to-Project Links:   {len([r for r in relationships if 'similar' in r['relation'] or 'shares' in r['relation']])}")

        if relationships:
            print(f"\n{'─' * 80}")
            print("PROJECT RELATIONSHIPS FOUND")
            print(f"{'─' * 80}")

            for rel in relationships:
                if rel['relation'] == 'similar_tech_stack':
                    print(f"\n  {rel['source']} ↔ {rel['target']}")
                    print(f"    Similarity: {rel['relation'].replace('_', ' ').title()}")
                    print(f"    Shared categories: {', '.join(rel['shared_categories'])}")
                else:
                    print(f"\n  {rel['source']} ↔ {rel['target']}")
                    print(f"    Connection: Both use {rel['category'].upper()} technology")
                    print(f"    {rel['source']}: {', '.join(rel['proj1_entities'][:3])}")
                    print(f"    {rel['target']}: {', '.join(rel['proj2_entities'][:3])}")

        print(f"\n{'=' * 80}")
        print(f"✓ Interactive graph saved to:")
        print(f"  {output_file}")
        print(f"{'=' * 80}")
        print(f"\n💡 Open in browser:")
        print(f"   {output_file.absolute()}")
        print()

    except Exception as e:
        logger.error(f"Failed: {e}")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
