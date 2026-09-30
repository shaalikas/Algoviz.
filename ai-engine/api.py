from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai.analyzer import AIAnalyzer

app = FastAPI(title="AlgoViz AI Engine", version="1.0.0")
analyzer = AIAnalyzer()


class AnalysisInput(BaseModel):
    metadata: dict


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(payload: AnalysisInput):
    try:
        return analyzer.analyze(payload.metadata)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Analysis metadata must be a valid object") from exc
