from dash import dcc, html
import dash_bootstrap_components as dbc

# File upload section
def get_file_upload():
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5("Assembly Metrics Dashboard - Upload Excel File", className="text-white"),
                className="bg-primary"
            ),
            dbc.CardBody(
                [
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            html.I(className="bi bi-upload me-2"),
                            'Drag and Drop or ',
                            html.A('Select a File', className="text-primary fw-bold")
                        ]),
                        style={
                            'width': '100%',
                            'height': '70px',
                            'lineHeight': '70px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '10px',
                            'textAlign': 'center',
                            'margin': '10px',
                            'backgroundColor': '#f8f9fa',
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', className='mt-2 text-success'),
                    html.Div(
                        [
                            html.Label("Select a Sheet:", className="fw-bold mt-3"),
                            dcc.Dropdown(id='sheet-dropdown', placeholder="No sheet selected yet"),
                        ],
                        className="mt-3"
                    ),
                ]
            ),
        ],
        className="shadow-sm mb-4"
    )

# Data display section with bar plot
def get_data_display():
    return dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H5("Spreadsheet Data", className="text-white"),
                            className="bg-secondary"
                        ),
                        dbc.CardBody(
                            [
                                dcc.Loading(
                                    children=[html.Div(id="data-table-container")],
                                    type="default"
                                )
                            ]
                        ),
                    ],
                    className="shadow-sm mb-4"
                ),
                width=6
            ),

            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H5("Bar Plot Controls", className="text-white"),
                            className="bg-secondary"
                        ),
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Label("Select X-Axis:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='x-axis-dropdown',
                                            placeholder="Select column for X-axis"
                                        ),
                                    ],
                                    className="mb-3"
                                ),
                                html.Div(
                                    [
                                        html.Label("Select Y-Axis:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='y-axis-dropdown',
                                            placeholder="Select column for Y-axis"
                                        ),
                                    ],
                                    className="mb-3"
                                ),
                                dcc.Graph(id='coverage-bar-plot', style={'height': '500px'}),
                            ]
                        ),
                    ],
                    className="shadow-sm mb-4"
                ),
                width=6
            ),
        ]
    )

# Sankey plot section
def get_sankey_section():
    return dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H5("Sankey Plot Controls", className="text-white"),
                            className="bg-secondary"
                        ),
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Label("Select a Sheet:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='sankey-sheet-dropdown',
                                            placeholder="Select a sheet"
                                        ),
                                    ],
                                    className="mb-3"
                                ),
                                html.Div(
                                    [
                                        html.Label("Select a Sample:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id='sample-dropdown',
                                            placeholder="Select a sample"
                                        ),
                                    ],
                                    className="mb-3"
                                ),
                            ]
                        ),
                    ],
                    className="shadow-sm mb-4"
                ),
                width=6
            ),

            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H5("Sankey Plot", className="text-white"),
                            className="bg-secondary"
                        ),
                        dbc.CardBody(
                            dcc.Graph(id='sankey-plot', style={'height': '500px'})
                        ),
                    ],
                    className="shadow-sm mb-4"
                ),
                width=6
            ),
        ]
    )

# Main layout combining all sections
def create_layout():
    return dbc.Container(
        fluid=True,
        children=[
            # Header Section
            dbc.Row(
                dbc.Col(
                    html.Div(
                        "Taxonomic Analysis Dashboard",
                        className="text-center bg-primary text-white p-3 rounded",
                        style={"fontSize": "24px", "fontWeight": "bold"}
                    ),
                    width=12
                )
            ),
            html.Br(),

            # Upload Section
            dbc.Row(
                dbc.Col(get_file_upload(), width=12)
            ),
            html.Br(),

            # Data Display Section
            get_data_display(),
            html.Br(),

            # Sankey Section
            get_sankey_section(),
        ],
        style={"padding": "20px"}
    )
