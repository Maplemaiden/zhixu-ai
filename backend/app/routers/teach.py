from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services import llm, rag
from app.services.classify import classify_question
from app.services.lesson_reading import get_lesson_reading
from app.services.step_cards import (
    SECTION_LABELS,
    format_card_for_prompt,
    get_step_card,
)

router = APIRouter(prefix="/teach", tags=["teach"])


class AskBody(BaseModel):
    question: str = Field(..., min_length=1)
    method_id: str = "expected_value"
    section: int | None = Field(default=None, ge=0, le=2)
    section_label: str | None = None


class ClassifyBody(BaseModel):
    question: str = Field(..., min_length=1)


@router.get("/step_card/{method_id}")
def step_card(method_id: str):
    card = get_step_card(method_id)
    if not card:
        return {"ok": False, "detail": "未知方法"}
    return {"ok": True, "card": card}


@router.get("/reading/{method_id}")
def reading(method_id: str):
    """讲解页正文：从课程知识 md 抽取，而不是只显示步骤提纲。"""
    card = get_step_card(method_id)
    if not card:
        return {"ok": False, "detail": "未知方法", "sections": []}
    data = get_lesson_reading(method_id)
    return {"ok": True, **data}


@router.post("/classify")
def classify(body: ClassifyBody):
    return classify_question(body.question)


def _build_system(card: dict | None, section: int | None, section_label: str | None) -> str:
    label = section_label or (SECTION_LABELS.get(section) if section is not None else None)
    parts = [
        "你是《决策理论与方法》课程助教。",
        "只依据给定课程资料与步骤卡讲解；符号与步骤必须与步骤卡一致，禁止另造记号。",
        "凡出现公式，必须使用 LaTeX：行内用 $...$，独立式用 $$...$$。",
        "禁止写成 E(ai)=sum 这类伪代码；优先引用步骤卡中的标准公式模板。",
        "若学生说「这一步 / 这里 / 刚才」，默认指当前学习段对应内容，结合步骤卡解释。",
        "资料检索不足时：先用步骤卡能回答的部分（符号表、标准步骤、公式），再说明缺哪段教材细节；不要整段空拒。",
        "不要编造课程资料中没有的数值；回答末尾列出引用的来源文件名。",
    ]
    if label == "实验台":
        parts.append(
            "学生正在实验台：若问题中附带「调整前/调整后」程序验算结果，"
            "解释时必须原样引用这些数字与最优方案，禁止重新口算或改写。"
        )
    elif label == "案例" or section == 1:
        parts.append(
            "学生正在看本讲案例：结合案例要素与教材规则讲解；"
            "不要编造未给出的数值，也不要假装这里有程序调参。"
        )
    if card:
        if label:
            parts.append(f"当前学习段：{label}" + (f"（第 {section + 1} 段）" if section is not None else ""))
        parts.append("当前方法步骤卡：\n" + format_card_for_prompt(card))
    else:
        parts.append(
            "本次是全课程答疑，不限定某一讲或某一个知识点。"
            "根据问题在全课资料中作答；不要假设学生正在学习某一个固定方法。"
        )
    return "\n".join(parts)


@router.post("/ask")
def ask(body: AskBody):
    method_id = (body.method_id or "").strip()
    # 空或 course：全课答疑，不挂某一讲的步骤卡
    card = None if method_id in ("", "course") else get_step_card(method_id)
    # 检索时附带方法关键词，减轻「这一步/符号」等空指代导致的零命中
    query = body.question
    if card and card.get("title"):
        query = f"{body.question} {card['title']}"
    hits = rag.retrieve(query)
    context = "\n\n---\n\n".join(
        f"来源：{h['source']}\n标题：{h['title']}\n{h['text'][:1200]}" for h in hits
    ) or "（未检索到足够课程片段；请优先依据步骤卡作答）"

    answer = llm.chat(
        [
            {"role": "system", "content": _build_system(card, body.section, body.section_label)},
            {
                "role": "user",
                "content": f"课程资料：\n{context}\n\n学生问题：{body.question}",
            },
        ]
    )
    return {
        "answer": answer,
        "sources": [{"source": h["source"], "title": h["title"]} for h in hits],
        "step_card": card,
    }
