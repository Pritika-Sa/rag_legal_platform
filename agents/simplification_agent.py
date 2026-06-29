from pydantic import BaseModel, Field
from utils.llm_client import invoke_llm_structured


class SimplificationResult(BaseModel):
    original_clause: str = Field(description="The original legal text")
    simplified_clause: str = Field(description="The clause rewritten in plain, accessible English")
    explanation: str = Field(description="A brief explanation of what the clause means in practical terms")
    real_world_example: str = Field(description="A concrete real-world example illustrating how this clause applies")


def simplify_clause(clause_text: str) -> SimplificationResult:
    """Agent 7: Legal Simplification Agent."""
    system_instruction = (
        "You are an expert Legal Simplification Agent. Translate dense legalese "
        "into plain English that a non-lawyer can easily understand, without sacrificing legal accuracy. "
        "Return the original clause, the simplified version, a brief explanation, "
        "and a concrete real-world example."
    )
    prompt = f"Please simplify this legal clause:\n\n{clause_text}"

    try:
        return invoke_llm_structured(system_instruction, prompt, SimplificationResult, temperature=0.1)
    except Exception as e:
        print(f"Error in simplification agent: {e}")
        return SimplificationResult(
            original_clause=clause_text,
            simplified_clause="Error generating simplification.",
            explanation="N/A",
            real_world_example="N/A",
        )
