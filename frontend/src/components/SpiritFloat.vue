<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { api } from "../api";
import { useSpeech } from "../composables/useSpeech";
import { findTopic, resolveTopicRef } from "../data/catalog";
import { renderRichText } from "../utils/renderRichText";

const props = defineProps({
  visible: { type: Boolean, default: true },
  contextId: { type: String, default: "lecture_ch2" },
  backendOk: { type: Boolean, default: true },
  /** 外部口播（学习台等） */
  externalSpeaking: { type: Boolean, default: false },
  externalPaused: { type: Boolean, default: false },
  externalLine: { type: String, default: "" },
  bottomPad: { type: Number, default: 24 },
  /** 进入时默认展开（课件页用） */
  defaultExpanded: { type: Boolean, default: false },
});

const emit = defineEmits(["open-qa", "open-topic", "stop-external"]);

const POS_KEY = "zhixu_spirit_dock_v2";
const { speaking, paused, currentLine, stop, speakText } = useSpeech();

const expanded = ref(false);
const input = ref("");
const loading = ref(false);
const error = ref("");
const lastReply = ref("");
const rootEl = ref(null);

/** 屏幕坐标：当前浮层左上角 */
const pos = ref({ x: 0, y: 0 });
/** 收起态用户拖到的位置；展开/收起后都要回到这里 */
const dockPos = ref({ x: 0, y: 0 });
const dragging = ref(false);
const dragMoved = ref(false);
let dragOffset = { x: 0, y: 0 };
let ptrId = null;

const contextMeta = computed(() => resolveTopicRef(props.contextId) || findTopic("lecture_ch2"));
const methodId = computed(
  () => contextMeta.value?.topic?.methodId || contextMeta.value?.topic?.id || "expected_value"
);
const contextTitle = computed(() => contextMeta.value?.topic?.title || "课程答疑");

const isSpeaking = computed(() => props.externalSpeaking || speaking.value);
const isPaused = computed(() => (props.externalSpeaking ? props.externalPaused : paused.value));
const line = computed(() => {
  if (loading.value) return "知知思考中…";
  if (props.externalSpeaking && props.externalLine) return props.externalLine;
  if (currentLine.value) return currentLine.value;
  if (lastReply.value) return lastReply.value.slice(0, 80);
  return expanded.value ? contextTitle.value : "知知";
});

/** 侧栏图标条宽 76px；浮层最小 x 留 8px 间隙，避免拖过去把导航盖死 */
const SIDEBAR_RAIL = 84;
/** 侧栏只在桌面端存在（≤720 隐藏），那时才需要让开图标条 */
function minX() {
  return window.innerWidth > 720 ? SIDEBAR_RAIL : 8;
}
function clampToSize(x, y, w, h) {
  const gap = 8;
  const lo = minX();
  // 关键：右边界必须先满足可用空间，否则窄屏下 Math.max 会把面板推出视口
  const maxX = Math.max(lo, window.innerWidth - w - gap);
  const maxY = Math.max(8, window.innerHeight - h - props.bottomPad);
  return {
    x: Math.min(maxX, Math.max(lo, x)),
    y: Math.min(maxY, Math.max(8, y)),
  };
}

function clampPos(x, y) {
  const w = rootEl.value?.offsetWidth || (expanded.value ? 320 : 74);
  const h = rootEl.value?.offsetHeight || (expanded.value ? 360 : 88);
  return clampToSize(x, y, w, h);
}

function saveDock() {
  try {
    localStorage.setItem(POS_KEY, JSON.stringify(dockPos.value));
  } catch {
    /* ignore */
  }
}

function defaultDock() {
  const thumb = document.querySelector(".thumb-rail");
  const rightReserve = thumb ? thumb.getBoundingClientRect().width + 104 : 120;
  return clampToSize(window.innerWidth - rightReserve, window.innerHeight - 200, 74, 88);
}

function loadPos() {
  try {
    const raw = localStorage.getItem(POS_KEY);
    if (raw) {
      const p = JSON.parse(raw);
      const dock = clampToSize(Number(p.x) || 0, Number(p.y) || 0, 74, 88);
      dockPos.value = dock;
      pos.value = { ...dock };
      return;
    }
  } catch {
    /* ignore */
  }
  const dock = defaultDock();
  dockPos.value = dock;
  pos.value = { ...dock };
}

/** 展开时尽量贴着 dock，只在越界时轻推，避免弹到屏幕角。
 *  额外避让右栏数字人面板（.avatar-panel）：展开后若与之重叠，
 *  整体左移到它的左侧，避免盖住播放/停止按钮。 */
