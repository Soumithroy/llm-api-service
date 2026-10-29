from pydantic import BaseModel, Field


class Usage(BaseModel):
    input_tokens: int
    output_tokens: int


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=50_000)
    max_words: int = Field(80, ge=10, le=500)


class SummarizeResponse(BaseModel):
    summary: str
    model: str
    cached: bool
    usage: Usage


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20_000)
    labels: list[str] = Field(..., min_length=2, max_length=20)


class ClassifyResponse(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    model: str
    cached: bool


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20_000)


class ExtractResponse(BaseModel):
    data: dict
    model: str
    cached: bool
