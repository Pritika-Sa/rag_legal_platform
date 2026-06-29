from pydantic import BaseModel, Field
from utils.llm_client import invoke_llm_structured


class TranslationResult(BaseModel):
    translated_clause: str = Field(description="The fully translated legal clause")
    confidence_score: int = Field(description="Confidence score of the translation accuracy from 0 to 100")


def translate_clause(clause_text: str, target_language: str) -> TranslationResult:
    """Agent 8: Translation Agent."""
    system_instruction = (
        f"You are an expert, certified legal translator. Translate the following contract clause into {target_language}. "
        "CRITICAL REQUIREMENTS:\n"
        "1. Preserve the exact legal meaning and nuances.\n"
        "2. Preserve any clause numbering (e.g., '1.1', '(a)').\n"
        "3. Preserve all named legal entities and company names without translating them.\n"
        "4. Assign a 'confidence_score' between 0 and 100 for legal accuracy."
    )
    prompt = f"Clause to translate:\n\n{clause_text}"

    try:
        return invoke_llm_structured(system_instruction, prompt, TranslationResult)
    except Exception as e:
        print(f"Error in translation agent: {e}")
        return TranslationResult(translated_clause=f"Translation failed: {str(e)}", confidence_score=0)
