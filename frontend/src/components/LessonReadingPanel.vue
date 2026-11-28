<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { renderLessonMarkdown } from "../utils/renderRichText";
import { applyHighlights, extractText } from "../utils/applyHighlights";

const props = defineProps({
  sections: { type: Array, default: () => [] },
  notes: { type: Array, default: () => [] },
  source: { type: String, default: "" },
  emptyHint: { type: String, default: "" },
  createNote: { type: Function, required: true },
  updateNote: { type: Function, default: null },
  deleteNote: { type: Function, default: null },
});

const emit = defineEmits(["reload"]);

const COLORS = [
  { id: "amber", label: "琥珀" },
  { id: "mint", label: "薄荷" },
  { id: "rose", label: "玫红" },
  { id: "sky", label: "天蓝" },
];
const TAGS = ["重点", "公式", "易错", "案例", "待复习"];

const rootRef = ref(null);
const toolbar = ref({
  show: false,
  x: 0,
  y: 0,
  flip: false,
  quote: "",
  sectionIndex: 0,
  editingId: "",
});
const color = ref("amber");
const tag = ref("重点");
const remark = ref("");
const saving = ref(false);
const saveError = ref("");
let touchTimer = null;

const notesBySection = computed(() => {
  const map = {};
  for (const n of props.notes || []) {
    const i = n.section_index ?? 0;
    if (!map[i]) map[i] = [];
    map[i].push(n);
  }
  return map;
});

function paint() {
  nextTick(() => {
    if (!rootRef.value) return;
    rootRef.value.querySelectorAll("[data-section-index]").forEach((el) => {
      const idx = Number(el.getAttribute("data-section-index") || 0);
      applyHighlights(el.querySelector(".lesson-md"), notesBySection.value[idx] || []);
    });
  });
}

function hideToolbar() {
  toolbar.value.show = false;
  toolbar.value.editingId = "";
  saveError.value = "";
}

function computeToolbarCoords(anchorRect) {
  const host = rootRef.value.getBoundingClientRect();
  const viewportH = window.innerHeight || document.documentElement.clientHeight;
  const TOOLBAR_W = Math.min(320, (window.innerWidth || 800) * 0.9);
  const halfW = Math.min(TOOLBAR_W / 2 + 8, Math.max(80, host.width / 2 - 8));
  const TOOLBAR_H = 216;
  const GAP = 12;
  const SAFE = 8;
  const spaceAbove = anchorRect.top - GAP;
  const spaceBelow = viewportH - anchorRect.bottom - GAP;
  const putBelow = spaceBelow >= TOOLBAR_H + SAFE || spaceAbove < TOOLBAR_H + SAFE;

  let yViewportTop = putBelow ? anchorRect.bottom + GAP : anchorRect.top - GAP - TOOLBAR_H;
  const maxTop = Math.max(SAFE, viewportH - TOOLBAR_H - SAFE);
  yViewportTop = Math.min(Math.max(yViewportTop, SAFE), maxTop);

  let x = Math.min(
    Math.max(anchorRect.left - host.left + anchorRect.width / 2, halfW),
    Math.max(halfW, host.width - halfW)
  );

  // 若右下角浮层知知与当前浮层重叠，向左避让
  const spirit = document.querySelector(".spirit-float");
  if (spirit && spirit.offsetWidth > 0) {
    const sr = spirit.getBoundingClientRect();
    const leftVp = host.left + x - TOOLBAR_W / 2;
    const rightVp = leftVp + TOOLBAR_W;
    const overlapX = rightVp > sr.left - 8 && leftVp < sr.right + 8;
    const overlapY = yViewportTop + TOOLBAR_H > sr.top - 8 && yViewportTop < sr.bottom + 8;
    if (overlapX && overlapY) {
      const shiftedCenter = sr.left - 12 - TOOLBAR_W / 2 - host.left;
      x = Math.max(halfW, Math.min(x, shiftedCenter));
    }
  }

  return {
    x,
    y: putBelow ? yViewportTop - host.top : yViewportTop + TOOLBAR_H - host.top,
    flip: putBelow,
  };
}

