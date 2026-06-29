from pydantic import BaseModel, Field
from typing import List
from utils.llm_client import invoke_llm_structured


class GraphNode(BaseModel):
    id: str = Field(description="Unique node identifier")
    label: str = Field(description="Display label")
    color: str = Field(description="Hex color code. Parties=#636EFA, Jurisdictions=#00CC96, Risks=#EF553B, Obligations=#FECB52")
    size: int = Field(default=15, description="Node size based on importance (15 to 30)")


class GraphEdge(BaseModel):
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    label: str = Field(description="Relationship label")
    color: str = Field(default="#888888", description="Hex color code for edge")


class ContractGraphSchema(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


def extract_knowledge_graph(doc_name: str, doc_text: str) -> dict:
    """Agent 11: Legal Knowledge Graph Agent."""
    system_instruction = (
        "You are an expert Legal Knowledge Graph Agent. Construct a graph of entities "
        "and relationships from the contract text. Extract:\n"
        "1. Parties (Signatories)\n2. Dates (Effective dates, deadlines)\n"
        "3. Obligations (Deliverables, duties)\n4. Payments (Amounts, currencies)\n"
        "5. Penalties (Liquidated damages, late fees)\n6. Jurisdictions (Governing law, venue)\n\n"
        "Assign colors: Parties=#636EFA, Jurisdictions=#00CC96, Penalties=#EF553B, Obligations/Dates/Payments=#FECB52."
    )
    prompt = f"Document Name: {doc_name}\n\nDocument Text Content:\n{doc_text}"

    try:
        result = invoke_llm_structured(system_instruction, prompt, ContractGraphSchema)
        return {
            "nodes": [n.model_dump() for n in result.nodes],
            "edges": [e.model_dump() for e in result.edges],
        }
    except Exception as e:
        print(f"Error in knowledge graph agent: {e}")
        return {"nodes": [], "edges": []}
