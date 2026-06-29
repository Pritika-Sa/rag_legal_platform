from pydantic import BaseModel, Field
from typing import List, Dict, Any
from utils.llm_client import invoke_llm_structured


class ContradictionItem(BaseModel):
    contradiction_type: str = Field(description="Type: Conflicting Clauses, Inconsistent Obligations, Contradictory Dates, Payment Conflicts, or Timeline Conflicts.")
    severity: str = Field(description="Severity: High, Medium, or Low")
    affected_clauses: List[str] = Field(description="List of section names or clause snippets that are in conflict")
    explanation: str = Field(description="Detailed explanation of why these clauses conflict")
    resolution: str = Field(description="Suggested resolution or redrafting advice")


class ContradictionReport(BaseModel):
    contradictions: List[ContradictionItem] = Field(description="List of all detected contradictions")


def find_contradictions(clauses: List[Dict[str, Any]]) -> List[ContradictionItem]:
    """Agent 5: Legal Contradiction Detection Agent."""
    if len(clauses) < 2:
        return []

    system_instruction = (
        "You are an expert contract auditor. Review the provided list of contract clauses. "
        "Detect: 1. Conflicting clauses, 2. Inconsistent obligations, 3. Contradictory dates, "
        "4. Payment conflicts, 5. Timeline conflicts. "
        "Identify the 'contradiction_type', 'severity' (High, Medium, Low), 'affected_clauses', "
        "provide a clear 'explanation', and suggest a 'resolution'."
    )

    formatted_clauses = ""
    for i, row in enumerate(clauses):
        c = dict(row) if hasattr(row, 'keys') else row
        section = c.get('section_name', f"Clause {i+1}")
        text = c.get('text_content', '')
        formatted_clauses += f"--- {section} ---\n{text}\n\n"

    prompt = f"Please review these clauses and identify all internal contradictions:\n\n{formatted_clauses}"

    try:
        result = invoke_llm_structured(system_instruction, prompt, ContradictionReport, temperature=0.1)
        return result.contradictions
    except Exception as e:
        print(f"Error in contradiction agent: {e}")
        return []
