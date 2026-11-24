# 知序 AI · 《决策理论与方法》数字人助教 — 交接说明

> 更新时间：2026-11-24  
> 用途：接手时快速对齐现状。细勾选见 [`项目交付Todolist.md`](项目交付Todolist.md)；选型见 [`docs/技术选型.md`](docs/技术选型.md)。

---

## 1. 是什么

北化「人工智能+管理」竞赛 · **数字人赛道**：课后 AI 助教。主路径：

**登录 → 首页 → 课程学习（课件 / 知识点）→ 学习台（讲解 / 做题答疑）→ 答疑空间 / 浮层知知**

- **首页**：一屏 Hero（知序品牌 + 今日继续学什么）；**开始学习**进目录，**继续学习**进上次知识点；无导图 / 无学习概览统计卡。  
- **课程学习**：上方「课件讲解」入口；下方知识点树（默认全折叠）+ 卡片；搜索栏在知识点区。  
- **课件讲解**：一屏锁死（不整页滚动）；主区展示**课堂真实 PPT 导出图**（`frontend/public/lectures/{ch}/slide-XX.jpg`），右侧缩略图条；答疑用浮层知知（`PptClassroom.vue`；口播优先 slide.`narration`；索引 `lectureSlides.js` ← `lectureDecks.generated.json`）；返回在左上角。重建：`python scripts/build_lecture_decks.py`（源 `资源/_解压_教学PPT/教学PPT/*.pptx`，第九讲用 `11（多属性决策）`）。  
- **学习台**：讲义 + 划词标注 + 步骤卡 + 案例/验算 + 做题答疑。  
- **答疑空间**：全屏沉浸（无侧栏）；**全课答疑**（`method_id: "course"`），不挂某一讲；左对话右知知；背景 `frontend/public/ask-space-bg.png`。  
- **浮层知知**：可拖动；首页大知知仍在视口时隐藏；答疑空间隐藏；**课件页用浮层知知**（右侧改缩略图条，不再占大栏）。  

产品名：**知序 AI**；教师：王军。不用高价 3D。  
桌面侧栏可折叠（`zhixu_sidebar_collapsed`）；手机端顶栏 + 底栏（≤720px）。

---

## 2. 内容结构（重要）

- 目录按 **讲** 分组，讲内再拆 **细知识点**（约 28 个 `ready`）。  
- **第九讲 · 多属性决策**：教材「第九章」；课堂 PPT 曾标「第十一讲」，**已合并进第九讲**，不再单列。  
- **有 Solver**：期望值、不确定型五准则；决策树/贝叶斯用等价期望值验算。  
- 细知识点：`methodId` → 步骤卡/讲义；`bankId` / `casesId` 可共用整讲题库与案例（**不要**用 bankId 回退整讲叙事/口诀）。  
- 错题「按步骤重讲」：用 `resolveTopicRef` 解析 topic/methodId/bankId，进学习台 **讲解段**（`catalog.js`）。  
- 首页 / 打开知识点：无效旧 id 用 `resolveReadyTopicId` 回退到可学知识点。

权威目录：`frontend/src/data/catalog.js`。  
课件页：`frontend/public/lectures/` 图片 + `lectureDecks.generated.json`（由课堂 `.pptx` 导出；口播暂统一「请看第 N 页」，教学文案后续再导入 `narration`）。  
步骤卡：`backend/app/services/step_cards*.py`。  
讲义：`backend/app/services/lesson_reading.py` ← `knowledge/midterm/*.md`。

### 知识 md（`knowledge/midterm/`）

概述_第一讲 · 期望值_第二讲 · 不确定型_第三讲 · 效用并合_第四讲 · DEA_第五讲 · 目标规划_第六讲 · AHP_第七讲 · 马尔可夫_第八讲 · **多属性决策_第九章**（文件名可能仍叫 `…第十一讲.md`）· 离散事件仿真_第十讲

---

## 3. 技术栈

| 层 | 选型 |
|----|------|
| 前端 | Vue3 + Vite + KaTeX；讲义 Markdown 本地渲染 |
| 后端 | FastAPI；密钥仅服务端；可托管 `frontend/dist` |
| 账号 | SQLite（`backend/data/zhixu_users.db`）；演示 `demo/demo123` |
| LLM | DeepSeek（`.env`）；402/无 Key 有降级 |
| 检索 | 关键词切片 RAG（Chroma 二期） |
| 数字人 | CSS 占位 + 浮层 / 课件侧边 / 答疑右侧知知 + 浏览器中文 TTS（租用 Web SDK 可后换壳，通常含更好音色） |

