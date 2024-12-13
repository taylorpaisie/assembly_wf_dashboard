from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import sys, os

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
                        options=[{'label': name, 'value': name} for name in sheets],
                        value=sheets[0]
                    ),
                    html.Label("Select X-Axis:"),
                    dcc.Dropdown(id='x-axis-dropdown', className="mt-2"),
                    html.Label("Select Y-Axis:"),
                    dcc.Dropdown(id='y-axis-dropdown', className="mt-2")
                ])
            ], className="mb-4")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Graph"),
                dbc.CardBody(dcc.Graph(id='sheet-graph'))
            ], className="mb-4")
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Data Preview"),
                dbc.CardBody(id='sheet-display', 
                className="overflow-auto", style={"maxHeight": "400px"})
            ])
        ])
    ])
], fluid=True)
# Callbacks for dropdowns
@app.callback(
    [Output('x-axis-dropdown', 'options'),
     Output('y-axis-dropdown', 'options'),
     Output('x-axis-dropdown', 'value'),
     Output('y-axis-dropdown', 'value')],
    Input('sheet-dropdown', 'value')
)
def update_dropdowns(sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    if df.empty:
        return [], [], None, None
    options = [{'label': col, 'value': col} for col in df.columns]
    x_default = df.select_dtypes(include=['object', 'string']).columns[0] if not df.select_dtypes(include=['object', 'string']).empty else df.columns[0]
    y_default = df.select_dtypes(include=['number']).columns[0] if not df.select_dtypes(include=['number']).empty else df.columns[0]
    return options, options, x_default, y_default
# Callbacks for graph and data table
@app.callback(
    [Output('sheet-graph', 'figure'),
     Output('sheet-display', 'children')],
    [Input('sheet-dropdown', 'value'),
     Input('x-axis-dropdown', 'value'),
     Input('y-axis-dropdown', 'value')]
)
def update_graph_and_table(sheet_name, x_column, y_column):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    if x_column and y_column:
        fig = px.bar(df, x=x_column, y=y_column, color=x_column)
        fig.update_layout(
            title=f"{y_column} vs {x_column}",
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="#ffffff",
            plot_bgcolor="#f9f9f9",
            font_color="#333333"
        )
    else:
        fig = px.scatter(title="Select parameters to visualize")
    if df.empty:
        table = html.Div("No data available", className="text-center text-muted")
    else:
        table = html.Table([
            html.Thead(html.Tr([html.Th(col) for col in df.columns])),
            html.Tbody([
                html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
                for i in range(min(len(df), 10))
            ])
        ], className="table table-striped table-bordered")
    return fig, table

if __name__ == "__main__":
    app.run_server(debug=True)
