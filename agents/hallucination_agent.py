from pydantic import BaseModel, Field
from typing import List
from utils.llm_client import invoke_llm_structured


class HallucinationEvaluation(BaseModel):
    hallucination_score: int = Field(description="Score 0-100 where 100=completely hallucinated, 0=fully grounded.")
    trust_score: int = Field(description="Overall Trust score 0-100 based on groundedness and faithfulness.")
    confidence_score: int = Field(description="Confidence of this evaluation 0-100.")
    groundedness_analysis: str = Field(description="Explanation of whether the output is strictly derived from context.")
    citation_quality: str = Field(description="Analysis of whether citations accurately match the source context.")
    unsupported_statements: List[str] = Field(description="List of claims NOT supported by the source context.")


def evaluate_hallucination(context: str, generated_answer: str) -> HallucinationEvaluation:
    """Agent 14: Hallucination Detection Agent."""
    system_instruction = (
        "You are an expert Hallucination Detection Agent for Legal AI. "
        "Your sole job is to verify if a generated answer is 100% grounded in the source context. "
        "If the answer invents legal obligations, misquotes, or hallucinates, flag it with a high hallucination_score."
    )
    prompt = (
        f"--- SOURCE CONTEXT ---\n{context}\n\n"
        f"--- AI GENERATED ANSWER TO EVALUATE ---\n{generated_answer}"
    )

    try:
        return invoke_llm_structured(system_instruction, prompt, HallucinationEvaluation)
    except Exception as e:
        print(f"Error in hallucination agent: {e}")
        return HallucinationEvaluation(
            hallucination_score=100, trust_score=0, confidence_score=0,
            groundedness_analysis=f"Evaluation failed: {e}",
            citation_quality="Unknown", unsupported_statements=["Error during evaluation"],
        )
