import os
import re
import json
import logging
from typing import Type, TypeVar
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel

load_dotenv()
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

_embeddings_instance = None


def get_llm(temperature: float = 0.0) -> ChatGroq:
    """Returns a ChatGroq instance."""
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=8192,
        request_timeout=120,
    )


def get_embeddings() -> HuggingFaceEmbeddings:
    """Returns cached embeddings singleton — loads model once."""
    global _embeddings_instance
    if _embeddings_instance is None:
        model_kwargs = {"device": "cpu"}
        encode_kwargs = {"normalize_embeddings": True}
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
    return _embeddings_instance


def _extract_json_from_text(text: str) -> str:
    """Extracts the first JSON object or array from raw LLM text."""
    match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def invoke_llm_structured(
    system_prompt: str,
    user_prompt: str,
    output_schema: Type[T],
    temperature: float = 0.0,
) -> T:
    """Invokes Groq LLM and parses the response into a Pydantic model."""
    schema_json = json.dumps(output_schema.model_json_schema(), indent=2)

    full_system = (
        f"{system_prompt}\n\n"
        f"CRITICAL: You must respond with ONLY a valid JSON object matching this exact schema. "
        f"Do not include any text before or after the JSON. No markdown, no explanation, just raw JSON.\n\n"
        f"JSON Schema:\n{schema_json}"
    )

    llm = get_llm(temperature=temperature)
    response = llm.invoke([
        {"role": "system", "content": full_system},
        {"role": "user", "content": user_prompt},
    ])

    raw_text = response.content.strip()
    json_str = _extract_json_from_text(raw_text)

    try:
        parsed = json.loads(json_str)
        return output_schema.model_validate(parsed)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"First parse failed ({e}), retrying with correction prompt...")

        correction_prompt = (
            f"Your previous response was not valid JSON. The raw output was:\n"
            f"---\n{raw_text[:2000]}\n---\n\n"
            f"Please output ONLY a valid JSON object matching this schema:\n{schema_json}\n\n"
            f"No explanation. No markdown. Just the JSON."
        )
        response2 = llm.invoke([
            {"role": "system", "content": full_system},
            {"role": "user", "content": correction_prompt},
        ])
        raw_text2 = response2.content.strip()
        json_str2 = _extract_json_from_text(raw_text2)
        parsed2 = json.loads(json_str2)
        return output_schema.model_validate(parsed2)


def invoke_llm_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0,
) -> str:
    """Invokes Groq LLM and returns plain text."""
    llm = get_llm(temperature=temperature)
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])
    return response.content.strip()
