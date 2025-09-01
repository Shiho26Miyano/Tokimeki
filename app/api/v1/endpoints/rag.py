"""RAG endpoints: ingest documents and ask questions over a corpus."""

from typing import List, Optional
import time
import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup
import io
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False
    pdf_extract_text = None
try:
    from pypdf import PdfReader  # optional fallback
    PYPDF_AVAILABLE = True
except Exception:
    PYPDF_AVAILABLE = False
import httpx

from ....core.dependencies import get_usage_service, get_ai_service, get_rag_service, get_http_client
from ....services.usage_service import AsyncUsageService
from ....services.ai_service import AsyncAIService
from ....services.rag_service import AsyncRAGService

logger = logging.getLogger(__name__)

router = APIRouter()


class IngestRequest(BaseModel):
    corpus_id: str = Field(..., min_length=1, max_length=64)
    texts: Optional[List[str]] = Field(default=None)
    urls: Optional[List[str]] = Field(default=None)
    metadatas: Optional[List[dict]] = None
    only_html: Optional[bool] = Field(default=False, description="If true, reject non-HTML (e.g., PDFs)")


class AskRequest(BaseModel):
    corpus_id: str = Field(..., min_length=1, max_length=64)
    question: str = Field(..., min_length=3, max_length=2000)
    k: int = Field(default=4, ge=1, le=12)
    model: str = Field(default="mistral-small")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=800, ge=100, le=2000)


# Use singleton provided by core.dependencies


@router.post("/ingest")
async def ingest_corpus(
    request: IngestRequest,
    rag_service: AsyncRAGService = Depends(get_rag_service),
    usage_service: AsyncUsageService = Depends(get_usage_service),
    http_client: httpx.AsyncClient = Depends(get_http_client)
):
    start_time = time.time()
    try:
        combined_texts: List[str] = []
        combined_metas: List[dict] = []

        if request.texts:
            combined_texts.extend([t for t in request.texts if (t or "").strip()])
            if request.metadatas:
                combined_metas.extend(request.metadatas[: len(combined_texts)])

        # Fetch and parse URLs if provided (supports HTML and PDF)
        if request.urls:
            for url in request.urls:
                try:
                    # Be explicit about headers; some CDNs require a UA
                    resp = await http_client.get(
                        url,
                        headers={
                            "User-Agent": "Tokimeki-RAG/1.0 (+https://example.com)",
                            "Accept": "application/pdf, text/html, */*"
                        },
                        timeout=60.0
                    )
                    resp.raise_for_status()
                    content_type = resp.headers.get("content-type", "").lower()
                    text = ""
                    title = url
                    if ("application/pdf" in content_type or url.lower().endswith(".pdf")):
                        if request.only_html:
                            logger.warning(f"Skipping non-HTML URL due to only_html=True: {url}")
                            continue
                        # Extract text from PDF bytes
                        if PDFMINER_AVAILABLE:
                            try:
                                text = pdf_extract_text(io.BytesIO(resp.content))
                            except Exception as pdf_exc:
                                logger.warning(f"PDF extract failed for {url} using pdfminer: {pdf_exc}")
                                text = ""
                        else:
                            text = ""
                        
                        if not text and PYPDF_AVAILABLE:
                                try:
                                    reader = PdfReader(io.BytesIO(resp.content))
                                    pages = []
                                    for p in reader.pages:
                                        try:
                                            pages.append(p.extract_text() or "")
                                        except Exception:
                                            pages.append("")
                                    text = "\n".join([t for t in pages if t])
                                except Exception as pypdf_exc:
                                    logger.warning(f"PDF extract fallback failed for {url}: {pypdf_exc}")
                    else:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        for tag in soup(["script", "style", "noscript"]):
                            tag.extract()
                        text = "\n".join([line.strip() for line in soup.get_text("\n").splitlines() if line.strip()])
                        if soup.title and soup.title.string:
                            title = soup.title.string.strip()
                    if text and text.strip():
                        combined_texts.append(text)
                        combined_metas.append({"source": url, "title": title, "type": "url"})
                    else:
                        logger.warning(f"Fetched URL but no extractable text: {url} (content-type: {content_type})")
                except Exception as fetch_exc:
                    logger.warning(f"Failed to fetch URL {url}: {fetch_exc}")

        if not combined_texts:
            raise ValueError("No texts to ingest. Provide 'texts' or valid 'urls'.")

        # Align metadata lengths
        if len(combined_metas) < len(combined_texts):
            combined_metas.extend([{}] * (len(combined_texts) - len(combined_metas)))

        result = await rag_service.ingest(
            corpus_id=request.corpus_id,
            texts=combined_texts,
            metadatas=combined_metas,
        )
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="rag_ingest",
            response_time=response_time,
            success=True
        )
        return result
    except ValueError as exc:
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="rag_ingest",
            response_time=response_time,
            success=False,
            error=str(exc)
        )
        logger.error(f"RAG ingest error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="rag_ingest",
            response_time=response_time,
            success=False,
            error=str(exc)
        )
        logger.error(f"RAG ingest error: {exc}")
        raise HTTPException(status_code=503, detail="RAG dependencies missing. Please install langchain, langchain-community, sentence-transformers, faiss-cpu.")
    except Exception as exc:
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="rag_ingest",
            response_time=response_time,
            success=False,
            error=str(exc)
        )
        logger.error(f"RAG ingest error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ask")
