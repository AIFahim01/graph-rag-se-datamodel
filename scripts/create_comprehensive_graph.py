"""
Create Comprehensive Knowledge Graph

Shows ALL relationships:
- All entities (nodes)
- All triplets within each project (edges)
- Cross-project entity connections (highlighted)
- Project groupings

This creates a large, complete graph showing everything.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from pyvis.network import Network


def create_comprehensive_graph(unified_kg_file: Path, output_file: Path):
    """Create comprehensive graph with all nodes and edges"""

    # Load data
    with open(unified_kg_file, 'r') as f:
        data = json.load(f)

    # Create network
    net = Network(
        height='1000px',
        width='100%',
        bgcolor='#ffffff',
        font_color='#000000',
        directed=True
    )

    # Physics for large graph
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "stabilization": {"iterations": 1000},
        "barnesHut": {
          "gravitationalConstant": -5000,
          "centralGravity": 0.2,
          "springLength": 150,
          "springConstant": 0.01,
          "damping": 0.5
        }
      },
      "nodes": {
        "font": {"size": 11}
      },
      "edges": {
        "font": {"size": 10},
        "smooth": {"type": "continuous"}
      }
    }
    """)

    # Colors
    project_colors = {
        'alpha_erp_system': '#FF6B6B',
        'beta_cloud_migration': '#4ECDC4',
        'gamma_analytics_platform': '#95E1D3'
    }

    # Track entities
    entity_to_projects = defaultdict(set)
    entity_frequency = defaultdict(int)

    for triplet in data['all_triplets']:
        entity_to_projects[triplet['head']].add(triplet['project'])
        entity_to_projects[triplet['tail']].add(triplet['project'])
        entity_frequency[triplet['head']] += 1
        entity_frequency[triplet['tail']] += 1

    # Add ALL entities as nodes
    for entity, projects in entity_to_projects.items():
        num_projects = len(projects)
        freq = entity_frequency[entity]

        # Determine color
        if num_projects > 1:
            # Cross-project entity - GOLD
            color = '#FFD700'
            border_color = '#FF6B00'
            border_width = 4
            shape = 'star'
            size = 25 + freq * 3
        else:
            # Single project entity - project color
            project = list(projects)[0]
            color = project_colors.get(project, '#95E1D3')
            border_color = color
            border_width = 2
            shape = 'dot'
            size = 15 + freq * 2

        hover = f"""
        <b>{entity}</b><br>
        {'<b>CROSS-PROJECT ENTITY!</b><br>' if num_projects > 1 else ''}
        Projects: {', '.join(p.replace('_', ' ').title() for p in projects)}<br>
        Mentions: {freq}
        """

        net.add_node(
            entity,
            label=entity if len(entity) < 30 else entity[:27] + '...',
            title=hover,
            color={'background': color, 'border': border_color},
            borderWidth=border_width,
            size=size,
            shape=shape,
            font={'size': 10 if num_projects == 1 else 14, 'bold': num_projects > 1}
        )

    # Add ALL triplets as edges
    cross_project_edge_count = 0
    within_project_edge_count = 0

    for triplet in data['all_triplets']:
        head = triplet['head']
        tail = triplet['tail']
        project = triplet['project']

        # Check if this is a cross-project edge
        head_projects = entity_to_projects[head]
        tail_projects = entity_to_projects[tail]
        is_cross_project = len(head_projects) > 1 or len(tail_projects) > 1

        if is_cross_project:
            # Cross-project edge - HIGHLIGHT
            color = '#FF6B00'  # Orange
            width = 4
            opacity = 0.9
            cross_project_edge_count += 1
        else:
            # Within-project edge - project color
            color = project_colors.get(project, '#95E1D3')
            width = 2
            opacity = 0.5
            within_project_edge_count += 1

        hover = f"""
        <b>{triplet['relation']}</b><br>
        {'<b>CROSS-PROJECT CONNECTION!</b><br>' if is_cross_project else ''}
        Project: {project.replace('_', ' ').title()}<br>
        Source: {triplet['source_pdf']}<br>
        Page: {triplet['page_number']}<br>
        Chunk: {triplet['chunk_id']}<br>
        <hr>
        {triplet['source_text'][:120]}...
        """

        net.add_edge(
            head,
            tail,
            label=triplet['relation'] if len(triplet['relation']) < 20 else triplet['relation'][:17] + '...',
            title=hover,
            color={'color': color, 'opacity': opacity},
            width=width,
            arrows={'to': {'enabled': True, 'scaleFactor': 0.5}},
            font={'size': 9, 'color': color if is_cross_project else '#666666'}
        )

    # Calculate statistics
    total_nodes = len(net.nodes)
    total_edges = len(net.edges)
    cross_project_entities = len([e for e, p in entity_to_projects.items() if len(p) > 1])

    # Legend
    legend_html = f"""
    <div style="position: fixed; top: 10px; right: 10px; background: white; padding: 20px; border: 3px solid #333; border-radius: 10px; font-family: Arial; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.3); max-width: 350px;">
        <h2 style="margin-top: 0; border-bottom: 2px solid #333; padding-bottom: 10px;">Comprehensive Knowledge Graph</h2>

        <div style="background: #e3f2fd; padding: 12px; border-radius: 5px; margin-bottom: 15px;">
            <h3 style="margin: 0 0 10px 0;">Statistics</h3>
            <div><b>Total Nodes:</b> {total_nodes}</div>
            <div><b>Total Edges:</b> {total_edges}</div>
            <div><b>Cross-Project Entities:</b> {cross_project_entities}</div>
            <div><b>Cross-Project Edges:</b> {cross_project_edge_count}</div>
            <div><b>Within-Project Edges:</b> {within_project_edge_count}</div>
        </div>

        <h3>Node Types</h3>
        <div style="margin-left: 10px; font-size: 13px;">
            <div><span style="color: #FFD700; font-size: 18px;">★</span> <b>Cross-Project Entity</b></div>
            <div style="margin-left: 20px;">Gold star = appears in 2+ projects</div>
            <div style="margin-top: 8px;"><span style="color: #FF6B6B; font-size: 18px;">●</span> Alpha entities (red)</div>
            <div><span style="color: #4ECDC4; font-size: 18px;">●</span> Beta entities (teal)</div>
            <div><span style="color: #95E1D3; font-size: 18px;">●</span> Gamma entities (mint)</div>
        </div>

        <h3 style="margin-top: 15px;">Edge Types</h3>
        <div style="margin-left: 10px; font-size: 13px;">
            <div><span style="color: #FF6B00; font-size: 16px; font-weight: bold;">━━</span> <b>Cross-Project (ORANGE)</b></div>
            <div style="margin-left: 20px;">Connects entities in multiple projects</div>
            <div style="margin-top: 8px;"><span style="color: #FF6B6B; font-size: 16px;">──</span> Within Alpha (red, thin)</div>
            <div><span style="color: #4ECDC4; font-size: 16px;">──</span> Within Beta (teal, thin)</div>
            <div><span style="color: #95E1D3; font-size: 16px;">──</span> Within Gamma (mint, thin)</div>
        </div>

        <hr style="margin: 15px 0;">

        <div style="padding: 12px; background: #e8f5e9; border-radius: 5px; font-size: 13px;">
            <b>✅ Cross-Project Entities:</b><br>
            • <b>Kubernetes</b> (beta + gamma)<br>
            • <b>October 29, 2025</b> (beta + gamma)
        </div>

        <div style="margin-top: 10px; padding: 12px; background: #fff3cd; border-radius: 5px; font-size: 13px;">
            <b>ℹ️ Alpha ERP:</b> Uses SAP/ERP stack - no exact entity overlap with cloud-based projects
        </div>

        <hr style="margin: 15px 0;">
        <div style="font-size: 12px;">
            <b>Instructions:</b><br>
            • <b>Drag</b> nodes to rearrange<br>
            • <b>Scroll</b> to zoom<br>
            • <b>Hover</b> for details<br>
            • <b>Look for ORANGE edges</b> = cross-project<br>
            • <b>Look for GOLD STARS</b> = shared entities
        </div>
    </div>
    """

    # Save
    net.save_graph(str(output_file))
    with open(output_file, 'r', encoding='utf-8') as f:
        html = f.read()
    html = html.replace('</body>', f'{legend_html}</body>')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✓ Comprehensive graph saved!")
    print(f"\nStatistics:")
    print(f"  Total nodes (entities):       {total_nodes}")
    print(f"  Total edges (triplets):       {total_edges}")
    print(f"  Cross-project entities:       {cross_project_entities}")
    print(f"  Cross-project edges:          {cross_project_edge_count}")
    print(f"  Within-project edges:         {within_project_edge_count}")


def main():
    parser = argparse.ArgumentParser(description="Create comprehensive KG visualization")
    parser.add_argument('--datasets-dir', type=str, default='./datasets')
    args = parser.parse_args()

    datasets_dir = Path(args.datasets_dir)
    kg_dir = datasets_dir / 'knowledge_graphs'
    unified_kg = kg_dir / 'unified_rebel_cross_project.json'
    output_file = kg_dir / 'comprehensive_knowledge_graph.html'

    if not unified_kg.exists():
        print(f"❌ File not found: {unified_kg}")
        return

    print("\n" + "=" * 80)
    print("COMPREHENSIVE KNOWLEDGE GRAPH BUILDER")
    print("=" * 80)

    create_comprehensive_graph(unified_kg, output_file)

    print(f"\n{'=' * 80}")
    print(f"✓ File: {output_file.absolute()}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
