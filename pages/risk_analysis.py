import streamlit as st
from database import crud
from utils.llm_client import invoke_llm_text

st.title("⚠️ Risk Analysis & Mitigation Advisor")

doc_id = st.session_state.active_doc_id
doc_name = st.session_state.active_doc_name

if not doc_id:
    st.warning("⚠️ Please select an active document in the sidebar to review risks.")
else:
    st.info(f"Auditing Risks for: **{doc_name}**")
    
    clauses = crud.get_clauses_for_document(doc_id)
    
    # ---------------------------------------------------------
    # AGENT 4: EXPLAINABLE RISK SCORING AGENT
    # ---------------------------------------------------------
    st.markdown("### 📊 Overall Document Risk Profile")
    if st.button("Generate Document Risk Score (Agent 4)"):
        with st.spinner("Agent 4 is analyzing the document for overall risk..."):
            try:
                from agents.risk_scoring_agent import assess_document_risk
                from utils.visualizer import generate_risk_gauge_chart
                
                risk_result = assess_document_risk(doc_name, clauses)
                
                # Display Gauge Chart
                gauge_fig = generate_risk_gauge_chart(risk_result.risk_score)
                st.plotly_chart(gauge_fig, use_container_width=True)
                
                # Display Risk Details
                st.markdown(f"**Risk Level:** `{risk_result.risk_level}`")
                
                st.markdown("#### 🧠 Agent Reasoning")
                st.info(risk_result.reasoning)
                
                st.markdown("#### 💡 Key Recommendations")
                st.success(risk_result.recommendations)
                
                if risk_result.affected_clauses:
                    st.markdown("#### 🔍 Affected Clauses")
                    for ac in risk_result.affected_clauses:
                        st.markdown(f"- {ac}")
                    
            except Exception as e:
                st.error(f"Failed to generate document risk score: {e}")

    st.divider()
    
    # Filter clauses with High/Medium risk
    risky_clauses = [c for c in clauses if c['risk_level'] in ('High', 'Medium')]
    
    if not risky_clauses:
        st.success("✅ Excellent! No High or Medium risk clauses were detected in this agreement.")
    else:
        st.markdown(f"Detected **{len(risky_clauses)}** risky clauses requiring review:")
        
        # Display each risky clause
        for c in risky_clauses:
            border_color = "#EF553B" if c['risk_level'] == "High" else "#FECB52"
            
            st.markdown(
                f"""
                <div style="
                    border: 1px solid {border_color}; 
                    border-radius: 8px; 
                    padding: 15px; 
                    margin-bottom: 20px;
                    background: rgba(255,255,255,0.01);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #FFFFFF;">⚠️ {c['section_name']}</h4>
                        <span style="
                            background-color: {border_color}; 
                            color: #121212; 
                            font-weight: bold; 
                            padding: 3px 10px; 
                            border-radius: 4px;
                            font-size: 0.8rem;
                        ">{c['risk_level'].upper()} RISK</span>
                    </div>
                    <div style="margin-bottom: 10px; font-size: 0.85rem;">
                        <strong style="color: #a0aabf;">Category:</strong> {c['risk_category']} | 
                        <strong style="color: #a0aabf;">Type:</strong> {c['classification']}
                    </div>
                    <p style="font-size: 0.95rem; line-height: 1.5; color: #CCCCCC; background: #0c0e14; padding: 12px; border-radius: 6px;">
                        {c['text_content']}
                    </p>
                    <div style="background: rgba(0, 0, 0, 0.2); padding: 12px; border-radius: 6px; border-left: 3px solid {border_color}; margin-top: 10px;">
                        <strong style="color: #FFFFFF;">Risk Explanation:</strong><br>
                        <span style="font-size: 0.9rem; color: #E0E0E0;">{c['explanation']}</span>
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            # Interactive LLM Mitigation Advisor
            with st.expander(f"💡 Request AI Mitigation Strategy for {c['section_name']}"):
                if st.button("Generate Mitigation", key=f"mitigate_{c['id']}"):
                    with st.spinner("Analyzing legal mitigations..."):
                        try:
                            system_prompt = "You are an expert contract lawyer providing risk mitigation advice."
                            user_prompt = (
                                f"The following clause was flagged as having a {c['risk_level']} risk "
                                f"in the category '{c['risk_category']}'.\n\n"
                                f"Clause Text:\n{c['text_content']}\n\n"
                                f"Risk Explanation:\n{c['explanation']}\n\n"
                                f"Please write a professional advice report:\n"
                                f"1. Explain the specific threat/exposure to our organization.\n"
                                f"2. Suggest a revised or marked-up version of the clause text to mitigate this risk.\n"
                                f"3. Detail negotiation strategies to present to the opposing party."
                            )
                            response = invoke_llm_text(system_prompt, user_prompt, temperature=0.2)
                            st.markdown("### 💡 Recommended Mitigation Strategy")
                            st.write(response)
                        except Exception as e:
                            st.error(f"Failed to generate mitigation: {e}")
