from dash import Dash, html
import dash_bootstrap_components as dbc
from layouts import get_file_upload, get_data_display, get_sankey_section
from callbacks import register_callbacks

# Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])
server = app.server

# Global variable for uploaded data
uploaded_data = {}

# Define app layout
app.layout = dbc.Container([
    get_file_upload(),      # File upload section
    get_data_display(),     # Spreadsheet data and bar plot section
    html.Br(),              # Add space between sections (Fix: Now html is imported)
    get_sankey_section()    # Sankey plot section (Moved Below)
], fluid=True, style={"backgroundColor": "#1e1e1e", "paddingBottom": "20px"})

# Register callbacks
register_callbacks(app, uploaded_data)

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True, port=8052)


