# 知序 AI · 《决策理论与方法》数字人助教

院级竞赛数字人赛道。中期竖切：**期望值准则** + 图文分步 + RAG 答疑 + 题库判分 + 2D/TTS（后续接）。

## 技术选型

见 [docs/技术选型.md](docs/技术选型.md)。交付清单见 [项目交付Todolist.md](项目交付Todolist.md)。

## 目录

```
backend/          FastAPI 后端
frontend/         前端（待建 Vue3）
knowledge/        课程知识（中期：第二讲）
questions/        题库 JSON
docs/             选型与原型参考
资源/             原始资料（PPT/知识库压缩包等）
```

## 后端快速启动

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt

# 项目根目录复制环境变量
copy ..\.env.example ..\.env
# 编辑 ..\.env 填入 DEEPSEEK_API_KEY（可先不填，计算/题库仍可用）

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开接口文档：http://127.0.0.1:8000/docs

### 关键接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查、知识切片数、是否配置 LLM |
| GET | `/teach/step_card/expected_value` | 期望值步骤卡 |
| POST | `/teach/ask` | 课程约束答疑 |
| POST | `/compute/expected_value` | 程序化期望值求解 |
| GET | `/quiz/expected_value` | 题库列表 |
| POST | `/quiz/grade` | 判分 |

### 跑测试

```bash
cd backend
pytest -q
```

## 中期录视频建议路径

1. 调用 `/compute/expected_value` 展示「程序算得准」  
2. `/teach/ask` 问「期望值准则前提是什么」展示讲法对齐  
3. `/quiz` 做选择题并展示 `panel`/`speak` 字段（前端接通后由数字人播报）
