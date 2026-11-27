<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { api } from "../api";
import { useSpeech } from "../composables/useSpeech";

/** 课件设计稿尺寸（16:9），主舞台与缩略图按此等比缩放 */
const SLIDE_W = 1280;
const SLIDE_H = 720;

const props = defineProps({
  deck: { type: Object, required: true },
});

const emit = defineEmits(["back", "open-topic", "speech"]);

const current = ref(0);
const mode = ref("ppt");
const autoPlay = ref(false);
const askInput = ref("");
const askLoading = ref(false);
const thumbRail = ref(null);
const stageSlot = ref(null);
const stageScale = ref(1);
/** 右侧缩略图：按实际槽宽 / 1280 算出的缩放比 */
const thumbScale = ref(0.16);
const lastCaption = ref("");
const { speaking, currentLine, stop: stopSpeech, speakLines } = useSpeech();
let advanceTimer = null;
let stageRo = null;
let thumbRo = null;

const slides = computed(() => props.deck?.slides || []);
const slide = computed(() => slides.value[current.value] || null);
const caption = computed(() => currentLine.value || lastCaption.value || "");

function emitSpeech() {
  emit("speech", {
    speaking: speaking.value,
    line: currentLine.value || "",
  });
}

/** 这一页要讲的话；来自 knowledge/narration，未导入时只报页码 */
function lectureLines(s, pageIndex = 0) {
  if (!s) return [];
  if (Array.isArray(s.narration) && s.narration.length) {
    return s.narration.map((x) => String(x).trim()).filter(Boolean);
  }
  return [`请看第 ${pageIndex + 1} 页。`];
}

function pageNarrationText(s) {
  const lines = Array.isArray(s?.narration) ? s.narration : [];
  const joined = lines.map((x) => String(x).trim()).filter(Boolean).join("");
  return joined.slice(0, 480);
}

function say(text) {
  const lines = String(text || "")
    .split(/\n+/)
    .map((x) => x.trim())
    .filter(Boolean);
  if (!lines.length) return;
  speakLines(lines);
}

function narrateCurrent() {
  const lines = lectureLines(slide.value, current.value);
  if (!lines.length) return;
  speakLines(lines);
}

function clearAdvance() {
  if (advanceTimer) {
    clearTimeout(advanceTimer);
    advanceTimer = null;
  }
}

function scrollActiveThumb() {
  nextTick(() => {
    const el = thumbRail.value?.querySelector(".thumb.active");
    el?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  });
}

function fitStage() {
  const el = stageSlot.value;
  if (!el) return;
  const { clientWidth: w, clientHeight: h } = el;
  if (!w || !h) return;
  stageScale.value = Math.min(w / SLIDE_W, h / SLIDE_H);
}

function fitThumbs() {
  const rail = thumbRail.value;
  if (!rail) return;
  const sample = rail.querySelector(".thumb-viewport");
  const w = sample?.clientWidth || rail.clientWidth;
  if (!w) return;
  // 留出 4px 边框，避免裁切
  thumbScale.value = Math.max(0.05, (w - 4) / SLIDE_W);
}

function go(i) {
  if (i < 0 || i >= slides.value.length) return;
  clearAdvance();
  current.value = i;
  lastCaption.value = "";
  narrateCurrent();
  scrollActiveThumb();
}

function advance() {
  if (!autoPlay.value) return;
  if (current.value >= slides.value.length - 1) {
    autoPlay.value = false;
    mode.value = "ppt";
    say("这一段讲完了。可以点「考我一下」，或回看任一页。");
    return;
  }
  go(current.value + 1);
}

function stopAuto() {
  autoPlay.value = false;
  clearAdvance();
  stopSpeech();
  emitSpeech();
}

function play() {
  if (autoPlay.value) {
    stopAuto();
    mode.value = "ppt";
    return;
  }
  if (current.value >= slides.value.length - 1) current.value = 0;
  mode.value = "video";
  autoPlay.value = true;
  narrateCurrent();
}

