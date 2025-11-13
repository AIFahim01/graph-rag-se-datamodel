"""
Visualize Chunk-to-Chunk Relationships Across Projects

Shows which specific chunks from different projects are connected
through shared entities.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from pyvis.network import Network


def create_chunk_level_graph(unified_kg_file: Path, output_file: Path):
    """Create interactive graph showing chunk-to-chunk connections"""

    # Load data
    with open(unified_kg_file, 'r') as f:
        data = json.load(f)

    # Create network
    net = Network(
        height='900px',
        width='100%',
        bgcolor='#ffffff',
        font_color='#000000',
        directed=True
    )

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "stabilization": {"iterations": 500},
        "barnesHut": {
          "gravitationalConstant": -10000,
          "centralGravity": 0.4,
          "springLength": 250
        }
      }
    }
    """)

    # Colors
    project_colors = {
        'alpha_erp_system': '#FF6B6B',
        'beta_cloud_migration': '#4ECDC4',
        'gamma_analytics_platform': '#95E1D3'
    }

    # Track which chunks mention each cross-project entity
    entity_to_chunks = defaultdict(list)

    for triplet in data['all_triplets']:
        for entity in data['cross_project_entities'].keys():
            if entity.lower() in triplet['head'].lower() or entity.lower() in triplet['tail'].lower():
                chunk_key = f"{triplet['project']}::{triplet['chunk_id']}"
                entity_to_chunks[entity].append({
                    'chunk_key': chunk_key,
                    'project': triplet['project'],
                    'chunk_id': triplet['chunk_id'],
                    'pdf': triplet['source_pdf'],
                    'page': triplet['page_number'],
                    'triplet': triplet,
                    'text': triplet['source_text']
                })

    # Add project nodes (large)
    for project in set(t['project'] for t in data['all_triplets']):
        hover = f"<b>{project.replace('_', ' ').title()}</b>"
        net.add_node(
            f"PROJECT_{project}",
            label=project.replace('_', ' ').title(),
            title=hover,
            color=project_colors.get(project, '#95E1D3'),
            size=80,
            shape='box',
            font={'size': 24, 'bold': True},
            borderWidth=4
        )

    # Add cross-project entity nodes (gold stars)
    for entity in data['cross_project_entities'].keys():
        chunks = entity_to_chunks[entity]
        projects = list(data['cross_project_entities'][entity])

        hover = f"""
        <b>CROSS-PROJECT ENTITY</b><br>
        <b>{entity}</b><br>
        <hr>
        Appears in:<br>
        {('<br>').join([f'  • {p.replace("_", " ").title()}' for p in projects])}<br>
        <br>
        Mentioned in {len(chunks)} chunks
        """

        net.add_node(
            f"ENTITY_{entity}",
            label=entity,
            title=hover,
            color='#FFD700',
            size=50,
            shape='star',
            font={'size': 18, 'bold': True}
        )

    # Add chunk nodes (smaller, connected to entities)
    chunk_nodes_added = set()

    for entity, chunks in entity_to_chunks.items():
        for chunk_data in chunks:
            chunk_key = chunk_data['chunk_key']

            if chunk_key not in chunk_nodes_added:
                hover = f"""
                <b>Chunk: {chunk_data['chunk_id']}</b><br>
                Project: {chunk_data['project'].replace('_', ' ').title()}<br>
                PDF: {chunk_data['pdf']}<br>
                Page: {chunk_data['page']}<br>
                <hr>
                Triplet: {chunk_data['triplet']['head']} --[{chunk_data['triplet']['relation']}]--> {chunk_data['triplet']['tail']}<br>
                <br>
                Context: {chunk_data['text'][:150]}...
                """

                net.add_node(
                    chunk_key,
                    label=f"{chunk_data['chunk_id']}\\n({chunk_data['pdf'][:20]}...)",
                    title=hover,
                    color=project_colors.get(chunk_data['project'], '#95E1D3'),
                    size=25,
                    shape='dot',
                    font={'size': 10}
                )

                # Connect chunk to its project
                net.add_edge(
                    f"PROJECT_{chunk_data['project']}",
                    chunk_key,
                    color={'color': '#CCCCCC', 'opacity': 0.3},
                    width=1,
                    dashes=True
                )

                chunk_nodes_added.add(chunk_key)

            # Connect chunk to the cross-project entity
            net.add_edge(
                chunk_key,
                f"ENTITY_{entity}",
                label='mentions',
                color={'color': project_colors.get(chunk_data['project'], '#95E1D3'), 'opacity': 0.6},
                width=3,
                arrows={'to': {'enabled': True}}
            )

    # Add chunk-to-chunk connections (via shared entities)
    chunk_connections = []
    for entity, chunks in entity_to_chunks.items():
        if len(chunks) > 1:
            # Connect all chunks that mention this entity
            for i, chunk1 in enumerate(chunks):
                for chunk2 in chunks[i+1:]:
                    # Only connect chunks from DIFFERENT projects
                    if chunk1['project'] != chunk2['project']:
                        chunk_connections.append({
                            'chunk1': chunk1['chunk_key'],
                            'chunk2': chunk2['chunk_key'],
                            'entity': entity,
                            'project1': chunk1['project'],
                            'project2': chunk2['project'],
                            'pdf1': chunk1['pdf'],
                            'pdf2': chunk2['pdf']
                        })

                        # Add visible chunk-to-chunk edge
                        hover = f"""
                        <b>CHUNK-TO-CHUNK CONNECTION</b><br>
                        Via entity: <b>{entity}</b><br>
                        <hr>
                        {chunk1['project'].replace('_', ' ').title()}<br>
                        └─ {chunk1['pdf']}, {chunk1['chunk_id']}<br>
                        <br>
                        {chunk2['project'].replace('_', ' ').title()}<br>
                        └─ {chunk2['pdf']}, {chunk2['chunk_id']}
                        """

                        net.add_edge(
                            chunk1['chunk_key'],
                            chunk2['chunk_key'],
                            label=f'via {entity}',
                            title=hover,
                            color={'color': '#FF6B00', 'opacity': 0.9},
                            width=5,
                            dashes=False,
                            font={'size': 12, 'bold': True, 'color': '#FF6B00'}
                        )

    # Legend
    legend_html = f"""
    <div style="position: fixed; top: 10px; right: 10px; background: white; padding: 20px; border: 3px solid #333; border-radius: 10px; font-family: Arial; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
        <h2 style="margin-top: 0; border-bottom: 2px solid #333; padding-bottom: 10px;">Chunk-to-Chunk Connections</h2>

        <h3>Legend</h3>
        <div style="margin-left: 10px;">
            <div><span style="font-size: 20px;">■</span> Large Boxes = Projects</div>
            <div><span style="color: #FFD700; font-size: 20px;">★</span> Gold Stars = Cross-Project Entities</div>
            <div><span style="font-size: 16px;">●</span> Small Dots = Chunks</div>
        </div>

        <h3 style="margin-top: 15px;">Connections</h3>
        <div style="margin-left: 10px;">
            <div><span style="color: #FF6B00; font-size: 18px; font-weight: bold;">━━</span> <b>Chunk ↔ Chunk (ORANGE)</b></div>
            <div style="margin-left: 20px; font-size: 12px;">Shows chunks from different projects<br>connected via shared entity</div>
            <div style="margin-top: 8px;"><span style="color: #CCCCCC; font-size: 18px;">┄┄</span> Chunk → Project (gray)</div>
            <div style="margin-top: 8px;"><span style="color: #4ECDC4; font-size: 18px;">──</span> Chunk → Entity (colored)</div>
        </div>

        <hr style="margin: 15px 0;">
        <div style="padding: 12px; background: #e8f5e9; border-radius: 5px;">
            <b>Found:</b> {len(chunk_connections)} chunk-to-chunk connections<br>
            <b>Via:</b> {len(entity_to_chunks)} cross-project entities
        </div>

        <div style="margin-top: 10px; padding: 12px; background: #fff3cd; border-radius: 5px; font-size: 13px;">
            <b>💡 Key Insight:</b><br>
            Beta's cloud_migration_commercial.pdf chunk_1<br>
            ↔ Gamma's analytics_specifications.pdf chunk_4<br>
            Both mention <b>"Kubernetes"</b>!
        </div>

        <hr style="margin: 15px 0;">
        <div><b>Instructions:</b></div>
        <div style="margin-left: 10px; font-size: 12px;">
            <div>• <b>Look for ORANGE lines</b> = chunk connections</div>
            <div>• <b>Hover</b> over orange lines for details</div>
            <div>• <b>Drag</b> nodes to untangle</div>
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

    print(f"\n✓ Chunk-to-chunk visualization saved!")
    print(f"\nChunk-to-chunk connections found: {len(chunk_connections)}")
    for conn in chunk_connections:
        print(f"  {conn['chunk1']} ↔ {conn['chunk2']} (via {conn['entity']})")

    return chunk_connections


def main():
    parser = argparse.ArgumentParser(description="Visualize chunk-to-chunk connections")
    parser.add_argument('--datasets-dir', type=str, default='./datasets')
    args = parser.parse_args()

    datasets_dir = Path(args.datasets_dir)
    kg_dir = datasets_dir / 'knowledge_graphs'
    unified_kg = kg_dir / 'unified_rebel_cross_project.json'
    output_file = kg_dir / 'chunk_to_chunk_connections.html'

    if not unified_kg.exists():
        print(f"❌ File not found: {unified_kg}")
        return

    print("\n" + "=" * 80)
    print("CHUNK-TO-CHUNK CONNECTION VISUALIZER")
    print("=" * 80)

    connections = create_chunk_level_graph(unified_kg, output_file)

    print(f"\n{'=' * 80}")
    print(f"File: {output_file.absolute()}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
