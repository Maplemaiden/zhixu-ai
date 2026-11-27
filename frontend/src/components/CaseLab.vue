<script setup>
import { computed, ref, watch } from "vue";
import { api } from "../api";
import { renderRichText } from "../utils/renderRichText";

const props = defineProps({
  caseItem: { type: Object, default: null },
  casesCount: { type: Number, default: 0 },
  methodId: { type: String, default: "expected_value" },
  backendOk: { type: Boolean, default: true },
  partName: { type: String, default: "" },
});

const emit = defineEmits(["change-case", "speak"]);

const CRITERIA = [
  { id: "optimistic", label: "乐观准则" },
  { id: "pessimistic", label: "悲观准则" },
  { id: "hurwicz", label: "折中准则" },
  { id: "regret", label: "后悔值准则" },
  { id: "laplace", label: "等概率准则" },
];

const MADM_METHODS = [
  { id: "topsis", label: "TOPSIS" },
  { id: "weighted_sum", label: "加权和" },
  { id: "weighted_product", label: "加权积" },
];

const TYPE_LABEL = { benefit: "效益", cost: "成本", interval: "区间" };

const draft = ref(null);
const baselineResult = ref(null);
const currentResult = ref(null);
const caseBrief = ref(null);
const loading = ref(false);
const explainLoading = ref(false);
const error = ref("");
const explainText = ref("");
const explainSources = ref([]);

const isWalkthrough = computed(() => !!props.caseItem && !props.caseItem.computeKind);
const isUncertainty = computed(() => props.caseItem?.computeKind === "uncertainty");
const isExpected = computed(() => props.caseItem?.computeKind === "expected_value");
const isMadm = computed(() => props.caseItem?.computeKind === "madm");
const hasLab = computed(() => !!props.caseItem);
const heading = computed(() => {
  if (props.partName) return props.partName;
  return props.caseItem?.computeKind ? "实验台" : "案例";
});
const lead = computed(() =>
  props.caseItem?.computeKind
    ? "改参数看结果变。数字只信程序验算；知知只负责解释。"
    : "对照教材规则拆开本讲案例。这里没有程序调参。"
);
const probSum = computed(() => {
  if (!draft.value?.probs) return 0;
  return draft.value.probs.reduce((s, p) => s + (Number(p) || 0), 0);
});
const probOk = computed(() => Math.abs(probSum.value - 1) <= 1e-6);
const weightSum = computed(() => {
  if (!draft.value?.weights) return 0;
  return draft.value.weights.reduce((s, w) => s + (Number(w) || 0), 0);
});
const weightOk = computed(() => Math.abs(weightSum.value - 1) <= 1e-6);
const canCompute = computed(() => {
  if (loading.value) return false;
  if (isExpected.value && !probOk.value) return false;
  if (isMadm.value && !weightOk.value) return false;
  return true;
});
const changedBest = computed(() => {
  if (!baselineResult.value || !currentResult.value) return false;
  return baselineResult.value.best !== currentResult.value.best;
});
const changedRanking = computed(() => {
  if (!baselineResult.value?.ranking || !currentResult.value?.ranking) return false;
  return baselineResult.value.ranking.join(">") !== currentResult.value.ranking.join(">");
});

function clonePayload(p) {
  return JSON.parse(JSON.stringify(p || {}));
}

function resetDraftFromCase() {
  const c = props.caseItem;
  baselineResult.value = null;
  currentResult.value = null;
  caseBrief.value = null;
  explainText.value = "";
  explainSources.value = [];
  error.value = "";
  if (!c) {
    draft.value = null;
    return;
  }
  if (c.computeKind && c.payload) {
    draft.value = clonePayload(c.payload);
  } else {
    draft.value = null;
  }
}

