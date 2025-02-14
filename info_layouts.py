from dash import html
import dash_bootstrap_components as dbc

# About Section
def get_about_section():
    return dbc.Container(
        [
            html.H3("About This Dashboard", className="text-primary"),
            html.P("""
                This dashboard is designed for analyzing taxonomic data. It supports Kraken2 TSV outputs and Excel files,
                allowing users to visualize Sankey plots and bar plots for assembly depth.
            """),
            html.P("""
                By uploading a dataset, users can explore taxonomic classifications, assess sequencing depth,
                and gain insights into their biological data in a user-friendly interface.
            """),
            html.H4("Features:", className="text-secondary"),
            html.Ul([
                html.Li("🔹 Upload TSV or Excel files"),
                html.Li("🔹 Visualize taxonomic classifications using Sankey diagrams"),
                html.Li("🔹 Generate stacked bar plots for coverage depth"),
                html.Li("🔹 Select individual sheets and samples for analysis"),
            ]),
            html.P("This tool is developed to assist bioinformaticians in taxonomic and assembly depth analysis."),
        ],
        style={'padding': '20px'}
    )

# How to Use Section
def get_how_to_use_section():
    return dbc.Container(
        [
            html.H3("How to Use", className="text-primary"),
            html.P("""
                Follow these steps to analyze your data with the dashboard:
            """),
            html.Ol([
                html.Li("Click on 'Upload' to select a Kraken2 TSV or Excel file."),
                html.Li("Choose the correct sheet from the dropdown."),
                html.Li("Use the available controls to filter and analyze the data."),
                html.Li("View taxonomic classification in a Sankey diagram."),
                html.Li("Check assembly depth using the bar plot."),
            ]),
            html.H4("📌 Tips:", className="text-secondary"),
            html.Ul([
                html.Li("Ensure your file format matches the expected input."),
                html.Li("If using Kraken2 data, confirm that it includes taxonomic rank information."),
                html.Li("For large datasets, expect a short processing time."),
            ]),
            html.P("By following these steps, you can easily explore your dataset."),
        ],
        style={'padding': '20px'}
    )
