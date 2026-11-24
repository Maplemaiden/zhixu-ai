# 知序 AI · 《决策理论与方法》数字人助教 — 交接说明

> 更新时间：2026-11-24  
> 用途：接手时快速对齐现状。细勾选见 [`项目交付Todolist.md`](项目交付Todolist.md)；选型见 [`docs/技术选型.md`](docs/技术选型.md)；产品回正落地见 [`docs/产品回正落地方案.md`](docs/产品回正落地方案.md)。  
> 代码仓库（公开）：https://github.com/Maplemaiden/zhixu-ai （勿提交 `.env`）

---

## 1. 是什么

北化「人工智能+管理」竞赛 · **数字人赛道**：课后 AI 助教。

**登录 → 首页 → 课程学习（一讲一入口）→ 学习台（讲解 / 做题答疑）→ 课件全屏 / 答疑空间 / 浮层知知**

- **首页**：Hero（知序 + 今日继续学哪一讲）；开始学习 / 继续学习；可直达全课答疑。  
- **课程学习**：目录为 **10 个整讲学习台卡片**（可搜讲次）；卡上可进学习台或打开课件。  
- **学习台**：本讲提纲 + 讲义 + 划词标注 + 案例/验算 +「进入课件讲解」入口 + 做题答疑。  
- **课件讲解**：全屏 `PptClassroom.vue`（16:9 真 PPT 图 + 右侧缩略图 + 浮层知知默认展开）；从学习台进则返回学习台。  
- **答疑空间**：全屏；`method_id: "course"`；助教气泡走 Markdown（含 `**` / 标题 / 列表）+ KaTeX。  
- **浮层知知**：可拖动；首页大知知在视口时隐藏；答疑空间隐藏。

产品名：**知序 AI**；教师：王军。不用高价 3D。  
侧栏折叠键：`zhixu_sidebar_collapsed`；浮层位置：`zhixu_spirit_dock_v2`。

---

## 2. 内容结构（重要）

- **一讲一个学习台**：`lecture_ch1` … `lecture_ch10`（[`frontend/src/data/catalog.js`](frontend/src/data/catalog.js)）。  
- 旧细知识点 id（如 `overview_elements`、`madm9_scoring`）经 `TOPIC_ALIASES` / `resolveTopicRef` 映射到本讲。  
- 每讲主 `methodId` 管步骤卡/答疑/讲义；`bankId` / `casesId` 挂题库与案例。  
- **第九讲 · 多属性决策** = 教材第九章（原课堂「第十一讲」PPT 已并入，不单列）。  
- **有 Solver**：期望值、不确定型五准则；决策树/贝叶斯用等价期望值验算。  
- 课件图：`frontend/public/lectures/{ch}/slide-XX.jpg`；索引 `lectureSlides.js` ← `lectureDecks.generated.json`。  
  - 重建：`python scripts/build_lecture_decks.py`（源 `资源/_解压_教学PPT/教学PPT/*.pptx`，第九讲用 `11（多属性决策）`）。  
  - 口播暂统一「请看第 N 页」；教学文案后续写入 slide.`narration`。  
- 步骤卡：`backend/app/services/step_cards*.py`。  
- 讲义：`lesson_reading.py` ← `knowledge/midterm/*.md`；前端 `renderLessonMarkdown`（支持到 `#####`、加粗、列表、表格、公式）。

### 一讲一入口：整合了什么 / 缺什么（重要）

**不是**把以前每个细知识点的讲义、题库、案例、步骤卡都拼进同一页；只是**目录入口收拢**。

| 已整合 | 说明 |
|--------|------|
| 导航 | 一讲进一个台；旧细 id 能跳进对应讲 |
| 提纲 | `outline` 列出原细点名称（指路，不等于已加载） |
| 课件 | 整讲 PPT 可从学习台进 |
| 主线内容 | **仅主 `methodId` / `bankId` / `casesId`** 的步骤卡、讲义切片、案例、题库、答疑 |

| 未整合（缺口） | 说明 |
|----------------|------|
| 讲义 | `/teach/reading` 按主 method 切片；如第二讲偏期望值，决策树/贝叶斯专属切片默认进不来 |
| 题库/案例 | 未按讲合并抽题池；第二讲目前主要是 `expected_value`，不含 `decision_tree` / `bayes` 库 |
| 步骤卡/叙事 | 只加载主 method；细入口专属叙事不会自动串播 |
| 进度 | 键为 `lecture_chN`；旧细 id 进度不自动合并 |
| 实验室 | 未做；入口形态便于以后挂整讲实验室 |