async def rag_ask(
    request: AskRequest,
    rag_service: AsyncRAGService = Depends(get_rag_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    start_time = time.time()
    try:
        result = await rag_service.ask(
            corpus_id=request.corpus_id,
            question=request.question,
            k=request.k,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="rag_ask",
            response_time=response_time,
            success=True
        )
        return result
    except ValueError as exc:
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="rag_ask",
            response_time=response_time,
            success=False,
            error=str(exc)
        )
        logger.error(f"RAG ask error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="rag_ask",
            response_time=response_time,
            success=False,
            error=str(exc)
        )
        logger.error(f"RAG ask error: {exc}")
        raise HTTPException(status_code=503, detail="RAG dependencies missing. Please install langchain, langchain-community, sentence-transformers, faiss-cpu.")
    except Exception as exc:
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="rag_ask",
            response_time=response_time,
            success=False,
            error=str(exc)
        )
        logger.error(f"RAG ask error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/graph")
async def rag_graph(
    rag_service: AsyncRAGService = Depends(get_rag_service)
):
    try:
        return {"success": True, "graph": rag_service.get_graph_definition()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/health")
async def rag_health():
    try:
        from ....services.rag_service import LANGCHAIN_AVAILABLE  # type: ignore
        return {"success": True, "langchain_available": bool(LANGCHAIN_AVAILABLE)}
    except Exception:
        return {"success": False, "langchain_available": False}


@router.post("/ingest_file")
async def ingest_file(
    corpus_id: str,
    file: UploadFile = File(...),
    rag_service: AsyncRAGService = Depends(get_rag_service),
    usage_service: AsyncUsageService = Depends(get_usage_service)
):
    """Ingest an uploaded file (PDF or text) into the corpus."""
    start_time = time.time()
    try:
        filename = (file.filename or "uploaded")
        content_type = (file.content_type or "").lower()
        raw_bytes = await file.read()

        text = ""
        if "application/pdf" in content_type or filename.lower().endswith(".pdf"):
            try:
                text = pdf_extract_text(io.BytesIO(raw_bytes))
            except Exception as pdf_exc:
                if PYPDF_AVAILABLE:
                    try:
                        reader = PdfReader(io.BytesIO(raw_bytes))
                        pages = []
                        for p in reader.pages:
                            try:
                                pages.append(p.extract_text() or "")
                            except Exception:
                                pages.append("")
                        text = "\n".join([t for t in pages if t])
                    except Exception as pypdf_exc:
                        raise HTTPException(status_code=400, detail=f"PDF parse failed: {pypdf_exc}")
                else:
                    raise HTTPException(status_code=400, detail=f"PDF parse failed: {pdf_exc}")
        else:
            # Assume UTF-8 text fallback
            try:
                text = raw_bytes.decode("utf-8", errors="ignore")
            except Exception:
                raise HTTPException(status_code=400, detail="Unsupported file format or encoding")

        text = (text or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="No extractable text in file")

        result = await rag_service.ingest(
            corpus_id=corpus_id,
            texts=[text],
            metadatas=[{"source": filename, "type": "upload"}]
        )
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="rag_ingest_file",
            response_time=response_time,
            success=True
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        response_time = time.time() - start_time
        await usage_service.track_request(
            endpoint="rag_ingest_file",
            response_time=response_time,
            success=False,
            error=str(exc)
        )
        raise HTTPException(status_code=500, detail=str(exc))


