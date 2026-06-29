import streamlit as st
from database import crud
from utils.visualizer import render_pyvis_graph
from agents.knowledge_graph_agent import extract_knowledge_graph

st.title("🕸️ Legal Entity Knowledge Graph (Agent 11)")
st.markdown("Interactive visualization showing the key parties, signing dates, governing jurisdictions, obligations, payments, and penalties.")

doc_id = st.session_state.active_doc_id
doc_name = st.session_state.active_doc_name

if not doc_id:
    st.warning("⚠️ Please select an active document in the sidebar to generate the knowledge graph.")
else:
    st.info(f"Generating Knowledge Graph for: **{doc_name}**")
    
    # Retrieve clauses text to construct the document text
    clauses = crud.get_clauses_for_document(doc_id)
    if not clauses:
        st.info("No text content found for this document.")
    else:
        full_text = "\n".join([c['text_content'] for c in clauses])
        
        # Limit text length to avoid token limits on very large contracts
        if len(full_text) > 40000:
            full_text = full_text[:40000] + "\n...(truncated for analysis)"
            
        if st.button("Generate Graph (Agent 11)"):
            with st.spinner("Agent 11 is extracting Entities, Obligations, Payments, and Penalties..."):
                try:
                    graph_data = extract_knowledge_graph(doc_name, full_text)
                    
                    if not graph_data["nodes"]:
                        st.warning("No nodes were extracted from the document.")
                    else:
                        st.markdown("### 🔍 Interactive Network Map")
                        st.caption("Drag nodes to rearrange, zoom in/out, or hover to inspect relationships.")
                        
                        # Display network
                        render_pyvis_graph(graph_data["nodes"], graph_data["edges"], directed=False)
                        
                        # Legend display
                        st.markdown(
                            """
                            **Legend:**
                            - 🔵 **Blue**: Signatory Parties
                            - 🟢 **Green**: Jurisdictions / Governing Law
                            - 🟡 **Yellow**: Obligations, Dates, & Payments
                            - 🔴 **Red**: Penalties & Key Risks
                            """
                        )
                        
                        crud.add_audit_log("knowledge_graph_generation", f"Generated knowledge graph for document '{doc_name}' with Agent 11")
                except Exception as e:
                    st.error(f"Failed to generate knowledge graph: {e}")
