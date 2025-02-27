import pandas as pd
import plotly.graph_objects as go

def plot_stacked_bar_kraken(df):
    print(f"DEBUG: Initial dataframe rows: {len(df)}")

    # Ensure the dataframe has necessary columns
    if not {'rank', 'direct_reads', 'name'}.issubset(df.columns):
        print("ERROR: Required columns missing from dataframe")
        return go.Figure().update_layout(title="Error: Required columns missing")

    # Strip leading spaces in taxon names
    df["name"] = df["name"].str.strip()

    # Filter for Species (S), Genus (G), and Unclassified Genus (G1)
    phylum_df = df[df["rank"].isin(["S", "G", "G1"])]
    print(f"DEBUG: Rows after filtering for Species (S), Genus (G), and Genus Unclassified (G1): {len(phylum_df)}")

    # If no valid data, return an empty plot with a message
    if phylum_df.empty:
        print("WARNING: No valid species-level or genus-level data for Kraken bar plot.")
        return go.Figure().update_layout(title="No Species/Genus-Level Data Available")

    # Select relevant columns and allow species with zero reads
    phylum_df = phylum_df[["name", "direct_reads"]]
    phylum_df["direct_reads"] = pd.to_numeric(phylum_df["direct_reads"], errors="coerce").fillna(0).astype(int)

    print(f"DEBUG: Including species with zero reads. Rows available: {len(phylum_df)}")

    # Calculate total reads for normalization
    total_reads = phylum_df["direct_reads"].sum()
    if total_reads == 0:
        print("ERROR: No valid reads available for plotting")
        return go.Figure().update_layout(title="Error: No Valid Reads Available")

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
        title="Stacked Bar Chart of Reads by Species/Genus",
        xaxis_title="",
        yaxis_title="Proportion of Reads",
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        showlegend=True 
    )

    return fig
