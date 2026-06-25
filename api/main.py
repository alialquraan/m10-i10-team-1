"""FastAPI application — recipe service (reference implementation).

Discipline gates the autograder enforces:
- Neo4j driver, Weaviate client, spaCy pipeline, and the flan-t5-base
  generator are constructed exactly once per process inside `lifespan`.
- `CORSMiddleware` registered with `allow_origins=[WEB_ORIGIN]`.
- `/extract`, `/kg/query`, `/rag/answer` use Pydantic shapes from `models.py`.
- `/kg/query` converts `UnsupportedQueryError` to 422 with structured detail.
- `/readyz` probes Neo4j (`RETURN 1`) AND Weaviate (`client.is_ready()`)
  within 2 seconds; failure → 503.
- `/healthz` does NOT touch Neo4j or Weaviate.
"""
import os
import asyncio  
from contextlib import asynccontextmanager

import spacy
import weaviate
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

from .deps import get_embedder, get_generator, get_nlp, get_session, get_weaviate
from .kg import wrap_kg_query
from .m8_rag import load_generator
from .models import (
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    KGRequest,
    KGResponse,
    RAGRequest,
    RAGResponse,
    UnsupportedQueryDetail,
)
from .nlp import extract_entities
from .rag import compose_rag
from .w9b_mapper.errors import UnsupportedQueryError
from .w9b_mapper.shapes import SUPPORTED_PATTERNS


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.neo4j_driver = GraphDatabase.driver(
        os.environ.get("NEO4J_URI", "bolt://neo4j:7687"),
        auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ.get("NEO4J_PASSWORD", "password")),
    )
    app.state.weaviate_client = weaviate.Client(os.environ.get("WEAVIATE_URL", "http://weaviate:8080"))
    app.state.nlp = spacy.load("en_core_web_sm")
    app.state.generator = load_generator()
    app.state.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    yield
    app.state.neo4j_driver.close()


app = FastAPI(title="M10 Recipe Service", lifespan=lifespan)

WEB_ORIGIN = os.environ.get("WEB_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEB_ORIGIN],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest, nlp=Depends(get_nlp)) -> ExtractResponse:
    try:
        return ExtractResponse(entities=extract_entities(req.text, nlp))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failure: {str(exc)}"
        )


@app.post("/kg/query", response_model=KGResponse)
def kg_query(req: KGRequest, session=Depends(get_session)) -> KGResponse:
    try:
        cypher, params = wrap_kg_query(req.question)
    except UnsupportedQueryError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=UnsupportedQueryDetail(
                reason="unsupported_question",
                supported_patterns=list(SUPPORTED_PATTERNS),
            ).model_dump(),
        )
    
    try:
        rows = [r.data() for r in session.run(cypher, **params)]
        return KGResponse(cypher=cypher, rows=rows, count=len(rows))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge Graph execution error: {str(exc)}"
        )


@app.post("/rag/answer", response_model=RAGResponse)
def rag_answer(
    req: RAGRequest,
    weaviate_client=Depends(get_weaviate),
    generator=Depends(get_generator),
    embedder=Depends(get_embedder),
) -> RAGResponse:
    try:
        result = compose_rag(req.question, embedder, weaviate_client, generator, k=req.k)
        return RAGResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG processing failure: {str(exc)}"
        )


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/readyz")
async def readyz(
    session=Depends(get_session),
    weaviate_client=Depends(get_weaviate),
):
    detail = {"neo4j": "unknown", "weaviate": "unknown"}
    
    def check_neo4j():
        session.run("RETURN 1").single()
        
    def check_weaviate():
        return weaviate_client.is_ready()

    try:
        await asyncio.wait_for(
            asyncio.to_thread(check_neo4j), 
            timeout=2.0
        )
        detail["neo4j"] = "ok"
    except asyncio.TimeoutError:
        detail["neo4j"] = "unavailable: timeout after 2 seconds"
    except Exception as exc:
        detail["neo4j"] = f"unavailable: {exc.__class__.__name__}"

    try:
        is_weaviate_ready = await asyncio.wait_for(
            asyncio.to_thread(check_weaviate), 
            timeout=2.0
        )
        if is_weaviate_ready:
            detail["weaviate"] = "ok"
        else:
            detail["weaviate"] = "not ready"
    except asyncio.TimeoutError:
        detail["weaviate"] = "unavailable: timeout after 2 seconds"
    except Exception as exc:
        detail["weaviate"] = f"unavailable: {exc.__class__.__name__}"

    if detail["neo4j"] != "ok" or detail["weaviate"] != "ok":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
        
    return detail