function placeExpandedNearDock() {
  const dock = dockPos.value;
  const w = rootEl.value?.offsetWidth || 320;
  const h = rootEl.value?.offsetHeight || 360;
  const dockW = 74;
  const dockH = 88;
  // 优先：面板右下角对齐小精灵右下角（右下角浮层展开时几乎不跳）
  let x = dock.x + dockW - w;
  let y = dock.y + dockH - h;

  // 避让右栏播放器、课件右侧缩略图栏与讲义划词浮层
  const avoidSelectors = [".avatar-panel .player", ".thumb-rail", ".anno-toolbar"];
  for (const sel of avoidSelectors) {
    const el = document.querySelector(sel);
    if (!el) continue;
    const pr = el.getBoundingClientRect();
    if (!pr.width || !pr.height) continue;
    const overlapsX = x + w > pr.left - 8 && x < pr.right + 8;
    const overlapsY = y + h > pr.top - 8 && y < pr.bottom + 8;
    if (overlapsX && overlapsY) {
      if (sel === ".thumb-rail") {
        x = Math.max(minX(), pr.left - w - 12);
      } else {
        const above = pr.top - h - 10;
        y = above >= 8 ? above : Math.min(pr.bottom + 10, window.innerHeight - h - props.bottomPad);
      }
    }
  }

  pos.value = clampToSize(x, y, w, h);
}

function restoreDock() {
  pos.value = clampToSize(dockPos.value.x, dockPos.value.y, 74, 88);
}

function onResize() {
  if (expanded.value) placeExpandedNearDock();
  else restoreDock();
}

function shouldIgnoreDrag(target) {
  if (!target?.closest) return false;
  // 输入与操作按钮不触发拖拽
  if (target.closest("textarea, input, a, .no-drag")) return true;
  return false;
}

function onPointerDown(e) {
  if (e.button != null && e.button !== 0) return;
  if (shouldIgnoreDrag(e.target)) return;
  dragging.value = true;
  dragMoved.value = false;
  ptrId = e.pointerId;
  try {
    rootEl.value?.setPointerCapture?.(ptrId);
  } catch {
    /* ignore */
  }
  dragOffset = {
    x: e.clientX - pos.value.x,
    y: e.clientY - pos.value.y,
  };
  e.preventDefault();
}

function onPointerMove(e) {
  if (!dragging.value) return;
  if (ptrId != null && e.pointerId !== ptrId) return;
  const next = clampPos(e.clientX - dragOffset.x, e.clientY - dragOffset.y);
  if (Math.abs(next.x - pos.value.x) > 3 || Math.abs(next.y - pos.value.y) > 3) {
    dragMoved.value = true;
  }
  pos.value = next;
}

function onPointerUp(e) {
  if (!dragging.value) return;
  if (ptrId != null && e.pointerId !== ptrId) return;
  const wasDrag = dragMoved.value;
  dragging.value = false;
  try {
    rootEl.value?.releasePointerCapture?.(ptrId);
  } catch {
    /* ignore */
  }
  ptrId = null;

  if (wasDrag) {
    if (expanded.value) {
      // 展开态拖完：把「原位」记为当前位置映射回的小精灵锚点（面板右下 → dock 右下）
      const w = rootEl.value?.offsetWidth || 320;
      const h = rootEl.value?.offsetHeight || 360;
      dockPos.value = clampToSize(pos.value.x + w - 74, pos.value.y + h - 88, 74, 88);
    } else {
      dockPos.value = { ...pos.value };
    }
    saveDock();
    return;
  }

  // 收起态单击 → 展开，贴着原 dock 位置
  if (!expanded.value) {
    dockPos.value = { ...pos.value };
    saveDock();
    expanded.value = true;
    nextTick(() => placeExpandedNearDock());
  }
}

/** 键盘激活（Enter/Space）：无鼠标坐标，展开并贴着 dock */
function expandFromKeyboard() {
  if (expanded.value) return;
  dockPos.value = { ...pos.value };
  saveDock();
  expanded.value = true;
  nextTick(() => placeExpandedNearDock());
}

/** 展开态的兜底出口：Esc / 点面板外部都收起 */
function onDocKeydown(e) {
  if (e.key === "Escape" && expanded.value) collapse();
}
function onDocPointerDown(e) {
  if (!expanded.value) return;
  const t = e.target;
  if (rootEl.value && t instanceof Node && rootEl.value.contains(t)) return;
  collapse();
}

function collapse() {
  expanded.value = false;
  nextTick(() => {
    restoreDock();
  });
}

