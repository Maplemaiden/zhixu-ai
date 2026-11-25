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
  /** true = 渲染在选区下方（靠近视口顶部时翻转，避免浮层跑出屏幕） */
  flip: false,
  quote: "",
  sectionIndex: 0,
});
const color = ref("amber");
const tag = ref("重点");
const remark = ref("");
const saving = ref(false);
const saveError = ref("");

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
  saveError.value = "";
}

function onMouseUp(e) {
  // 浮层内部的 mouseup 一律不参与选区判定。
  // 否则点「颜色 / 标签 / 备注 / 保存」时，e.target 在 .anno-toolbar 里、
  // 不在 [data-section-index] 里，会被下面误判成「点到别处」而把浮层关掉。
  if (e.target?.closest?.(".anno-toolbar")) return;
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || !sel.rangeCount) {
    if (!e.target?.closest?.(".anno-toolbar")) hideToolbar();
    return;
  }
  const range0 = sel.getRangeAt(0);
  // 归属哪一篇，以**选区起点**所在的 article 为准（用户从哪儿开始选，就标哪儿）
  const startNode = range0.startContainer;
  const startEl =
    startNode.nodeType === Node.TEXT_NODE ? startNode.parentElement : startNode;
  let article = startEl?.closest?.("[data-section-index]");
  if (!article) article = e.target?.closest?.("[data-section-index]");
  if (!article || !rootRef.value?.contains(article)) {
    hideToolbar();
    return;
  }

  // 选区若跨了多篇讲义，把终点裁到本篇末尾。
  // 否则 quote 会包含别篇的文字，渲染时在本篇里永远找不到 → 保存了却看不到高亮。
  let range = range0.cloneRange();
  if (!article.contains(range.endContainer)) {
    range.setEnd(article, article.childNodes.length);
  }
  if (!article.contains(range.startContainer)) {
    range.setStart(article, 0);
  }

  // 用与渲染端同一套归一化逻辑提取文本：
  // range.toString() 在块级边界不加空格，而渲染端会补空格，两边不一致会导致
  // 「保存成功但高亮不出现」（跨段落/跨表格时必然踩到）。
  const frag = range.cloneContents();
  const holder = document.createElement("div");
  holder.appendChild(frag);
  const quote = extractText(holder);
  if (quote.length < 2) {
    hideToolbar();
    return;
  }
  const host = rootRef.value.getBoundingClientRect();
  // 长选区时 range.getBoundingClientRect() 是整段的外接矩形，可能远超视口，
  // 直接拿它定位会把浮层画到屏幕外。改用 getClientRects() 里**最后一个可见矩形**作锚点
  // （也就是选区结束的位置，用户视线通常在这儿）。
  const viewportH = window.innerHeight || document.documentElement.clientHeight;
  const allRects = Array.from(range.getClientRects()).filter((r) => r.width > 1 && r.height > 1);
  const visibleRects = allRects.filter((r) => r.bottom > 8 && r.top < viewportH - 8);
  const rect =
    (visibleRects.length ? visibleRects[visibleRects.length - 1] : null) ||
    (allRects.length ? allRects[allRects.length - 1] : range.getBoundingClientRect());
  // 浮层默认渲染在选区上方（transform: translateY(-100%)）。
  // 判断「上方放得下吗」必须用**视口坐标** rect.top，而不是相对容器的 host.top
  // —— 页面滚动后 host.top 是负值，用它会把「上方只剩 100px」误判成「上方有 480px」。
  const TOOLBAR_H = 210; // 实测渲染高度 192~210
  const GAP = 12;
  const SAFE = 8;
  const spaceAbove = rect.top - GAP;
  const spaceBelow = viewportH - rect.bottom - GAP;
  // 优先放**选区下方**：桌面浏览器的选区迷你菜单（Edge 迷你工具条、移动端复制条）
  // 默认出现在选区上方，放上方会和它叠在一起。
  // 下方放不下、而上方放得下时，才翻到上方。
  const putBelow = spaceBelow >= TOOLBAR_H + SAFE || spaceAbove < TOOLBAR_H + SAFE;

  // 先按锚点算 y，再把「最终渲染出来的 top」clamp 进视口，最后反算回 y。
  let yViewportTop = putBelow ? rect.bottom + GAP : rect.top - GAP - TOOLBAR_H;
  const maxTop = Math.max(SAFE, viewportH - TOOLBAR_H - SAFE);
  yViewportTop = Math.min(Math.max(yViewportTop, SAFE), maxTop);

  toolbar.value = {
    show: true,
    x: Math.min(Math.max(rect.left - host.left + rect.width / 2, 80), host.width - 80),
    // y 是相对 host 的偏移；flip=false 时还要再被 translateY(-100%) 上移一个自身高度
    y: putBelow ? yViewportTop - host.top : yViewportTop + TOOLBAR_H - host.top,
    flip: putBelow,
    quote,
    sectionIndex: Number(article.getAttribute("data-section-index") || 0),
  };
  remark.value = "";
  saveError.value = "";
}

