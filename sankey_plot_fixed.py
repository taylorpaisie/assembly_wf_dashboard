import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import dash_table, html
import numpy as np

def build_sankey_from_kraken(df, min_reads=1, rank_filter=None, taxonomic_ranks=['G']):
    try:
        column_mapping = {
            "direct_reads": "reads_taxon"
        }
        df = df.rename(columns=column_mapping)

        required_columns = {"rank", "reads_taxon", "name", "reads_clade"}
        if not required_columns.issubset(df.columns):
            return (
                go.Figure().update_layout(title="Error: Missing Required Columns"),
                html.Div("Error: Missing Required Columns")
            )

        total_reads = df["reads_clade"].sum()
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
                    values.append(row["reads_clade"])  # Use actual reads count instead of log scaling

        color_palette = px.colors.qualitative.Plotly
        node_colors = [color_palette[i % len(color_palette)] for i in range(len(nodes))]
        # link_colors = [node_colors[sources[i]] for i in range(len(sources))]
        link_colors = ['rgba(180,180,180,0.5)' for _ in sources]  # Match parent node colors

        fig = go.Figure(data=[go.Sankey(
            arrangement='snap',  # Clearer hierarchical layout
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
                color=link_colors,
                hovertemplate='%{source.label} → %{target.label}: %{value} reads'
            )
        )])

        fig.update_layout(
            title_text='Enhanced Kraken2 Genus-Level Sankey Diagram',
            font_size=10,
            height=min(900, max(600, len(nodes) * 40)),
            width=min(1300, max(800, len(nodes) * 50)),
            margin=dict(l=80, r=80, t=80, b=80),
            hovermode='x unified'
        )

        df["percentage"] = (df["reads_clade"] / total_reads * 100).map("{:.2f}%".format)

        table = dash_table.DataTable(
            columns=[
                {"name": "Percentage", "id": "percentage"},
                {"name": "CladeReads", "id": "reads_clade"},
                {"name": "TaxonReads", "id": "reads_taxon"},
                {"name": "TaxRank", "id": "rank"},
                {"name": "TaxID", "id": "NCBI_tax_ID"},
                {"name": "Name", "id": "name_clean"}
            ],
            data=df.to_dict("records"),
            style_data={"color": "black", "backgroundColor": "white"},
            style_header={"color": "black", "backgroundColor": "white", "fontWeight": "bold"},
            style_table={"overflowX": "auto"},
            page_size=10
        )

        return fig, table

    except Exception as e:
        return (
            go.Figure().update_layout(title=f"Error: {e}"),
            html.Div(f"Error generating table: {e}")
        )
