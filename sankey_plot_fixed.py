import pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc

def build_sankey_from_kraken(df):
    """
    Generates a Sankey diagram from a Kraken2 TSV DataFrame.
    :param df: Pandas DataFrame containing the Kraken2 classification.
    :return: Plotly figure object
    """

    # Ensure correct filtering: Select only Bacteria-related entries
    filtered_data = df[df['name'].str.contains('Bacteria', na=False, case=False)].copy()
    
    # Extract hierarchical relationships based on taxonomy rank
    filtered_data['name_clean'] = filtered_data['name'].str.strip()
    
    # Build node and link mappings
    node_indices = {}
    nodes = []
    sources, targets, values = [], [], []
    
    # Define a structured taxonomic hierarchy
    taxonomic_ranks = ['D', 'K', 'P', 'C', 'O', 'F', 'G', 'S']  # Domain to Species
    filtered_data['rank_level'] = filtered_data['rank'].apply(lambda x: taxonomic_ranks.index(x) if x in taxonomic_ranks else len(taxonomic_ranks))
    
    # Sort by rank level to maintain order
    filtered_data = filtered_data.sort_values(by='rank_level')
    
    for _, row in filtered_data.iterrows():
        node_name = row['name_clean']
        parent_rank = row['rank']
        reads = row['reads_clade']
        
        if node_name not in node_indices:
            node_indices[node_name] = len(nodes)
            nodes.append(node_name)
        
        # Find a valid parent from previous ranks
        parent_candidates = filtered_data[(filtered_data['rank_level'] < row['rank_level']) & (filtered_data['rank_level'] >= 0)]
        if not parent_candidates.empty:
            parent_name = parent_candidates.iloc[-1]['name_clean']
            if parent_name in node_indices:
                sources.append(node_indices[parent_name])
                targets.append(node_indices[node_name])
                values.append(reads)
    
    # Ensure there are valid links before generating the Sankey diagram
    if not sources or not targets or not values:
        print("Error: No valid links were created. Check input data structure.")
        return go.Figure().update_layout(title="No Data Available for Sankey Plot")
    
    # Define color scheme with gradient flow
    color_palette = pc.qualitative.Set2  # More distinct colors
    node_colors = [color_palette[i % len(color_palette)] for i in range(len(nodes))]
    
    # Build Sankey diagram with improved hierarchical structuring
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',  # Better hierarchical flow
        node=dict(
            pad=50,  # Increase spacing
            thickness=25,  # Adjust thickness for better clarity
            line=dict(color='black', width=1.2),
            label=nodes,
            color=node_colors,
            hoverinfo='all'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color='rgba(100,100,100,0.4)',  # Adjusted transparency for readability
            hoverinfo='none'  # Clean UI by removing hover on links
        )
    )])
    
    fig.update_layout(
        title_text='Kraken2 Bacteria Taxonomic Classification Sankey Diagram',
        font_size=14,
        height=600,
        width=900,
        margin=dict(l=120, r=120, t=80, b=80),
        hovermode='x unified'  # Improve interactivity
    )
    
    return fig
