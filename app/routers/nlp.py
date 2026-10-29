import json

from fastapi import APIRouter, Depends, HTTPException

from app.cache import TTLCache
from app.config import get_settings
from app.providers import LLMProvider, get_provider
from app.schemas import (
    ClassifyRequest, ClassifyResponse, ExtractRequest, ExtractResponse,
    SummarizeRequest, SummarizeResponse, Usage,
)
from app.security import rate_limit

router = APIRouter(prefix="/v1", tags=["nlp"], dependencies=[Depends(rate_limit)])
cache = TTLCache(get_settings().cache_ttl_seconds)


async def _run(provider: LLMProvider, system: str, prompt: str, max_tokens: int = 512):
    k = TTLCache.key(provider.name, system, prompt)
    if (hit := cache.get(k)) is not None:
        return hit, True
    completion = await provider.complete(system, prompt, max_tokens)
    cache.set(k, completion)
    return completion, False


def _parse_json(text: str) -> dict:
    """LLMs sometimes wrap JSON in prose/code fences – pull out the object."""
    start, end = text.find("{"), text.rfind("}")
    try:
        return json.loads(text[start : end + 1])
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(502, "Model returned malformed JSON")


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest, provider: LLMProvider = Depends(get_provider)):
    system = f"Summarize: write a faithful summary in at most {req.max_words} words. No preamble."
    c, cached = await _run(provider, system, f"Text to summarize:\n\n{req.text}")
    return SummarizeResponse(
        summary=c.text.strip(), model=c.model, cached=cached,
        usage=Usage(input_tokens=c.input_tokens, output_tokens=c.output_tokens),
    )


@router.post("/classify", response_model=ClassifyResponse)
async def classify(req: ClassifyRequest, provider: LLMProvider = Depends(get_provider)):
    system = (
        "Classify: pick exactly one label for the text. Respond ONLY with JSON "
        '{"label": <one of the labels>, "confidence": <0..1>}.'
    )
    prompt = f"Labels: [{', '.join(req.labels)}]\n\n{req.text}"
    c, cached = await _run(provider, system, prompt, 100)
    data = _parse_json(c.text)
    if data.get("label") not in req.labels:
        raise HTTPException(502, f"Model returned unknown label {data.get('label')!r}")
    return ClassifyResponse(label=data["label"], confidence=float(data.get("confidence", 0.5)),
                            model=c.model, cached=cached)


@router.post("/extract", response_model=ExtractResponse)
async def extract(req: ExtractRequest, provider: LLMProvider = Depends(get_provider)):
    system = (
        "Extract: return ONLY a JSON object with keys `emails` (list), `people` (list), "
        "`organizations` (list), `dates` (list) found in the text."
    )
    c, cached = await _run(provider, system, f"Text:\n\n{req.text}")
    return ExtractResponse(data=_parse_json(c.text), model=c.model, cached=cached)