function stopAll() {
  stop();
  emit("stop-external");
}

async function sendQuick() {
  const q = input.value.trim();
  if (!q || loading.value) return;
  loading.value = true;
  error.value = "";
  emit("stop-external");
  stop();
  try {
    const res = await api.ask(q, methodId.value, {
      section: null,
      sectionLabel: "浮层知知",
    });
    const answer = res.answer || "这次没答上来，换个问法试试。";
    lastReply.value = answer;
    input.value = "";
    speakText(String(answer).replace(/\s+/g, " ").slice(0, 320));
  } catch (e) {
    error.value = e.message || String(e);
    lastReply.value = error.value;
  } finally {
    loading.value = false;
  }
}

function openQa() {
  emit("open-qa");
}

function goTopic() {
  const id = contextMeta.value?.topic?.id;
  if (id) emit("open-topic", id);
}

function applyOpenState() {
  loadPos();
  if (props.defaultExpanded) {
    expanded.value = true;
    nextTick(() => placeExpandedNearDock());
    return;
  }
  if (expanded.value) placeExpandedNearDock();
  else restoreDock();
}

watch(
  () => [props.visible, props.defaultExpanded],
  ([v]) => {
    if (!v) {
      expanded.value = false;
      return;
    }
    nextTick(applyOpenState);
  }
);

function onSpiritKeydown(e) {
  if (e.isComposing || e.keyCode === 229) return;
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendQuick();
  }
}

// 移动端首次挂载时 innerWidth/innerHeight 还没稳定，等两帧后再定位一次
function settlePos() {
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      if (expanded.value) placeExpandedNearDock();
      else restoreDock();
    });
  });
}

onMounted(() => {
  settlePos();
  window.addEventListener("resize", settlePos);
  document.addEventListener("keydown", onDocKeydown);
  document.addEventListener("pointerdown", onDocPointerDown, true);
  loadPos();
  if (props.visible && props.defaultExpanded) {
    expanded.value = true;
    nextTick(() => placeExpandedNearDock());
  }
  window.addEventListener("resize", onResize);
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp);
  window.addEventListener("pointercancel", onPointerUp);
});

onUnmounted(() => {
  window.removeEventListener("resize", settlePos);
  document.removeEventListener("keydown", onDocKeydown);
  document.removeEventListener("pointerdown", onDocPointerDown, true);
  window.removeEventListener("resize", onResize);
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  window.removeEventListener("pointercancel", onPointerUp);
  stop();
});
</script>

