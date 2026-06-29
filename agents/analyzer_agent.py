from pydantic import BaseModel, Field
from typing import List
from utils.llm_client import invoke_llm_structured


class EntityRelation(BaseModel):
    source: str = Field(description="The source entity or party")
    relation: str = Field(description="The action or link, e.g., 'must pay', 'indemnifies'")
    target: str = Field(description="The target entity, party, or location")


class ClauseAnalysisResult(BaseModel):
    classification: str = Field(description="The clause classification (e.g., Liability, Termination, Confidentiality)")
    risk_category: str = Field(description="The category of risk (e.g., Financial, Compliance, Operational, Legal, None)")
    risk_level: str = Field(description="Severity: High, Medium, Low, or None")
    explanation: str = Field(description="Why this risk level was assigned and the legal implications")
    simplification: str = Field(description="A redrafted version of this clause in plain English")
    entities: List[EntityRelation] = Field(description="Extracted key entities and their relationships")
    dependencies: List[str] = Field(description="Any section names or numbers that this clause references")


def analyze_clause(section_name: str, text_content: str) -> ClauseAnalysisResult:
    """Invokes Groq LLM to analyze a single contract clause and return structured results."""
    system_instruction = (
        "You are an expert legal counsel and risk analyst. Analyze the provided contract clause. "
        "Classify the clause, assess its risk profile, simplify its terms, and extract entities "
        "and relationships for graph mapping. If the clause has no significant risk, set risk_level to 'None'."
    )
    prompt = f"Section Heading: {section_name}\nClause Content:\n{text_content}"

    return invoke_llm_structured(system_instruction, prompt, ClauseAnalysisResult)