function setMode(m) {
  mode.value = m;
  if (m === "video") {
    if (!autoPlay.value) play();
    return;
  }
  autoPlay.value = false;
  clearAdvance();
  narrateCurrent();
}

async function quickAsk(kind) {
  const s = slide.value;
  if (!s) return;
  if (kind === "simplify") {
    say(s.simple || "我们换个说法：先抓住本页标题里的关键词，再对照页脚提示。");
    return;
  }
  if (kind === "example") {
    say(s.example || "可以结合本讲学习台里的案例再看一遍。");
    return;
  }
  if (kind === "review") {
    go(0);
    return;
  }
  if (kind === "quiz") {
    say(s.prompt || `用一句话说明「${s.title}」要你记住什么？`);
  }
}

async function sendAsk() {
  const text = askInput.value.trim();
  if (!text || askLoading.value) return;
  askInput.value = "";

  const s = slide.value;
  if (s) {
    if (/没听懂|通俗|简单|再讲/.test(text)) {
      say(s.simple);
      return;
    }
    if (/例子|举例|案例/.test(text)) {
      say(s.example);
      return;
    }
  }

  askLoading.value = true;
  try {
    const spoken = pageNarrationText(s);
    const q = [
      `【课件页】${props.deck.chapterTitle} · ${s?.meta || ""} · ${s?.title || ""}`,
      s?.intro ? `本页导语：${s.intro}` : "",
      spoken ? `本页口播：${spoken}` : "",
      `学生问题：${text}`,
    ]
      .filter(Boolean)
      .join("\n");
    const res = await api.ask(q, props.deck.methodId, {
      section: 0,
      sectionLabel: `课件讲解 · ${s?.meta || ""}`,
    });
    say(res.answer || res.text || "我这边暂时没有生成出回答，请换个问法，或进入知识点学习台。");
  } catch (e) {
    say(
      (s?.simple || "先看本页要点。") +
        `（在线答疑暂不可用：${e.message || "网络错误"}。）`
    );
  } finally {
    askLoading.value = false;
  }
}

function bootDeck() {
  stopAuto();
  current.value = 0;
  mode.value = "ppt";
  lastCaption.value = "";
  narrateCurrent();
  scrollActiveThumb();
  nextTick(() => {
    fitStage();
    fitThumbs();
  });
}

watch(speaking, (now, prev) => {
  emitSpeech();
  if (!(prev && !now && autoPlay.value)) return;
  clearAdvance();
  advanceTimer = setTimeout(() => {
    if (autoPlay.value && !speaking.value) advance();
  }, 700);
});

watch(currentLine, (v) => {
  if (v) lastCaption.value = v;
  emitSpeech();
});

watch(
  () => props.deck?.chapterId,
  () => {
    bootDeck();
  },
  { immediate: true }
);

watch(stageSlot, (el) => {
  stageRo?.disconnect();
  stageRo = null;
  if (!el) return;
  fitStage();
  if (typeof ResizeObserver === "undefined") return;
  stageRo = new ResizeObserver(() => fitStage());
  stageRo.observe(el);
});

watch(thumbRail, (el) => {
  thumbRo?.disconnect();
  thumbRo = null;
  if (!el) return;
  nextTick(() => {
    fitThumbs();
    if (typeof ResizeObserver === "undefined") return;
    thumbRo = new ResizeObserver(() => fitThumbs());
    thumbRo.observe(el);
    const vp = el.querySelector(".thumb-viewport");
    if (vp) thumbRo.observe(vp);
  });
});

function onWinResize() {
  fitStage();
  fitThumbs();
}

onMounted(() => {
  window.addEventListener("resize", onWinResize);
  nextTick(onWinResize);
});

onBeforeUnmount(() => {
  stopAuto();
  emit("speech", { speaking: false, line: "" });
  stageRo?.disconnect();
  thumbRo?.disconnect();
  window.removeEventListener("resize", onWinResize);
});

