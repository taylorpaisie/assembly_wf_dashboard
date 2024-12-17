from dash import Dash, html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
import plotly.graph_objects as go

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
    navbar,
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
        ], width=6, className="offset-3")
    ]),
    dbc.Row([
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
        ], width=8, className="offset-2")
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Coverage Bar Plot", className="text-white")),
                dbc.CardBody([
                    dcc.Graph(id='coverage-bar-plot', style={'height': '500px'}),
                ])
            ], className="shadow-sm mb-4")
        ], width=10, className="offset-1")
    ])
], fluid=True, style={"backgroundColor": "#1e1e1e", "paddingBottom": "20px"})

# Callbacks remain the same as your provided script

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
            return f"Uploaded: {filename}", [{'label': sheet, 'value': sheet} for sheet in sheets]
        except Exception as e:
            return f"Error uploading file: {e}", []
    return "No file uploaded yet", []

# Callback to update dropdowns
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

            # Handle case where Y-axis is a coverage column
            if y_axis == "Coverage_(mean[x]_+/-_stdev[x])":
                coverage_data = df[y_axis].str.extract(r'(?P<mean>[\d.]+)x_.*(?P<stddev>[\d.]+)x')
                df['mean'] = pd.to_numeric(coverage_data['mean'], errors='coerce')
                df['stddev'] = pd.to_numeric(coverage_data['stddev'], errors='coerce')
                y_values = df['mean']
                error_values = df['stddev']
            else:
                y_values = pd.to_numeric(df[y_axis], errors='coerce')
                error_values = None

            # Dynamic color mapping
            from plotly.colors import qualitative
            unique_x_values = df[x_axis].unique()
            color_palette = qualitative.Vivid  # Use the Plotly qualitative palette
            color_map = {value: color for value, color in zip(unique_x_values, color_palette)}
            colors = df[x_axis].map(color_map)

            # Create the bar plot
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df[x_axis],
                y=y_values,
                marker=dict(color=colors),
                error_y=dict(
                    type='data',
                    array=error_values,
                    visible=bool(error_values is not None)
                ),
                name="Coverage with StdDev" if error_values is not None else "Coverage"
            ))

            # Update layout
            fig.update_layout(
                title="Coverage Bar Plot with Dynamic Colors",
                xaxis_title=f"{x_axis}",
                yaxis_title=f"{y_axis} (Mean ± StdDev)" if error_values is not None else y_axis,
                xaxis=dict(tickangle=-45),
                plot_bgcolor='#2c2f34',
                paper_bgcolor='#1e1e1e',
                font_color="white",
                showlegend=False
            )
            return fig

        except Exception as e:
            return go.Figure().update_layout(title=f"Error: {e}")

    return go.Figure().update_layout(title="No Data to Display")


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
