import plotly.graph_objects as go

# Function to create the bar plot
def generate_bar_plot(x, y, error_y=None):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x,
        y=y,
        error_y=dict(type='data', array=error_y, visible=error_y is not None)
    ))
    fig.update_layout(
        title="Coverage Bar Plot",
        xaxis_title="X-Axis",
        yaxis_title="Y-Axis",
        plot_bgcolor='#2c2f34',
        paper_bgcolor='#1e1e1e',
        font_color="white"
    )
    return fig

# Function to create a Sankey plot
def generate_sankey_plot(nodes, links):
    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=nodes),
        link=dict(source=links["source"], target=links["target"], value=links["value"])
    )])
    fig.update_layout(title_text="Taxonomic Classification Sankey", font_size=10)
    return fig
