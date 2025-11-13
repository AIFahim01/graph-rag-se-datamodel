"""
Visualize Knowledge Graphs

Creates visualizations of knowledge graphs extracted by REBEL
"""

import json
import argparse
from pathlib import Path
from collections import Counter

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend


def load_knowledge_graph(kg_file: Path) -> dict:
    """Load knowledge graph from JSON file"""
    with open(kg_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_graph_from_triplets(triplets: list) -> nx.DiGraph:
    """
    Create NetworkX directed graph from triplets

    Args:
        triplets: List of dicts with 'head', 'relation', 'tail' keys

    Returns:
        NetworkX DiGraph
    """
    G = nx.DiGraph()

    for triplet in triplets:
        head = triplet['head']
        relation = triplet['relation']
        tail = triplet['tail']

        G.add_edge(head, tail, relation=relation)

    return G


def visualize_graph(G: nx.DiGraph, output_file: Path, title: str = "Knowledge Graph"):
    """
    Visualize knowledge graph and save to file

    Args:
        G: NetworkX graph
        output_file: Path to save visualization
        title: Graph title
    """
    plt.figure(figsize=(20, 16))

    # Use spring layout for better visualization
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos,
        node_color='lightblue',
        node_size=3000,
        alpha=0.9
    )

    # Draw edges
    nx.draw_networkx_edges(
        G, pos,
        edge_color='gray',
        arrows=True,
        arrowsize=20,
        arrowstyle='->',
        width=1.5,
        alpha=0.6
    )

    # Draw labels
    nx.draw_networkx_labels(
        G, pos,
        font_size=8,
        font_weight='bold'
    )

    # Draw edge labels (relations)
    edge_labels = nx.get_edge_attributes(G, 'relation')
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=edge_labels,
        font_size=6,
        font_color='red'
    )

    plt.title(title, fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved visualization: {output_file}")


def generate_statistics(kg_data: dict, output_file: Path):
    """
    Generate and save statistics about the knowledge graph

    Args:
        kg_data: Knowledge graph data
        output_file: Path to save statistics
    """
    triplets = kg_data['triplets']

    # Entity counts
    heads = [t['head'] for t in triplets]
    tails = [t['tail'] for t in triplets]
    all_entities = heads + tails
    entity_counts = Counter(all_entities)

    # Relation counts
    relations = [t['relation'] for t in triplets]
    relation_counts = Counter(relations)

    # Create statistics report
    stats_text = f"""KNOWLEDGE GRAPH STATISTICS
{'=' * 80}

Project: {kg_data['project_name']}
Timestamp: {kg_data['timestamp']}

OVERVIEW
--------
PDFs Processed:          {kg_data['num_pdfs']}
Text Segments:           {kg_data['num_text_segments']}
Total Triplets:          {kg_data['num_total_triplets']}
Unique Triplets:         {kg_data['num_unique_triplets']}
Unique Entities:         {len(entity_counts)}
Unique Relations:        {len(relation_counts)}

TOP 10 MOST FREQUENT ENTITIES
------------------------------
"""
    for entity, count in entity_counts.most_common(10):
        stats_text += f"{entity:50s} : {count:3d} occurrences\n"

    stats_text += f"\nTOP 10 MOST FREQUENT RELATIONS\n"
    stats_text += "-" * 80 + "\n"
    for relation, count in relation_counts.most_common(10):
        stats_text += f"{relation:50s} : {count:3d} occurrences\n"

    stats_text += f"\nSAMPLE TRIPLETS\n"
    stats_text += "-" * 80 + "\n"
    for triplet in triplets[:20]:
        stats_text += f"{triplet['head']} --[{triplet['relation']}]--> {triplet['tail']}\n"

    # Save statistics
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(stats_text)

    print(f"  ✓ Saved statistics: {output_file}")

    return entity_counts, relation_counts


def create_subgraph_visualizations(
    G: nx.DiGraph,
    kg_data: dict,
    output_dir: Path,
    top_n: int = 5
):
    """
    Create visualizations for subgraphs around top entities

    Args:
        G: Full knowledge graph
        kg_data: Knowledge graph data
        output_dir: Directory to save visualizations
        top_n: Number of top entities to visualize
    """
    # Get entity frequencies
    triplets = kg_data['triplets']
    heads = [t['head'] for t in triplets]
    tails = [t['tail'] for t in triplets]
    all_entities = heads + tails
    entity_counts = Counter(all_entities)

    # Create subgraph for each top entity
    for i, (entity, count) in enumerate(entity_counts.most_common(top_n), 1):
        # Get neighbors
        neighbors = set()
        neighbors.add(entity)

        # Add 1-hop neighbors
        if entity in G:
            neighbors.update(G.successors(entity))
            neighbors.update(G.predecessors(entity))

        # Create subgraph
        subG = G.subgraph(neighbors)

        if len(subG.nodes()) > 1:  # Only visualize if there are connections
            # Sanitize filename - replace invalid characters
            safe_name = entity.replace(' ', '_').replace('/', '_').replace('\\', '_').replace(':', '_')[:30]
            output_file = output_dir / f"subgraph_{i:02d}_{safe_name}.png"
            visualize_graph(
                subG,
                output_file,
                title=f"Subgraph around '{entity}' ({count} connections)"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Visualize knowledge graphs"
    )
    parser.add_argument(
        '--project',
        type=str,
        help='Project name to visualize (e.g., alpha_erp_system)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Visualize all knowledge graphs'
    )
    parser.add_argument(
        '--datasets-dir',
        type=str,
        default='./datasets',
        help='Path to datasets directory (default: ./datasets)'
    )
    parser.add_argument(
        '--subgraphs',
        action='store_true',
        help='Generate subgraph visualizations for top entities'
    )

    args = parser.parse_args()

    # Setup paths
    datasets_dir = Path(args.datasets_dir)
    kg_dir = datasets_dir / 'knowledge_graphs'

    if not kg_dir.exists():
        print(f"❌ Knowledge graphs directory not found: {kg_dir}")
        print("   Run build_knowledge_graph_rebel.py first")
        return

    print("\n" + "=" * 80)
    print("KNOWLEDGE GRAPH VISUALIZER")
    print("=" * 80)

    # Find knowledge graph files
    if args.all:
        kg_files = list(kg_dir.glob("*_knowledge_graph.json"))
        print(f"\n📊 Visualizing {len(kg_files)} knowledge graphs...")
    elif args.project:
        kg_file = kg_dir / f"{args.project}_knowledge_graph.json"
        if not kg_file.exists():
            print(f"❌ Knowledge graph not found: {kg_file}")
            return
        kg_files = [kg_file]
        print(f"\n📊 Visualizing knowledge graph: {args.project}")
    else:
        print("❌ Please specify --project PROJECT_NAME or --all")
        parser.print_help()
        return

    # Process each knowledge graph
    for kg_file in kg_files:
        print(f"\n{'─' * 80}")
        print(f"Processing: {kg_file.stem}")
        print(f"{'─' * 80}")

        # Load knowledge graph
        kg_data = load_knowledge_graph(kg_file)
        project_name = kg_data['project_name']

        # Create output directory
        vis_dir = kg_dir / f"{project_name}_visualizations"
        vis_dir.mkdir(exist_ok=True)

        # Create graph
        G = create_graph_from_triplets(kg_data['triplets'])

        print(f"\n  Graph Statistics:")
        print(f"    Nodes (entities):    {G.number_of_nodes()}")
        print(f"    Edges (relations):   {G.number_of_edges()}")

        # Generate statistics
        stats_file = vis_dir / f"{project_name}_statistics.txt"
        entity_counts, relation_counts = generate_statistics(kg_data, stats_file)

        # Visualize full graph
        if G.number_of_nodes() < 100:  # Only visualize if not too large
            output_file = vis_dir / f"{project_name}_full_graph.png"
            visualize_graph(G, output_file, title=f"Knowledge Graph: {project_name}")
        else:
            print(f"  ⚠️  Graph too large ({G.number_of_nodes()} nodes), skipping full visualization")

        # Generate subgraph visualizations
        if args.subgraphs:
            print(f"\n  Generating subgraph visualizations...")
            subgraph_dir = vis_dir / "subgraphs"
            subgraph_dir.mkdir(exist_ok=True)
            create_subgraph_visualizations(G, kg_data, subgraph_dir, top_n=5)

        print(f"\n  ✓ All visualizations saved to: {vis_dir}")

    print(f"\n" + "=" * 80)
    print("✓ Visualization complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
