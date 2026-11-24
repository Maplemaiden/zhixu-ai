<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { renderLessonMarkdown } from "../utils/renderRichText";
import { applyHighlights } from "../utils/applyHighlights";

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
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || !sel.rangeCount) {
    if (!e.target?.closest?.(".anno-toolbar")) hideToolbar();
    return;
  }
  const article = e.target?.closest?.("[data-section-index]");
  if (!article || !rootRef.value?.contains(article)) {
    hideToolbar();
    return;
  }
  const quote = sel.toString().replace(/\s+/g, " ").trim();
  if (quote.length < 2) {
    hideToolbar();
    return;
  }
  const range = sel.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  const host = rootRef.value.getBoundingClientRect();
  toolbar.value = {
    show: true,
    x: Math.min(Math.max(rect.left - host.left + rect.width / 2, 80), host.width - 80),
    y: Math.max(rect.top - host.top - 12, 8),
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

onMounted(() => {
  paint();
  document.addEventListener("mousedown", onDocClick);
});
onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onDocClick);
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
  color: #8a91ab;
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
  width: min(320px, 90vw);
  background: #24253b;
  color: #fff;
  border-radius: 14px;
  padding: 12px;
  box-shadow: 0 12px 30px rgba(36, 37, 59, 0.28);
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
  border-radius: 3px;
  padding: 0 2px;
  cursor: help;
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
