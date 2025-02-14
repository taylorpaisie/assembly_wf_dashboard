from dash import Input, Output, State, html
import pandas as pd
import base64
import io
import plotly.graph_objects as go
from dash.dash_table import DataTable
from plots import generate_sankey_plot
from plotly.colors import qualitative
from sankey_plot_fixed import build_sankey_from_kraken 
from kraken_bar_plot import plot_stacked_bar_kraken


def register_callbacks(app, uploaded_data):
    @app.callback(
        [
            Output('upload-status', 'children'),
            Output('sankey-sheet-dropdown', 'options'),
            Output('sheet-dropdown', 'options'),
            Output('kraken-sheet-dropdown', 'options')
        ],
        Input('upload-data', 'contents'),
        State('upload-data', 'filename'),
    )
    def handle_file_upload(contents, filename):
        if contents is not None:
            try:
                print(f"File uploaded: {filename}")  # Debugging message
                content_type, content_string = contents.split(',')
                decoded = io.BytesIO(base64.b64decode(content_string))

                if filename.endswith('.xlsx') or filename.endswith('.xls'):
                    print("Detected Excel file")  # Debugging message
                    excel_data = pd.ExcelFile(decoded)
                    uploaded_data['data'] = excel_data
                    sheets = excel_data.sheet_names
                elif filename.endswith('.tsv') or filename.endswith('.txt'):
                    print("Detected TSV file")  # Debugging message
                    kraken_columns = ['percentage', 'reads_clade', 'reads_taxon', 'rank', 'NCBI_tax_ID', 'name']
                    df = pd.read_csv(decoded, sep='\t', names=kraken_columns, header=None)

                    print(f"TSV Loaded: {df.head()}")  # Print first few rows
                    uploaded_data['data'] = {"TSV File": df}  # Simulate a "sheet" for TSV
                    sheets = ["TSV File"]
                else:
                    print("Unsupported file format")  # Debugging message
                    return f"Unsupported file format: {filename}", [], [], []

                if not sheets:
                    return "No sheets found in the uploaded file.", [], [], []

                # Generate options for dropdowns
                sheet_options = [{'label': sheet, 'value': sheet} for sheet in sheets]
                return f"Uploaded: {filename}", sheet_options, sheet_options, sheet_options
            except Exception as e:
                print(f"Error processing file: {e}")
                return f"Error uploading file: {e}", [], [], []
        return "No file uploaded yet", [], [], []


    @app.callback(
        [Output('x-axis-dropdown', 'options'), Output('y-axis-dropdown', 'options')],
        Input('sheet-dropdown', 'value')
    )
    def update_axis_dropdowns(sheet_name):
        if sheet_name and 'data' in uploaded_data:
            try:
                if isinstance(uploaded_data['data'], pd.ExcelFile):  # Excel File
                    df = uploaded_data['data'].parse(sheet_name)
                elif isinstance(uploaded_data['data'], dict) and sheet_name in uploaded_data['data']:  # TSV File
                    df = uploaded_data['data'][sheet_name]
                else:
                    return []


                # Extract numeric columns for Y-axis and all columns for X-axis
                all_cols = df.columns.tolist()
                numeric_cols = df.select_dtypes(include='number').columns.tolist()
                pattern_based_cols = [
                    col for col in df.columns
                    if df[col].astype(str).str.contains(r'^[\d.]+x_.*[\d.]+x$', na=False).any()
                ]

                combined_y_cols = numeric_cols + pattern_based_cols

                return (
                    [{'label': col, 'value': col} for col in all_cols],  # X-axis options
                    [{'label': col, 'value': col} for col in combined_y_cols]  # Y-axis options
                )
            except Exception as e:
                print(f"Error updating axis dropdowns: {e}")
                return [], []
        return [], []

    @app.callback(
        Output('coverage-bar-plot', 'figure'),
        Input('sheet-dropdown', 'value'),
        Input('x-axis-dropdown', 'value'),
        Input('y-axis-dropdown', 'value'),
    )
    def generate_coverage_bar_plot(sheet_name, x_axis, y_axis):
        if sheet_name and x_axis and y_axis and 'data' in uploaded_data:
            try:
                df = uploaded_data['data'].parse(sheet_name)

                if "Coverage" in y_axis and "mean" in y_axis:
                    coverage_data = df[y_axis].str.extract(r'(?P<mean>[\d.]+)x_.*(?P<stddev>[\d.]+)x')
                    df['mean'] = pd.to_numeric(coverage_data['mean'], errors='coerce')
                    df['stddev'] = pd.to_numeric(coverage_data['stddev'], errors='coerce')
                    df = df.dropna(subset=['mean'])

                    x_values = df[x_axis]
                    y_values = df['mean']
                    error_values = df['stddev']
                else:
                    df = df.dropna(subset=[x_axis, y_axis])
                    x_values = df[x_axis]
                    y_values = pd.to_numeric(df[y_axis], errors='coerce')
                    error_values = None

                unique_x_values = x_values.unique()
                color_palette = qualitative.Vivid
                color_map = {value: color for value, color in zip(unique_x_values, color_palette)}
                colors = x_values.map(color_map)

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
                print(f"Error generating bar plot: {e}")
                return go.Figure().update_layout(title=f"Error: {e}")

        return go.Figure().update_layout(title="No Data to Display")

    @app.callback(
        Output('data-table-container', 'children'),
        Input('sheet-dropdown', 'value'),
        Input('x-axis-dropdown', 'value'),
        Input('y-axis-dropdown', 'value')
    )
    def display_data_table(sheet_name, x_axis, y_axis):
        if sheet_name and x_axis and y_axis and 'data' in uploaded_data:
            try:
                df = uploaded_data['data'].parse(sheet_name)
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

    @app.callback(
        Output('sample-dropdown', 'options'),
        Input('sankey-sheet-dropdown', 'value')
    )
    def populate_sample_dropdown(sheet_name):
        print("populate_sample_dropdown triggered")
        if sheet_name and 'data' in uploaded_data:
            try:
                excel_data = uploaded_data['data']
                df = excel_data.parse(sheet_name)
                print(f"Loaded sheet: {sheet_name}, Rows: {len(df)}, Columns: {list(df.columns)}")

                # Normalize column names
                df.columns = df.columns.str.strip()

                if 'Sample_name' not in df.columns:
                    print(f"'Sample_name' not found in sheet {sheet_name}. Available columns: {df.columns}")
                    return []

                sample_names = df['Sample_name'].dropna().unique()
                print(f"Sample names found: {sample_names}")
                return [{'label': name, 'value': name} for name in sample_names]
            except Exception as e:
                print(f"Error loading samples: {e}")
                return []
        return []


    @app.callback(
        [Output('sankey-plot', 'figure'), Output('sankey-table', 'children')],
        Input('sankey-sheet-dropdown', 'value'),
        Input('sample-dropdown', 'value')
    )
    def generate_sankey_plot_callback(sheet_name, selected_sample):
        print("generate_sankey_plot_callback triggered")
        
        if sheet_name and 'data' in uploaded_data:
            try:
                data_source = uploaded_data['data']

                if isinstance(data_source, pd.ExcelFile):  # Excel File
                    print(f"Loading Excel sheet: {sheet_name}")
                    df = data_source.parse(sheet_name)
                elif isinstance(data_source, dict) and sheet_name in data_source:  # TSV File
                    print("Using TSV data")
                    df = data_source[sheet_name]
                else:
                    print("Error: Sheet not found in uploaded data")
                    return (
                        go.Figure().update_layout(title="Error: Sheet not found"),
                        html.Div("Error: Sheet not found")
                    )

                print(f"Data Loaded for Sankey Plot: {df.head()}")  # Debugging message

                # **Call function correctly to extract both Figure and Table**
                fig, table = build_sankey_from_kraken(df)  # Extract figure and table separately
                
                return fig, table  # Return both outputs

            except Exception as e:
                print(f"Error generating Sankey plot: {e}")
                return (
                    go.Figure().update_layout(title=f"Error: {e}"),
                    html.Div(f"Error generating table: {e}")
                )

        return (
            go.Figure().update_layout(title="No Data to Display"),
            html.Div("No Data Available")
        )



    @app.callback(
        Output('kraken-bar-plot', 'figure'),
        Input('kraken-sheet-dropdown', 'value')
    )
    def generate_kraken_stacked_bar_plot(sheet_name):
        print(f"DEBUG: Selected Sheet: {sheet_name}")  # Debug log

        if sheet_name and 'data' in uploaded_data:
            try:
                if isinstance(uploaded_data['data'], dict):
                    df = uploaded_data['data'][sheet_name]  # For TSV files
                else:
                    df = uploaded_data['data'].parse(sheet_name)  # For Excel files

                # Debug: Print column names
                print(f"DEBUG: DataFrame Columns Before Renaming: {df.columns.tolist()}")

                # Rename Kraken2 TSV columns to match expected names
                rename_mapping = {
                    "rank": "rank",
                    "reads_taxon": "direct_reads",  # Ensure this matches expected column in plot_stacked_bar_kraken()
                    "name": "name"
                }
                
                df.rename(columns=rename_mapping, inplace=True)

                # Debug: Print renamed columns
                print(f"DEBUG: DataFrame Columns After Renaming: {df.columns.tolist()}")

                # Pass to function after renaming
                fig = plot_stacked_bar_kraken(df)
                print("DEBUG: Kraken bar plot generated!")  # Debug log

                return fig

            except Exception as e:
                print(f"ERROR: {e}")
                return go.Figure().update_layout(title=f"Error: {e}")

        print("DEBUG: No data selected.")
        return go.Figure().update_layout(title="No Data to Display")


