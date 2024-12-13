from dash import Dash, html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
import plotly.graph_objects as go

# Initialize Dash app with external stylesheets
app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
server = app.server  # Expose server for Gunicorn

# Global variable to hold the uploaded data
uploaded_data = {}

# Define the layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Assembly Workflow Dashboard",
                        className="text-center text-primary my-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Upload Excel File"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select a File')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        multiple=False  # Single file upload
                    ),
                    html.Div(id='upload-status', className='mt-2 text-success')
                ])
            ]),
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Select Data"),
                dbc.CardBody([
                    html.Label("Select a Sheet:"),
                    dcc.Dropdown(
                        id='sheet-dropdown',
                        placeholder="Upload a file to populate",
                    ),
                ])
            ])
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Coverage Bar Plot"),
                dbc.CardBody([
                    dcc.Graph(id='coverage-bar-plot')
                ])
            ])
        ])
    ])
])

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
            # Decode and read the file
            content_type, content_string = contents.split(',')
            decoded = io.BytesIO(base64.b64decode(content_string))
            uploaded_data = pd.ExcelFile(decoded)

            # Get the sheet names
            sheets = uploaded_data.sheet_names
            return f"Uploaded: {filename}", [{'label': sheet, 'value': sheet} for sheet in sheets]
        except Exception as e:
            return f"Error uploading file: {e}", []
    return "No file uploaded yet", []

# Callback to generate the coverage bar plot
@app.callback(
    Output('coverage-bar-plot', 'figure'),
    Input('sheet-dropdown', 'value')
)
def generate_coverage_bar_plot(sheet_name):
    if sheet_name and uploaded_data:
        try:
            # Load the selected sheet
            df = uploaded_data.parse(sheet_name)
            
            # Ensure the selected sheet is "Assembly_Depth"
            if sheet_name != "Assembly_Depth":
                return go.Figure().update_layout(title="Select the 'Assembly_Depth' sheet")
            
            # Parse the 'Coverage_(mean[x]_+/-_stdev[x])' column
            coverage_data = df['Coverage_(mean[x]_+/-_stdev[x])'].str.extract(r'(?P<mean>[\d.]+)x_.*(?P<stddev>[\d.]+)x')
            df['mean'] = coverage_data['mean'].astype(float)
            df['stddev'] = coverage_data['stddev'].astype(float)

            # Create a bar plot with error bars
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df['Sample_name'],
                y=df['mean'],
                error_y=dict(type='data', array=df['stddev'], visible=True),
                name='Coverage with StdDev',
                marker=dict(color='blue')
            ))

            fig.update_layout(
                title="Coverage Bar Plot with Error Bars",
                xaxis_title="Sample Name",
                yaxis_title="Coverage (Mean ± StdDev)",
                xaxis=dict(tickangle=-45),
                plot_bgcolor="white",
                showlegend=False
            )
            return fig
        except Exception as e:
            return go.Figure().update_layout(title=f"Error generating plot: {e}")
    return go.Figure().update_layout(title="No data to display")

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
