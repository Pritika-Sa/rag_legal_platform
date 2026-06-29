import os
import logging
from typing import List, Tuple
from dotenv import load_dotenv
from sentence_transformers import CrossEncoder

load_dotenv()
logger = logging.getLogger(__name__)

RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")

_reranker_instance = None


def _get_reranker() -> CrossEncoder:
    """Lazy-loads and caches the BGE reranker model."""
    global _reranker_instance
    if _reranker_instance is None:
        logger.info(f"Loading reranker model: {RERANKER_MODEL}")
        _reranker_instance = CrossEncoder(RERANKER_MODEL, max_length=512)
    return _reranker_instance


def rerank_documents(
    query: str,
    documents: list,
    top_k: int = 5,
) -> List[Tuple[object, float]]:
    """Reranks LangChain Document objects using BGE cross-encoder scoring.

    Args:
        query: The user's search query.
        documents: List of LangChain Document objects from vector retrieval.
        top_k: Number of top results to return after reranking.

    Returns:
        List of (document, score) tuples sorted by relevance descending.
    """
    if not documents:
        return []

    reranker = _get_reranker()

    pairs = [(query, doc.page_content) for doc in documents]
    scores = reranker.predict(pairs)

    scored = list(zip(documents, scores))
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[:top_k]
