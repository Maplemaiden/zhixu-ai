from fastapi import APIRouter

from app.services import llm, rag
from app.services.step_cards import list_method_ids

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    chunks = rag.load_chunks()
    return {
        "ok": True,
        "project": "知序AI-决策理论数字人助教",
        "midterm_methods": list_method_ids(),
        "llm_configured": llm.available(),
        "knowledge_chunks": len(chunks),
    }
