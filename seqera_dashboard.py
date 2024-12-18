from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
import plotly.graph_objects as go
from dash.dash_table import DataTable


# Initialize Dash app with external stylesheets
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, dbc.icons.BOOTSTRAP])
server = app.server  # Expose server for deployment

# Global variable to hold the uploaded data
uploaded_data = {}

# Define the navbar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="#")),
        dbc.NavItem(dbc.NavLink("About", href="#")),
    ],
    brand="Assembly Workflow Dashboard",
    brand_href="#",
    color="dark",
    dark=True,
    className="mb-4",
)

# Define the layout
app.layout = dbc.Container([
    # Navbar
    navbar,

    # Row for file upload and data selection
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Upload Excel File", className="text-white")),
                dbc.CardBody([
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
                            'backgroundColor': '#2c2f34',
                        },
                        multiple=False
                    ),
                    html.Div(id='upload-status', className='mt-2 text-success'),
                ])
            ], className="shadow-sm mb-4")
        ], width=6),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Select Data", className="text-white")),
                dbc.CardBody([
                    html.Div([
                        html.Label("Select a Sheet:", className="fw-bold"),
                        dcc.Dropdown(id='sheet-dropdown', placeholder="Upload a file to populate"),
                    ], className="mb-3"),
                    html.Div([
                        html.Label("Select X-Axis:", className="fw-bold"),
                        dcc.Dropdown(id='x-axis-dropdown'),
                    ], className="mb-3"),
                    html.Div([
                        html.Label("Select Y-Axis:", className="fw-bold"),
                        dcc.Dropdown(id='y-axis-dropdown'),
                    ]),
                ])
            ], className="shadow-sm mb-4")
        ], width=6),
    ]),

    # Row for spreadsheet data and bar plot (above Sankey plot)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Spreadsheet Data", className="text-white")),
                dbc.CardBody([
                    dcc.Loading(
                        children=[
                            html.Div(id="data-table-container")
                        ],
                        type="default"
                    )
                ])
            ], className="shadow-sm mb-4")
        ], width=6),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Bar Plot", className="text-white")),
                dbc.CardBody([
                    dcc.Graph(id='coverage-bar-plot', style={'height': '500px'}),
                ])
            ], className="shadow-sm mb-4")
        ], width=6)
    ]),

    # Row for Sankey plot (below spreadsheet data and bar plot)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Select Sheet for Sankey Plot", className="text-white")),
                dbc.CardBody([
                    dcc.Dropdown(
                        id='sankey-sheet-dropdown',
                        options=[
                            {'label': 'Kraken', 'value': 'kraken'},
                            {'label': 'Kraken2', 'value': 'kraken2'}
                        ],
                        placeholder="Select a sheet",
                        style={'color': 'black'}
                    ),
                    html.Div(className="mt-3"),
                    dcc.Dropdown(
                        id='sample-dropdown',
                        placeholder="Select a sample",
                        style={'color': 'black'}
                    ),
                ])
            ], className="shadow-sm mb-4")
        ], width=6),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Sankey Plot", className="text-white")),
                dbc.CardBody([
                    dcc.Graph(id='sankey-plot', style={'height': '500px'}),
                ])
            ], className="shadow-sm mb-4")
        ], width=6),
    ])
], fluid=True, style={"backgroundColor": "#1e1e1e", "paddingBottom": "20px"})




# Callback to handle file upload
@app.callback(
    Output('upload-status', 'children'),
    Output('sheet-dropdown', 'options'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
)
def handle_file_upload(contents, filename):
    global uploaded_data
    if contents is not None:
        try:
            content_type, content_string = contents.split(',')
            decoded = io.BytesIO(base64.b64decode(content_string))
            
            uploaded_data = pd.ExcelFile(decoded)
            sheets = uploaded_data.sheet_names
            if not sheets:
                raise ValueError("No sheets found in the uploaded Excel file.")
            
            return f"Uploaded: {filename}", [{'label': sheet, 'value': sheet} for sheet in sheets]
        except Exception as e:
            print(f"Error: {e}")  # Debugging
            return f"Error uploading file: {e}", []
    return "No file uploaded yet", []

# Callback to update X-axis and Y-axis dropdowns
@app.callback(
    Output('x-axis-dropdown', 'options'),
    Output('y-axis-dropdown', 'options'),
    Input('sheet-dropdown', 'value')
)
def update_axis_dropdowns(sheet_name):
    if sheet_name and uploaded_data:
        try:
            df = uploaded_data.parse(sheet_name)
            options = [{'label': col, 'value': col} for col in df.columns]
            return options, options
        except Exception:
            return [], []
    return [], []

# Callback to generate the coverage bar plot
@app.callback(
    Output('coverage-bar-plot', 'figure'),
    Input('sheet-dropdown', 'value'),
    Input('x-axis-dropdown', 'value'),
    Input('y-axis-dropdown', 'value')
)
def generate_coverage_bar_plot(sheet_name, x_axis, y_axis):
    if sheet_name and x_axis and y_axis and uploaded_data:
        try:
            # Load the selected sheet into a DataFrame
            df = uploaded_data.parse(sheet_name)

            # Handle special "Coverage_(mean[x]_+/-_stdev[x])" column
            if "Coverage" in y_axis and "mean" in y_axis:
                # Extract mean and stddev using regex
                coverage_data = df[y_axis].str.extract(r'(?P<mean>[\d.]+)x_.*(?P<stddev>[\d.]+)x')
                
                # Convert extracted data to numeric
                df['mean'] = pd.to_numeric(coverage_data['mean'], errors='coerce')
                df['stddev'] = pd.to_numeric(coverage_data['stddev'], errors='coerce')

                # Filter out rows where mean is NaN
                df = df.dropna(subset=['mean'])

                x_values = df[x_axis]
                y_values = df['mean']
                error_values = df['stddev']
            else:
                # Standard column plotting without error bars
                df = df.dropna(subset=[x_axis, y_axis])
                x_values = df[x_axis]
                y_values = pd.to_numeric(df[y_axis], errors='coerce')
                error_values = None

            # Dynamic color mapping for unique X-axis values
            from plotly.colors import qualitative
            unique_x_values = x_values.unique()
            color_palette = qualitative.Vivid
            color_map = {value: color for value, color in zip(unique_x_values, color_palette)}
            colors = x_values.map(color_map)

            # Build the bar plot
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=x_values,
                y=y_values,
                error_y=dict(
                    type='data',
                    array=error_values,
                    visible=error_values is not None
                ),
                marker=dict(color=colors),
            ))

            # Update layout
            fig.update_layout(
                title="Coverage Bar Plot with Error Bars" if error_values is not None else "Coverage Bar Plot",
                xaxis_title=x_axis,
                yaxis_title="Coverage (Mean ± StdDev)" if error_values is not None else y_axis,
                xaxis=dict(tickangle=-45),
                plot_bgcolor='#2c2f34',
                paper_bgcolor='#1e1e1e',
                font_color="white"
            )
            return fig

        except Exception as e:
            print(f"Error: {e}")  # Debugging
            return go.Figure().update_layout(title=f"Error: {e}")

    return go.Figure().update_layout(title="No Data to Display")



