from dash import Dash, html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import io

# Initialize Dash app with external stylesheets
app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
server = app.server  # Expose server for Gunicorn

# Global variable to hold the uploaded data
uploaded_data = {}

# Define the layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Dynamic Excel Dashboard",
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
                    html.Label("Select X-Axis:"),
                    dcc.Dropdown(id='x-axis-dropdown', className="mt-2"),
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

# Callback to update X-axis dropdown
@app.callback(
    Output('x-axis-dropdown', 'options'),
    Input('sheet-dropdown', 'value')
)
def update_x_axis_options(sheet_name):
    if sheet_name and uploaded_data:
        try:
            # Load the selected sheet
            df = uploaded_data.parse(sheet_name)
            return [{'label': col, 'value': col} for col in df.columns]
        except Exception as e:
            return []
    return []

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