function onMarkClick(e) {
  const markEl = e.target?.closest?.("mark.zhixu-hl");
  if (!markEl || !rootRef.value?.contains(markEl)) return false;
  const sel = window.getSelection();
  if (sel && !sel.isCollapsed && sel.toString().trim().length >= 2) return false;
  const noteId = markEl.dataset?.noteId;
  const existing = (props.notes || []).find((n) => n.id === noteId);
  if (!existing) return false;

  const rect = markEl.getBoundingClientRect();
  const coords = computeToolbarCoords(rect);
  color.value = existing.color || "amber";
  tag.value = existing.tag || "重点";
  remark.value = existing.remark || "";
  saveError.value = "";
  toolbar.value = {
    show: true,
    ...coords,
    quote: existing.quote,
    sectionIndex: existing.section_index ?? 0,
    editingId: existing.id,
  };
  return true;
}

function onMouseUp(e) {
  if (e.target?.closest?.(".anno-toolbar")) return;
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || !sel.rangeCount) {
    if (onMarkClick(e)) return;
    if (!e.target?.closest?.(".anno-toolbar")) hideToolbar();
    return;
  }
  const range0 = sel.getRangeAt(0);
  const startNode = range0.startContainer;
  const startEl =
    startNode.nodeType === Node.TEXT_NODE ? startNode.parentElement : startNode;
  let article = startEl?.closest?.("[data-section-index]");
  if (!article) article = e.target?.closest?.("[data-section-index]");
  if (!article || !rootRef.value?.contains(article)) {
    hideToolbar();
    return;
  }

  let range = range0.cloneRange();
  if (!article.contains(range.endContainer)) {
    range.setEnd(article, article.childNodes.length);
  }
  if (!article.contains(range.startContainer)) {
    range.setStart(article, 0);
  }

  const frag = range.cloneContents();
  const holder = document.createElement("div");
  holder.appendChild(frag);
  const quote = extractText(holder);
  if (quote.length < 2) {
    hideToolbar();
    return;
  }

  const viewportH = window.innerHeight || document.documentElement.clientHeight;
  const allRects = Array.from(range.getClientRects()).filter((r) => r.width > 1 && r.height > 1);
  const visibleRects = allRects.filter((r) => r.bottom > 8 && r.top < viewportH - 8);
  const rect =
    (visibleRects.length ? visibleRects[visibleRects.length - 1] : null) ||
    (allRects.length ? allRects[allRects.length - 1] : range.getBoundingClientRect());

  const coords = computeToolbarCoords(rect);
  toolbar.value = {
    show: true,
    ...coords,
    quote,
    sectionIndex: Number(article.getAttribute("data-section-index") || 0),
    editingId: "",
  };
  remark.value = "";
  saveError.value = "";
}

function onTouchEnd(e) {
  if (touchTimer) clearTimeout(touchTimer);
  touchTimer = setTimeout(() => onMouseUp(e), 80);
}

async function saveNote() {
  if (!toolbar.value.quote || saving.value) return;
  saving.value = true;
  saveError.value = "";
  try {
    if (toolbar.value.editingId && props.updateNote) {
      await props.updateNote(toolbar.value.editingId, {
        color: color.value,
        tag: tag.value,
        remark: remark.value.trim(),
      });
    } else {
      await props.createNote({
        quote: toolbar.value.quote,
        section_index: toolbar.value.sectionIndex,
        color: color.value,
        tag: tag.value,
        remark: remark.value.trim(),
      });
    }
    hideToolbar();
    window.getSelection()?.removeAllRanges();
  } catch (err) {
    saveError.value = err?.message || "保存失败";
  } finally {
    saving.value = false;
  }
}