主 method 对照：ch1 `overview_elements` · ch2 `expected_value` · ch3 `uncertainty_criteria` · ch4 `utility_combine` · ch5 `dea` · ch6 `goal_programming` · ch7 `ahp` · ch8 `markov` · ch9 `madm` · ch10 `discrete_sim`。

若要「真整合」：按讲合并讲义切片 + 题库/案例池，或台内按提纲分段切换（不必再回目录）。

### 知识 md（`knowledge/midterm/`）

概述_第一讲 · 期望值_第二讲 · 不确定型_第三讲 · 效用并合_第四讲 · DEA_第五讲 · 目标规划_第六讲 · AHP_第七讲 · 马尔可夫_第八讲 · **多属性决策_第九章** · 离散事件仿真_第十讲

---

## 3. 技术栈

| 层 | 选型 |
|----|------|
| 前端 | Vue3 + Vite + KaTeX；讲义/答疑 Markdown 本地渲染 |
| 后端 | FastAPI；密钥仅服务端；可托管 `frontend/dist` |
| 账号 | SQLite（`backend/data/*.db` 已 gitignore）；演示 `demo/demo123` |
| LLM | DeepSeek（`.env`）；402/无 Key 有降级 |
| 检索 | 关键词切片 RAG（Chroma 二期） |
| 数字人 | CSS 占位 + 浮层知知 + 浏览器中文 TTS |

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
- 打包给别人测：`cd frontend && npm run build` 后开 http://127.0.0.1:8001/  
- 远端临时：`ngrok http 127.0.0.1:8001`（免费版先点 Visit Site）  
- 健康：`GET /health` · 文档：`/docs`  
- `.env.example` → `.env`，填 `DEEPSEEK_API_KEY`

### 关键接口

| 路径 | 说明 |
|------|------|
| `POST /auth/login` · `/register` · `GET /auth/me` | 登录（`demo/demo123`） |
| `GET/POST /notes` · `DELETE /notes/{id}` | 高亮/标注 |
| `GET /teach/step_card/{method_id}` | 步骤卡 |
| `GET /teach/reading/{method_id}` | 讲义切片 |
| `POST /teach/ask` | RAG 答疑；`course` = 全课 |
| `POST /teach/classify` | 方法分类兜底 |
| `POST /compute/expected_value` · `/uncertainty` | Solver |
| `GET /quiz/{id}` · `POST /quiz/grade` | 题库与判分 |

学习段 `section`：`0` 讲解 · `1` 做题答疑。

---

## 5. 改代码约定

1. 数字只信 Solver；模型不口算。  
2. `ask`：学习台带本讲 `method_id` + `section`；答疑空间用 `course`。  
3. 目录只维护 `lecture_chN`；旧 id 只加别名，勿再加细入口。  
4. 公式 `$...$` / `$$...$$`；讲义/答疑 Markdown 走 `renderLessonMarkdown` / `renderRichText`。  
5. 课件改图后跑 `build_lecture_decks.py`；口播优先 `narration`。  
6. UI 少写操作说明；浮层/侧栏状态用现有 localStorage 键。  
7. TTS：`useSpeech` cancel 后稍等再 speak。  
8. 不提交 `.env` / `*.db` / `node_modules` / `frontend/dist`。

---

## 6. 还差什么

**中期（B6）**

- [ ] 录屏脚本 + 演示视频 + 一页纸  
- [ ] 功能冻结后只修 blocker  
- [ ] DeepSeek 余额实测  

**产品回正（见落地方案，未做完）**

- [ ] 动态案例实验室（TOPSIS 调权优先 / 期望值保底）  
- [ ] 答疑右侧从大形象改为学习辅助面板  
- [ ] 课件各页教学文案 `narration` 统一导入  
- [ ] 「再做一题」/ 错题回流打磨  

**刻意二期**：云口型、Chroma、内嵌原始 pptx 编辑器、全方法 Solver、正式上云。

**小债**：请求日志；`README` 可能过时；端口占用清 `8001`/`5173`。

---

## 7. 接手 15 分钟

1. 起后端 `8001 --reload` + 前端；登录 `demo/demo123`；看 `/health`。  
2. 课程学习：应看到约 10 张整讲卡；点进学习台 → 课件入口 → 返回学习台。  
3. 答疑空间：Markdown/公式正常；无「第十一讲」独立章。  
4. 中期优先 Todolist **B6**；大改看 [`docs/产品回正落地方案.md`](docs/产品回正落地方案.md)。

有冲突时：**可运行代码与 Todolist > 本 HANDOFF > 开题文档 > 过时 README**。