<template>
  <div
    v-show="visible"
    ref="rootEl"
    class="spirit-float"
    :class="{ expanded, dragging, speaking: isSpeaking && !isPaused }"
    :style="{ left: `${pos.x}px`, top: `${pos.y}px` }"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
  >
    <!-- 收起：可拖小精灵（div，避免 button 拦截拖拽） -->
    <div
      v-if="!expanded"
      class="spirit-dock"
      title="拖动或点击展开"
      role="button"
      tabindex="0"
      aria-label="展开知知对话"
      @keydown.enter.prevent="expandFromKeyboard"
      @keydown.space.prevent="expandFromKeyboard"
    >
      <span class="spirit-fig" aria-hidden="true">
        <i class="hair" /><i class="face" /><i class="body" />
      </span>
      <span class="spirit-tag">知知</span>
      <span v-if="isSpeaking" class="spirit-pulse" />
    </div>

    <!-- 展开：功能面板 -->
    <div v-else class="spirit-panel">
      <div class="spirit-panel-head">
        <div class="spirit-mini">
          <span class="spirit-fig sm" aria-hidden="true">
            <i class="hair" /><i class="face" /><i class="body" />
          </span>
          <div>
            <strong>知知</strong>
            <small>{{ isSpeaking ? (isPaused ? "已暂停" : "讲话中") : "在线" }}</small>
          </div>
        </div>
        <button class="icon-btn no-drag" type="button" title="收起" @click="collapse">–</button>
      </div>

      <div class="spirit-line" v-html="renderRichText(line, { math: true })" />

      <textarea
        v-model="input"
        class="no-drag"
        rows="2"
        placeholder="提问…"
        @keydown="onSpiritKeydown"
      />

      <div class="spirit-actions no-drag">
        <button class="btn" type="button" :disabled="loading || !backendOk || !input.trim()" @click="sendQuick">
          {{ loading ? "…" : "发送" }}
        </button>
        <button class="btn ghost" type="button" @click="openQa">答疑空间</button>
        <button class="btn ghost" type="button" @click="goTopic">学习台</button>
        <button class="btn ghost" type="button" @click="stopAll">停止</button>
      </div>
      <p v-if="error" class="err">{{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
.spirit-float {
  position: fixed;
  z-index: 80;
  touch-action: none;
  user-select: none;
}
.spirit-float.dragging {
  cursor: grabbing;
}
.spirit-dock:focus-visible {
  outline: 2px solid #6658df;
  outline-offset: 3px;
}
.spirit-dock {
  width: 74px;
  border: 0;
  padding: 8px 6px 10px;
  border-radius: 22px;
  background: rgba(24, 38, 63, 0.92);
  color: #fff;
  box-shadow: 0 14px 36px rgba(18, 40, 48, 0.28);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: grab;
  position: relative;
  outline: none;
}
.spirit-float.dragging .spirit-dock {
  cursor: grabbing;
}
.spirit-tag {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
}
.spirit-pulse {
  position: absolute;
  inset: -4px;
  border-radius: 26px;
  border: 2px solid #9be2cd;
  animation: pulse 1.2s ease-out infinite;
  pointer-events: none;
}
@keyframes pulse {
  from {
    opacity: 0.9;
    transform: scale(0.96);
  }
  to {
    opacity: 0;
    transform: scale(1.08);
  }
}
.spirit-fig {
  position: relative;
  width: 46px;
  height: 58px;
  display: block;
}
.spirit-fig .hair,
.spirit-fig .face,
.spirit-fig .body {
  position: absolute;
  display: block;
}
.spirit-fig .hair {
  top: 2px;
  left: 8px;
  width: 30px;
  height: 16px;
  background: #1d2636;
  border-radius: 12px 12px 4px 4px;
}
.spirit-fig .face {
  top: 12px;
  left: 11px;
  width: 24px;
  height: 28px;
  background: #e7b6a0;
  border-radius: 50% 50% 46% 46%;
}
.spirit-fig .face::before,
.spirit-fig .face::after {
  content: "";
  position: absolute;
  top: 12px;
  width: 3px;
  height: 3px;
  background: #24313d;
  border-radius: 50%;
}
.spirit-fig .face::before {
  left: 6px;
}
.spirit-fig .face::after {
  right: 6px;
}
.spirit-fig .body {
  bottom: 0;
  left: 8px;
  width: 30px;
  height: 22px;
  background: #2a6268;
  border-radius: 12px 12px 6px 6px;
}
.spirit-float.speaking .face {
  animation: talk 0.28s infinite alternate;
}
@keyframes talk {
  to {
    filter: brightness(1.05);
  }
}
.spirit-fig.sm {
  width: 40px;
  height: 50px;
  flex: none;
}
.spirit-panel {
  width: min(320px, calc(100vw - 24px));
  background: #fff;
  border: 1px solid #d7e5df;
  border-radius: 18px;
  box-shadow: 0 18px 48px rgba(18, 40, 48, 0.22);
  padding: 12px;
  cursor: grab;
}
.spirit-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: flex-start;
  margin-bottom: 8px;
}
.spirit-mini {
  display: flex;
  gap: 8px;
  align-items: center;
  min-width: 0;
}
.spirit-mini strong {
  display: block;
  font-size: 13px;
  color: #18263f;
}
.spirit-mini small {
  display: block;
  font-size: 11px;
  color: #6d7f8c;
  margin-top: 2px;
}
.icon-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #dce6e1;
  border-radius: 8px;
  background: #f5faf7;
  color: #456;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}
.spirit-line {
  background: #f0f7f3;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.55;
  color: #2c4450;
  min-height: 52px;
  margin-bottom: 8px;
  word-break: break-word;
}
.spirit-line :deep(.md-p) {
  margin: 0 0 4px;
}
.spirit-line :deep(.md-p:last-child) {
  margin-bottom: 0;
}
.spirit-panel textarea {
  width: 100%;
  border: 1px solid #d5e0db;
  border-radius: 10px;
  padding: 8px 10px;
  font: inherit;
  font-size: 13px;
  resize: none;
  background: #fafcfb;
  color: #18263f;
  cursor: text;
}
.spirit-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.btn {
  border: 0;
  border-radius: 10px;
  padding: 7px 12px;
  background: #18263f;
  color: #fff;
  font-size: 12px;
  font-weight: 750;
  cursor: pointer;
}
.btn.ghost {
  background: #e8f3ed;
  color: #185c53;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.err {
  margin: 6px 0 0;
  color: #b95f51;
  font-size: 12px;
}

@media (max-width: 720px) {
  .spirit-panel {
    width: min(300px, calc(100vw - 20px));
  }
}
</style>