async function removeEditingNote() {
  if (!toolbar.value.editingId || !props.deleteNote || saving.value) return;
  saving.value = true;
  saveError.value = "";
  try {
    await props.deleteNote(toolbar.value.editingId);
    hideToolbar();
  } catch (err) {
    saveError.value = err?.message || "删除失败";
  } finally {
    saving.value = false;
  }
}

function onDocClick(e) {
  if (!toolbar.value.show) return;
  if (e.target?.closest?.(".anno-toolbar") || e.target?.closest?.("[data-section-index]")) return;
  hideToolbar();
}

function onDocKeydown(e) {
  if (e.key === "Escape" && toolbar.value.show) hideToolbar();
}

onMounted(() => {
  paint();
  document.addEventListener("pointerdown", onDocClick);
  document.addEventListener("keydown", onDocKeydown);
});
onBeforeUnmount(() => {
  if (touchTimer) clearTimeout(touchTimer);
  document.removeEventListener("pointerdown", onDocClick);
  document.removeEventListener("keydown", onDocKeydown);
});

watch(() => [props.sections, props.notes], paint, { deep: true });
</script>

<template>
  <div ref="rootRef" class="reading-panel" @mouseup="onMouseUp" @touchend="onTouchEnd">
    <div class="anno-hint">
      在讲解正文中划选文字，可添加高亮与标签；点击已有高亮可修改或删除。
      <button v-if="!sections.length" class="linkish" type="button" @click="$emit('reload')">重新加载讲义</button>
    </div>

    <div v-if="!sections.length" class="empty">
      {{ emptyHint || "讲义正文未加载到。" }}
    </div>

    <article
      v-for="(sec, i) in sections"
      :key="'read-' + i"
      class="lesson-article"
      :data-section-index="i"
    >
      <h4>{{ sec.title }}</h4>
      <div class="lesson-md" v-html="renderLessonMarkdown(sec.text)" />
    </article>

    <div
      v-if="toolbar.show"
      class="anno-toolbar"
      :class="{ flip: toolbar.flip }"
      :style="{ left: toolbar.x + 'px', top: toolbar.y + 'px' }"
      @mousedown.stop
    >
      <div class="quote">「{{ toolbar.quote.slice(0, 48) }}{{ toolbar.quote.length > 48 ? "…" : "" }}」</div>
      <div class="row">
        <button
          v-for="c in COLORS"
          :key="c.id"
          type="button"
          class="swatch"
          :class="[c.id, { active: color === c.id }]"
          :title="c.label"
          @click="color = c.id"
        />
      </div>
      <div class="row tags">
        <button
          v-for="t in TAGS"
          :key="t"
          type="button"
          class="tag"
          :class="{ active: tag === t }"
          @click="tag = t"
        >
          {{ t }}
        </button>
      </div>
      <input v-model="remark" class="remark" maxlength="120" placeholder="可选备注" />
      <div class="actions">
        <button
          v-if="toolbar.editingId && deleteNote"
          type="button"
          class="danger"
          :disabled="saving"
          @click="removeEditingNote"
        >
          删除
        </button>
        <button type="button" class="ghost" @click="hideToolbar">取消</button>
        <button type="button" class="primary" :disabled="saving" @click="saveNote">
          {{ saving ? "保存中…" : toolbar.editingId ? "更新标注" : "保存标注" }}
        </button>
      </div>
      <p v-if="saveError" class="err">{{ saveError }}</p>
    </div>
  </div>
</template>