async function runCompute(asBaseline = false) {
  const c = props.caseItem;
  if (!c?.computeKind || !draft.value) return;
  loading.value = true;
  error.value = "";
  try {
    const payload = clonePayload(draft.value);
    const res =
      c.computeKind === "uncertainty"
        ? await api.computeUncertainty(payload)
        : c.computeKind === "madm"
          ? await api.computeMadm(payload)
          : await api.computeEV(payload);
    const prevBest = baselineResult.value?.best;
    if (asBaseline || !baselineResult.value) {
      baselineResult.value = res;
      currentResult.value = res;
    } else {
      currentResult.value = res;
    }
    const bestChanged = !asBaseline && prevBest && prevBest !== res.best;
    emit("speak", [
      ...(res.speak_lines || []),
      asBaseline
        ? isMadm.value
          ? "这是当前权重与方法下的基准结果。你可以改权重或换方法，看排序会不会变。"
          : "这是当前参数下的基准结果。你可以改概率或收益，再点计算看最优方案会不会变。"
        : bestChanged
          ? `调整后最优方案变为「${res.best}」。`
          : `调整后最优方案仍是「${res.best}」。`,
    ]);
  } catch (e) {
    error.value = e.message || String(e);
  } finally {
    loading.value = false;
  }
}

async function onCompute() {
  if (!baselineResult.value) await runCompute(true);
  else await runCompute(false);
}

function resetToOriginal() {
  resetDraftFromCase();
  if (props.caseItem?.computeKind) runCompute(true);
}

function normalizeProbs() {
  if (!draft.value?.probs?.length) return;
  const sum = draft.value.probs.reduce((s, p) => s + (Number(p) || 0), 0);
  if (sum <= 0) return;
  draft.value.probs = draft.value.probs.map((p) => Number(((Number(p) || 0) / sum).toFixed(4)));
}

function normalizeWeights() {
  if (!draft.value?.weights?.length) return;
  const sum = draft.value.weights.reduce((s, w) => s + (Number(w) || 0), 0);
  if (sum <= 0) return;
  draft.value.weights = draft.value.weights.map((w) => Number(((Number(w) || 0) / sum).toFixed(4)));
}

function setWeight(j, raw) {
  if (!draft.value?.weights) return;
  const n = Math.max(0, Math.min(1, Number(raw)));
  if (!Number.isFinite(n)) return;
  const prev = draft.value.weights.map((w) => Number(w) || 0);
  const k = prev.length;
  if (k === 1) {
    draft.value.weights = [1];
    return;
  }
  const leftover = 1 - n;
  const restIdx = prev.map((_, i) => i).filter((i) => i !== j);
  const restSum = restIdx.reduce((s, i) => s + prev[i], 0);
  const next = prev.slice();
  next[j] = n;
  if (restSum <= 1e-12) {
    const share = leftover / restIdx.length;
    restIdx.forEach((i) => {
      next[i] = share;
    });
  } else {
    restIdx.forEach((i) => {
      next[i] = (prev[i] / restSum) * leftover;
    });
  }
  const rounded = next.map((w) => Number(w.toFixed(4)));
  const drift = Number((1 - rounded.reduce((s, w) => s + w, 0)).toFixed(4));
  const fixAt = restIdx[restIdx.length - 1];
  rounded[fixAt] = Number((rounded[fixAt] + drift).toFixed(4));
  draft.value.weights = rounded;
}

function onMadmParamChange() {
  if (!isMadm.value || !weightOk.value || loading.value) return;
  onCompute();
}

function setMatrixCell(i, j, raw) {
  const n = Number(raw);
  if (!draft.value?.matrix?.[i]) return;
  draft.value.matrix[i][j] = Number.isFinite(n) ? n : 0;
}

function setPayoff(i, j, raw) {
  const n = Number(raw);
  if (!draft.value?.payoffs?.[i]) return;
  draft.value.payoffs[i][j] = Number.isFinite(n) ? n : 0;
}

function setProb(j, raw) {
  const n = Number(raw);
  if (!draft.value?.probs) return;
  draft.value.probs[j] = Number.isFinite(n) ? n : 0;
}

function expandWalkthrough() {
  const c = props.caseItem;
  if (!c || c.computeKind) return;
  if (caseBrief.value) {
    caseBrief.value = null;
    return;
  }
  caseBrief.value = {
    title: c.title,
    panel: c.panel || "",
    takeaway: c.takeaway || "",
  };
  emit("speak", [
    ...(c.speak || [c.title, c.intro]),
    c.takeaway || "案例讲完了。可以回到讲解，或去做小测答疑。",
  ]);
}

