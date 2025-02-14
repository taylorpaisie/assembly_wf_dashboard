from dash import dcc, html
import dash_bootstrap_components as dbc


# File upload section
def get_file_upload():
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5("Assembly Metrics Dashboard - Upload Excel or Kraken TSV File", className="text-white"),
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
                            'color': '#000000'
                        },
                        multiple=False
                    ),
                    # Add this Div to display upload status
                    html.Div(id='upload-status', className='mt-2 text-success'),
                    html.Div(
                        [
                            html.Label("Select a Sheet:", className="fw-bold mt-3"),
                            dcc.Dropdown(
                                id='sheet-dropdown',
                                placeholder="No sheet selected yet",
                                style={
                                    'color': '#000000',  # Black text
                                    'backgroundColor': '#ffffff',  # White background
                                }
                            )
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
            # Column for displaying spreadsheet data
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H5("Spreadsheet Data", className="text-white"), className="bg-secondary"),
                        dbc.CardBody([dcc.Loading(children=[html.Div(id="data-table-container")], type="default")]),
                    ],
                    className="shadow-sm mb-4"
                ),
                width=6
            ),

            # Column for Assembly_Depth bar plot
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H5("Assembly Metrics Bar Plot", className="text-white"), className="bg-secondary"),
                        dbc.CardBody(
                            [
                                html.Div([
                                    html.Label("Select X-Axis:", className="fw-bold"),
                                    dcc.Dropdown(id='x-axis-dropdown', placeholder="Select column for X-axis",
                                        style={'color': '#000000', 'backgroundColor': '#ffffff'})
                                ], className="mb-3"),
                                html.Div([
                                    html.Label("Select Y-Axis:", className="fw-bold"),
                                    dcc.Dropdown(id='y-axis-dropdown', placeholder="Select column for Y-axis",
                                    style={'color': '#000000', 'backgroundColor': '#ffffff'})
                                ], className="mb-3"),
                                dcc.Graph(id='coverage-bar-plot', style={'height': '500px'}),
                            ]
                        ),
                    ],
                    className="shadow-sm mb-4"
                ),
                width=6
            ),

            # Kraken Controls and Bar Plot (Fix: Ensuring they're always in the layout)
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H5("Kraken Controls", className="text-white"), className="bg-secondary"),
                        dbc.CardBody(
                            [
                                html.Div([
                                    html.Label("Select a Kraken Sheet:", className="fw-bold"),
                                    dcc.Dropdown(id='kraken-sheet-dropdown', placeholder="Select a sheet",
                                        style={'color': '#000000', 'backgroundColor': '#ffffff'})
                                ], className="mb-3"),
                            ]
                        ),
                    ],
                    className="shadow-sm mb-4"
                ),
                width=3
            ),

            # Kraken Bar Plot (Restoring missing plot)
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H5("Kraken Bar Plot", className="text-white"), className="bg-secondary"),
                        dbc.CardBody(
                            dcc.Graph(id="kraken-bar-plot", figure={}, style={"height": "500px"})
                        ),
                    ],
                    className="shadow-sm mb-4"
                ),
                width=9
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
                                html.Label("Select a Sheet for Sankey:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='sankey-sheet-dropdown',
                                    placeholder="Select a sheet",
                                    style={'color': '#000000', 'backgroundColor': '#ffffff'},
                                ),
                            ]
                        ),
                    ]
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
                            dcc.Graph(id='sankey-plot', style={'height': '600px'})  # Increased height
                        ),
                    ]
                ),
                width=6
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H5("Sankey Table", className="text-white"), className="bg-secondary"),
                        dbc.CardBody(
                            html.Div(id='sankey-table')  # Placeholder for the table
                        ),
                    ],
                    className="shadow-sm mb-4"
                ),
                width=12
            ),
        ]
    )



    return html.Div([
        html.H3("How to Use", className="text-primary"),
        html.P("1. Upload a TSV or Excel file using the upload section."),
        html.P("2. Select a sheet from the dropdown to visualize the data."),
        html.P("3. Use the available controls to customize the plots."),
        html.P("4. The Sankey plot requires selecting a sample from the dataset."),
    ], style={'padding': '20px'})

def get_tabs_section():
    return dbc.Tabs([
        dbc.Tab(label="Dashboard", tab_id="tab-dashboard"),
        dbc.Tab(label="About", tab_id="tab-about"),
        dbc.Tab(label="How to Use", tab_id="tab-how-to-use"),
    ], id="tabs", active_tab="tab-dashboard")

def get_content():
    return html.Div(id="tab-content")

def create_layout():
    return dbc.Container([
        dbc.Row(
            dbc.Col(
                html.Div(
                    "Assembly Metrics and Taxonomic Analysis Dashboard",
                    className="text-center bg-primary text-white p-3 rounded",
                    style={"fontSize": "24px", "fontWeight": "bold"}
                ),
                width=12
            )
        ),
        html.Br(),
        get_tabs_section(),
        html.Br(),
        get_content(),
    ], fluid=True, style={"padding": "20px"})