<style scoped>
.reading-panel {
  position: relative;
}
.anno-hint {
  font-size: 12px;
  color: #5f6781;
  margin: 0 0 12px;
}
.linkish {
  border: 0;
  background: none;
  color: #6658df;
  cursor: pointer;
  padding: 0;
  margin-left: 6px;
}
.empty {
  padding: 16px;
  border-radius: 12px;
  background: #f4f5fb;
  color: #6b7290;
  font-size: 14px;
}
.lesson-article {
  margin: 14px 0 18px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #fbfbfd;
  border: 1px solid #e8ebf5;
}
.lesson-article h4 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #24253b;
}
.lesson-md :deep(.katex-display) {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 6px 2px;
  max-width: 100%;
}
.anno-toolbar {
  position: absolute;
  transform: translate(-50%, -100%);
  z-index: 20;
  max-height: 70vh;
  overflow-y: auto;
  user-select: none;
  width: min(320px, 90vw);
  background: #24253b;
  color: #fff;
  border-radius: 14px;
  padding: 12px;
  box-shadow: 0 12px 30px rgba(36, 37, 59, 0.28);
}
.anno-toolbar.flip {
  transform: translate(-50%, 0);
}
@media (max-width: 720px), (hover: none) {
  .anno-toolbar,
  .anno-toolbar.flip {
    position: fixed !important;
    left: 12px !important;
    right: 12px !important;
    top: auto !important;
    bottom: 12px !important;
    width: auto !important;
    transform: none !important;
    max-height: 56vh;
    z-index: 200;
    box-shadow: 0 -8px 40px rgba(20, 24, 45, 0.32);
  }
}
.quote {
  font-size: 12px;
  color: #c5cae0;
  margin-bottom: 8px;
  line-height: 1.5;
}
.row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.swatch {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  border: 2px solid transparent;
  cursor: pointer;
}
.swatch.amber {
  background: #f6d56a;
}
.swatch.mint {
  background: #7ddec0;
}
.swatch.rose {
  background: #f3a6b5;
}
.swatch.sky {
  background: #8ec5f5;
}
.swatch.active {
  border-color: #fff;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.25);
}
.tag {
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: transparent;
  color: #d7dbef;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}
.tag.active {
  background: #6658df;
  border-color: #6658df;
  color: #fff;
}
.anno-toolbar input,
.anno-toolbar textarea {
  user-select: text;
}
.remark {
  width: 100%;
  box-sizing: border-box;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  padding: 8px 10px;
  margin-bottom: 8px;
  outline: none;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.ghost,
.danger,
.primary {
  border: 0;
  border-radius: 10px;
  padding: 7px 12px;
  cursor: pointer;
  font-size: 13px;
}
.ghost {
  background: transparent;
  color: #c5cae0;
}
.danger {
  margin-right: auto;
  background: rgba(243, 120, 120, 0.18);
  color: #ffb4b4;
}
.primary {
  background: #6658df;
  color: #fff;
  font-weight: 600;
}
.primary:disabled {
  opacity: 0.6;
}
.err {
  margin: 8px 0 0;
  color: #ffb4b4;
  font-size: 12px;
}
</style>

<style>
.zhixu-hl {
  cursor: pointer;
  border-radius: 0;
  padding: 0;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
}
.zhixu-hl .katex {
  background: inherit;
}
.zhixu-hl.hl-flash {
  outline: 2px solid #6658df;
  outline-offset: 2px;
  transition: outline-color 0.4s ease;
}
.zhixu-hl.hl-part-only {
  border-radius: 3px;
  padding: 0 2px;
}
.zhixu-hl.hl-part-first {
  border-radius: 3px 0 0 3px;
  padding-left: 2px;
}
.zhixu-hl.hl-part-last {
  border-radius: 0 3px 3px 0;
  padding-right: 2px;
}
.zhixu-hl.hl-amber {
  background: rgba(246, 213, 106, 0.55);
}
.zhixu-hl.hl-mint {
  background: rgba(125, 222, 192, 0.45);
}
.zhixu-hl.hl-rose {
  background: rgba(243, 166, 181, 0.5);
}
.zhixu-hl.hl-sky {
  background: rgba(142, 197, 245, 0.5);
}
.zhixu-hl[data-tag]::after {
  content: attr(data-tag);
  display: inline-block;
  margin-left: 4px;
  padding: 0 5px;
  border-radius: 999px;
  background: rgba(36, 37, 59, 0.72);
  color: #fff;
  font-size: 10px;
  line-height: 1.5;
  vertical-align: middle;
}
</style>
