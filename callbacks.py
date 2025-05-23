from dash import Input, Output, State, html
import pandas as pd
import base64
import io
import plotly.graph_objects as go
from dash.dash_table import DataTable
from plots import generate_sankey_plot
from plotly.colors import qualitative
from plotly.colors import sequential
from sankey_plot_fixed import build_sankey_from_kraken 
from kraken_bar_plot import plot_stacked_bar_kraken

from dash.exceptions import PreventUpdate
from dash import callback_context


def register_callbacks(app, uploaded_data):

    # Callback for Dashboard file upload (Excel)
    @app.callback(
        [
            Output('upload-status', 'children'),
            Output('sheet-dropdown', 'options')
        ],
        [Input('upload-data', 'contents')],
        [State('upload-data', 'filename')],
        prevent_initial_call=True
    )
    def handle_excel_upload(upload_contents, upload_filename):
        if not upload_contents:
            raise PreventUpdate

        try:
            content_type, content_string = upload_contents.split(',')
            decoded = io.BytesIO(base64.b64decode(content_string))

            if upload_filename.endswith('.xlsx') or upload_filename.endswith('.xls'):
                print("Detected Excel file")  # Debugging
                excel_data = pd.ExcelFile(decoded)
                uploaded_data['data'] = excel_data
                sheets = excel_data.sheet_names
            else:
                return f"Unsupported format: {upload_filename}", []

        except Exception as e:
            print(f"Error processing file: {e}")
            return f"Error uploading file: {e}", []

        sheet_options = [{'label': sheet, 'value': sheet} for sheet in sheets]
        return f"Uploaded: {upload_filename}", sheet_options



    # Callback for Taxonomy Analysis Kraken TSV upload
    @app.callback(
        [
            Output('kraken-upload-status', 'children'),
            Output('kraken-sheet-dropdown', 'options')
        ],
        [Input('upload-kraken-data', 'contents')],
        [State('upload-kraken-data', 'filename')],
        prevent_initial_call=True
    )
    def handle_kraken_upload(kraken_contents, kraken_filename):
        print("\n=== DEBUG: Kraken Upload Callback Triggered ===")  # Debugging log

        if not kraken_contents:
            print("DEBUG: No file detected in upload-kraken-data.")
            raise PreventUpdate

        try:
            print(f"DEBUG: Kraken File Uploaded - {kraken_filename}")  # Debugging

            # Decode file
            content_type, content_string = kraken_contents.split(',')
            decoded = io.BytesIO(base64.b64decode(content_string))

            # Read Kraken TSV with tab separator
            df = pd.read_csv(decoded, sep='\t', header=None)

            # Debugging: Print first few rows
            print(f"DEBUG: First few rows of the uploaded Kraken file:\n{df.head()}")

            # Define expected Kraken TSV column headers
            kraken_columns = ['percentage', 'reads_clade', 'reads_taxon', 'rank', 'NCBI_tax_ID', 'name']

            # Verify column count
            if df.shape[1] == len(kraken_columns):
                df.columns = kraken_columns
            else:
                print(f"DEBUG: Unexpected column count in Kraken TSV (Expected: {len(kraken_columns)}, Found: {df.shape[1]})")
                return f"Error: Unexpected number of columns in Kraken TSV", []

            # Store in global uploaded_data dictionary
            uploaded_data['data'] = {"Kraken TSV": df}

            # Populate dropdowns
            sample_label = kraken_filename.split("_")[0]  # Use "3N09_L006_L000" as label
            kraken_sheets = [sample_label]
            uploaded_data['data'] = {sample_label: df}

            kraken_options = [{'label': sheet, 'value': sheet} for sheet in kraken_sheets]

            print("DEBUG: Kraken TSV successfully stored in uploaded_data.")
            return f"Uploaded: {kraken_filename}", kraken_options  # ✅ Fixed: Now returns only 2 values

        except Exception as e:
            print(f"ERROR: Failed to process Kraken TSV file - {e}")
            return f"Error processing file: {e}", []




    @app.callback(
        [
            Output('x-axis-dropdown', 'options'),
            Output('y-axis-dropdown', 'options'),
            Output('new-x-axis-dropdown', 'options'),
            Output('new-y-axis-dropdown', 'options')
        ],
        Input('sheet-dropdown', 'value')
    )
    def update_all_axis_dropdowns(sheet_name):
        if sheet_name and 'data' in uploaded_data:
            try:
                df = uploaded_data['data'].parse(sheet_name)
                
                # Force numeric conversion
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                # Extract numeric columns for Y-axis and all columns for X-axis
                all_cols = df.columns.tolist()
                numeric_cols = df.select_dtypes(include='number').columns.tolist()

                # Debugging: Print column types
                print("All Columns:", all_cols)
                print("Numeric Columns:", numeric_cols)

                return (
                    [{'label': col, 'value': col} for col in all_cols],
                    [{'label': col, 'value': col} for col in numeric_cols],
                    [{'label': col, 'value': col} for col in all_cols],
                    [{'label': col, 'value': col} for col in numeric_cols]
                )
            except Exception as e:
                print(f"Error updating axis dropdowns: {e}")
                return [], [], [], []
        return [], [], [], []




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
                color_palette = qualitative.Alphabet
                # color_palette = sequential.Viridis
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
                    title=f"{y_axis}" if error_values is not None else f"{y_axis} Plot",
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
        [
            Output('new-bar-plot', 'figure'),
            Output('new-bar-plot-table', 'children')  # New output for data table
        ],
        [
            Input('sheet-dropdown', 'value'),
            Input('new-x-axis-dropdown', 'value'),
            Input('new-y-axis-dropdown', 'value')
        ]
    )
    def generate_new_dynamic_bar_plot(sheet_name, x_axis, y_axis):
        if sheet_name and x_axis and y_axis and 'data' in uploaded_data:
            try:
                df = uploaded_data['data'].parse(sheet_name)
                df = df.dropna(subset=[x_axis, y_axis])  # Remove rows with NaN values
                x_values = df[x_axis]
                y_values = pd.to_numeric(df[y_axis], errors='coerce')
                
                # Create color mapping for bar plot
                unique_x_values = x_values.unique()
                color_palette = qualitative.Plotly
                color_map = {value: color_palette[i % len(color_palette)] for i, value in enumerate(unique_x_values)}
                colors = x_values.map(color_map)

                # Generate the bar plot
                fig = go.Figure(
                    go.Bar(
                        x=x_values,
                        y=y_values,
                        marker=dict(color=colors),
                    )
                )

                fig.update_layout(
                    title="Custom Bar Plot",
                    xaxis_title=x_axis,
                    yaxis_title=y_axis,
                    plot_bgcolor='#2c2f34',
                    paper_bgcolor='#1e1e1e',
                    font_color="white"
                )

                # Generate Data Table
                table = DataTable(
                    data=df[[x_axis, y_axis]].to_dict('records'),
                    columns=[{"name": col, "id": col} for col in [x_axis, y_axis]],
                    style_table={'overflowX': 'auto', 'backgroundColor': '#2c2f34'},
                    style_header={'fontWeight': 'bold', 'color': 'white', 'backgroundColor': '#1e1e1e'},
                    style_data={'color': 'white', 'backgroundColor': '#2c2f34'},
                    page_size=10,
                )

                return fig, table  # Return both figure and table

            except Exception as e:
                return go.Figure().update_layout(title=f"Error: {e}"), html.Div(f"Error displaying data: {e}")

        return go.Figure().update_layout(title="Select X and Y Axis"), html.Div("No data to display", className="text-muted")






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
        [Input('kraken-sheet-dropdown', 'value')]
    )
    def generate_sankey_plot_callback(sheet_name):
        if sheet_name and 'data' in uploaded_data:
            try:
                data_source = uploaded_data['data']
                if isinstance(data_source, dict) and sheet_name in data_source:
                    df = data_source[sheet_name]
                else:
                    return (
                        go.Figure().update_layout(title="Error: Kraken TSV Data Not Found"),
                        html.Div("Error: Kraken TSV Data Not Found")
                    )

                fig, table = build_sankey_from_kraken(df, sample_name=sheet_name)
                return fig, table

            except Exception as e:
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
        [Input('kraken-sheet-dropdown', 'value')]
    )
    def generate_kraken_stacked_bar_plot(sheet_name):
        print(f"\n=== DEBUG: Kraken Sheet Selected: {sheet_name} ===")  # Debugging log

        if sheet_name and 'data' in uploaded_data:
            try:
                df = uploaded_data['data'].get(sheet_name, None)

                if df is None:
                    print("DEBUG: No data found for selected Kraken sheet.")
                    return go.Figure().update_layout(title="Error: No data found")

                # Debug: Print DataFrame Columns
                print(f"DEBUG: DataFrame Columns: {df.columns.tolist()}")

                # Ensure required columns exist
                required_columns = {"rank", "reads_taxon", "name"}
                if not required_columns.issubset(df.columns):
                    print("DEBUG: Missing required Kraken columns.")
                    return go.Figure().update_layout(title="Error: Missing required columns")

                # Rename columns for consistency
                rename_mapping = {"rank": "rank", "reads_taxon": "direct_reads", "name": "name"}
                df.rename(columns=rename_mapping, inplace=True)

                # Convert direct_reads to integers
                df["direct_reads"] = pd.to_numeric(df["direct_reads"], errors="coerce").fillna(0).astype(int)

                # Pass to plotting function
                fig = plot_stacked_bar_kraken(df)

                print("DEBUG: Kraken bar plot successfully generated.")  # Debug log
                return fig

            except Exception as e:
                print(f"ERROR: Kraken bar plot generation failed - {e}")
                return go.Figure().update_layout(title=f"Error: {e}")

        print("DEBUG: No Kraken sheet selected.")
        return go.Figure().update_layout(title="No Data to Display")




