import pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc
import plotly.express as px
from dash import dash_table
from dash import html

def build_sankey_from_kraken(df, min_reads=1, rank_filter=None, 
taxonomic_ranks=['G','S']):
# taxonomic_ranks=['D', 'K', 'P', 'C', 'O', 'F', 'G', 'S']):
    """
    Generates a Sankey diagram from a Kraken2 TSV DataFrame with improved hierarchy and filtering.
    
    :param df: Pandas DataFrame containing the Kraken2 classification.
    :param min_reads: Minimum read count threshold to include taxa.
    :param rank_filter: Specific rank to filter by (e.g., 'P' for phylum, 'G' for genus, etc.).
    :param taxonomic_ranks: List defining the order of taxonomic levels.
    :return: Plotly figure object and Dash DataTable component
    """
    # Compute total reads for percentage calculation
    total_reads = df['reads_clade'].sum()
    
    # Filter data
    df = df[df['reads_clade'] >= min_reads].copy()
    if rank_filter:
        df = df[df['rank'] == rank_filter]

    # Clean taxon names
    df['name_clean'] = df['name'].str.strip()
    
    # Assign taxonomic rank levels
    df['rank_level'] = df['rank'].apply(lambda x: taxonomic_ranks.index(x) if x in taxonomic_ranks else len(taxonomic_ranks))
    df = df.sort_values(by=['rank_level', 'reads_clade'], ascending=[True, False])

    # Build Sankey nodes and links
    node_indices = {}
    nodes = []
    sources, targets, values = [], [], []

    for _, row in df.iterrows():
        node_name = row['name_clean']
        reads_percentage = (row['reads_clade'] / total_reads) * 100  # Convert reads to percentage

        if node_name not in node_indices:
            node_indices[node_name] = len(nodes)
            nodes.append(node_name)

        # Find closest parent in previous ranks
        parent_candidates = df[(df['rank_level'] < row['rank_level'])]
        if not parent_candidates.empty:
            parent_name = parent_candidates.iloc[-1]['name_clean']
            if parent_name in node_indices:
                sources.append(node_indices[parent_name])
                targets.append(node_indices[node_name])
                values.append(reads_percentage)  # Use percentage instead of raw count

    # Handle empty plots
    if not sources or not targets or not values:
        return go.Figure().update_layout(title="No Data Available for Sankey Plot"), html.Div("No Data Available")

    # Define dynamic color scheme
    color_palette = px.colors.qualitative.Vivid
    node_colors = [color_palette[i % len(color_palette)] for i in range(len(nodes))]

    # Generate Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',  # Maintain structured flow
        node=dict(
            pad=20,  
            thickness=15,  
            line=dict(color='black', width=1),
            label=nodes,
            color=node_colors,
            hoverinfo='all'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color='rgba(100,100,100,0.5)',  # Better link visibility
            hoverinfo='all'
        )
    )])

    # Improve layout
    num_nodes = len(nodes)
    height = min(800, max(400, num_nodes * 20))  # Keep between 400-800px
    width = min(900, max(500, num_nodes * 30))  # Keep between 600-1000px

    fig.update_layout(
        title_text='Kraken2 Taxonomic Classification Sankey Diagram (Percentage)',
        font_size=12,
        height=height,
        width=width,
        margin=dict(l=50, r=50, t=50, b=50),
        hovermode='x unified'
    )

    # Add color-coded bar plots in the percentage column
    df['percentage_bar'] = df['reads_clade'] / total_reads * 100
    df['percentage'] = df['percentage_bar'].apply(lambda x: f'{x:.2f}%')
    
    table = dash_table.DataTable(
        columns=[
            {'name': 'Percentage', 'id': 'percentage', 'type': 'text', 'presentation': 'markdown'},
            {'name': 'CladeReads', 'id': 'reads_clade', 'type': 'numeric'},
            {'name': 'TaxonReads', 'id': 'reads_taxon', 'type': 'numeric'},
            {'name': 'TaxRank', 'id': 'rank', 'type': 'text'},
            {'name': 'TaxID', 'id': 'NCBI_tax_ID', 'type': 'numeric'},
            {'name': 'Name', 'id': 'name_clean', 'type': 'text'},
            {'name': 'TaxLineage', 'id': 'tax_lineage', 'type': 'text'}
        ],
        data=df.to_dict('records'),
        style_data_conditional=[
            {
                'if': {'column_id': 'percentage'},
                'background': 'linear-gradient(to right, #1f77b4 0%, #1f77b4 {}%, white {}%)'.format(row['percentage_bar'], row['percentage_bar'] + 1),
                'color': 'black'
            } for _, row in df.iterrows()
        ],
        style_table={'overflowX': 'auto', 'backgroundColor': 'white'},
        style_cell={'textAlign': 'left', 'color': 'black', 'backgroundColor': 'white'},
        page_size=10
    )

    return fig, table