function resultSummary(res, label) {
  if (!res) return `${label}：暂无`;
  const lines = [
    `${label}：最优方案「${res.best}」，取值 ${res.best_value}`,
  ];
  if (res.expectations) {
    lines.push(
      "各方案期望：" +
        Object.entries(res.expectations)
          .map(([k, v]) => `${k}=${v}`)
          .join("，")
    );
  }
  if (res.scores) {
    lines.push(
      "各方案得分：" +
        Object.entries(res.scores)
          .map(([k, v]) => `${k}=${v}`)
          .join("，")
    );
  }
  if (res.criterion_name) lines.push(`准则：${res.criterion_name}`);
  if (res.method_name) lines.push(`方法：${res.method_name}`);
  if (res.ranking?.length) lines.push("排序：" + res.ranking.join(" ≻ "));
  return lines.join("。");
}

async function explainChange() {
  if (!currentResult.value || explainLoading.value) return;
  explainLoading.value = true;
  explainText.value = "";
  explainSources.value = [];
  error.value = "";
  try {
    const before = resultSummary(baselineResult.value, "调整前");
    const after = resultSummary(currentResult.value, "调整后");
    const q = [
      "请根据程序验算结果，解释调整前后最优方案为什么变化（或不变化）。",
      "数字必须以下方程序结果为准，禁止重新口算或改写数值。",
      before,
      after,
      props.caseItem?.title ? `案例：${props.caseItem.title}` : "",
    ]
      .filter(Boolean)
      .join("\n");
    const res = await api.ask(q, props.methodId, {
      section: 1,
      sectionLabel: heading.value,
    });
    explainText.value = res.answer || "暂时没有生成解释。";
    explainSources.value = res.sources || [];
    emit("speak", [String(explainText.value).replace(/\s+/g, " ").slice(0, 360)]);
  } catch (e) {
    error.value = e.message || String(e);
  } finally {
    explainLoading.value = false;
  }
}

watch(
  () => props.caseItem?.id,
  () => {
    resetDraftFromCase();
    if (props.caseItem?.computeKind) runCompute(true);
  },
  { immediate: true }
);
</script>