# Callback to display spreadsheet data
@app.callback(
    Output('data-table-container', 'children'),
    Input('sheet-dropdown', 'value'),
    Input('x-axis-dropdown', 'value'),
    Input('y-axis-dropdown', 'value')
)
def display_data_table(sheet_name, x_axis, y_axis):
    if sheet_name and x_axis and y_axis and uploaded_data:
        try:
            df = uploaded_data.parse(sheet_name)
            filtered_df = df[[x_axis, y_axis]].dropna()
            table = DataTable(
                data=filtered_df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in filtered_df.columns],
                style_table={'overflowX': 'auto', 'backgroundColor': '#2c2f34'},
                style_header={'fontWeight': 'bold', 'color': 'white', 'backgroundColor': '#1e1e1e'},
                style_data={'color': 'white', 'backgroundColor': '#2c2f34'},
                page_size=10,
            )
            return table
        except Exception as e:
            return html.Div(f"Error displaying data: {e}", className="text-danger")
    return html.Div("No data to display", className="text-muted")

# sankey plot
@app.callback(
    Output('sankey-plot', 'figure'),
    Input('upload-data', 'contents'),
    Input('sankey-sheet-dropdown', 'value'),
    Input('sample-dropdown', 'value')
)
def update_sankey_plot(contents, selected_sheet, selected_sample):
    if contents and selected_sheet and selected_sample:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            excel_data = pd.ExcelFile(io.BytesIO(decoded))
            sheet_map = {sheet.strip().lower(): sheet for sheet in excel_data.sheet_names}
            df = excel_data.parse(sheet_map[selected_sheet.lower()])

            # Filter the DataFrame to the selected sample
            df = df[df['Sample_name'] == selected_sample]

            # Build the Sankey plot
            nodes = []
            links = {"source": [], "target": [], "value": []}
            node_map = {}

            def get_node_index(name):
                if name not in node_map:
                    node_map[name] = len(nodes)
                    nodes.append(name)
                return node_map[name]

            for _, row in df.iterrows():
                parent_index = get_node_index(selected_sample)  # Root node
                for genus, species, reads_pct in [
                    (row.get('Genus'), row.get('Species'), row.get('Reads_(%)')),
                    (row.get('Genus.1'), row.get('Species.1'), row.get('Reads_(%).1')),
                    (row.get('Genus.2'), row.get('Species.2'), row.get('Reads_(%).2'))
                ]:
                    if pd.notna(genus):
                        genus_index = get_node_index(genus)
                        links["source"].append(parent_index)
                        links["target"].append(genus_index)
                        links["value"].append(reads_pct)
                        parent_index = genus_index
                    if pd.notna(species):
                        species_index = get_node_index(species)
                        links["source"].append(parent_index)
                        links["target"].append(species_index)
                        links["value"].append(reads_pct)
                        parent_index = species_index

            # Generate the Sankey plot
            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=nodes
                ),
                link=dict(
                    source=links["source"],
                    target=links["target"],
                    value=links["value"]
                )
            )])

            fig.update_layout(title_text=f"Sankey Plot for {selected_sample}", font_size=10)
            return fig

        except Exception as e:
            print(f"Error: {e}")
            return go.Figure().update_layout(title=f"Error: {e}")

    return go.Figure().update_layout(title="No Data to Display")

@app.callback(
    Output('sample-dropdown', 'options'),
    Input('upload-data', 'contents'),
    Input('sankey-sheet-dropdown', 'value')
)
def populate_sample_dropdown(contents, selected_sheet):
    if contents and selected_sheet:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            # Load Excel file and selected sheet
            excel_data = pd.ExcelFile(io.BytesIO(decoded))
            sheet_map = {sheet.strip().lower(): sheet for sheet in excel_data.sheet_names}
            if selected_sheet.lower() not in sheet_map:
                raise ValueError(f"Sheet '{selected_sheet}' not found in file.")
            
            # Parse the sheet and get unique sample names
            df = excel_data.parse(sheet_map[selected_sheet.lower()])
            sample_names = df['Sample_name'].unique()
            
            # Return dropdown options
            return [{'label': sample, 'value': sample} for sample in sample_names]
        except Exception as e:
            print(f"Error: {e}")
            return []
    return []




# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)