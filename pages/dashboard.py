import streamlit as st
from database import crud
from utils import visualizer

st.markdown("<h1 style='text-align: center; color: #636EFA;'>LQ-LegalAI Platform</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #a0aabf;'>Next-generation AI Legal Intelligence Platform powered by LangGraph, Groq & MongoDB</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

st.title("📊 Platform Dashboard")
# Get active document from session state
doc_id = st.session_state.active_doc_id
doc_name = st.session_state.active_doc_name

if doc_id:
    st.info(f"Viewing metrics for Active Document: **{doc_name}**")
    metrics = crud.get_dashboard_metrics(doc_id=doc_id)
    clauses = crud.get_clauses_for_document(doc_id=doc_id)
else:
    st.warning("No active document selected. Showing aggregate workspace metrics.")
    metrics = crud.get_dashboard_metrics()
    # For aggregate workspace, fetch clauses from all documents
    clauses = []
    documents = crud.get_all_documents()
    for doc in documents:
        clauses.extend(crud.get_clauses_for_document(doc['id']))

# Visual Metrics Grid
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Documents", value=metrics["total_documents"])
with col2:
    st.metric(label="Total Clauses", value=metrics["total_clauses"])
with col3:
    st.metric(label="Risky Clauses (High/Med)", value=metrics["risky_clauses"])
with col4:
    st.metric(label="Contradictions", value=metrics["total_contradictions"])

st.markdown("---")

# Visual Charts
if clauses:
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        pie_fig = visualizer.generate_risk_pie_chart(metrics["risk_distribution"])
        st.plotly_chart(pie_fig, use_container_width=True)
    with chart_col2:
        bar_fig = visualizer.generate_category_bar_chart(clauses)
        st.plotly_chart(bar_fig, use_container_width=True)
else:
    st.info("Upload and parse a document to view risk distributions.")

st.markdown("---")

# Recent Audit Logs
st.subheader("📜 Recent System & Audit Activity")
logs = crud.get_audit_logs(limit=10)
if logs:
    for log in logs:
        # Style logs depending on severity/type of action
        icon = "⚙️"
        if "upload" in log['action']:
            icon = "📤"
        elif "risk" in log['action'] or "contradiction" in log['action']:
            icon = "⚠️"
        elif "update" in log['action']:
            icon = "✏️"
            
        st.markdown(f"**{icon} {log['action'].upper()}** — *{log['timestamp']}*")
        st.write(log['details'])
        st.markdown("---")
else:
    st.text("No audit logs available.")
