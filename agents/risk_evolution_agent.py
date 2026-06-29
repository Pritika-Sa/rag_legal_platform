from pydantic import BaseModel, Field
from typing import List, Dict, Any
from utils.llm_client import invoke_llm_structured


class VersionRiskData(BaseModel):
    version: str = Field(description="The version identifier, e.g. 'V1', 'V2'")
    avg_risk_score: float = Field(description="The calculated risk score for this version (0-10)")
    high_count: int = Field(description="Number of high risk clauses in this version")


class RiskEvolutionResult(BaseModel):
    risk_trend: str = Field(description="Narrative analysis of the overall risk trajectory across versions")
    risk_reduction_factors: List[str] = Field(description="Specific legal changes that drove risk down")
    risk_increase_factors: List[str] = Field(description="Specific legal changes that introduced new risks")
    risk_timeline: List[VersionRiskData] = Field(description="Chronological list of risk data points")


def analyze_risk_evolution(versions_history: List[Dict[str, Any]]) -> RiskEvolutionResult:
    """Agent 13: Multi-Version Risk Evolution Agent."""
    history_text = "Chronological Version History of Document Risks:\n\n"
    for v in versions_history:
        history_text += f"[{v['version']}] High Risks: {v['high_count']} | Score: {v['avg_risk']}\n"
        history_text += f"Changes made: {v.get('changes_summary', 'Baseline version')}\n\n"

    system_instruction = (
        "You are an expert Multi-Version Risk Evolution Analyst. "
        "Analyze the chronological sequence of document states. "
        "Determine the overall risk trend, identify factors that reduced or increased risk, "
        "and reconstruct a precise timeline of risk scores."
    )
    prompt = f"Analyze this risk history:\n\n{history_text}"

    try:
        return invoke_llm_structured(system_instruction, prompt, RiskEvolutionResult)
    except Exception as e:
        print(f"Error in risk evolution agent: {e}")
        fallback_timeline = [
            VersionRiskData(version=v['version'], avg_risk_score=v['avg_risk'], high_count=v['high_count'])
            for v in versions_history
        ]
        return RiskEvolutionResult(
            risk_trend="Error evaluating trend",
            risk_reduction_factors=[], risk_increase_factors=[],
            risk_timeline=fallback_timeline,
        )
