import pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc
import plotly.express as px

def build_sankey_from_kraken(df, min_reads=1, rank_filter=None):
    """
    Generates a Sankey diagram from a Kraken2 TSV DataFrame with improved hierarchy and filtering.
    :param df: Pandas DataFrame containing the Kraken2 classification.
    :param min_reads: Minimum read count threshold to include taxa.
    :param rank_filter: Specific rank to filter by (e.g., 'P' for phylum, 'G' for genus, etc.).
    :return: Plotly figure object
    """
    # Filter out low-abundance taxa
    df = df[df['reads_clade'] >= min_reads].copy()
    
    # If rank filter is provided, apply it
    if rank_filter:
        df = df[df['rank'] == rank_filter]
    
    # Extract hierarchical relationships based on taxonomy rank
    df['name_clean'] = df['name'].str.strip()
    
    # Build node and link mappings
    node_indices = {}
    nodes = []
    sources, targets, values = [], [], []
    
    # Define a structured taxonomic hierarchy
    # taxonomic_ranks = ['D', 'K', 'P', 'C', 'O', 'F', 'G', 'S']
    taxonomic_ranks = ['G', 'S']
    df['rank_level'] = df['rank'].apply(lambda x: taxonomic_ranks.index(x) if x in taxonomic_ranks else len(taxonomic_ranks))
    
    # Sort by rank level to maintain order
    df = df.sort_values(by=['rank_level', 'reads_clade'], ascending=[True, False])
    
    for _, row in df.iterrows():
        node_name = row['name_clean']
        reads = row['reads_clade']
        
        if node_name not in node_indices:
            node_indices[node_name] = len(nodes)
            nodes.append(node_name)
        
        # Find a valid parent from previous ranks
        parent_candidates = df[(df['rank_level'] < row['rank_level'])]
        if not parent_candidates.empty:
            parent_name = parent_candidates.iloc[-1]['name_clean']
            if parent_name in node_indices:
                sources.append(node_indices[parent_name])
                targets.append(node_indices[node_name])
                values.append(reads)
    
    # Ensure there are valid links before generating the Sankey diagram
    if not sources or not targets or not values:
        return go.Figure().update_layout(title="No Data Available for Sankey Plot")
    
    # Define color scheme dynamically
    color_palette = px.colors.qualitative.Set3
    node_colors = [color_palette[i % len(color_palette)] for i in range(len(nodes))]
    
    # Build Sankey diagram with improved hierarchical structuring
    fig = go.Figure(data=[go.Sankey(
        arrangement='perpendicular',  # Cleaner hierarchical flow
        node=dict(
            pad=30,  # Adjusted spacing for clarity
            thickness=20,  # Slimmer nodes for better visualization
            line=dict(color='black', width=1.0),
            label=nodes,
            color=node_colors,
            hoverinfo='all'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color='rgba(150,150,150,0.3)',  # Softer link colors for better readability
            hoverinfo='none'  # Clean UI by removing hover on links
        )
    )])
    
    fig.update_layout(
        title_text='Kraken2 Taxonomic Classification Sankey Diagram',
        font_size=12,
        height=600,
        width=1000,
        margin=dict(l=80, r=80, t=50, b=50),
        hovermode='x unified'
    )
    
    return fig
