"""
Create Interactive Unified Knowledge Graph

Generates an interactive HTML visualization showing all projects and their
relationships in one unified, explorable graph.

Features:
- Interactive nodes (click, hover, drag)
- Zoom and pan
- Color-coded by project
- Shows metadata on hover
- Physics-based layout
- Filterable and searchable
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from loguru import logger

from pyvis.network import Network
import networkx as nx


class InteractiveKnowledgeGraphBuilder:
    """Build interactive unified knowledge graph visualization"""

    def __init__(self, kg_dir: Path, use_metadata: bool = True):
        """
        Initialize interactive graph builder

        Args:
            kg_dir: Directory containing knowledge graph files
            use_metadata: Use metadata-enriched KG files if available
        """
        self.kg_dir = Path(kg_dir)
        self.use_metadata = use_metadata
        self.logger = logger

        # Color palette for projects
        self.project_colors = {
            'alpha_erp_system': '#FF6B6B',       # Red
            'beta_cloud_migration': '#4ECDC4',   # Teal
            'gamma_analytics_platform': '#95E1D3', # Mint
            'project': '#FFA07A'                  # Orange for project nodes
        }

    def load_all_knowledge_graphs(self) -> dict:
        """Load all project knowledge graphs"""
        projects = {}

        # Try to load metadata version first
        if self.use_metadata:
            kg_pattern = "*_with_metadata.json"
        else:
            kg_pattern = "*_knowledge_graph.json"

        kg_files = list(self.kg_dir.glob(kg_pattern))

        # Filter out unified KG
        kg_files = [f for f in kg_files if 'unified' not in f.name]

        if not kg_files:
            # Fallback to non-metadata version
            kg_files = [f for f in self.kg_dir.glob("*_knowledge_graph.json")
                       if 'unified' not in f.name and 'with_metadata' not in f.name]

        for kg_file in kg_files:
            with open(kg_file, 'r', encoding='utf-8') as f:
                kg_data = json.load(f)
                project_name = kg_data['project_name']
                projects[project_name] = kg_data
                self.logger.info(f"Loaded {project_name}: {len(kg_data['triplets'])} triplets")

        return projects

    def create_interactive_graph(
        self,
        projects: dict,
        output_file: Path,
        include_project_nodes: bool = True
    ):
        """
        Create interactive unified knowledge graph

        Args:
            projects: Dictionary of project knowledge graphs
            output_file: Path to save HTML file
            include_project_nodes: Add project nodes to graph
        """
        # Create pyvis network
        net = Network(
            height='900px',
            width='100%',
            bgcolor='#ffffff',
            font_color='#000000',
            directed=True
        )

        # Configure physics
        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "stabilization": {
              "enabled": true,
              "iterations": 200
            },
            "barnesHut": {
              "gravitationalConstant": -8000,
              "centralGravity": 0.3,
              "springLength": 200,
              "springConstant": 0.04,
              "damping": 0.09
            }
          },
          "nodes": {
            "font": {
              "size": 14,
              "face": "arial"
            }
          },
          "edges": {
            "font": {
              "size": 12,
              "align": "middle"
            },
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 0.5
              }
            },
            "smooth": {
              "type": "continuous"
            }
          }
        }
        """)

        # Track all entities
        entity_projects = defaultdict(set)

        # Add project nodes (if enabled)
        if include_project_nodes:
            for project_name in projects.keys():
                net.add_node(
                    project_name,
                    label=project_name.replace('_', ' ').title(),
                    title=f"<b>Project:</b> {project_name}<br><b>PDFs:</b> {projects[project_name]['num_pdfs']}<br><b>Triplets:</b> {projects[project_name]['num_unique_triplets']}",
                    color=self.project_colors.get('project', '#FFA07A'),
                    size=40,
                    shape='box',
                    font={'size': 18, 'bold': True}
                )

        # Add entity nodes and relationships
        for project_name, kg_data in projects.items():
            project_color = self.project_colors.get(project_name, '#95E1D3')

            for triplet in kg_data['triplets']:
                head = triplet['head']
                relation = triplet['relation']
                tail = triplet['tail']

                # Track which projects this entity appears in
                entity_projects[head].add(project_name)
                entity_projects[tail].add(project_name)

                # Create hover text with metadata
                if 'metadata' in triplet:
                    meta = triplet['metadata']
                    head_title = f"<b>{head}</b><br>Project: {project_name}<br>Source: {meta['source_pdf']}<br>Page: {meta['page_number']}"
                    tail_title = f"<b>{tail}</b><br>Project: {project_name}<br>Source: {meta['source_pdf']}<br>Page: {meta['page_number']}"
                    edge_title = f"<b>{relation}</b><br>From: {meta['source_pdf']} (p.{meta['page_number']})<br>Context: {meta['source_text'][:100]}..."

                    if 'mention_count' in triplet:
                        edge_title += f"<br><b>Mentions:</b> {triplet['mention_count']}"
                else:
                    head_title = f"<b>{head}</b><br>Project: {project_name}"
                    tail_title = f"<b>{tail}</b><br>Project: {project_name}"
                    edge_title = f"<b>{relation}</b>"

                # Determine node color (cross-project entities get special color)
                head_color = project_color
                tail_color = project_color

                # Add nodes
                if head not in net.get_nodes():
                    net.add_node(
                        head,
                        label=head,
                        title=head_title,
                        color=head_color,
                        size=20,
                        shape='dot'
                    )

                if tail not in net.get_nodes():
                    net.add_node(
                        tail,
                        label=tail,
                        title=tail_title,
                        color=tail_color,
                        size=20,
                        shape='dot'
                    )

                # Add edge
                net.add_edge(
                    head,
                    tail,
                    label=relation,
                    title=edge_title,
                    color={'color': project_color, 'opacity': 0.6},
                    width=2
                )

        # Highlight cross-project entities
        cross_project_entities = {e for e, projs in entity_projects.items() if len(projs) > 1}
        if cross_project_entities:
            for entity in cross_project_entities:
                # Update node to show it's cross-project
                projects_str = ', '.join(entity_projects[entity])
                net.get_node(entity)['color'] = '#FFD700'  # Gold color
                net.get_node(entity)['size'] = 30
                net.get_node(entity)['title'] = f"<b>{entity}</b><br><b>CROSS-PROJECT!</b><br>Appears in: {projects_str}"

        # Add project-to-entity edges (if project nodes exist)
        if include_project_nodes:
            for entity, projs in entity_projects.items():
                for project in projs:
                    net.add_edge(
                        project,
                        entity,
                        label='mentions',
                        title=f"{project} mentions {entity}",
                        color={'color': '#CCCCCC', 'opacity': 0.3},
                        dashes=True,
                        width=1
                    )

        # Add legend to the graph
        legend_html = """
        <div style="position: fixed; top: 10px; right: 10px; background: white; padding: 15px; border: 2px solid #333; border-radius: 8px; font-family: Arial; z-index: 1000;">
            <h3 style="margin-top: 0;">Legend</h3>
            <div><span style="color: #FF6B6B;">●</span> Alpha ERP System</div>
            <div><span style="color: #4ECDC4;">●</span> Beta Cloud Migration</div>
            <div><span style="color: #95E1D3;">●</span> Gamma Analytics Platform</div>
            <div><span style="color: #FFD700;">●</span> Cross-Project Entity (GOLD)</div>
            <div><span style="color: #FFA07A;">■</span> Project Node</div>
            <hr>
            <div><b>Instructions:</b></div>
            <div>• Drag nodes to rearrange</div>
            <div>• Scroll to zoom</div>
            <div>• Hover for details</div>
            <div>• Click to highlight connections</div>
        </div>
        """

        # Save with custom HTML
        net.save_graph(str(output_file))

        # Add legend to HTML
        with open(output_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Insert legend before closing body tag
        html_content = html_content.replace('</body>', f'{legend_html}</body>')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"Interactive graph saved to: {output_file}")

        return net


