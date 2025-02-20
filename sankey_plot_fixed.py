import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import dash_table, html
import numpy as np

def build_sankey_from_kraken(df, min_reads=1, rank_filter=None, taxonomic_ranks=['S']):
    print("\n=== DEBUG: Entering build_sankey_from_kraken ===")  # Debugging log
    print(f"DEBUG: Kraken TSV DataFrame Shape: {df.shape}")
    print(f"DEBUG: DataFrame Columns Before Processing: {df.columns}")  # Debugging

    try:
        # Rename columns if needed
        column_mapping = {
            "direct_reads": "reads_taxon"  # Rename to expected column name
        }
        df = df.rename(columns=column_mapping)

        # Check required columns
        required_columns = {"rank", "reads_taxon", "name", "reads_clade"}
        if not required_columns.issubset(df.columns):
            print(f"ERROR: Missing required columns. Found: {df.columns}")
            return (
                go.Figure().update_layout(title="Error: Missing Required Columns"),
                html.Div("Error: Missing Required Columns")
            )

        total_reads = df["reads_clade"].sum()

        # Filter data based on min_reads
        df = df[df["reads_clade"] >= min_reads].copy()
        if rank_filter:
            df = df[df["rank"] == rank_filter]

        df["name_clean"] = df["name"].str.strip()
        df["rank_level"] = df["rank"].apply(lambda x: taxonomic_ranks.index(x) if x in taxonomic_ranks else len(taxonomic_ranks))
        df = df.sort_values(by=["rank_level", "reads_clade"], ascending=[True, False])

        node_indices = {}
        nodes = []
        sources, targets, values = [], [], []

        for _, row in df.iterrows():
            node_name = row["name_clean"]

            if node_name not in node_indices:
                node_indices[node_name] = len(nodes)
                nodes.append(node_name)

            parent_candidates = df[df["rank_level"] < row["rank_level"]]
            if not parent_candidates.empty:
                parent_name = parent_candidates.iloc[-1]["name_clean"]
                if parent_name in node_indices:
                    sources.append(node_indices[parent_name])
                    targets.append(node_indices[node_name])
                    values.append(np.log10(row["reads_clade"] + 1) * 3)  # Log-scaled for better visualization

        if not sources or not targets or not values:
            print("DEBUG: No valid Sankey links generated.")
            return (
                go.Figure().update_layout(title="No Data Available for Sankey Plot"),
                html.Div("No Data Available")
            )

        color_palette = px.colors.qualitative.Pastel1  # Soft colors for better grouping
        node_colors = [color_palette[i % len(color_palette)] for i in range(len(nodes))]

        fig = go.Figure(data=[go.Sankey(
            arrangement='perpendicular',  # Structured hierarchical layout
            node=dict(
                pad=20,
                thickness=10,
                line=dict(color='black', width=1),
                label=nodes,
                color=node_colors,
                hoverinfo='all'
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color='rgba(180,180,180,0.5)',  # Soft gray for links
                hoverinfo='all'
            )
        )])

        num_nodes = len(nodes)
        fig.update_layout(
            title_text='Kraken2 Genus-Level Sankey Diagram (Refined & Log-Scaled)',
            font_size=12,
            height=min(1000, max(600, num_nodes * 30)),
            width=min(1200, max(800, num_nodes * 40)),
            margin=dict(l=80, r=80, t=80, b=80),
            hovermode='x unified'
        )

        df["percentage_bar"] = df["reads_clade"] / total_reads * 100
        df["percentage"] = df["percentage_bar"].apply(lambda x: f"{x:.2f}%")

        table = dash_table.DataTable(
            columns=[
                {"name": "Percentage", "id": "percentage", "type": "text"},
                {"name": "CladeReads", "id": "reads_clade", "type": "numeric"},
                {"name": "TaxonReads", "id": "reads_taxon", "type": "numeric"},
                {"name": "TaxRank", "id": "rank", "type": "text"},
                {"name": "TaxID", "id": "NCBI_tax_ID", "type": "numeric"},
                {"name": "Name", "id": "name_clean", "type": "text"}
            ],
            data=df.to_dict("records"),
            style_data={"color": "black", "backgroundColor": "white"},
            style_header={"color": "black", "backgroundColor": "white", "fontWeight": "bold"},
            style_table={"overflowX": "auto"},
            page_size=10
        )

        print("DEBUG: Sankey Plot and Table Successfully Created")  # Debugging log
        return fig, table

    except Exception as e:
        print(f"ERROR: Sankey plot generation failed - {e}")

        # Ensure two values are always returned
        return (
            go.Figure().update_layout(title=f"Error: {e}"),
            html.Div(f"Error generating table: {e}")
        )