async function saveNote() {
  if (!toolbar.value.quote || saving.value) return;
  saving.value = true;
  saveError.value = "";
  try {
    await props.createNote({
      quote: toolbar.value.quote,
      section_index: toolbar.value.sectionIndex,
      color: color.value,
      tag: tag.value,
      remark: remark.value.trim(),
    });
    hideToolbar();
    window.getSelection()?.removeAllRanges();
  } catch (err) {
    saveError.value = err?.message || "保存失败";
  } finally {
    saving.value = false;
  }
}

function onDocClick(e) {
  if (!toolbar.value.show) return;
  if (e.target?.closest?.(".anno-toolbar") || e.target?.closest?.("[data-section-index]")) return;
  hideToolbar();
}

/** Esc 关闭浮层（键盘用户除「取消」之外的快捷出口） */
function onDocKeydown(e) {
  if (e.key === "Escape" && toolbar.value.show) hideToolbar();
}

onMounted(() => {
  paint();
  // pointerdown 同时覆盖鼠标与触屏（mousedown 在部分触屏场景不触发）
  document.addEventListener("pointerdown", onDocClick);
  document.addEventListener("keydown", onDocKeydown);
});
onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", onDocClick);
  document.removeEventListener("keydown", onDocKeydown);
});

watch(() => [props.sections, props.notes], paint, { deep: true });
</script>

<template>
  <div ref="rootRef" class="reading-panel" @mouseup="onMouseUp">
    <div class="anno-hint">
      在讲解正文中划选文字，可添加高亮与标签；标注会随当前账号保存。
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
        <button type="button" class="ghost" @click="hideToolbar">取消</button>
        <button type="button" class="primary" :disabled="saving" @click="saveNote">
          {{ saving ? "保存中…" : "保存标注" }}
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
.anno-toolbar {
  position: absolute;
  transform: translate(-50%, -100%);
  z-index: 20;
  max-height: 70vh;
  overflow-y: auto;
  /* 浮层自身不可被划选，避免在浮层上拖动时把里面的文字选进去 */
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
/* 触屏 / 窄屏：浮层固定到底部（bottom sheet）。
   移动端长按选词必然弹系统「复制/全选」菜单，浮层贴着选区一定打架；
   固定底部可以彻底避开，也更好点。 */
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
/* 高亮样式需非 scoped，因为 mark 是运行时插入的 */
.zhixu-hl {
  cursor: help;
  /* 默认中间碎片：无圆角、无内边距，与前一片无缝相连 */
  border-radius: 0;
  padding: 0;
  /* 单个 mark 跨行时两行各自完整着色 */
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
}
/* 一次标注被拆成多片时，只有首尾有圆角，视觉上是一条连续高亮 */
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
