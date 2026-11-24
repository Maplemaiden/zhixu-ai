from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import ROOT, get_settings
from app.routers import auth, compute, health, notes, quiz, teach
from app.services import rag, user_db

settings = get_settings()
FRONTEND_DIST = ROOT / "frontend" / "dist"

app = FastAPI(
    title="知序AI · 决策理论数字人助教 API",
    version="0.1.0",
    description="课程助教：概述 / 期望值 / 决策树 / 贝叶斯 / 不确定型准则 + RAG 答疑 + 题库判分",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(compute.router)
app.include_router(teach.router)
app.include_router(quiz.router)


@app.on_event("startup")
def _startup():
    user_db.init_db()
    rag.load_chunks(force=True)


# 远端试用：npm run build 后由后端托管前端；ngrok 只需打 8001（避免 Vite 开发服白屏）
if FRONTEND_DIST.is_dir() and (FRONTEND_DIST / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="spa")
