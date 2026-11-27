# 知序 AI · 《决策理论与方法》数字人助教 — 交接说明

> 更新时间：2026-11-26（口播文案已接入）  
> 用途：接手时快速对齐现状。细勾选见 [`项目交付Todolist.md`](项目交付Todolist.md)；选型见 [`docs/技术选型.md`](docs/技术选型.md)；产品回正落地见 [`docs/产品回正落地方案.md`](docs/产品回正落地方案.md)。  
> 近期前端改动概览见 [`CHANGES-简版.md`](CHANGES-简版.md)（侧栏曾做过悬停压开，**已回退为按钮折叠**）。  
> 代码仓库：https://github.com/Maplemaiden/zhixu-ai （勿提交 `.env`）

---

## 1. 是什么

北化「人工智能+管理」竞赛 · **数字人赛道**：课后 AI 助教。

**登录 → 首页 → 课程学习（一讲一入口）→ 学习台（讲解 / 实验台或案例 / 做题答疑）→ 课件全屏 / 答疑空间 / 浮层知知**

- **登录**：左右分栏（`LoginView.vue`）：左产品说明，右登录/注册；演示账号一键填入。  
- **首页**：压缩 Hero + DeepSeek 风格窄对话框；输入/点预设后跳进答疑空间并自动提问；保留开始学习 / 继续学习。  
- **课程学习**：约 10 个整讲学习台卡片；可进学习台或打开课件。  
- **学习台**：顶栏步骤按钮（在「返回目录」左侧）三段：  
  - `0` 讲解（讲义 + 划词标注 + 课件入口）  
  - `1` 有 Solver 叫 **实验台**，否则叫 **案例**（`CaseLab.vue`；名称随本讲是否挂 `computeKind` 变）  
  - `2` 做题答疑  
- **课件讲解**：全屏 `PptClassroom.vue`；浮层知知默认展开（可拖开避开缩略图）。  
- **答疑空间**：嵌在主壳内（左侧导航可用）；浅色 UI；右侧课程目录可点进知识点；`method_id: "course"`。  
- **浮层知知**：可拖动；首页大知知在视口时 / 答疑空间 / 目录页隐藏；课件页显示。

产品名：**知序 AI**；教师：王军。不用高价 3D。  
侧栏：点 `‹`/`›` 折叠（`zhixu_sidebar_collapsed`）；浮层位置：`zhixu_spirit_dock_v2`。

---

## 2. 内容结构（重要）

- **一讲一个学习台**：`lecture_ch1` … `lecture_ch10`（[`frontend/src/data/catalog.js`](frontend/src/data/catalog.js)）。  
- 旧细知识点 id 经 `TOPIC_ALIASES` / `resolveTopicRef` 映射到本讲。  
- 每讲主 `methodId` 管步骤卡/答疑/讲义；`bankId` / `casesId` 挂题库与案例。  
- **第九讲 · 多属性决策** = 教材第九章（原课堂「第十一讲」PPT 已并入，不单列）。  
- **有 Solver / 实验台**（顶栏第二段才叫实验台）：  
  - 第二讲期望值、第三讲不确定型五准则：改概率/收益/准则。  
  - 第九讲 MADM：同一张决策矩阵可切 **加权和 / 加权积 / TOPSIS**，拖权重看排序变。  
  - 决策树/贝叶斯仍用等价期望值验算，不单开引擎。  
- **其余讲第二段叫「案例」**：教材规则对照（walkthrough），没有调参。  
- 课件图：`frontend/public/lectures/{ch}/slide-XX.jpg`；索引 `lectureSlides.js` ← `lectureDecks.generated.json`。  
  - 重建：`python scripts/build_lecture_decks.py`（第九讲用 `11（多属性决策）`）。  
  - 口播：`knowledge/narration/chN.md`（按「第N页」）写入每页 `narration`；十讲页数已与课件对齐。  
- 步骤卡：`backend/app/services/step_cards*.py`。  
- 讲义：`lesson_reading.py` ← `knowledge/midterm/*.md`。  
- MADM Solver：`backend/app/solvers/madm.py`；案例：`frontend/src/data/extraCases_ch781011.js`（`computeKind: "madm"`）。

