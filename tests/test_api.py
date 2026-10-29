import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import TokenBucketLimiter, limiter

client = TestClient(app)
H = {"X-API-Key": "dev-key"}


@pytest.fixture(autouse=True)
def reset_limiter():
    limiter.buckets.clear()


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_requires_api_key():
    r = client.post("/v1/summarize", json={"text": "x" * 30})
    assert r.status_code == 401


def test_summarize_and_cache():
    body = {"text": "FastAPI is a web framework. It is fast. It uses type hints.", "max_words": 20}
    r1 = client.post("/v1/summarize", json=body, headers=H)
    assert r1.status_code == 200
    assert r1.json()["summary"].startswith("FastAPI is a web framework.")
    assert r1.json()["cached"] is False
    r2 = client.post("/v1/summarize", json=body, headers=H)
    assert r2.json()["cached"] is True


def test_summarize_validation():
    r = client.post("/v1/summarize", json={"text": "too short"}, headers=H)
    assert r.status_code == 422


def test_classify():
    r = client.post("/v1/classify",
                    json={"text": "I want a refund for my order", "labels": ["billing", "refund", "other"]},
                    headers=H)
    assert r.status_code == 200
    assert r.json()["label"] == "refund"


def test_extract():
    r = client.post("/v1/extract", json={"text": "Contact jane@acme.io or bob@x.com"}, headers=H)
    assert r.status_code == 200
    assert r.json()["data"]["emails"] == ["jane@acme.io", "bob@x.com"]


def test_request_id_header():
    r = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["X-Request-ID"] == "abc123"


def test_token_bucket():
    tb = TokenBucketLimiter(per_minute=3)
    assert [tb.allow("k")[0] for _ in range(4)] == [True, True, True, False]
    assert tb.allow("other")[0] is True  # buckets are per key
