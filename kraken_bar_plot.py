# kraken_bar_plot.py

import pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc

def plot_stacked_bar_kraken(df, top_n=10):
    if not {'rank', 'direct_reads', 'name'}.issubset(df.columns):
        return go.Figure().update_layout(title="Error: Required columns missing")

    df["name"] = df["name"].str.strip()

    genus_df = df[df["rank"] == "G"].groupby("name", as_index=False)["direct_reads"].sum()
    species_df = df[df["rank"] == "S"].groupby("name", as_index=False)["direct_reads"].sum()

    if genus_df.empty and species_df.empty:
        return go.Figure().update_layout(title="No Genus/Species-Level Data Available")

    genus_df = genus_df.sort_values("direct_reads", ascending=False).head(top_n)
    species_df = species_df.sort_values("direct_reads", ascending=False).head(top_n)

    genus_total = genus_df["direct_reads"].sum()
    species_total = species_df["direct_reads"].sum()

    genus_df["proportion"] = genus_df["direct_reads"] / genus_total if genus_total > 0 else 0
    species_df["proportion"] = species_df["direct_reads"] / species_total if species_total > 0 else 0

    # Colors
    color_palette = pc.qualitative.Bold
    all_names = pd.concat([genus_df["name"], species_df["name"]]).unique()
    color_map = {name: color_palette[i % len(color_palette)] for i, name in enumerate(all_names)}

    fig = go.Figure()

    for _, row in genus_df.iterrows():
        fig.add_trace(go.Bar(
            x=["Genus"],
            y=[row["proportion"]],
            name=f"G: {row['name']}",
            hovertemplate=f"{row['name']}<br>Proportion: {row['proportion']:.2%}",
            marker=dict(color=color_map[row["name"]])
        ))

    for _, row in species_df.iterrows():
        fig.add_trace(go.Bar(
            x=["Species"],
            y=[row["proportion"]],
            name=f"S: {row['name']}",
            hovertemplate=f"{row['name']}<br>Proportion: {row['proportion']:.2%}",
            marker=dict(color=color_map[row["name"]])
        ))

    fig.update_layout(
        title="Top Taxa - Stacked Bar Chart of Kraken2 Reads",
        xaxis_title="Taxonomic Rank",
        yaxis_title="Proportion of Reads",
        barmode="stack",
        font=dict(size=12, color="white"),
        plot_bgcolor="#2c2f34",
        paper_bgcolor="#1e1e1e",
        legend=dict(title="Taxa", font=dict(size=10)),
        margin=dict(t=60, b=60)
    )

    return fig
