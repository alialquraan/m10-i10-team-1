"""RAG composer — retrieve → assemble → generate → cite → grounding check.

Grounding contract: when `answer` is not the empty-retrieval sentinel,
`len(citations) > 0` is required. Every cited `chunk_id` corresponds to
a chunk in the top-`k` retrieved from Weaviate.

Generator called with `do_sample=False` for reproducibility.
"""
import re
import json
import time
import logging
from typing import Tuple

logger = logging.getLogger("api.rag")
logger.setLevel(logging.INFO)

PROMPT_TEMPLATE = """\
You are answering a recipe question. Use ONLY the numbered sources below.
Cite each claim with the source number in square brackets, e.g. [1].
If the sources do not contain the answer, say: I cannot answer this from the available sources.

Sources:
{sources}

Question: {question}
Answer:"""

SENTINEL = "I cannot answer this from the available sources"
CITATION_PATTERN = re.compile(r"\[(\d+)\]")


def log_structured(level: str, event: str, **kwargs):
    log_data = {
        "timestamp": time.time(),
        "level": level,
        "event": event,
        **kwargs
    }
    print(json.dumps(log_data), flush=True)


def assemble_prompt(question: str, chunks: list[dict]) -> Tuple[str, dict[int, dict]]:
    """Number the retrieved chunks 1..k and substitute into the prompt template.

    Returns (prompt_str, {citation_index: chunk_dict}). Index starts at 1.
    """
    numbered: dict[int, dict] = {}
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        numbered[i] = chunk
        lines.append(f"[{i}] {chunk['text']}")
    sources = "\n".join(lines)
    return PROMPT_TEMPLATE.format(sources=sources, question=question), numbered


def extract_citations(answer: str, numbered: dict[int, dict]) -> list[dict]:
    """Pull [N]-style markers from `answer` and resolve to retrieved chunks.

    Returns one {"chunk_id", "score"} dict per unique resolvable index.
    """
    cited: list[dict] = []
    seen: set[int] = set()
    for match in CITATION_PATTERN.finditer(answer):
        idx = int(match.group(1))
        if idx in numbered and idx not in seen:
            seen.add(idx)
            chunk = numbered[idx]
            cited.append({"chunk_id": chunk["chunk_id"], "score": chunk["score"]})
    return cited


def compose_rag(question: str, embedder, weaviate_client, generator, k: int = 4) -> dict:
    """Run the four-stage RAG pipeline.

    Encodes the question via the externally-loaded sentence-transformers
    embedder and queries Weaviate with `with_near_vector`. The Weaviate
    class is `vectorizer=none`, so `with_near_text` would fail at
    runtime with `KeyError: 'data'`.

    Returns {"answer": str, "citations": list[dict], "confidence": float}.
    """
    start_time = time.time()
    
    vector = embedder.encode(question).tolist()
    try:
        raw_query = (
            weaviate_client.query.get("Chunk", ["chunk_id", "text"])
            .with_near_vector({"vector": vector})
            .with_limit(k)
            .with_additional(["distance"])
            .do()
        )
        retrieved = [
            {
                "chunk_id": c["chunk_id"],
                "text": c["text"],
                "score": 1.0 - c["_additional"]["distance"],
            }
            for c in raw_query["data"]["Get"]["Chunk"]
        ]
    except Exception as exc:
        log_structured("ERROR", "weaviate_query_failed", error=str(exc), question=question)
        return {"answer": SENTINEL, "citations": [], "confidence": 0.0}

    if not retrieved:
        log_structured("INFO", "empty_retrieval", question=question)
        return {"answer": SENTINEL, "citations": [], "confidence": 0.0}

    prompt, numbered = assemble_prompt(question, retrieved)
    
    log_structured("INFO", "generator_start", chunk_count=len(retrieved))
    
    try:
        raw = generator(prompt, max_new_tokens=256, do_sample=False)[0]["generated_text"]
    except Exception as exc:
        log_structured("ERROR", "generator_invocation_failed", error=str(exc))
        return {"answer": SENTINEL, "citations": [], "confidence": 0.0}

    citations = extract_citations(raw, numbered)
    
    if not citations:
        log_structured("WARN", "grounding_refusal_triggered", raw_answer=raw)
        return {"answer": SENTINEL, "citations": [], "confidence": 0.0}

    # حساب الـ Confidence بناءً على متوسط السكورات
    confidence = sum(c["score"] for c in citations) / len(citations)
    confidence = max(0.0, min(1.0, confidence))
    
    duration = time.time() - start_time
    log_structured(
        "INFO", 
        "rag_pipeline_success", 
        duration_seconds=duration, 
        confidence=confidence,
        citation_count=len(citations)
    )

    return {"answer": raw, "citations": citations, "confidence": confidence}