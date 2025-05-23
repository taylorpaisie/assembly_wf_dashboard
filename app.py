from dash import Dash, html, Output, Input
import dash_bootstrap_components as dbc
from layouts import create_layout, get_file_upload, get_data_display, get_sankey_section, get_taxonomy_analysis_section
from callbacks import register_callbacks
from info_layouts import get_about_section, get_how_to_use_section  # Import new layouts

# Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

# Global variable for uploaded data
uploaded_data = {}

# Define app layout
app.layout = create_layout()

# Register callbacks
register_callbacks(app, uploaded_data)

# Callback to switch tabs and ensure correct components are loaded
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab")
)
def update_tab_content(active_tab):
    if active_tab == "tab-about":
        return get_about_section()
    elif active_tab == "tab-how-to-use":
        return get_how_to_use_section()
    elif active_tab == "tab-taxonomy-analysis":
        return get_taxonomy_analysis_section()
    else:
        # Dashboard should only have file upload and data display
        return html.Div([
            get_file_upload(),  
            get_data_display(),
        ])


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True, port=8052)