defineExpose({
  stopAll: stopAuto,
});
</script>

<template>
  <div class="ppt-shell" v-if="deck && slide">
    <header class="ppt-top">
      <div class="top-left">
        <button class="back-btn" type="button" @click="stopAuto(); $emit('back')">← 返回</button>
        <div class="brand"><i>知</i><span>知序 AI</span></div>
        <span class="crumb">{{ deck.chapterTitle }} · 课件讲解</span>
      </div>
      <div class="top-right">
        <div class="mode-switch">
          <button type="button" :class="{ active: mode === 'ppt' }" @click="setMode('ppt')">▣ PPT</button>
          <button type="button" :class="{ active: mode === 'video' }" @click="setMode('video')">▶ 自动</button>
        </div>
        <span class="pill">{{ String(current + 1).padStart(2, "0") }} / {{ String(slides.length).padStart(2, "0") }}</span>
        <button type="button" class="linkish" @click="$emit('open-topic', deck.topicId)">进入学习台 →</button>
      </div>
    </header>

    <div class="ppt-body">
      <section class="classroom">
        <div class="screen" :class="{ 'video-mode': mode === 'video' }">
          <div class="screen-top">
            <span class="live">{{ speaking ? "知知讲解中" : autoPlay ? "自动演示 · 播放中" : "课件 · 正在学习" }}</span>
            <span>《决策理论与方法》</span>
          </div>

          <div class="stage-slot" ref="stageSlot">
            <div
              class="stage-board"
              :style="{
                width: `${SLIDE_W * stageScale}px`,
                height: `${SLIDE_H * stageScale}px`,
              }"
            >
              <div
                class="slide-surface"
                :class="{ 'is-image': !!slide.image }"
                :style="{
                  width: `${SLIDE_W}px`,
                  height: `${SLIDE_H}px`,
                  transform: `scale(${stageScale})`,
                }"
              >
                <div class="video-badge">自动演示 · 课件轮播</div>
                <template v-if="slide.image">
                  <img class="slide-photo" :src="slide.image" :alt="slide.title" draggable="false" />
                </template>
                <template v-else>
                  <span class="slide-meta">{{ slide.meta }}</span>
                  <h2>{{ slide.title }}</h2>
                  <p class="slide-intro">{{ slide.intro }}</p>
                  <div class="slide-body" v-html="slide.body" />
                  <div class="slide-foot">
                    <span>{{ slide.footer }}</span>
                    <b>知序 AI · 决策理论助教</b>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <div class="caption-bar" :class="{ live: !!currentLine, empty: !caption }">
            <span class="caption-tag">知知</span>
            <p class="caption-text">{{ caption || "点播放，听知知讲这一页" }}</p>
          </div>

          <div class="screen-bar">
            <div class="screen-controls">
              <button class="control" type="button" :disabled="current === 0" @click="go(current - 1)">← 上一页</button>
              <button class="control primary" type="button" @click="play">
                {{ autoPlay ? "❚❚ 暂停" : "▶ 播放" }}
              </button>
              <button
                class="control"
                type="button"
                :disabled="current >= slides.length - 1"
                @click="go(current + 1)"
              >
                下一页 →
              </button>
              <button type="button" class="chip" @click="quickAsk('simplify')">这页没听懂</button>
              <button type="button" class="chip" @click="quickAsk('example')">举个例子</button>
              <button type="button" class="chip" @click="quickAsk('quiz')">考我一下</button>
              <form class="ask-inline" @submit.prevent="sendAsk">
                <input v-model="askInput" :disabled="askLoading" placeholder="提问本页…" />
                <button type="submit" :disabled="askLoading">{{ askLoading ? "…" : "问" }}</button>
              </form>
            </div>
          </div>
        </div>
      </section>

      <aside class="thumb-rail" ref="thumbRail" aria-label="课件缩略图">
        <button
          v-for="(s, i) in slides"
          :key="i"
          type="button"
          class="thumb"
          :class="{ active: i === current }"
          @click="go(i)"
        >
          <span class="thumb-num">{{ String(i + 1).padStart(2, "0") }}</span>
          <div class="thumb-viewport">
            <img
              v-if="s.image"
              class="thumb-photo"
              :src="s.image"
              :alt="s.title"
              loading="lazy"
              draggable="false"
            />
            <div
              v-else
              class="slide-surface thumb-surface"
              :style="{
                width: `${SLIDE_W}px`,
                height: `${SLIDE_H}px`,
                transform: `scale(${thumbScale})`,
              }"
              aria-hidden="true"
            >
              <span class="slide-meta">{{ s.meta }}</span>
              <h2>{{ s.title }}</h2>
              <p class="slide-intro">{{ s.intro }}</p>
              <div class="slide-body" v-html="s.body" />
              <div class="slide-foot">
                <span>{{ s.footer }}</span>
                <b>知序 AI</b>
              </div>
            </div>
          </div>
        </button>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.ppt-shell {
  --ink: #18283e;
  --navy: #172940;
  --teal: #146e65;
  --mint: #d9efe5;
  --paper: #e8ece7;
  --sub: #68798a;
  --line: #dce4e1;
  --slide-w: 1280;
  height: 100dvh;
  max-height: 100dvh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--paper);
  color: var(--ink);
}
.ppt-top {
  flex: 0 0 auto;
  height: 48px;
  padding: 0 clamp(12px, 2vw, 24px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid var(--line);
  background: #fff;
}
.top-left,
.top-right {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.back-btn {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 750;
  cursor: pointer;
  color: var(--ink);
  flex-shrink: 0;
}
.back-btn:hover {
  border-color: var(--teal);
  color: var(--teal);
  background: #f3faf7;
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 900;
  font-size: 14px;
  flex-shrink: 0;
}
.brand i {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  background: var(--mint);
  color: var(--navy);
  font-style: normal;
  border-radius: 9px;
  font-size: 13px;
}
.crumb {
  color: var(--sub);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pill {
  background: #e8f4ed;
  color: var(--teal);
  padding: 5px 10px;
  border-radius: 99px;
  font-size: 12px;
  font-weight: 800;
  flex-shrink: 0;
}
.mode-switch {
  padding: 3px;
  background: #e8ede9;
  border-radius: 10px;
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}
.mode-switch button {
  border: 0;
  background: transparent;
  border-radius: 8px;
  color: #657685;
  font-size: 12px;
  font-weight: 800;
  padding: 6px 10px;
  cursor: pointer;
}
.mode-switch button.active {
  background: #fff;
  color: var(--teal);
}
.linkish {
  border: 0;
  background: none;
  color: var(--teal);
  font-weight: 800;
  cursor: pointer;
  padding: 0;
  font-size: 12px;
  white-space: nowrap;
}
.ppt-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 228px;
  gap: 12px;
  padding: 10px clamp(10px, 1.5vw, 16px) 10px;
  overflow: hidden;
}
.classroom {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.screen {
  flex: 1;
  min-height: 0;
  background: #14283e;
  border-radius: 14px;
  padding: 8px 10px 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 12px 28px rgba(20, 40, 57, 0.12);
  overflow: hidden;
}
.screen-top {
  display: flex;
  justify-content: space-between;
  color: #b9cbd4;
  font-size: 11px;
  padding: 0 4px;
  flex: 0 0 auto;
}
.live {
  display: flex;
  align-items: center;
  gap: 7px;
}
.live::before {
  content: "";
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #9ae1c7;
}

/* 主舞台：在可用区域内居中放入 16:9 */
.stage-slot {
  flex: 1;
  min-height: 0;
  display: grid;
  place-items: center;
  overflow: hidden;
}
.stage-board {
  position: relative;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28);
  background: #fbfcf8;
}
.slide-surface {
  position: absolute;
  left: 0;
  top: 0;
  transform-origin: top left;
  background: #fbfcf8;
  display: flex;
  flex-direction: column;
  padding: 42px 56px 36px;
  box-sizing: border-box;
  overflow: hidden;
  color: var(--ink);
}
.slide-surface.is-image {
  padding: 0;
  background: #0b1724;
}
.slide-photo {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  background: #0b1724;
  user-select: none;
}
.thumb-photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  background: #0b1724;
  user-select: none;
  pointer-events: none;
}
.video-badge {
  display: none;
  position: absolute;
  right: 28px;
  top: 24px;
  background: #172940;
  color: #fff;
  border-radius: 99px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 800;
}
.video-mode .video-badge {
  display: block;
}
.slide-meta {
  font-size: 14px;
  font-weight: 900;
  color: var(--teal);
  letter-spacing: 0.16em;
  flex: 0 0 auto;
}
.slide-surface h2 {
  font-size: 44px;
  letter-spacing: -0.04em;
  line-height: 1.18;
  margin: 16px 0 10px;
  flex: 0 0 auto;
}
.slide-intro {
  font-size: 18px;
  color: #536579;
  line-height: 1.55;
  margin: 0;
  max-width: 920px;
  flex: 0 0 auto;
}
.slide-body {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  padding: 18px 0;
  overflow: hidden;
}
.slide-foot {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  color: #7b8b93;
  border-top: 1px solid #e5ece8;
  padding-top: 14px;
  flex: 0 0 auto;
}
.slide-foot b {
  color: var(--teal);
}

/* 字幕：数字人口播 */
.caption-bar {
  flex: 0 0 auto;
  min-height: 52px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(8, 18, 28, 0.55);
  border: 1px solid rgba(158, 201, 186, 0.28);
}
.caption-bar.live {
  border-color: rgba(154, 225, 199, 0.55);
  background: rgba(12, 36, 40, 0.72);
}
.caption-bar.empty {
  opacity: 0.72;
}
.caption-tag {
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 900;
  color: #104d47;
  background: #c5edda;
  border-radius: 999px;
  padding: 3px 9px;
  margin-top: 1px;
}
.caption-text {
  margin: 0;
  flex: 1;
  min-width: 0;
  color: #e8f2f0;
  font-size: 14px;
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.screen-bar {
  flex: 0 0 auto;
}
.screen-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #d2dfe3;
  flex-wrap: wrap;
}
.control {
  border: 1px solid #516578;
  color: #e6f0f0;
  background: transparent;
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}
.control.primary {
  border-color: #c5edda;
  background: #c5edda;
  color: #104d47;
}
.control:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.chip {
  border: 1px solid #516578;
  color: #d7e6e8;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  padding: 6px 9px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}
.ask-inline {
  display: flex;
  gap: 6px;
  margin-left: auto;
  min-width: 0;
  flex: 1 1 180px;
  max-width: 280px;
}
.ask-inline input {
  min-width: 0;
  flex: 1;
  border: 1px solid #516578;
  background: rgba(255, 255, 255, 0.06);
  color: #e8f2f2;
  border-radius: 8px;
  padding: 6px 9px;
  font-size: 12px;
}
.ask-inline input::placeholder {
  color: #8aa0a8;
}
.ask-inline button {
  border: 0;
  background: #1c6d62;
  color: #fff;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

/* 右侧：真实 16:9 缩略图（整页内容等比缩小） */
.thumb-rail {
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 2px 4px 2px 0;
  scrollbar-width: thin;
  scrollbar-color: #9bb0ae transparent;
}
.thumb {
  position: relative;
  display: block;
  width: 100%;
  border: 0;
  background: transparent;
  padding: 0;
  cursor: pointer;
  text-align: left;
  flex: 0 0 auto;
}
.thumb-num {
  position: absolute;
  z-index: 2;
  left: 6px;
  top: 6px;
  font-size: 10px;
  font-weight: 900;
  color: #6f8480;
  background: rgba(232, 241, 236, 0.95);
  border-radius: 4px;
  padding: 1px 5px;
  pointer-events: none;
}
.thumb.active .thumb-num {
  background: #146e65;
  color: #fff;
}
.thumb-viewport {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 8px;
  overflow: hidden;
  background: #fbfcf8;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(20, 40, 57, 0.08);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.thumb:hover .thumb-viewport {
  border-color: #9ec9ba;
}
.thumb.active .thumb-viewport {
  border-color: var(--teal);
  box-shadow: 0 0 0 1px rgba(20, 110, 101, 0.2), 0 8px 18px rgba(20, 40, 57, 0.12);
}
.thumb-surface {
  position: absolute;
  left: 0;
  top: 0;
  transform-origin: top left;
  pointer-events: none;
  user-select: none;
}

/* v-html 课件块（设计稿字号，靠外层 scale/zoom 缩小） */
.slide-surface :deep(.ppt-bullets) {
  margin: 0;
  padding-left: 1.2em;
  font-size: 24px;
  line-height: 1.55;
  color: #274b49;
}
.slide-surface :deep(.ppt-bullets li) {
  margin: 10px 0;
}
.slide-surface :deep(.condition) {
  display: flex;
  align-items: stretch;
  gap: 16px;
  max-width: 980px;
  width: 100%;
}
.slide-surface :deep(.condition .node) {
  border: 1px solid #d7e3db;
  background: #fff;
  border-radius: 14px;
  padding: 22px;
  flex: 1;
  min-height: 96px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 24px;
  font-weight: 800;
}
.slide-surface :deep(.condition .node.em) {
  background: #daf0e4;
  border-color: #a8d9bd;
  color: #125e55;
}
.slide-surface :deep(.condition .arrow) {
  align-self: center;
  font-size: 30px;
  color: var(--teal);
}
.slide-surface :deep(.data-table) {
  width: min(900px, 100%);
  border-collapse: separate;
  border-spacing: 0;
  font-size: 20px;
  border: 1px solid #d8e5df;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}
.slide-surface :deep(.data-table th),
.slide-surface :deep(.data-table td) {
  padding: 14px 12px;
  text-align: center;
  border-bottom: 1px solid #e0e9e5;
}
.slide-surface :deep(.data-table th) {
  background: #e7f2eb;
  color: #205c54;
}
.slide-surface :deep(.data-table td:first-child) {
  font-weight: 800;
}
.slide-surface :deep(.equations) {
  display: grid;
  gap: 12px;
  max-width: 900px;
  width: 100%;
}
.slide-surface :deep(.equation) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid #dce7e0;
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  font-size: 22px;
  font-weight: 800;
}
.slide-surface :deep(.equation.highlight) {
  border-color: #79bfaa;
  background: #e2f3e8;
  color: #105b51;
}
.slide-surface :deep(.equation small) {
  font-size: 14px;
  color: #688076;
  font-weight: 500;
}
.slide-surface :deep(.result) {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}
.slide-surface :deep(.big-number) {
  font-size: 72px;
  font-weight: 900;
  letter-spacing: -0.06em;
  color: var(--teal);
}
.slide-surface :deep(.result-rule) {
  font-size: 24px;
  font-weight: 800;
  max-width: 360px;
}

@media (max-width: 980px) {
  .ppt-body {
    grid-template-columns: minmax(0, 1fr) 168px;
  }
  .crumb,
  .linkish {
    display: none;
  }
  .ask-inline {
    max-width: none;
    flex-basis: 100%;
    margin-left: 0;
  }
}

@media (max-width: 640px) {
  .ppt-body {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(0, 1fr) 108px;
  }
  .thumb-rail {
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
    gap: 8px;
  }
  .thumb {
    flex: 0 0 168px;
  }
  .caption-text {
    -webkit-line-clamp: 2;
    font-size: 13px;
  }
}
</style>
