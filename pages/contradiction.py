import streamlit as st
from database import crud
from agents.contradiction_agent import find_contradictions

st.title("⚖️ Contradiction & Inconsistency Finder")
st.markdown("Identifies conflicting statements, inconsistent obligations, and contradictory terms within the document using Agent 5.")

doc_id = st.session_state.active_doc_id
doc_name = st.session_state.active_doc_name

if not doc_id:
    st.warning("⚠️ Please select an active document in the sidebar to review contradictions.")
else:
    st.info(f"Checking Contradictions for: **{doc_name}**")
    
    clauses = crud.get_clauses_for_document(doc_id)
    
    if st.button("Analyze Contradictions with AI (Agent 5)"):
        with st.spinner("Agent 5 is analyzing the document for contradictions..."):
            contradictions = find_contradictions(clauses)
            
            if not contradictions:
                st.success("✅ No conflicting clauses or internal contradictions were detected in this agreement!")
            else:
                st.markdown(f"### Found **{len(contradictions)}** internal conflicts:")
                
                for i, c in enumerate(contradictions):
                    sev_color = "#FECB52"  # Medium
                    if c.severity.capitalize() == "High":
                        sev_color = "#EF553B"
                    elif c.severity.capitalize() == "Low":
                        sev_color = "#636EFA"
                    
                    with st.expander(f"⚠️ {c.contradiction_type} - {c.severity.upper()} Severity", expanded=True):
                        st.markdown(
                            f"""
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                <span style="
                                    background-color: {sev_color}; 
                                    color: #121212; 
                                    font-weight: bold; 
                                    padding: 3px 10px; 
                                    border-radius: 4px;
                                    font-size: 0.8rem;
                                ">{c.severity.upper()} SEVERITY</span>
                                <strong style="color: #a0aabf;">{c.contradiction_type}</strong>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                        
                        st.markdown("#### 🔍 Affected Clauses")
                        for ac in c.affected_clauses:
                            st.markdown(f"- {ac}")
                            
                        st.markdown(
                            f"""
                            <div style="background: rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 6px; border-left: 3px solid {sev_color}; margin-top: 10px; margin-bottom: 15px;">
                                <strong style="color: #E0E0E0;">Explanation of Conflict:</strong><br>
                                <span style="font-size: 0.95rem; color: #CCCCCC;">{c.explanation}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        st.markdown("#### 💡 Suggested Resolution")
                        st.success(c.resolution)