def main():
    parser = argparse.ArgumentParser(
        description="Create interactive unified knowledge graph visualization"
    )
    parser.add_argument(
        '--datasets-dir',
        type=str,
        default='./datasets',
        help='Path to datasets directory (default: ./datasets)'
    )
    parser.add_argument(
        '--no-project-nodes',
        action='store_true',
        help='Do not include project nodes (only show entities)'
    )
    parser.add_argument(
        '--no-metadata',
        action='store_true',
        help='Use non-metadata KG files'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='unified_knowledge_graph_interactive.html',
        help='Output HTML file name'
    )

    args = parser.parse_args()

    # Setup paths
    datasets_dir = Path(args.datasets_dir)
    kg_dir = datasets_dir / 'knowledge_graphs'
    output_file = kg_dir / args.output

    if not kg_dir.exists():
        print(f"❌ Knowledge graphs directory not found: {kg_dir}")
        print("   Run build_knowledge_graph_rebel.py first")
        return

    print("\n" + "=" * 80)
    print("INTERACTIVE UNIFIED KNOWLEDGE GRAPH BUILDER")
    print("=" * 80)

    try:
        # Build interactive graph
        builder = InteractiveKnowledgeGraphBuilder(
            kg_dir,
            use_metadata=not args.no_metadata
        )

        print("\n📊 Loading knowledge graphs...")
        projects = builder.load_all_knowledge_graphs()

        if not projects:
            print("❌ No knowledge graphs found")
            return

        print(f"✓ Loaded {len(projects)} projects")

        print("\n🎨 Creating interactive visualization...")
        net = builder.create_interactive_graph(
            projects,
            output_file,
            include_project_nodes=not args.no_project_nodes
        )

        # Display statistics
        print(f"\n{'─' * 80}")
        print("GRAPH STATISTICS")
        print(f"{'─' * 80}")
        print(f"Projects:              {len(projects)}")
        print(f"Total Nodes:           {len(net.nodes)}")
        print(f"Total Edges:           {len(net.edges)}")

        # Count entities per project
        entity_counts = defaultdict(int)
        for project_name, kg_data in projects.items():
            all_entities = set()
            for t in kg_data['triplets']:
                all_entities.add(t['head'])
                all_entities.add(t['tail'])
            entity_counts[project_name] = len(all_entities)

        print(f"\nEntities per project:")
        for project, count in entity_counts.items():
            print(f"  {project:30s}: {count:3d} entities")

        print(f"\n{'=' * 80}")
        print(f"✓ Interactive graph saved to:")
        print(f"  {output_file}")
        print(f"{'=' * 80}")
        print(f"\n💡 Open this file in your web browser to explore the graph!")
        print(f"   File path: {output_file.absolute()}")
        print()

    except Exception as e:
        logger.error(f"Failed to create interactive graph: {e}")
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
