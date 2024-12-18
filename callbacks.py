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
        ],
        Input('upload-data', 'contents'),
        State('upload-data', 'filename'),
    )
    def handle_file_upload(contents, filename):
        if contents is not None:
            try:
                print(f"Processing file: {filename}")
                content_type, content_string = contents.split(',')
                decoded = io.BytesIO(base64.b64decode(content_string))

                # Load the uploaded Excel file
                excel_data = pd.ExcelFile(decoded)
                uploaded_data['data'] = excel_data
                sheets = excel_data.sheet_names

                if not sheets:
                    return "No sheets found in the uploaded file.", [], []

                # Generate options for dropdowns
                sheet_options = [{'label': sheet, 'value': sheet} for sheet in sheets]
                return f"Uploaded: {filename}", sheet_options, sheet_options
            except Exception as e:
                print(f"Error processing file: {e}")
                return f"Error uploading file: {e}", [], []
        return "No file uploaded yet", [], []

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

                # Identify numeric columns and columns with extractable numeric patterns
                numeric_cols = df.select_dtypes(include='number').columns.tolist()
                pattern_based_cols = [
                    col for col in df.columns
                    if df[col].astype(str).str.contains(r'^[\d.]+x_.*[\d.]+x$', na=False).any()
                ]

                # Combine numeric and pattern-based columns
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
                # Load the selected sheet into a DataFrame
                df = uploaded_data['data'].parse(sheet_name)

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
