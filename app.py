import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*HF_TOKEN.*")
warnings.filterwarnings("ignore", message=".*huggingface_hub.*cache.*symlinks.*")

import streamlit as st
from dotenv import load_dotenv
from database.models import init_db
from database import crud

load_dotenv()

# Page configurations
st.set_page_config(
    page_title="LQ-LegalAI | Legal Intelligence Platform",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling inject
st.markdown("""
<style>
    /* Dark glassmorphic background styling */
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #161a24 100%);
        color: #e0e0e0;
    }
    
    /* Elegant Title and Header styling */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Outfit', 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar styling override */
    [data-testid="stSidebar"] {
        background-color: #0c0e14 !important;
        border-right: 1px solid #222b3c;
    }
    
    /* Premium visual KPI cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        transition: transform 0.3s ease, border-color 0.3s ease;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: rgba(99, 110, 250, 0.5);
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 800;
        color: #636EFA;
        margin-bottom: 5px;
    }
    .metric-title {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #a0aabf;
    }
    
    /* Gradient Button */
    .stButton>button {
        background: linear-gradient(90deg, #5e60ce 0%, #636EFA 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(99, 110, 250, 0.3) !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 110, 250, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# 1. Initialize MongoDB Database
init_db()

# Ensure directories exist
os.makedirs(os.getenv("UPLOADS_DIR", "uploads"), exist_ok=True)
os.makedirs(os.getenv("REPORTS_DIR", "reports"), exist_ok=True)

# Global Session State
if "active_doc_id" not in st.session_state:
    st.session_state.active_doc_id = None
if "active_doc_name" not in st.session_state:
    st.session_state.active_doc_name = None

# Sidebar document selector
st.sidebar.markdown("<h2 style='text-align: center; color: #636EFA;'>⚖️ LQ-LegalAI</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

documents = crud.get_all_documents()
if documents:
    doc_options = {doc['id']: doc['name'] for doc in documents}
    
    # Selected doc configuration
    selected_id = st.sidebar.selectbox(
        "Active Workspace Document:",
        options=list(doc_options.keys()),
        format_func=lambda x: doc_options[x]
    )
    
    # Store in session state
    st.session_state.active_doc_id = selected_id
    st.session_state.active_doc_name = doc_options[selected_id]
else:
    st.sidebar.warning("No documents uploaded yet.")
    st.session_state.active_doc_id = None
    st.session_state.active_doc_name = None

st.sidebar.markdown("---")
st.sidebar.info("💡 Select a document above, then navigate using the pages menu to audit and interact.")


# Define Pages
pg_dashboard = st.Page("pages/dashboard.py", title="1. Dashboard", icon="📊", default=True)
pg_upload = st.Page("pages/upload.py", title="2. Upload Document", icon="📤")
pg_clause = st.Page("pages/clause_analysis.py", title="3. Clause Analysis", icon="📑")
pg_risk = st.Page("pages/risk_analysis.py", title="4. Risk Analysis", icon="⚠️")
pg_contradiction = st.Page("pages/contradiction.py", title="5. Contradiction Detection", icon="⚡")
pg_simplification = st.Page("pages/simplification.py", title="6. Simplification", icon="✨")
pg_translation = st.Page("pages/translation.py", title="7. Translation", icon="🌍")
pg_qa = st.Page("pages/legal_qa.py", title="8. Legal Q&A", icon="💬")
pg_comparison = st.Page("pages/comparison.py", title="9. Comparison Center", icon="🔄")
pg_kg = st.Page("pages/knowledge_graph.py", title="10. Knowledge Graph", icon="🕸️")
pg_dg = st.Page("pages/dependency_graph.py", title="11. Dependency Graph", icon="🔗")
pg_re = st.Page("pages/risk_evolution.py", title="12. Risk Evolution", icon="📈")
pg_vh = st.Page("pages/version_history.py", title="13. Version History", icon="🕒")
pg_audit = st.Page("pages/audit_report.py", title="14. Audit Report", icon="📋")

pg = st.navigation({
    "Core Platform": [pg_dashboard, pg_upload],
    "Analytics & Risk": [pg_clause, pg_risk, pg_contradiction, pg_comparison],
    "AI Tools": [pg_simplification, pg_translation, pg_qa],
    "Visualizations": [pg_kg, pg_dg, pg_re],
    "Governance": [pg_vh, pg_audit]
})

pg.run()