### 一讲一入口：整合了什么 / 缺什么

**不是**把以前每个细知识点内容都拼进同一页；只是**目录入口收拢**。主线内容仍只加载本讲主 `methodId` / `bankId` / `casesId`。

主 method：ch1 `overview_elements` · ch2 `expected_value` · ch3 `uncertainty_criteria` · ch4 `utility_combine` · ch5 `dea` · ch6 `goal_programming` · ch7 `ahp` · ch8 `markov` · ch9 `madm` · ch10 `discrete_sim`。

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
- 打包给别人测 / ngrok：`cd frontend && npm run build` 后开 http://127.0.0.1:8001/（ngrok 打 `8001`，改前端后要重新 build）  
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
| `POST /teach/ask` | RAG 答疑；`course` = 全课；`section` 0～2 |
| `POST /teach/classify` | 方法分类兜底 |
| `POST /compute/expected_value` · `/uncertainty` · `/madm` | Solver（实验台调用） |
| `GET /quiz/{id}` · `POST /quiz/grade` | 题库与判分 |

学习段 `section`：`0` 讲解 · `1` 实验台或案例 · `2` 做题答疑。前端会把实际段名当 `section_label` 传给 `ask`。

---

## 5. 改代码约定

1. 数字只信 Solver；模型不口算；实验台「知知解释」须带程序结果摘要。  
2. `ask`：学习台带本讲 `method_id` + `section` + `section_label`；答疑空间用 `course`。  
3. 目录只维护 `lecture_chN`；旧 id 只加别名，勿再加细入口。  
4. 公式 `$...$` / `$$...$$`；讲义/答疑走 `renderLessonMarkdown` / `renderRichText`。  
5. 课件改图或改口播后跑 `build_lecture_decks.py`；口播只改 `knowledge/narration/chN.md`，不要手改 generated json。  
6. UI 少写操作说明；侧栏用按钮折叠（勿再加悬停压开，除非产品明确要求）。  
7. 第二段命名：有 `computeKind` 才叫实验台，否则叫案例；不要再给无 Solver 的讲写「改参数」。  
8. TTS：`useSpeech` cancel 后稍等再 speak。  
9. 不提交 `.env` / `*.db` / `node_modules` / `frontend/dist`。

---

## 6. 还差什么

**中期（B6）**

- [ ] 录屏脚本 + 演示视频 + 一页纸  
- [ ] 功能冻结后只修 blocker  
- [ ] DeepSeek 余额实测  

**产品回正（部分已落地）**

- [x] 期望值 / 不确定型实验台（调参 + 前后对照 + 解释）  
- [x] 第九讲 MADM 实验台（加权和 / 加权积 / TOPSIS + 调权；ELECTRE/PROMETHEE 不做）  
- [x] 课件各页教学文案 `narration` 已导入（十讲 476 页）  
- [ ] 错题回流 / 题库加量打磨  

**刻意二期**：云口型、Chroma、内嵌原始 pptx 编辑器、AHP/DEA/目标规划等其余 Solver、正式上云。

**小债**：请求日志；`README` 可能过时；端口占用清 `8001`/`5173`。

---

## 7. 接手 15 分钟

1. 起后端 `8001 --reload` + 前端；登录页应是左右分栏；`demo/demo123`；看 `/health`。  
2. 首页：窄对话框提问应跳进答疑空间；侧栏用按钮折叠。  
3. 第二讲学习台：讲解 → **实验台**（改概率看最优方案变）→ 做题答疑。  
4. 第九讲学习台：顶栏应是「实验台」；切 TOPSIS/加权和/加权积或拖权重，排序会变。第一讲第二段应叫「案例」。  
5. 课件页应有可展开浮层知知；翻页应读该页口播（不是「请看第 N 页」）；答疑空间浅色 + 右侧目录。  
6. 中期优先 Todolist **B6**；大改看 [`docs/产品回正落地方案.md`](docs/产品回正落地方案.md)。

有冲突时：**可运行代码与 Todolist > 本 HANDOFF > 开题文档 > 过时 README**。
