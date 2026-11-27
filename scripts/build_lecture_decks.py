# -*- coding: utf-8 -*-
"""Scan frontend/public/lectures/*/slide-*.jpg and write lectureDecks.generated.json.

口播文案：knowledge/narration/chN.md（第N页：……），写入每页 narration。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LECTURE_ROOT = ROOT / "frontend" / "public" / "lectures"
NARRATION_ROOT = ROOT / "knowledge" / "narration"
OUT = ROOT / "frontend" / "src" / "data" / "lectureDecks.generated.json"

PAGE_HEAD = re.compile(r"^第(\d+)页[：:]\s*$", re.M)
# 字幕两行约 70 字；按句切，过长再按分号/逗号切开
TTS_MAX = 72

META = {
    "ch1": {
        "title": "决策理论与方法概述",
        "chapterTitle": "第一讲 · 决策理论与方法概述",
        "methodId": "overview_elements",
        "topicId": "lecture_ch1",
        "source": "1（决策理论与方法概述）.pptx",
    },
    "ch2": {
        "title": "风险型决策",
        "chapterTitle": "第二讲 · 风险型决策",
        "methodId": "expected_value",
        "topicId": "lecture_ch2",
        "source": "2（风险型决策）.pptx",
    },
    "ch3": {
        "title": "不确定型决策分析",
        "chapterTitle": "第三讲 · 不确定型决策分析",
        "methodId": "uncertainty_criteria",
        "topicId": "lecture_ch3",
        "source": "3（不确定型决策分析）.pptx",
    },
    "ch4": {
        "title": "多维效用并合模型",
        "chapterTitle": "第四讲 · 多维效用并合模型",
        "methodId": "utility_combine",
        "topicId": "lecture_ch4",
        "source": "4（多维效用并合模型）.pptx",
    },
    "ch5": {
        "title": "数据包络分析",
        "chapterTitle": "第五讲 · 数据包络分析",
        "methodId": "dea",
        "topicId": "lecture_ch5",
        "source": "5（数据包络分析）.pptx",
    },
    "ch6": {
        "title": "目标规划",
        "chapterTitle": "第六讲 · 目标规划",
        "methodId": "goal_programming",
        "topicId": "lecture_ch6",
        "source": "6（多目标决策问题的线性规划方法）.pptx",
    },
    "ch7": {
        "title": "层次分析法",
        "chapterTitle": "第七讲 · 层次分析法",
        "methodId": "ahp",
        "topicId": "lecture_ch7",
        "source": "7（层次分析法）.pptx",
    },
    "ch8": {
        "title": "马尔可夫决策",
        "chapterTitle": "第八讲 · 马尔可夫决策",
        "methodId": "markov",
        "topicId": "lecture_ch8",
        "source": "8（马尔可夫决策）.pptx",
    },
    "ch9": {
        "title": "多属性决策",
        "chapterTitle": "第九讲 · 多属性决策",
        "methodId": "madm",
        "topicId": "lecture_ch9",
        "source": "11（多属性决策）.pptx",
    },
    "ch10": {
        "title": "离散事件系统与仿真",
        "chapterTitle": "第十讲 · 离散事件系统与仿真",
        "methodId": "discrete_sim",
        "topicId": "lecture_ch10",
        "source": "10（离散事件系统与仿真）.pptx",
    },
}


def parse_narration_md(path: Path) -> dict[int, str]:
    text = path.read_text(encoding="utf-8")
    matches = list(PAGE_HEAD.finditer(text))
    pages: dict[int, str] = {}
    for i, m in enumerate(matches):
        n = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        pages[n] = text[start:end].strip()
    return pages


def split_for_tts(text: str) -> list[str]:
    raw = re.sub(r"[ \t]+", "", text or "")
    raw = re.sub(r"\n+", "", raw).strip()
    if not raw:
        return []
    sentences = [s.strip() for s in re.findall(r"[^。！？]+[。！？]?", raw) if s.strip()]
    lines: list[str] = []
    for s in sentences:
        if len(s) <= TTS_MAX:
            lines.append(s)
            continue
        pieces = [p.strip() for p in re.split(r"(?<=[；;])", s) if p.strip()]
        buf = ""
        for p in pieces:
            chunks = re.split(r"(?<=，)", p) if len(p) > TTS_MAX and "，" in p else [p]
            for q in chunks:
                q = q.strip()
                if not q:
                    continue
                if buf and len(buf) + len(q) > TTS_MAX:
                    lines.append(buf)
                    buf = q
                else:
                    buf += q
        if buf:
            lines.append(buf)
    return lines


def load_narration(ch: str, n_slides: int) -> dict[int, list[str]]:
    path = NARRATION_ROOT / f"{ch}.md"
    if not path.exists():
        raise SystemExit(f"missing narration {path}")
    pages = parse_narration_md(path)
    expected = set(range(1, n_slides + 1))
    got = set(pages)
    if got != expected:
        missing = sorted(expected - got)
        extra = sorted(got - expected)
        raise SystemExit(
            f"{ch} narration mismatch: slides={n_slides} "
            f"missing={missing[:8]} extra={extra[:8]}"
        )
    out: dict[int, list[str]] = {}
    empty = []
    for n, body in pages.items():
        lines = split_for_tts(body)
        if not lines:
            empty.append(n)
        out[n] = lines
    if empty:
        raise SystemExit(f"{ch} empty narration pages: {empty}")
    return out


def main() -> None:
    decks: dict = {}
    total = 0
    narr_pages = 0
    for ch, info in META.items():
        folder = LECTURE_ROOT / ch
        files = sorted(folder.glob("slide-*.jpg"))
        if not files:
            raise SystemExit(f"no slides for {ch} in {folder}")
        spoken = load_narration(ch, len(files))
        slides = []
        for idx, path in enumerate(files, start=1):
            lines = spoken[idx]
            slides.append(
                {
                    "meta": f"{idx:02d} / 课堂课件",
                    "title": f"{info['chapterTitle']} · 第 {idx} 页",
                    "image": f"/lectures/{ch}/{path.name}",
                    "intro": lines[0] if lines else "",
                    "narration": lines,
                    "footer": info["source"],
                }
            )
        decks[ch] = {
            "chapterId": ch,
            "title": info["title"],
            "chapterTitle": info["chapterTitle"],
            "methodId": info["methodId"],
            "topicId": info["topicId"],
            "sourceFile": info["source"],
            "slides": slides,
        }
        total += len(slides)
        narr_pages += len(spoken)

    OUT.write_text(json.dumps(decks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({len(decks)} decks, {total} slides, {narr_pages} narrations)")


if __name__ == "__main__":
    main()
