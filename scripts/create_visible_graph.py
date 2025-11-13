"""
Create HIGHLY VISIBLE Knowledge Graph

Makes all relationships clearly visible without needing to hover:
- THICK edges
- BRIGHT colors
- CLEAR labels on all edges
- High contrast
- Larger fonts
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from pyvis.network import Network


def create_highly_visible_graph(unified_kg_file: Path, output_file: Path):
    """Create graph with VERY visible edges and labels"""

    # Load data
    with open(unified_kg_file, 'r') as f:
        data = json.load(f)

    # Create network
    net = Network(
        height='1000px',
        width='100%',
        bgcolor='#FFFFFF',
        font_color='#000000',
        directed=True
    )

    # Stronger physics for better separation
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "stabilization": {"iterations": 1500},
        "barnesHut": {
          "gravitationalConstant": -8000,
          "centralGravity": 0.3,
          "springLength": 200,
          "springConstant": 0.005,
          "damping": 0.4,
          "avoidOverlap": 1
        }
      },
      "nodes": {
        "font": {"size": 14, "face": "arial", "strokeWidth": 3, "strokeColor": "#ffffff"}
      },
      "edges": {
        "font": {"size": 13, "face": "arial", "strokeWidth": 2, "strokeColor": "#ffffff", "align": "middle"},
        "smooth": {"type": "continuous", "roundness": 0.5},
        "arrows": {
          "to": {"enabled": true, "scaleFactor": 0.8}
        }
      }
    }
    """)

    # Colors
    project_colors = {
        'alpha_erp_system': '#E53935',      # Bright red
        'beta_cloud_migration': '#00ACC1',   # Bright teal
        'gamma_analytics_platform': '#43A047' # Bright green
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

        if num_projects > 1:
            # Cross-project entity - VERY BRIGHT GOLD
            color = '#FFD700'
            border_color = '#FF6B00'
            border_width = 6
            shape = 'star'
            size = 35 + freq * 5
            font_size = 18
        else:
            # Single project entity - bright project color
            project = list(projects)[0]
            color = project_colors.get(project, '#95E1D3')
            border_color = color
            border_width = 3
            shape = 'dot'
            size = 20 + freq * 3
            font_size = 12

        hover = f"<b>{entity}</b><br>Mentions: {freq}<br>Projects: {', '.join(projects)}"

        net.add_node(
            entity,
            label=entity if len(entity) < 25 else entity[:22] + '...',
            title=hover,
            color={'background': color, 'border': border_color, 'highlight': {'background': color, 'border': '#000000'}},
            borderWidth=border_width,
            size=size,
            shape=shape,
            font={'size': font_size, 'bold': True, 'color': '#000000'}
        )

    # Add ALL triplets as VERY VISIBLE edges
    edge_labels_shown = set()

    for idx, triplet in enumerate(data['all_triplets']):
        head = triplet['head']
        tail = triplet['tail']
        relation = triplet['relation']
        project = triplet['project']

        # Check if cross-project
        head_projects = entity_to_projects[head]
        tail_projects = entity_to_projects[tail]
        is_cross_project = len(head_projects) > 1 or len(tail_projects) > 1

        if is_cross_project:
            # CROSS-PROJECT - VERY VISIBLE!
            edge_color = '#FF4500'  # Bright orange-red
            width = 8
            opacity = 1.0
            dashes = False
            label_color = '#FF4500'
            font_size = 14
        else:
            # Within-project - still visible
            edge_color = project_colors.get(project, '#95E1D3')
            width = 4
            opacity = 0.8
            dashes = False
            label_color = edge_color
            font_size = 11

        # Always show relation label
        edge_label = relation if len(relation) < 25 else relation[:22] + '...'

        # Create edge ID to avoid duplicate labels
        edge_id = f"{head}_{tail}_{relation}"

        # Always show label (not just on hover!)
        hover = f"""
        <b>{relation}</b><br>
        {'<b>CROSS-PROJECT!</b><br>' if is_cross_project else ''}
        {head} → {tail}<br>
        Project: {project}<br>
        Source: {triplet['source_pdf']} (p.{triplet['page_number']})
        """

        net.add_edge(
            head,
            tail,
            label=edge_label,  # ALWAYS SHOW LABEL
            title=hover,
            color={'color': edge_color, 'opacity': opacity, 'highlight': edge_color, 'hover': edge_color},
            width=width,
            dashes=dashes,
            arrows={'to': {'enabled': True, 'scaleFactor': 1.0, 'type': 'arrow'}},
            font={'size': font_size, 'color': label_color, 'bold': is_cross_project, 'strokeWidth': 0, 'strokeColor': '#ffffff', 'align': 'middle', 'background': '#ffffff'}
        )

    # Statistics
    total_nodes = len(net.nodes)
    total_edges = len(net.edges)
    cross_project_entities = len([e for e, p in entity_to_projects.items() if len(p) > 1])
    cross_project_edges = len([t for t in data['all_triplets']
                               if len(entity_to_projects[t['head']]) > 1 or len(entity_to_projects[t['tail']]) > 1])

    # Enhanced legend
    legend_html = f"""
    <div style="position: fixed; top: 10px; right: 10px; background: rgba(255,255,255,0.95); padding: 20px; border: 4px solid #000; border-radius: 10px; font-family: Arial; z-index: 1000; box-shadow: 0 6px 16px rgba(0,0,0,0.4);">
        <h2 style="margin-top: 0; border-bottom: 3px solid #000; padding-bottom: 10px; color: #000;">Complete Knowledge Graph</h2>

        <div style="background: #1976D2; color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h3 style="margin: 0 0 10px 0; color: white;">📊 Graph Statistics</h3>
            <div><b>Total Entities:</b> {total_nodes}</div>
            <div><b>Total Relationships:</b> {total_edges}</div>
            <div><b>Cross-Project Entities:</b> {cross_project_entities} ⭐</div>
            <div><b>Cross-Project Edges:</b> {cross_project_edges} 🔥</div>
        </div>

        <h3 style="color: #000;">Entity Types</h3>
        <div style="margin-left: 10px; font-size: 14px;">
            <div><span style="color: #FFD700; font-size: 24px;">★</span> <b>GOLD STAR = Shared Entity</b></div>
            <div style="margin-left: 25px; font-size: 12px;">Appears in 2+ projects</div>
            <div style="margin-top: 8px;"><span style="color: #E53935; font-size: 20px;">●</span> <b>Red = Alpha ERP</b></div>
            <div><span style="color: #00ACC1; font-size: 20px;">●</span> <b>Teal = Beta Cloud</b></div>
            <div><span style="color: #43A047; font-size: 20px;">●</span> <b>Green = Gamma Analytics</b></div>
        </div>

        <h3 style="margin-top: 15px; color: #000;">Relationship Types</h3>
        <div style="margin-left: 10px; font-size: 14px;">
            <div><span style="color: #FF4500; font-size: 20px; font-weight: bold;">━━━</span> <b>CROSS-PROJECT</b></div>
            <div style="margin-left: 25px; font-size: 12px;">THICK ORANGE = Touches shared entity</div>
            <div style="margin-top: 8px;"><span style="color: #E53935; font-size: 16px;">──</span> Within Alpha (red)</div>
            <div><span style="color: #00ACC1; font-size: 16px;">──</span> Within Beta (teal)</div>
            <div><span style="color: #43A047; font-size: 16px;">──</span> Within Gamma (green)</div>
        </div>

        <hr style="margin: 15px 0; border: 2px solid #000;">

        <div style="background: #4CAF50; color: white; padding: 12px; border-radius: 5px; font-size: 13px;">
            <b>✅ ALL LABELS VISIBLE!</b><br>
            Every edge shows its relationship type
        </div>

        <div style="margin-top: 10px; background: #FF9800; color: white; padding: 12px; border-radius: 5px; font-size: 13px;">
            <b>🔥 Look for:</b><br>
            THICK ORANGE edges = Cross-project!
        </div>

        <hr style="margin: 15px 0;">
        <div style="font-size: 13px; color: #000;">
            <b>Controls:</b><br>
            • <b>Drag</b> nodes<br>
            • <b>Scroll</b> to zoom<br>
            • <b>Click</b> node to highlight<br>
            • <b>All edges have labels!</b>
        </div>
    </div>
    """

    # Save
    net.save_graph(str(output_file))
    with open(output_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Add legend
    html = html.replace('</body>', f'{legend_html}</body>')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ HIGHLY VISIBLE graph created!")
    print(f"\nStatistics:")
    print(f"  Total nodes:              {total_nodes}")
    print(f"  Total edges:              {total_edges}")
    print(f"  Cross-project entities:   {cross_project_entities}")
    print(f"  Cross-project edges:      {cross_project_edges}")
    print(f"\n🔥 ALL EDGE LABELS ARE VISIBLE (not just on hover!)")
    print(f"🔥 THICK ORANGE edges show cross-project connections!")


def main():
    parser = argparse.ArgumentParser(description="Create highly visible KG")
    parser.add_argument('--datasets-dir', type=str, default='./datasets')
    args = parser.parse_args()

    datasets_dir = Path(args.datasets_dir)
    kg_dir = datasets_dir / 'knowledge_graphs'
    unified_kg = kg_dir / 'unified_rebel_cross_project.json'
    output_file = kg_dir / 'HIGHLY_VISIBLE_graph.html'

    if not unified_kg.exists():
        print(f"❌ File not found: {unified_kg}")
        return

    print("\n" + "=" * 80)
    print("HIGHLY VISIBLE KNOWLEDGE GRAPH BUILDER")
    print("=" * 80)

    create_highly_visible_graph(unified_kg, output_file)

    print(f"\n{'=' * 80}")
    print(f"✅ OPEN THIS FILE:")
    print(f"   {output_file.absolute()}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
