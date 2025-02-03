import pandas as pd
import plotly.graph_objects as go

def plot_stacked_bar_kraken(df):
    # Ensure the dataframe has necessary columns
    if not {'rank', 'direct_reads', 'name'}.issubset(df.columns):
        print("ERROR: Required columns missing from dataframe")
        return go.Figure().update_layout(title="Error: Required columns missing")

    # Strip leading spaces in taxon names
    df["name"] = df["name"].str.strip()

    # Filter for Phylum level (rank = "P")
    phylum_df = df[df["rank"] == "P"]

    # Select relevant columns and convert read counts to integers
    phylum_df = phylum_df[["name", "direct_reads"]]
    phylum_df["direct_reads"] = phylum_df["direct_reads"].astype(int)

    # Calculate total reads for normalization
    total_reads = phylum_df["direct_reads"].sum()
    phylum_df["proportion"] = phylum_df["direct_reads"] / total_reads

    # Create stacked bar chart using Plotly
    fig = go.Figure()

    for i, row in phylum_df.iterrows():
        fig.add_trace(go.Bar(
            x=["Reads"],
            y=[row["proportion"]],
            name=row["name"],
            text=row["name"],
            textposition="inside",
            marker=dict(color=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"][i % 5])
        ))

    # Formatting
    fig.update_layout(
        title="Stacked Bar Chart of Reads by Phylum",
        xaxis_title="",
        yaxis_title="Proportion of Reads",
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        showlegend=True  # Enable legend
    )

    return fig
