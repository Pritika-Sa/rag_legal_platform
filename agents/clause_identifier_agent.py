import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from utils.llm_client import invoke_llm_structured

CLAUSE_RULES = {
    "Termination": {
        "keywords": ["terminate", "termination", "expiry", "expiration", "material breach", "cure period", "written notice"],
        "regex": r"\bterminate\b|\btermination\b|\bexpiry\b|\bexpiration\b|\bbreach\b",
    },
    "Liability": {
        "keywords": ["liability", "limitation of liability", "liable", "cap", "indirect damages", "consequential damages", "special damages"],
        "regex": r"\bliab(le|ility)\b|\blimit(ation)?\s+of\s+liability\b|\bconsequential\s+damages\b",
    },
    "Confidentiality": {
        "keywords": ["confidential", "confidentiality", "non-disclosure", "nda", "proprietary information", "trade secret"],
        "regex": r"\bconfidential(ity)?\b|\bnon-disclosure\b|\bproprietary\b|\bsecrets?\b",
    },
    "Arbitration": {
        "keywords": ["arbitration", "arbitrate", "arbitrator", "aaa", "jams", "binding", "dispute resolution"],
        "regex": r"\barbitrat(e|ion|or)\b|\bdispute\s+resolution\b",
    },
    "Payment": {
        "keywords": ["payment", "invoice", "fee", "price", "billing", "due date", "interest", "reimbursement"],
        "regex": r"\bpay(ment)?s?\b|\binvoic(es?|ing)\b|\bfee(s)?\b|\bbill(ing)?\b",
    },
    "Indemnity": {
        "keywords": ["indemnify", "indemnity", "indemnification", "hold harmless", "defend", "losses", "claims"],
        "regex": r"\bindemni(fy|t|fication)\b|\bhold\s+harmless\b|\bdefend\b",
    },
    "Compliance": {
        "keywords": ["compliance", "comply", "applicable laws", "regulations", "sanctions", "anti-corruption", "fcpa"],
        "regex": r"\bcompli(ance|y|ied)\b|\bapplicable\s+laws?\b|\bregulations?\b",
    },
    "Jurisdiction": {
        "keywords": ["jurisdiction", "governing law", "venue", "forum", "courts of", "governed by", "state of"],
        "regex": r"\bjurisdiction\b|\bgoverning\s+law\b|\bvenue\b|\bforum\b",
    },
    "Force Majeure": {
        "keywords": ["force majeure", "act of god", "natural disaster", "unforeseeable", "war", "strike", "riot", "fire"],
        "regex": r"\bforce\s+majeure\b|\bact\s+of\s+god\b|\bunforeseeable\b",
    },
}


class ClauseVerificationResult(BaseModel):
    is_match: bool = Field(description="True if the text is semantically a contract clause of the expected type")
    clause_type: str = Field(description="The verified contract clause type")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0")


class IdentifiedClause(BaseModel):
    clause_type: str
    clause_text: str
    confidence_score: float
    page_number: Optional[int] = None
    start_position: int
    end_position: int


def verify_clause_semantically(clause_text: str, expected_type: str) -> ClauseVerificationResult:
    """Uses Groq LLM to semantically verify if a text block matches a clause type."""
    system_instruction = (
        "You are an expert contract lawyer. Review the text block and verify if it represents "
        "a clause of the expected type. Determine is_match, assign the actual clause type, "
        "and calculate a semantic confidence score (0.0 to 1.0)."
    )
    prompt = f"Expected Clause Type: {expected_type}\nText Block:\n{clause_text}"

    try:
        return invoke_llm_structured(system_instruction, prompt, ClauseVerificationResult)
    except Exception as e:
        print(f"Clause verification failed for expected type '{expected_type}': {e}")
        return ClauseVerificationResult(is_match=True, clause_type=expected_type, confidence_score=0.5)


def identify_clauses(full_text: str, page_mapping: Optional[List[Dict[str, Any]]] = None) -> List[IdentifiedClause]:
    """Identifies clauses using keywords, regex rules, and LLM semantic verification."""
    identified_clauses = []
    paragraphs = [p.strip() for p in re.split(r'\n\n|\n(?=\d+\.)', full_text) if p.strip()]

    def find_page_number(clause_text):
        if not page_mapping:
            return None
        for mapping in page_mapping:
            if clause_text.lower() in mapping["text_content"].lower():
                return mapping["page_number"]
        return None

    processed_blocks = set()

    for block in paragraphs:
        if len(block) < 30 or block in processed_blocks:
            continue

        block_lower = block.lower()
        matched_types = []

        for c_type, rules in CLAUSE_RULES.items():
            kw_match = any(kw in block_lower for kw in rules["keywords"])
            reg_match = bool(re.search(rules["regex"], block_lower))
            if kw_match or reg_match:
                matched_types.append(c_type)

        for c_type in matched_types:
            verification = verify_clause_semantically(block, c_type)
            if verification.is_match:
                start_pos = full_text.find(block)
                if start_pos == -1:
                    start_pos = 0
                end_pos = start_pos + len(block)
                page_num = find_page_number(block)

                identified_clauses.append(IdentifiedClause(
                    clause_type=verification.clause_type,
                    clause_text=block,
                    confidence_score=verification.confidence_score,
                    page_number=page_num,
                    start_position=start_pos,
                    end_position=end_pos,
                ))
                processed_blocks.add(block)
                break

    return identified_clauses
