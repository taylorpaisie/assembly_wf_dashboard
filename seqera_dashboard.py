from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import os

# Initialize Dash app with external stylesheets
app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
server = app.server  # Expose server for Gunicorn

# Load the Excel file (ensure this path is valid inside the Docker container)
file_path = "/app/Summary-Report.xlsx"
try:
    if os.path.exists(file_path):
        sheets = pd.ExcelFile(file_path).sheet_names
        print(f"Loaded sheets: {sheets}")
    else:
        sheets = []
        print(f"File not found at {file_path}")
except Exception as e:
    sheets = []
    print(f"Error loading Excel file: {e}")

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
                        options=[{'label': name, 'value': name} for name in sheets],
                        value=sheets[0] if sheets else None,  # Avoid IndexError
                    ),
                    html.Label("Select X-Axis:"),
                    dcc.Dropdown(id='x-axis-dropdown', className="mt-2"),
                ])
            ])
        ])
    ])
])

# Define callbacks for interactivity
@app.callback(
    Output('x-axis-dropdown', 'options'),
    [Input('sheet-dropdown', 'value')]
)
def update_x_axis_options(sheet_name):
    if sheet_name:
        try:
            # Load the selected sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"Loaded sheet: {sheet_name} with columns: {df.columns.tolist()}")
            return [{'label': col, 'value': col} for col in df.columns]
        except Exception as e:
            print(f"Error loading sheet {sheet_name}: {e}")
            return []
    return []

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
