from pydantic import BaseModel, Field
from typing import List, Dict, Any
from utils.llm_client import invoke_llm_structured


class DocumentRiskScoreResult(BaseModel):
    risk_score: int = Field(description="Overall risk score from 0 to 100.")
    risk_level: str = Field(description="Risk level: 'Low', 'Medium', 'High', or 'Critical'.")
    affected_clauses: List[str] = Field(description="List of clause headings that primarily contributed to the risk score.")
    reasoning: str = Field(description="Detailed explanation of why this risk score was assigned.")
    recommendations: str = Field(description="Actionable recommendations to mitigate the identified risks.")


def assess_document_risk(document_name: str, clauses_data: List[Dict[str, Any]]) -> DocumentRiskScoreResult:
    """Uses Groq LLM to evaluate overall document risk based on its clauses."""
    system_instruction = (
        "You are an expert Chief Legal Officer reviewing a contract. "
        "Analyze the provided clauses and their risk categories. "
        "Calculate an aggregate 'risk_score' from 0 to 100. "
        "Assign a 'risk_level' from: Low, Medium, High, Critical. "
        "Identify the most problematic 'affected_clauses'. "
        "Provide detailed 'reasoning' and actionable 'recommendations'."
    )

    clauses_text = ""
    for i, row in enumerate(clauses_data):
        c = dict(row) if hasattr(row, 'keys') else row
        section = c.get('section_name', f"Clause {i+1}")
        text = c.get('text_content', '')
        prelim_risk = c.get('risk_level', 'Unknown')
        clauses_text += f"\n--- {section} (Preliminary Risk: {prelim_risk}) ---\n{text}\n"

    prompt = f"Document Name: {document_name}\n\nDocument Clauses:\n{clauses_text}"

    return invoke_llm_structured(system_instruction, prompt, DocumentRiskScoreResult, temperature=0.1)
