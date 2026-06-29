from pydantic import BaseModel, Field
from typing import List, Dict, Any
from utils.llm_client import invoke_llm_structured


class DependencyEdge(BaseModel):
    source_clause_id: int = Field(description="The integer ID of the source clause")
    target_clause_id: int = Field(description="The integer ID of the target clause it depends on")
    dependency_type: str = Field(description="Nature of the dependency (e.g., 'triggers', 'references', 'limits')")
    explanation: str = Field(description="Brief explanation of why this dependency exists")


class DependencyGraph(BaseModel):
    edges: List[DependencyEdge]


def extract_clause_dependencies(clauses: List[Dict[str, Any]]) -> List[DependencyEdge]:
    """Agent 12: Clause Dependency Graph Agent."""
    clause_text_list = ""
    for c in clauses:
        clause_text_list += f"ID: {c['id']} | Title: {c['section_name']}\nText: {c.get('text_content', '')}\n\n"

    system_instruction = (
        "You are an expert Legal Clause Dependency Agent. Analyze the provided clauses and identify "
        "semantic dependencies and legal relationships between them. "
        "Examples: 'Termination' triggers 'Liability', 'Payment' is subject to 'Penalty'. "
        "Return a list of directed edges using the exact integer IDs provided."
    )
    prompt = f"Analyze the following contract clauses and extract their dependencies:\n\n{clause_text_list}"

    try:
        result = invoke_llm_structured(system_instruction, prompt, DependencyGraph)
        return result.edges
    except Exception as e:
        print(f"Error in dependency agent: {e}")
        return []
