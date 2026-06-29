from pydantic import BaseModel, Field
from typing import List, Dict, Any
from utils.llm_client import invoke_llm_structured


class ComparisonResult(BaseModel):
    similarity_score: int = Field(description="Similarity score between the two documents from 0 to 100")
    change_summary: str = Field(description="A high-level summary of the major differences")
    added_clauses: List[str] = Field(description="Clauses added in Document B not in Document A")
    removed_clauses: List[str] = Field(description="Clauses removed from Document B that were in Document A")
    modified_clauses: List[str] = Field(description="Clauses that exist in both but were materially modified")
    risk_changes: str = Field(description="Analysis of how modifications impact the risk profile")
    difference_report: str = Field(description="Detailed difference report of textual and semantic variations")


def compare_documents(clauses_a: List[Dict[str, Any]], clauses_b: List[Dict[str, Any]],
                      doc_a_name: str, doc_b_name: str) -> ComparisonResult:
    """Agent 10: Document Comparison Agent."""
    text_a = ""
    for c in clauses_a:
        text_a += f"[{c.get('section_name', 'Unknown')}]\n{c.get('text_content', '')}\n\n"

    text_b = ""
    for c in clauses_b:
        text_b += f"[{c.get('section_name', 'Unknown')}]\n{c.get('text_content', '')}\n\n"

    system_instruction = (
        "You are an expert Document Comparison Agent. Compare Document A and Document B. "
        "Detect added clauses, removed clauses, modified clauses, and risk changes. "
        "Generate a similarity score (0-100), a change summary, and a detailed difference report."
    )
    prompt = f"Document A ({doc_a_name}):\n{text_a}\n\nDocument B ({doc_b_name}):\n{text_b}"

    try:
        return invoke_llm_structured(system_instruction, prompt, ComparisonResult)
    except Exception as e:
        print(f"Error in comparison agent: {e}")
        return ComparisonResult(
            similarity_score=0, change_summary=f"Error: {e}",
            added_clauses=[], removed_clauses=[], modified_clauses=[],
            risk_changes="N/A", difference_report="N/A",
        )