<template>
  <div class="case-lab">
    <h2>{{ heading }}</h2>
    <p class="lab-lead">{{ lead }}</p>

    <div v-if="!hasLab" class="lab-empty">
      <p>本讲暂无案例。</p>
      <p class="tiny">可以回到讲解继续学习，或去做小测答疑。</p>
    </div>

    <template v-else>
      <div class="lab-case-head">
        <div>
          <div class="case-title">{{ caseItem.title }}</div>
          <div class="tiny" style="margin-top: 5px">{{ caseItem.intro }}</div>
        </div>
        <button
          v-if="casesCount > 1"
          class="btn btn-small btn-soft"
          type="button"
          @click="emit('change-case')"
        >
          换个情境
        </button>
      </div>

      <!-- walkthrough -->
      <template v-if="isWalkthrough">
        <p class="tiny lab-note">本案例以教材规则对照为主，不调用数值 Solver。</p>
        <button
          class="btn"
          :class="{ 'btn-primary': !caseBrief }"
          type="button"
          @click="expandWalkthrough"
        >
          {{ caseBrief ? "收起案例" : "展开案例" }}
        </button>
        <div v-if="caseBrief" class="concept-box" style="margin-top: 12px">
          <h4>案例拆解</h4>
          <p v-if="caseBrief.takeaway">要点：<b>{{ caseBrief.takeaway }}</b></p>
          <div class="panel-md" v-html="renderRichText(caseBrief.panel, { math: true })" />
        </div>
      </template>

      <!-- editable solver lab -->
      <template v-else-if="draft">
        <div class="lab-grid">
          <div class="lab-params">
            <div class="lab-block">
              <div class="lab-block-title">参数</div>

              <template v-if="isMadm">
                <div class="field-row">
                  <label>排序方法</label>
                  <select v-model="draft.method" @change="onMadmParamChange">
                    <option v-for="m in MADM_METHODS" :key="m.id" :value="m.id">{{ m.label }}</option>
                  </select>
                </div>
                <p class="tiny lab-note">
                  加权和可完全补偿；加权积不可代偿；TOPSIS 同时看离正、负理想解的距离。
                </p>

                <div class="lab-sub">属性权重</div>
                <div
                  v-for="(attr, j) in draft.attributes"
                  :key="'w-' + j"
                  class="weight-row"
                >
                  <div class="weight-head">
                    <span>{{ attr }}</span>
                    <span class="tiny">{{ TYPE_LABEL[draft.types[j]] || draft.types[j] }}</span>
                  </div>
                  <input
                    class="weight-range"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    :value="draft.weights[j]"
                    @input="setWeight(j, $event.target.value)"
                    @change="onMadmParamChange"
                  />
                  <input
                    class="weight-num"
                    :value="draft.weights[j]"
                    type="number"
                    min="0"
                    max="1"
                    step="0.05"
                    @change="setWeight(j, $event.target.value); onMadmParamChange()"
                  />
                </div>
                <div class="prob-meta" :class="{ bad: !weightOk }">
                  权重和 = {{ weightSum.toFixed(4) }}
                  <button v-if="!weightOk" class="linkish" type="button" @click="normalizeWeights">归一化</button>
                </div>
                <p
                  v-if="draft.types.includes('interval') && draft.interval"
                  class="tiny lab-note"
                >
                  区间型按教案最优区间变换：
                  <span v-for="(b, name) in draft.interval" :key="name">
                    {{ name }} 最优 [{{ b.best_low }}, {{ b.best_high }}]，容忍 [{{ b.tol_low }}, {{ b.tol_high }}]
                  </span>
                </p>

                <div class="lab-sub">决策矩阵</div>
                <table class="lab-table">
                  <thead>
                    <tr>
                      <th>方案</th>
                      <th v-for="(attr, j) in draft.attributes" :key="'mh-' + j">{{ attr }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(alt, i) in draft.alternatives" :key="'ma-' + i">
                      <th>{{ alt }}</th>
                      <td v-for="(cell, j) in draft.matrix[i]" :key="'mc-' + i + '-' + j">
                        <input
                          :value="cell"
                          type="number"
                          step="any"
                          @change="setMatrixCell(i, j, $event.target.value)"
                        />
                      </td>
                    </tr>
                  </tbody>
                </table>
              </template>

              <template v-else>
                <div v-if="isUncertainty" class="field-row">
                  <label>决策准则</label>
                  <select v-model="draft.criterion">
                    <option v-for="c in CRITERIA" :key="c.id" :value="c.id">{{ c.label }}</option>
                  </select>
                </div>
                <div v-if="isUncertainty && draft.criterion === 'hurwicz'" class="field-row">
                  <label>折中系数 α</label>
                  <input v-model.number="draft.alpha" type="number" min="0" max="1" step="0.05" />
                </div>

                <div v-if="isExpected" class="prob-table-wrap">
                  <div class="lab-sub">自然状态概率</div>
                  <table class="lab-table">
                    <thead>
                      <tr>
                        <th v-for="(s, j) in draft.states" :key="'s-' + j">{{ s }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td v-for="(p, j) in draft.probs" :key="'p-' + j">
                          <input
                            :value="p"
                            type="number"
                            min="0"
                            max="1"
                            step="0.05"
                            @change="setProb(j, $event.target.value)"
                          />
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <div class="prob-meta" :class="{ bad: !probOk }">
                    概率和 = {{ probSum.toFixed(4) }}
                    <button v-if="!probOk" class="linkish" type="button" @click="normalizeProbs">归一化</button>
                  </div>
                </div>

                <div class="lab-sub">收益表</div>
                <table class="lab-table">
                  <thead>
                    <tr>
                      <th>方案</th>
                      <th v-for="(s, j) in draft.states" :key="'h-' + j">{{ s }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(alt, i) in draft.alternatives" :key="'a-' + i">
                      <th>{{ alt }}</th>
                      <td v-for="(cell, j) in draft.payoffs[i]" :key="'c-' + i + '-' + j">
                        <input
                          :value="cell"
                          type="number"
                          step="1"
                          @change="setPayoff(i, j, $event.target.value)"
                        />
                      </td>
                    </tr>
                  </tbody>
                </table>
              </template>

              <div class="lab-actions">
                <button
                  class="btn btn-primary"
                  type="button"
                  :disabled="!canCompute"
                  @click="onCompute"
                >
                  {{ loading ? "计算中…" : "计算" }}
                </button>
                <button class="btn" type="button" :disabled="loading" @click="resetToOriginal">
                  恢复原参数
                </button>
              </div>
            </div>
          </div>

          <div class="lab-results">
            <div class="lab-block">
              <div class="lab-block-title">结果对照</div>
              <div v-if="!baselineResult && !currentResult" class="tiny">点「计算」查看程序结果。</div>
              <div v-else class="compare-row">
                <div class="compare-card">
                  <span class="compare-label">调整前</span>
                  <strong>{{ baselineResult?.best || "—" }}</strong>
                  <span class="tiny">{{ baselineResult ? baselineResult.best_value : "" }}</span>
                </div>
                <div class="compare-card" :class="{ changed: changedBest }">
                  <span class="compare-label">调整后</span>
                  <strong>{{ currentResult?.best || "—" }}</strong>
                  <span class="tiny">{{ currentResult ? currentResult.best_value : "" }}</span>
                </div>
              </div>
              <p v-if="changedBest" class="change-tip">最优方案已变化，可让知知解释原因。</p>
              <p v-else-if="changedRanking" class="change-tip">排序已变化（最优方案仍是同一人）。</p>
              <p v-else-if="currentResult && baselineResult" class="change-tip muted">最优方案未变，可继续改参数试试。</p>
              <ol v-if="currentResult?.ranking?.length" class="rank-list">
                <li v-for="name in currentResult.ranking" :key="'r-' + name">
                  {{ name }}
                  <span v-if="currentResult.scores?.[name] != null" class="tiny">
                    {{ currentResult.scores[name] }}
                  </span>
                </li>
              </ol>

              <div v-if="currentResult" class="concept-box" style="margin-top: 12px">
                <h4>验算明细</h4>
                <div
                  class="panel-md"
                  v-html="renderRichText(currentResult.panel_markdown, { math: true })"
                />
              </div>

              <div class="lab-actions" style="margin-top: 12px">
                <button
                  class="btn btn-soft"
                  type="button"
                  :disabled="!currentResult || explainLoading || !backendOk"
                  @click="explainChange"
                >
                  {{ explainLoading ? "解释生成中…" : "知知解释这次变化" }}
                </button>
              </div>
              <div v-if="explainText" class="concept-box explain-box">
                <h4>知知解释</h4>
                <div class="panel-md" v-html="renderRichText(explainText, { math: true })" />
                <div v-if="explainSources.length" class="tiny" style="margin-top: 8px">
                  来源：
                  <span v-for="(s, i) in explainSources" :key="i">
                    {{ s.source }}{{ s.title ? " · " + s.title : "" }}{{ i < explainSources.length - 1 ? "；" : "" }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>

    <p class="err" v-if="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.case-lab h2 {
  margin: 0 0 8px;
  font-size: 22px;
}
.lab-lead {
  margin: 0 0 18px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
}
.lab-empty {
  padding: 18px;
  border: 1px dashed #e4e6f0;
  border-radius: 14px;
  background: #fafbff;
  color: var(--text);
}
.lab-case-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 14px;
}
.case-title {
  font-weight: 800;
  font-size: 15px;
  color: var(--ink);
}
.lab-note {
  margin: 0 0 12px;
}
.weight-row {
  display: grid;
  grid-template-columns: minmax(72px, 0.9fr) minmax(0, 1.4fr) 72px;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.weight-head {
  display: flex;
  flex-direction: column;
  gap: 1px;
  font-size: 12px;
  font-weight: 750;
  color: #4f5670;
}
.weight-range {
  width: 100%;
  accent-color: var(--primary);
}
.weight-num {
  width: 100%;
  border: 1px solid #e2e4ef;
  border-radius: 8px;
  padding: 6px 8px;
  font: inherit;
  font-size: 12px;
  text-align: center;
}
.rank-list {
  margin: 10px 0 0;
  padding-left: 18px;
  font-size: 13px;
  color: #3f4660;
  line-height: 1.7;
}
.lab-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  gap: 14px;
}
.lab-block {
  border: 1px solid #e6e8f1;
  border-radius: 16px;
  background: #fbfcff;
  padding: 14px;
}
.lab-block-title {
  font-size: 13px;
  font-weight: 800;
  color: #3f4660;
  margin-bottom: 12px;
}
.lab-sub {
  font-size: 12px;
  font-weight: 750;
  color: #686f84;
  margin: 10px 0 8px;
}
.field-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.field-row label {
  font-size: 12px;
  font-weight: 700;
  color: #5b6280;
  min-width: 72px;
}
.field-row select,
.field-row input {
  flex: 1;
  border: 1px solid #e2e4ef;
  border-radius: 10px;
  padding: 8px 10px;
  background: #fff;
  font: inherit;
  font-size: 13px;
}
.lab-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
}
.lab-table th,
.lab-table td {
  border: 1px solid #e8eaf3;
  padding: 6px;
  text-align: center;
}
.lab-table th {
  background: #f4f5fa;
  font-weight: 750;
  color: #4f5670;
}
.lab-table input {
  width: 100%;
  min-width: 56px;
  border: 0;
  background: transparent;
  text-align: center;
  font: inherit;
  font-size: 13px;
  padding: 4px;
}
.prob-meta {
  margin-top: 8px;
  font-size: 12px;
  color: #158a65;
  display: flex;
  align-items: center;
  gap: 10px;
}
.prob-meta.bad {
  color: var(--bad);
}
.linkish {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-size: 12px;
  font-weight: 750;
  padding: 0;
  cursor: pointer;
}
.lab-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid #e4e5ef;
  border-radius: 12px;
  padding: 11px 16px;
  background: #fff;
  color: #454b66;
  font: inherit;
  font-size: 13px;
  font-weight: 750;
  cursor: pointer;
}
.btn:hover:not(:disabled) {
  background: #f7f7fb;
  border-color: #d5d8e6;
}
.btn-primary {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background: #574be0;
  border-color: #574be0;
}
.btn-soft {
  background: var(--primary-soft);
  border-color: #e9e4ff;
  color: var(--primary);
}
.btn-soft:hover:not(:disabled) {
  background: #f4efff;
  border-color: #d8cffd;
}
.btn-small {
  font-size: 12px;
  padding: 8px 11px;
}
.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.compare-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.compare-card {
  border: 1px solid #e6e8f1;
  border-radius: 14px;
  background: #fff;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.compare-card.changed {
  border-color: #cfc8f5;
  background: #f6f4ff;
}
.compare-label {
  font-size: 11px;
  font-weight: 750;
  color: #8a90a5;
}
.compare-card strong {
  font-size: 18px;
  color: var(--ink);
}
.change-tip {
  margin: 10px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: #4f46a8;
}
.change-tip.muted {
  color: #8a90a5;
  font-weight: 650;
}
.concept-box {
  background: #f1f0ff;
  border-radius: 13px;
  padding: 14px 16px;
  font-size: 13px;
  color: #3f4660;
  line-height: 1.7;
}
.concept-box h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #2a3148;
}
.explain-box {
  margin-top: 12px;
  background: #f7f8fc;
}
.panel-md {
  font-size: 13px;
  line-height: 1.75;
}
.err {
  margin-top: 10px;
  color: var(--bad);
  font-size: 13px;
}
.tiny {
  font-size: 12px;
  color: var(--muted);
}
@media (max-width: 980px) {
  .lab-grid {
    grid-template-columns: 1fr;
  }
}
</style>
