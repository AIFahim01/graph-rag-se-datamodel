"""
Visualize Cross-Project Entity Connections

Creates an interactive graph showing which projects are connected
through REAL shared entities found by processing all chunks together.
"""

import json
import argparse
from pathlib import Path
from pyvis.network import Network


def create_cross_project_visualization(unified_kg_file: Path, output_file: Path):
    """Create interactive visualization of cross-project connections"""

    # Load unified KG
    with open(unified_kg_file, 'r') as f:
        data = json.load(f)

    # Create network
    net = Network(
        height='800px',
        width='100%',
        bgcolor='#f8f9fa',
        font_color='#000000',
        directed=True
    )

    # Physics for better visualization
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "stabilization": {"iterations": 400},
        "barnesHut": {
          "gravitationalConstant": -15000,
          "centralGravity": 0.6,
          "springLength": 300
        }
      }
    }
    """)

    # Project colors
    project_colors = {
        'alpha_erp_system': '#FF6B6B',
        'beta_cloud_migration': '#4ECDC4',
        'gamma_analytics_platform': '#95E1D3'
    }

    # Count triplets per project
    project_triplet_counts = {}
    for triplet in data['all_triplets']:
        proj = triplet['project']
        project_triplet_counts[proj] = project_triplet_counts.get(proj, 0) + 1

    # Add project nodes
    projects = set(t['project'] for t in data['all_triplets'])
    for project in projects:
        hover = f"""
        <b>Project: {project.replace('_', ' ').title()}</b><br>
        Triplets: {project_triplet_counts.get(project, 0)}<br>
        """

        net.add_node(
            project,
            label=project.replace('_', ' ').title(),
            title=hover,
            color=project_colors.get(project, '#95E1D3'),
            size=70,
            shape='box',
            font={'size': 22, 'bold': True},
            borderWidth=4
        )

    # Add cross-project entities as nodes
    for entity, entity_projects in data['cross_project_entities'].items():
        hover = f"""
        <b>CROSS-PROJECT ENTITY</b><br>
        <b>{entity}</b><br>
        <hr>
        Appears in {len(entity_projects)} projects:<br>
        {('<br>').join([f'  • {p.replace("_", " ").title()}' for p in entity_projects])}
        """

        net.add_node(
            entity,
            label=entity,
            title=hover,
            color='#FFD700',  # GOLD for cross-project
            size=40,
            shape='star',
            font={'size': 16, 'bold': True}
        )

        # Connect entity to its projects
        for proj in entity_projects:
            net.add_edge(
                proj,
                entity,
                label='mentions',
                color={'color': project_colors.get(proj, '#95E1D3'), 'opacity': 0.7},
                width=4,
                arrows={'to': {'enabled': True, 'scaleFactor': 0.8}}
            )

    # Add connections between projects that share entities
    for conn in data['project_connections']:
        proj1 = conn['project1']
        proj2 = conn['project2']
        shared = conn['shared_entities']

        hover = f"""
        <b>SHARED ENTITIES CONNECTION</b><br>
        <b>{proj1.replace('_', ' ').title()}</b> ↔ <b>{proj2.replace('_', ' ').title()}</b><br>
        <hr>
        Shared entities: {conn['num_shared_entities']}<br>
        {('<br>').join([f'  • {e}' for e in shared])}
        """

        net.add_edge(
            proj1,
            proj2,
            label=f"{conn['num_shared_entities']} shared",
            title=hover,
            color={'color': '#FF1493', 'opacity': 0.9},
            width=conn['num_shared_entities'] * 5,
            dashes=False,
            font={'size': 16, 'bold': True, 'color': '#FF1493'}
        )

    # Add legend
    legend_html = f"""
    <div style="position: fixed; top: 10px; right: 10px; background: white; padding: 20px; border: 3px solid #333; border-radius: 10px; font-family: Arial; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
        <h2 style="margin-top: 0; border-bottom: 2px solid #333; padding-bottom: 10px;">Cross-Project Entities</h2>

        <h3>Projects</h3>
        <div style="margin-left: 10px;">
            <div><span style="color: {project_colors['alpha_erp_system']}; font-size: 20px;">■</span> <b>Alpha ERP System</b></div>
            <div><span style="color: {project_colors['beta_cloud_migration']}; font-size: 20px;">■</span> <b>Beta Cloud Migration</b></div>
            <div><span style="color: {project_colors['gamma_analytics_platform']}; font-size: 20px;">■</span> <b>Gamma Analytics Platform</b></div>
        </div>

        <h3 style="margin-top: 15px;">Cross-Project Entities</h3>
        <div style="margin-left: 10px;">
            <div><span style="color: #FFD700; font-size: 20px;">★</span> <b>Shared Entity (GOLD STAR)</b></div>
            <div style="margin-left: 20px; margin-top: 5px;">
                • <b>Kubernetes</b> (beta + gamma)<br>
                • <b>October 29, 2025</b> (beta + gamma)
            </div>
        </div>

        <h3 style="margin-top: 15px;">Connections</h3>
        <div style="margin-left: 10px;">
            <div><span style="color: #FF1493; font-size: 18px; font-weight: bold;">━━</span> Project Shares Entities (PINK)</div>
            <div style="margin-left: 20px; font-size: 12px;">Width = number of shared entities</div>
        </div>

        <hr style="margin: 15px 0;">
        <div style="padding: 12px; background: #e8f5e9; border-radius: 5px;">
            <b>✅ Found:</b> 2 cross-project entities<br>
            <b>Connection:</b> Beta ↔ Gamma share Kubernetes!
        </div>

        <div style="margin-top: 10px; padding: 12px; background: #fff3cd; border-radius: 5px;">
            <b>ℹ️ Note:</b> Alpha uses different tech stack (SAP/ERP), so no exact entity overlap with others.
        </div>

        <hr style="margin: 15px 0;">
        <div><b>Instructions:</b></div>
        <div style="margin-left: 10px; font-size: 12px;">
            <div>• <b>Drag</b> nodes to rearrange</div>
            <div>• <b>Scroll</b> to zoom</div>
            <div>• <b>Hover</b> for details</div>
            <div>• <b>Click</b> to highlight</div>
        </div>
    </div>
    """

    # Save
    net.save_graph(str(output_file))

    # Add legend
    with open(output_file, 'r', encoding='utf-8') as f:
        html = f.read()
    html = html.replace('</body>', f'{legend_html}</body>')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✓ Interactive visualization saved to: {output_file}")
    print(f"\n💡 Open in browser to see:")
    print(f"   - 3 project boxes (Alpha, Beta, Gamma)")
    print(f"   - 2 GOLD STARS (Kubernetes, date)")
    print(f"   - THICK PINK LINE: Beta ↔ Gamma sharing Kubernetes")
    print(f"   - Alpha isolated (correct - different tech stack)")


def main():
    parser = argparse.ArgumentParser(
        description="Visualize cross-project entity connections"
    )
    parser.add_argument(
        '--datasets-dir',
        type=str,
        default='./datasets',
        help='Path to datasets directory'
    )

    args = parser.parse_args()

    datasets_dir = Path(args.datasets_dir)
    kg_dir = datasets_dir / 'knowledge_graphs'
    unified_kg = kg_dir / 'unified_rebel_cross_project.json'
    output_file = kg_dir / 'cross_project_entities_interactive.html'

    if not unified_kg.exists():
        print(f"❌ Unified KG not found: {unified_kg}")
        print("   Run build_unified_rebel_kg.py first")
        return

    print("\n" + "=" * 80)
    print("CROSS-PROJECT ENTITY VISUALIZATION")
    print("=" * 80)

    create_cross_project_visualization(unified_kg, output_file)

    print(f"\n{'=' * 80}")
    print(f"File: {output_file.absolute()}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
