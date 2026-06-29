import os
import hashlib
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

from agents.parser_agent import parse_document
from agents.clause_identifier_agent import identify_clauses
from agents.importance_agent import assess_clause_importance
from agents.analyzer_agent import analyze_clause
from agents.risk_scoring_agent import assess_document_risk
from agents.contradiction_agent import find_contradictions
from agents.impact_agent import analyze_clause_impact
from agents.knowledge_graph_agent import extract_knowledge_graph
from agents.dependency_agent import extract_clause_dependencies
from agents.audit_agent import perform_macro_audit

from database import crud
from vectorstore import chroma_client


class AgentState(TypedDict):
    file_path: str
    doc_name: str
    doc_hash: str
    doc_id: int
    raw_sections: List[Dict[str, Any]]
    identified_clauses: List[Dict[str, Any]]
    db_clauses: List[Dict[str, Any]]
    contradictions: List[Dict[str, Any]]
    audit_score: int
    error: str


def get_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def parse_document_node(state: AgentState) -> Dict[str, Any]:
    file_path = state["file_path"]
    doc_name = os.path.basename(file_path)
    try:
        doc_hash = get_file_hash(file_path)
        existing_doc = crud.get_document_by_hash(doc_hash)
        if existing_doc:
            return {"doc_name": doc_name, "doc_hash": doc_hash, "doc_id": existing_doc['id'],
                    "error": "Document already analyzed."}

        raw_sections = parse_document(file_path)
        doc_id = crud.add_document(doc_name, file_path, doc_hash)
        return {"doc_name": doc_name, "doc_hash": doc_hash, "doc_id": doc_id,
                "raw_sections": raw_sections, "error": ""}
    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}"}


def clause_identification_node(state: AgentState) -> Dict[str, Any]:
    if state.get("error"):
        return {}
    full_text = "\n".join([s['text_content'] for s in state["raw_sections"]])
    try:
        identified_objects = identify_clauses(full_text)
        identified = []
        for obj in identified_objects:
            identified.append({
                "section_name": obj.clause_type,
                "text_content": obj.clause_text,
                "classification": obj.clause_type,
                "confidence_score": obj.confidence_score,
            })

        if not identified:
            for sec in state["raw_sections"]:
                identified.append({
                    "section_name": sec["section_name"],
                    "text_content": sec["text_content"],
                    "classification": "General",
                })
    except Exception as e:
        print(f"Clause ID failed: {e}")
        identified = [
            {"section_name": s["section_name"], "text_content": s["text_content"], "classification": "General"}
            for s in state["raw_sections"]
        ]

    return {"identified_clauses": identified}


def importance_detection_node(state: AgentState) -> Dict[str, Any]:
    if state.get("error"):
        return {}
    clauses = state["identified_clauses"]

    # Sequential processing
    for c in clauses:
        try:
            res = assess_clause_importance(c.get("section_name", "Clause"), c["text_content"])
            c["importance_score"] = res.importance_score
            c["importance_category"] = res.importance_category
        except Exception:
            c["importance_score"] = 0
            c["importance_category"] = "Informational"

    return {"identified_clauses": clauses}


def risk_analysis_node(state: AgentState) -> Dict[str, Any]:
    if state.get("error"):
        return {}
    clauses = state["identified_clauses"]

    for c in clauses:
        try:
            res = analyze_clause(c.get("section_name", "Clause"), c["text_content"])
            c["risk_level"] = res.risk_level
            c["risk_category"] = res.risk_category
            c["explanation"] = res.explanation
            c["simplification"] = res.simplification
        except Exception:
            c["risk_level"] = "None"
            c["risk_category"] = "Unknown"
            c["explanation"] = "Error analyzing risk"
            c["simplification"] = c["text_content"]

    db_clauses = []
    for sec in clauses:
        clause_id = crud.add_clause(
            doc_id=state["doc_id"],
            section_name=sec.get("section_name", "Clause"),
            text_content=sec["text_content"],
            page_num=sec.get("page_num", 1),
            classification=sec.get("classification", "General"),
            risk_category=sec.get("risk_category", "Unknown"),
            risk_level=sec.get("risk_level", "None"),
            explanation=sec.get("explanation", ""),
            simplification=sec.get("simplification", ""),
        )
        sec["id"] = clause_id
        db_clauses.append(sec)

    try:
        doc_risk = assess_document_risk(state["doc_name"], db_clauses)
        crud.add_audit_log("document_risk",
                           f"Doc {state['doc_id']} scored {doc_risk.risk_score}/100 ({doc_risk.risk_level})")
    except Exception:
        pass

    chroma_client.add_clauses_to_vectorstore(db_clauses)
    return {"db_clauses": db_clauses}


