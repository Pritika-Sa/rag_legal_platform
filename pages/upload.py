import os
import streamlit as st
from agents.orchestrator import run_orchestration
from database import crud

st.title("📤 Upload & Parse Legal Documents")
st.markdown("Upload a PDF or Word (.docx) contract to parse its clauses and perform risk analysis.")

uploaded_file = st.file_uploader("Choose a legal file", type=["pdf", "docx"])

if uploaded_file is not None:
    # Save the file locally
    uploads_dir = os.getenv("UPLOADS_DIR", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    file_path = os.path.join(uploads_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.success(f"File saved successfully to {file_path}")
    
    # Process file button
    if st.button("🚀 Analyze Document"):
        with st.spinner("Executing Multi-Agent LangGraph Orchestration... (Parsing & Risk Assessment)"):
            try:
                # Run the LangGraph orchestration flow
                result = run_orchestration(file_path)
                
                if result.get("error") and "already analyzed" in result["error"].lower():
                    st.warning("⚠️ This document has already been analyzed and is available in the workspace.")
                    # Set as active anyway
                    st.session_state.active_doc_id = result["doc_id"]
                    st.session_state.active_doc_name = uploaded_file.name
                    st.rerun()
                elif result.get("error"):
                    st.error(f"❌ Analysis failed: {result['error']}")
                else:
                    st.success("🎉 Multi-agent analysis complete!")
                    st.session_state.active_doc_id = result["doc_id"]
                    st.session_state.active_doc_name = uploaded_file.name
                    
                    st.info(f"Active workspace document set to **{uploaded_file.name}**. Head to the Dashboard or Clause Analysis pages to view results.")
                    crud.add_audit_log(
                        "analysis_completed", 
                        f"Completed multi-agent processing for '{uploaded_file.name}'"
                    )
                    # Force sidebar refresh
                    st.rerun()
            except Exception as e:
                st.error(f"❌ An error occurred during orchestrator execution: {e}")
                
st.markdown("---")

# List existing documents in system
st.subheader("signed agreements in Workspace")
docs = crud.get_all_documents()
if docs:
    for doc in docs:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"📄 **{doc['name']}** — uploaded on {doc['upload_date']}")
        with col2:
            if st.button("Set Active", key=f"set_{doc['id']}"):
                st.session_state.active_doc_id = doc['id']
                st.session_state.active_doc_name = doc['name']
                st.rerun()
else:
    st.info("No documents analyzed yet. Please upload a file to begin.")
