import os
import tempfile
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from pyvis.network import Network
import streamlit as st

def generate_risk_pie_chart(risk_dist):
    """Generates a Plotly Pie Chart for risk level distribution."""
    # Ensure risk_dist is formatted nicely
    data = {"Risk Level": [], "Count": []}
    for level in ["High", "Medium", "Low", "None"]:
        data["Risk Level"].append(level)
        data["Count"].append(risk_dist.get(level, 0))
        
    colors = {
        "High": "#EF553B",    # Sleek Red
        "Medium": "#FECB52",  # Sleek Amber
        "Low": "#636EFA",     # Sleek Blue
        "None": "#00CC96"     # Sleek Green
    }
    
    fig = px.pie(
        data_frame=data,
        names="Risk Level",
        values="Count",
        color="Risk Level",
        color_discrete_map=colors,
        hole=0.4,
        title="Clause Risk Level Distribution"
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#E0E0E0',
        title_font_size=18,
        margin=dict(t=40, b=10, l=10, r=10)
    )
    return fig

def generate_category_bar_chart(clauses):
    """Generates a Plotly Bar Chart showing clause categories and their risk levels."""
    # clauses is a list of SQLite Row objects
    categories = {}
    for c in clauses:
        cat = c['risk_category'] or 'Uncategorized'
        level = c['risk_level'] or 'None'
        if cat not in categories:
            categories[cat] = {"High": 0, "Medium": 0, "Low": 0, "None": 0}
        categories[cat][level] += 1
        
    # Flatten database
    data = {"Category": [], "Risk Level": [], "Count": []}
    for cat, levels in categories.items():
        for lvl, val in levels.items():
            if val > 0:
                data["Category"].append(cat)
                data["Risk Level"].append(lvl)
                data["Count"].append(val)
                
    colors = {
        "High": "#EF553B",
        "Medium": "#FECB52",
        "Low": "#636EFA",
        "None": "#00CC96"
    }
    
    fig = px.bar(
        data_frame=data,
        x="Category",
        y="Count",
        color="Risk Level",
        color_discrete_map=colors,
        title="Risk Severity by Clause Category",
        barmode="stack"
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#E0E0E0',
        title_font_size=18,
        xaxis=dict(gridcolor='#333333'),
        yaxis=dict(gridcolor='#333333'),
        margin=dict(t=40, b=20, l=10, r=10)
    )
    return fig

def generate_risk_evolution_chart(versions_data):
    """Generates a trend chart of risk scores over different contract versions.
    
    versions_data: list of dicts/tuples with (version, average_risk_score, high_risk_count)
    """
    fig = go.Figure()
    
    versions = [v['version'] for v in versions_data]
    avg_scores = [v['avg_risk'] for v in versions_data]
    high_counts = [v['high_count'] for v in versions_data]
    
    fig.add_trace(go.Scatter(
        x=versions, y=avg_scores,
        mode='lines+markers',
        name='Avg Risk Score (0-10)',
        line=dict(color='#636EFA', width=3),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=versions, y=high_counts,
        mode='lines+markers',
        name='High Risk Clauses Count',
        line=dict(color='#EF553B', width=3, dash='dash'),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Contract Risk Profile Evolution",
        xaxis_title="Contract Version",
        yaxis_title="Metric Value",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#E0E0E0',
        title_font_size=18,
        xaxis=dict(gridcolor='#333333', tickmode='linear', tick0=1, dtick=1),
        yaxis=dict(gridcolor='#333333'),
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0.5)'),
        margin=dict(t=50, b=30, l=10, r=10)
    )
    return fig

def render_pyvis_graph(nodes, edges, directed=False):
    """Generates an HTML representation of a network using PyVis and renders it in Streamlit."""
    net = Network(
        height="500px",
        width="100%",
        bgcolor="#1E1E1E",
        font_color="#FFFFFF",
        directed=directed,
        notebook=False
    )
    
    # Configure options for sleek physics and styling
    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "shadow": true
      },
      "edges": {
        "color": {
          "inherit": true
        },
        "smooth": {
          "enabled": true,
          "type": "dynamic"
        }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -12000,
          "centralGravity": 0.3,
          "springLength": 95,
          "springConstant": 0.04,
          "damping": 0.09,
          "avoidOverlap": 0.5
        },
        "minVelocity": 0.75
      }
    }
    """)
    
    for n in nodes:
        net.add_node(
            n['id'], 
            label=n.get('label', str(n['id'])), 
            color=n.get('color', '#636EFA'), 
            title=n.get('title', ''), 
            size=n.get('size', 15)
        )
        
    for e in edges:
        net.add_edge(
            e['source'], 
            e['target'], 
            label=e.get('label', ''), 
            color=e.get('color', '#888888'), 
            width=e.get('width', 1)
        )
        
    # Write to a temporary file
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "graph.html")
        net.save_graph(path)
        with open(path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
    # Clean the HTML to avoid Streamlit iframe display issues
    st.components.v1.html(html_content, height=520, scrolling=True)

def generate_risk_gauge_chart(risk_score):
    """Generates a Plotly Gauge Chart for the overall Document Risk Score."""
    # Determine color based on score
    if risk_score < 40:
        bar_color = "#00CC96"  # Low risk - Green
    elif risk_score < 75:
        bar_color = "#FECB52"  # Medium risk - Amber
    else:
        bar_color = "#EF553B"  # High/Critical risk - Red

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = risk_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Document Risk Score", 'font': {'size': 24, 'color': '#FFFFFF'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#333333"},
            'bar': {'color': bar_color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#333333",
            'steps': [
                {'range': [0, 39], 'color': "rgba(0, 204, 150, 0.2)"},
                {'range': [40, 74], 'color': "rgba(254, 203, 82, 0.2)"},
                {'range': [75, 100], 'color': "rgba(239, 85, 59, 0.2)"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': risk_score
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#E0E0E0', 'family': "Arial"},
        margin=dict(t=50, b=20, l=20, r=20),
        height=350
    )
    
    return fig

def generate_impact_radar_chart(legal: int, financial: int, business: int, compliance: int):
    """Generates a Plotly Radar Chart for Agent 6 Impact Analysis."""
    categories = ['Legal Impact', 'Financial Impact', 'Business Impact', 'Compliance Impact']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=[legal, financial, business, compliance, legal], # close the loop
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(99, 110, 250, 0.5)',
        line=dict(color='#636EFA', width=3),
        name='Impact Profile'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickcolor="#333333",
                gridcolor="#333333",
                tickfont=dict(color="#888888")
            ),
            angularaxis=dict(
                gridcolor="#333333",
                tickfont=dict(color="#E0E0E0", size=14)
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#E0E0E0'},
        showlegend=False,
        margin=dict(t=40, b=40, l=40, r=40),
        height=400
    )
    
    return fig

