from pydantic import BaseModel, Field
from utils.llm_client import invoke_llm_structured


class ClauseImpactResult(BaseModel):
    clause: str = Field(description="The name or snippet of the clause being analyzed")
    legal_impact: int = Field(description="Legal Impact score from 0 to 100")
    financial_impact: int = Field(description="Financial Impact score from 0 to 100")
    business_impact: int = Field(description="Business Impact score from 0 to 100")
    compliance_impact: int = Field(description="Compliance Impact score from 0 to 100")


def analyze_clause_impact(section_name: str, clause_text: str) -> ClauseImpactResult:
    """Agent 6: Clause Impact Analysis Agent."""
    system_instruction = (
        "You are an expert Clause Impact Analysis Agent. "
        "Review the provided clause and assign a score from 0 to 100 across four impact dimensions: "
        "1. Legal Impact: Potential for liability, breach, or legal disputes. "
        "2. Financial Impact: Direct costs, penalties, lost revenue, or payment obligations. "
        "3. Business Impact: Operational constraints, required resources, or strategic limitations. "
        "4. Compliance Impact: Regulatory requirements, reporting obligations, or audit risks."
    )
    prompt = f"Clause Heading: {section_name}\nClause Text:\n{clause_text}"

    try:
        return invoke_llm_structured(system_instruction, prompt, ClauseImpactResult, temperature=0.1)
    except Exception as e:
        print(f"Error in impact agent: {e}")
        return ClauseImpactResult(
            clause=section_name,
            legal_impact=0, financial_impact=0, business_impact=0, compliance_impact=0,
        )
