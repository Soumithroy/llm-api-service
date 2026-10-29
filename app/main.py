import logging
import time
import uuid

from fastapi import FastAPI, Request

from app.config import get_settings
from app.routers import nlp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("llm-api")

app = FastAPI(
    title="LLM API Service",
    version="1.0.0",
    description="Production-style REST API that wraps LLMs for summarization, classification and extraction.",
)
app.include_router(nlp.router)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    """Attach a request id and log latency for every call (observability basics)."""
    rid = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = rid
    log.info("rid=%s %s %s -> %s %.1fms", rid, request.method, request.url.path, response.status_code, ms)
    return response


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "provider": get_settings().llm_provider}
