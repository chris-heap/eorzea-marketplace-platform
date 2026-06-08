from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    question: str
    sql: str
    rows: int = 0
    answer: str
    error: str | None = None
    data: list[dict] = []
