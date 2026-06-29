from pydantic import BaseModel, Field
from utils.llm_client import invoke_llm_structured


class VersionIntelligenceResult(BaseModel):
    clause_changes: str = Field(description="Summary of the core legal language changes made")
    risk_changes: str = Field(description="Analysis of how these changes impact legal and financial risk")
    compliance_changes: str = Field(description="Impact on regulatory or compliance requirements")
    jurisdiction_changes: str = Field(description="Shifts in governing law or venue from the edit")
    obligation_changes: str = Field(description="Changes to duties, timelines, or deliverables")


def analyze_version_diff(old_text: str, new_text: str) -> VersionIntelligenceResult:
    """Agent 15: Version Controlled Legal Intelligence Agent."""
    system_instruction = (
        "You are an expert Version Controlled Legal Intelligence Agent. "
        "Analyze the differences between the original and modified clause text. "
        "Provide a structured assessment of changes and their implications on Risk, Compliance, Jurisdiction, and Obligations. "
        "If a category is unaffected, explicitly state 'No material change'."
    )
    prompt = f"--- ORIGINAL VERSION ---\n{old_text}\n\n--- MODIFIED VERSION ---\n{new_text}"

    try:
        return invoke_llm_structured(system_instruction, prompt, VersionIntelligenceResult)
    except Exception as e:
        print(f"Error in version intelligence agent: {e}")
        return VersionIntelligenceResult(
            clause_changes="Analysis failed", risk_changes="Analysis failed",
            compliance_changes="Analysis failed", jurisdiction_changes="Analysis failed",
            obligation_changes="Analysis failed",
        )
