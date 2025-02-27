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

    # Filter for Species (S) and Genus (G)
    genus_df = df[df["rank"] == "G"]
    species_df = df[df["rank"] == "S"]
    
    print(f"DEBUG: Genus count: {len(genus_df)}, Species count: {len(species_df)}")

    # If no valid data, return an empty plot with a message
    if genus_df.empty and species_df.empty:
        print("WARNING: No valid genus-level or species-level data for Kraken bar plot.")
        return go.Figure().update_layout(title="No Genus/Species-Level Data Available")

    # Aggregate by name
    genus_df = genus_df.groupby("name", as_index=False)["direct_reads"].sum()
    species_df = species_df.groupby("name", as_index=False)["direct_reads"].sum()

    # Calculate proportions separately for Genus and Species
    total_genus_reads = genus_df["direct_reads"].sum()
    total_species_reads = species_df["direct_reads"].sum()

    genus_df["proportion"] = genus_df["direct_reads"] / total_genus_reads if total_genus_reads > 0 else 0
    species_df["proportion"] = species_df["direct_reads"] / total_species_reads if total_species_reads > 0 else 0

    # Create stacked bar chart using Plotly
    fig = go.Figure()

    # Add genus traces
    for i, row in genus_df.iterrows():
        fig.add_trace(go.Bar(
            x=["Genus"],
            y=[row["proportion"]],
            name=row["name"],
            text=row["name"],
            textposition="inside",
            marker=dict(color=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"][i % 5])
        ))

    # Add species traces
    for i, row in species_df.iterrows():
        fig.add_trace(go.Bar(
            x=["Species"],
            y=[row["proportion"]],
            name=row["name"],
            text=row["name"],
            textposition="inside",
            marker=dict(color=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"][i % 5])
        ))

    # Formatting
    fig.update_layout(
        title="Stacked Bar Chart of Reads by Genus and Species",
        xaxis_title="Taxonomic Rank",
        yaxis_title="Proportion of Reads",
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        showlegend=True 
    )

    return fig
