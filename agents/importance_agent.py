from pydantic import BaseModel, Field
from utils.llm_client import invoke_llm_structured


class ClauseImportanceResult(BaseModel):
    importance_score: int = Field(description="Importance score between 0 and 100.")
    importance_category: str = Field(description="Importance category: 'Critical', 'Important', or 'Informational'.")
    legal_significance_analysis: str = Field(description="Detailed evaluation of legal significance.")
    financial_impact_analysis: str = Field(description="Detailed evaluation of financial impact.")
    reasoning: str = Field(description="Summary explanation for the final category classification.")


def assess_clause_importance(section_name: str, clause_text: str) -> ClauseImportanceResult:
    """Uses Groq LLM to evaluate clause significance and classify it."""
    system_instruction = (
        "You are an expert corporate legal auditor. Evaluate the importance of the provided contract clause. "
        "Calculate a score from 0 to 100 and map it to an importance_category: "
        "1. 'Critical' (score 75-100): High legal exposure, financial liability caps, indemnification, termination triggers, governing law. "
        "2. 'Important' (score 40-74): Payment obligations, confidentiality limits, warranty terms, compliance regulations. "
        "3. 'Informational' (score 0-39): Boilerplate terms, notices, preambles, signatures, contact information."
    )
    prompt = f"Section Heading: {section_name}\nClause Content:\n{clause_text}"

    return invoke_llm_structured(system_instruction, prompt, ClauseImportanceResult)
