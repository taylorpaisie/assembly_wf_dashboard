from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd

# Initialize Dash app with external stylesheets
app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
server = app.server  # Expose server for Gunicorn

# Load the Excel file (ensure this path is valid inside the Docker container)
file_path = "/app/Summary-Report.xlsx"
try:
    sheets = pd.ExcelFile(file_path).sheet_names
except FileNotFoundError:
    sheets = []

# Define the layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Assembly Workflow Dashboard",
                        className="text-center text-primary my-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Select Data"),
                dbc.CardBody([
                    html.Label("Select a Sheet:"),
                    dcc.Dropdown(
                        id='sheet-dropdown',
                        options=[{'label': sheet, 'value': sheet} for sheet in sheets],
                        placeholder="Select a sheet"
                    )
                ])
            ])
        ])
    ])
])

if __name__ == "__main__":
    app.run_server(debug=True)
