from dash import Input, Output, State, html
import pandas as pd
import base64
import io
import plotly.graph_objects as go
from dash.dash_table import DataTable
from plots import generate_sankey_plot
from plotly.colors import qualitative


def register_callbacks(app, uploaded_data):
    @app.callback(
        [
            Output('upload-status', 'children'),
            Output('sankey-sheet-dropdown', 'options'),
            Output('sheet-dropdown', 'options'),
            Output('kraken-sheet-dropdown', 'options')  # Add this for Kraken dropdown
        ],
        Input('upload-data', 'contents'),
        State('upload-data', 'filename'),
    )
    def handle_file_upload(contents, filename):
        if contents is not None:
            try:
                content_type, content_string = contents.split(',')
                decoded = io.BytesIO(base64.b64decode(content_string))

                # Load the uploaded Excel file
                excel_data = pd.ExcelFile(decoded)
                uploaded_data['data'] = excel_data
                sheets = excel_data.sheet_names

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
                df = uploaded_data['data'].parse(sheet_name)

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
        Input('y-axis-dropdown', 'value')
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
        Output('sankey-plot', 'figure'),
        Input('sankey-sheet-dropdown', 'value'),
        Input('sample-dropdown', 'value')
    )
    def generate_sankey_plot_callback(sheet_name, selected_sample):
        print("generate_sankey_plot_callback triggered")
        if sheet_name and selected_sample and 'data' in uploaded_data:
            try:
                excel_data = uploaded_data['data']
                df = excel_data.parse(sheet_name)

                # Filter data for the selected sample
                df = df[df['Sample_name'] == selected_sample]
                print(f"Filtered data: {len(df)} rows")

                # Dynamically generate nodes and links
                nodes = []
                links = {"source": [], "target": [], "value": []}
                node_map = {}

                def get_node_index(name):
                    if name not in node_map:
                        node_map[name] = len(nodes)
                        nodes.append(name)
                    return node_map[name]

                # Build nodes and links based on hierarchical columns
                hierarchy = ['Genus', 'Species']
                for _, row in df.iterrows():
                    parent_index = get_node_index(selected_sample)
                    for level in hierarchy:
                        if pd.notna(row.get(level)):
                            current_index = get_node_index(row[level])
                            links["source"].append(parent_index)
                            links["target"].append(current_index)
                            links["value"].append(row.get('Reads_(%)', 1))
                            parent_index = current_index

                print(f"Nodes: {nodes}")
                print(f"Links: {links}")

                return generate_sankey_plot(nodes, links)

            except Exception as e:
                print(f"Error generating Sankey plot: {e}")
                return go.Figure().update_layout(title=f"Error: {e}")

        return go.Figure().update_layout(title="No Data to Display")
    

    @app.callback(
        Output('kraken-sample-dropdown', 'options'),
        Input('kraken-sheet-dropdown', 'value')
    )
    def update_sample_dropdown(sheet_name):
        if sheet_name and 'data' in uploaded_data:
            try:
                df = uploaded_data['data'].parse(sheet_name)
                if 'Sample_name' in df.columns:
                    unique_samples = df['Sample_name'].dropna().unique()
                    return [{'label': sample, 'value': sample} for sample in unique_samples]
                else:
                    return []
            except Exception as e:
                print(f"Error loading samples for sheet {sheet_name}: {e}")
                return []
        return []


    @app.callback(
        Output('kraken-bar-plot', 'figure'),
        Input('kraken-sheet-dropdown', 'value')
    )
    def generate_kraken_stacked_bar_plot(sheet_name):
        if sheet_name and 'data' in uploaded_data:
            try:
                # Load the selected sheet
                df = uploaded_data['data'].parse(sheet_name)

                # Normalize column names
                df.columns = df.columns.str.strip()

                # Validate required columns
                if 'Sample_name' not in df.columns or 'Reads_(%)' not in df.columns or 'Species.2' not in df.columns:
                    raise KeyError("'Sample_name', 'Reads_(%)', or 'Species.2' column not found in the DataFrame")

                # Group data by sample and category
                grouped_df = (
                    df.groupby(['Sample_name', 'Species.2'])['Reads_(%)']
                    .sum()
                    .reset_index()
                )

                # Pivot for stacking
                pivot_df = grouped_df.pivot(index='Sample_name', columns='Species.2', values='Reads_(%)').fillna(0)

                # Create stacked bar plot
                fig = go.Figure()
                for category in pivot_df.columns:
                    fig.add_trace(go.Bar(
                        name=category,
                        x=pivot_df.index,
                        y=pivot_df[category]
                    ))

                # Customize the layout
                fig.update_layout(
                    barmode='stack',  # Stacked bar mode
                    title=f"Kraken Stacked Bar Plot for {sheet_name}",
                    xaxis_title="Sample",
                    yaxis_title="Percentage of Reads (%)",
                    plot_bgcolor='#2c2f34',
                    paper_bgcolor='#1e1e1e',
                    font_color="white",
                    legend_title="Category"
                )
                return fig

            except Exception as e:
                print(f"Error generating Kraken stacked bar plot: {e}")
                return go.Figure().update_layout(title=f"Error: {e}")

        return go.Figure().update_layout(title="No Data to Display")



