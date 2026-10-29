"""Deterministic offline provider: lets the API, tests and CI run with no API key."""
import json
import re

from app.providers.base import Completion, LLMProvider


class MockProvider(LLMProvider):
    name = "mock"

    async def complete(self, system: str, prompt: str, max_tokens: int = 512) -> Completion:
        task = system.split(":", 1)[0].lower()
        body = prompt.split("\n\n", 1)[-1]

        if task.startswith("classify"):
            labels = re.findall(r"\[(.*?)\]", prompt)
            options = [l.strip() for l in labels[0].split(",")] if labels else ["unknown"]
            pick = next((o for o in options if o.lower() in body.lower()), options[0])
            text = json.dumps({"label": pick, "confidence": 0.9})
        elif task.startswith("extract"):
            emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", body)
            text = json.dumps({"emails": emails, "word_count": len(body.split())})
        else:  # summarize
            sentences = re.split(r"(?<=[.!?])\s+", body.strip())
            text = " ".join(sentences[:2])

        return Completion(
            text=text,
            model="mock-1",
            input_tokens=len(prompt.split()),
            output_tokens=len(text.split()),
        )