def contradiction_detection_node(state: AgentState) -> Dict[str, Any]:
    if state.get("error"):
        return {}
    try:
        contradictions = find_contradictions(state["db_clauses"])
        saved_contradictions = []
        clause_ids = [c["id"] for c in state["db_clauses"]]
        for item in contradictions:
            id_1 = clause_ids[0] if clause_ids else 0
            id_2 = clause_ids[1] if len(clause_ids) > 1 else id_1
            for i, c in enumerate(state["db_clauses"]):
                for ac in item.affected_clauses:
                    if (c.get("section_name", "").lower() in ac.lower()
                            or ac.lower() in c.get("text_content", "").lower()[:200]):
                        if i == 0 or id_1 == clause_ids[0]:
                            id_1 = c["id"]
                        else:
                            id_2 = c["id"]
                            break

            c_id = crud.add_contradiction(
                doc_id=state["doc_id"],
                clause_id_1=id_1, clause_id_2=id_2,
                explanation=item.explanation, severity=item.severity,
            )
            saved_contradictions.append({"id": c_id, "severity": item.severity})
        return {"contradictions": saved_contradictions}
    except Exception as e:
        print(f"Error in contradiction detection: {e}")
        return {"contradictions": []}


def impact_analysis_node(state: AgentState) -> Dict[str, Any]:
    high_risk_clauses = [c for c in state["db_clauses"] if c.get("risk_level") == "High"]
    for c in high_risk_clauses[:2]:
        try:
            analyze_clause_impact(c.get("section_name", "Clause"), c["text_content"])
        except Exception:
            pass
    return {}


def knowledge_graph_node(state: AgentState) -> Dict[str, Any]:
    full_text = "\n".join([c['text_content'] for c in state["db_clauses"]][:5])
    try:
        extract_knowledge_graph(state["doc_name"], full_text)
    except Exception:
        pass
    return {}


def dependency_graph_node(state: AgentState) -> Dict[str, Any]:
    try:
        extract_clause_dependencies(state["db_clauses"])
    except Exception:
        pass
    return {}


def audit_agent_node(state: AgentState) -> Dict[str, Any]:
    try:
        res = perform_macro_audit(state["doc_name"], state["db_clauses"], state["contradictions"])
        crud.add_audit_log("pipeline_audit", f"Orchestrator finished. Audit Score: {res.audit_score}")
        return {"audit_score": res.audit_score}
    except Exception:
        return {"audit_score": 0}


def route_after_contradiction(state: AgentState) -> str:
    high_risks = any(c.get("risk_level") == "High" for c in state.get("db_clauses", []))
    has_contradictions = len(state.get("contradictions", [])) > 0
    if high_risks or has_contradictions:
        return "impact_analysis"
    else:
        return "audit_agent"


def build_orchestrator():
    workflow = StateGraph(AgentState)

    workflow.add_node("parse_document", parse_document_node)
    workflow.add_node("clause_identification", clause_identification_node)
    workflow.add_node("importance_detection", importance_detection_node)
    workflow.add_node("risk_analysis", risk_analysis_node)
    workflow.add_node("contradiction_detection", contradiction_detection_node)
    workflow.add_node("impact_analysis", impact_analysis_node)
    workflow.add_node("knowledge_graph", knowledge_graph_node)
    workflow.add_node("dependency_graph", dependency_graph_node)
    workflow.add_node("audit_agent", audit_agent_node)

    workflow.set_entry_point("parse_document")
    workflow.add_edge("parse_document", "clause_identification")
    workflow.add_edge("clause_identification", "importance_detection")
    workflow.add_edge("importance_detection", "risk_analysis")
    workflow.add_edge("risk_analysis", "contradiction_detection")

    workflow.add_conditional_edges(
        "contradiction_detection",
        route_after_contradiction,
        {"impact_analysis": "impact_analysis", "audit_agent": "audit_agent"},
    )

    workflow.add_edge("impact_analysis", "knowledge_graph")
    workflow.add_edge("knowledge_graph", "dependency_graph")
    workflow.add_edge("dependency_graph", "audit_agent")
    workflow.add_edge("audit_agent", END)

    return workflow.compile()


def run_orchestration(file_path: str) -> Dict[str, Any]:
    app = build_orchestrator()
    initial_state = {
        "file_path": file_path,
        "doc_name": "", "doc_hash": "", "doc_id": -1,
        "raw_sections": [], "identified_clauses": [],
        "db_clauses": [], "contradictions": [],
        "audit_score": 0, "error": "",
    }
    return app.invoke(initial_state)