---

## 4. 怎么跑

**开发：后端 `8001`，前端 `127.0.0.1:5173`**。后端务必 `--reload`。

```bash
# 后端
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

# 前端（另开终端）
cd frontend
npm run dev
```

- 开发页：http://127.0.0.1:5173/  
- 打包给别人测：`cd frontend && npm run build` 后开 http://127.0.0.1:8001/（后端挂静态）  
- 远端临时：`ngrok http 127.0.0.1:8001`（免费版先点 Visit Site）  
- 文档：http://127.0.0.1:8001/docs · 健康：`GET /health`  
- `.env.example` → `.env`，填 `DEEPSEEK_API_KEY`

### 关键接口

| 路径 | 说明 |
|------|------|
| `POST /auth/login` · `/register` · `GET /auth/me` | 登录（`demo/demo123`） |
| `GET/POST /notes` · `DELETE /notes/{id}` | 高亮/标签（按账号） |
| `GET /teach/step_card/{method_id}` | 步骤卡 |
| `GET /teach/reading/{method_id}` | 讲义切片 |
| `POST /teach/ask` | RAG 答疑；`method_id: "course"` = 全课答疑（不挂步骤卡）；学习台/课件仍传具体 method |
| `POST /teach/classify` | 方法分类兜底 |
| `POST /compute/expected_value` · `/uncertainty` | Solver |
| `GET /quiz/{id}` · `POST /quiz/grade` | 题库与判分 |

学习段 `section`：`0` 讲解 · `1` 做题答疑。标注入口：复习页「我的标注」。

---

## 5. 改代码约定

1. 数字只信 Solver；模型不口算。  
2. `ask`：学习台带 `method_id` + `section`；课件可带页上下文；**答疑空间用 `course` + `section_label: 全课答疑`**。  
3. 细知识点文案按 `methodId`；勿用整讲 `bankId` 回退叙事。  
4. 推荐：规则关键词 → 空再 `/teach/classify`；失败不跳章。  
5. 公式 `$...$` / `$$...$$`；讲义表格走 `renderLessonMarkdown`。  
6. 多属性只维护「第九讲」一章；课件页改 `lectureSlides.js`；口播优先写 `narration` 数组，勿只念 bullet。  
7. UI 少写操作说明文案；交互靠标题与按钮自解释。  
8. 浮层位置记在 `localStorage`（`zhixu_spirit_dock_v2`）；侧栏折叠 `zhixu_sidebar_collapsed`。  
9. TTS：`useSpeech` 里 cancel 后稍等再 speak，避免 Chrome 同句读两遍。  
10. 不提交 `.env`；用户库 `*.db` 已在 `.gitignore`。

---

## 6. 还差什么（中期交付向）

- [ ] 录屏脚本 + 演示视频 + 一页纸  
- [ ] 功能冻结后只修 blocker  
- [ ] DeepSeek 余额（录屏前实测答疑）  
- [ ] 题库抽检/加量；各讲课件 `narration` / 页数可继续加厚（目前第一讲口播较完整）  
- [ ] 讲义切片匹配可再收紧  
- [ ] 手机端浮层 / 体验继续打磨  
- [ ] 浏览器 TTS 音色偏机器；二期租数字人通常自带更好语音  

**刻意不做（二期）**：云口型/租用数字人换壳、Chroma、浏览器内嵌原始 `.pptx` 编辑器、画树编辑器、全方法 Solver、正式上云、精读导图全文索引整页嵌入。（课堂 PPT 已导出为图片进课件页。）

**小债**：请求日志；`README` 可能过时；`CourseMindMap.vue` 已删；端口占用用 `netstat`/`taskkill` 清 `8001`/`5173`。

---

## 7. 接手 15 分钟

1. 起后端 `8001 --reload` + 前端；登录 `demo/demo123`；看 `/health`。  
2. 首页：开始学习 → 目录；继续学习 → 上次知识点；侧栏可折叠。  
3. 第一讲课件：听口播是否通顺；答疑空间是否全屏、是否全课检索。  
4. 确认无「第十一讲」独立章；中期只推 Todolist **B6**，别再开大功能。

有冲突时：**可运行代码与 Todolist > 开题文档 > 过时 README**。
