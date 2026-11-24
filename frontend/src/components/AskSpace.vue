<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from "vue";
import { api } from "../api";
import { useSpeech } from "../composables/useSpeech";
import { renderRichText } from "../utils/renderRichText";
import AvatarPanel from "./AvatarPanel.vue";

const props = defineProps({
  backendOk: { type: Boolean, default: true },
});

const emit = defineEmits(["back"]);

const { speaking, paused, currentLine, supported, stop, speakText, pause, resume } = useSpeech();

const input = ref("");
const loading = ref(false);
const error = ref("");
const messages = ref([]);
const logEl = ref(null);

const avatarLine = computed(() => {
  if (loading.value) return "知知思考中…";
  if (currentLine.value) return currentLine.value;
  const last = [...messages.value].reverse().find((m) => m.role === "assistant");
  if (last) return String(last.text).replace(/\s+/g, " ").slice(0, 72);
  return "你好，我是知知。有问题尽管问我。";
});

const suggestionPages = [
  [
    "风险型和不确定型怎么区分？",
    "期望值准则和决策树有什么关系？",
    "AHP 和 TOPSIS 分别适合什么情况？",
    "用一个小例子讲讲后悔值准则",
  ],
  [
    "效用是在衡量什么？",
    "DEA 适合比较什么样的单位？",
    "目标规划里的偏差变量是什么？",
    "马尔可夫链的无后效性怎么理解？",
  ],
  [
    "贝叶斯决策为什么要修正概率？",
    "乐观准则和悲观准则差在哪？",
    "多属性决策的权重从哪来？",
    "离散事件仿真在解决什么问题？",
  ],
];
const pageIndex = ref(0);
const rollPaused = ref(false);
const visibleSuggestions = computed(() => suggestionPages[pageIndex.value]);
let rollTimer = null;

function nextSuggestionPage() {
  pageIndex.value = (pageIndex.value + 1) % suggestionPages.length;
}

async function scrollBottom() {
  await nextTick();
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight;
}

function useSuggestion(q) {
  input.value = q;
}

function clearChat() {
  messages.value = [];
  error.value = "";
  stop();
}

async function send() {
  const q = input.value.trim();
  if (!q || loading.value) return;
  loading.value = true;
  error.value = "";
  messages.value.push({ role: "user", text: q });
  input.value = "";
  await scrollBottom();
  try {
    const res = await api.ask(q, "course", {
      section: null,
      sectionLabel: "全课答疑",
    });
    const answer = res.answer || "暂时没有生成回答，请换个问法再试。";
    messages.value.push({
      role: "assistant",
      text: answer,
      sources: res.sources || [],
      topic: "知知",
    });
    speakText(String(answer).replace(/\s+/g, " ").slice(0, 360));
  } catch (e) {
    error.value = e.message || String(e);
    messages.value.push({
      role: "assistant",
      text: `抱歉，这次没有答上：${error.value}`,
      topic: "系统",
    });
  } finally {
    loading.value = false;
    await scrollBottom();
  }
}

function onKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

function speakLast() {
  const last = [...messages.value].reverse().find((m) => m.role === "assistant");
  if (last) speakText(String(last.text).replace(/\s+/g, " ").slice(0, 360));
}

onMounted(() => {
  rollTimer = setInterval(() => {
    if (!rollPaused.value && !messages.value.length) nextSuggestionPage();
  }, 10000);
});
onUnmounted(() => {
  if (rollTimer) clearInterval(rollTimer);
});
</script>

<template>
  <section class="ask-space" aria-label="答疑空间">
    <div class="ask-bg" aria-hidden="true" />
    <div class="ask-bg-veil" aria-hidden="true" />

    <button class="ask-exit" type="button" @click="emit('back')">
      <span aria-hidden="true">←</span>
      退出
    </button>

    <div class="ask-layout">
      <div class="ask-chat">
        <header class="ask-chat-head">
          <div>
            <h1>答疑空间</h1>
            <p>《决策理论与方法》全课答疑</p>
          </div>
          <div class="ask-chat-links">
            <button class="linkish" type="button" :disabled="!messages.length" @click="clearChat">清空</button>
          </div>
        </header>

        <div ref="logEl" class="chat-stage">
          <div v-if="!messages.length" class="welcome">
            <p class="welcome-lead">直接问知知。概念、方法分流、解题步骤都可以。</p>
            <div
              class="suggest-viewport"
              @mouseenter="rollPaused = true"
              @mouseleave="rollPaused = false"
            >
              <Transition name="suggest-roll" mode="out-in">
                <div class="suggest-row" :key="pageIndex">
                  <button
                    v-for="s in visibleSuggestions"
                    :key="s"
                    class="chip"
                    type="button"
                    @click="useSuggestion(s)"
                  >
                    {{ s }}
                  </button>
                </div>
              </Transition>
            </div>
          </div>

          <div v-for="(m, i) in messages" :key="i" class="bubble-row" :class="{ mine: m.role === 'user' }">
            <div class="bubble-icon">{{ m.role === "user" ? "我" : "知" }}</div>
            <div class="bubble">
              <div
                class="bubble-text"
                v-html="renderRichText(m.text, { math: m.role !== 'user' })"
              />
              <div class="bubble-meta">{{ m.role === "user" ? "学生" : m.topic || "知知" }}</div>
              <div v-if="m.sources?.length" class="bubble-sources">
                教材来源：
                <span v-for="(s, si) in m.sources" :key="si">
                  {{ s.source }}{{ s.title ? " · " + s.title : "" }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="loading" class="thinking">知知思考中…</div>
        </div>

        <footer class="composer">
          <div v-if="messages.length" class="suggest-row compact">
            <button v-for="s in visibleSuggestions.slice(0, 3)" :key="s" class="chip" type="button" @click="useSuggestion(s)">
              {{ s }}
            </button>
          </div>
          <div class="composer-box">
            <textarea
              v-model="input"
              rows="2"
              placeholder="输入问题，Enter 发送…"
              @keydown="onKeydown"
            />
            <button
              class="send-btn"
              type="button"
              :disabled="loading || !backendOk || !input.trim()"
              @click="send"
            >
              {{ loading ? "…" : "发送" }}
            </button>
          </div>
          <div class="composer-foot">
            <button class="linkish" type="button" :disabled="!messages.length" @click="speakLast">口播上一条</button>
            <span class="composer-hint">Shift+Enter 换行</span>
          </div>
          <p v-if="error" class="err">{{ error }}</p>
        </footer>
      </div>

      <aside class="ask-avatar">
        <div class="ask-avatar-stage">
          <AvatarPanel
            :speaking="speaking"
            :paused="paused"
            :line="avatarLine"
            :supported="supported"
            section-label="答疑空间"
            @play="speakLast"
            @pause="pause"
            @resume="resume"
            @stop="stop"
            @prev="() => {}"
            @next="() => {}"
          />
        </div>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.ask-space {
  position: fixed;
  inset: 0;
  z-index: 40;
  overflow: hidden;
  color: #e8f2ee;
}
.ask-bg {
  position: absolute;
  inset: 0;
  background:
    url("/ask-space-bg.png") center / cover no-repeat,
    linear-gradient(160deg, #123041 0%, #1a3d48 45%, #0f2430 100%);
}
.ask-bg-veil {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(10, 22, 34, 0.55) 0%, rgba(10, 22, 34, 0.28) 58%, rgba(10, 22, 34, 0.42) 100%),
    radial-gradient(ellipse 60% 50% at 78% 42%, rgba(120, 190, 170, 0.12), transparent 62%);
  pointer-events: none;
}
.ask-exit {
  position: absolute;
  top: 18px;
  left: 18px;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(207, 238, 227, 0.28);
  background: rgba(16, 32, 46, 0.62);
  backdrop-filter: blur(12px);
  color: #e8f2ee;
  border-radius: 999px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 750;
  cursor: pointer;
}
.ask-exit:hover {
  background: rgba(24, 52, 64, 0.86);
  border-color: #9fd6c4;
  color: #cfeee3;
}
.ask-layout {
  position: relative;
  z-index: 2;
  height: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(300px, 0.78fr);
  gap: 18px;
  padding: 68px 22px 22px;
  box-sizing: border-box;
}
.ask-chat {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: 24px;
  border: 1px solid rgba(207, 238, 227, 0.16);
  background: rgba(12, 28, 40, 0.55);
  backdrop-filter: blur(16px);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
  overflow: hidden;
}
.ask-chat-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 18px 20px 12px;
  border-bottom: 1px solid rgba(207, 238, 227, 0.1);
  flex-shrink: 0;
}
.ask-chat-head h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 900;
  letter-spacing: -0.02em;
  color: #f3faf7;
}
.ask-chat-head p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #9fd6c4;
  font-weight: 650;
}
.ask-chat-links {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 4px;
}
.chat-stage {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 18px 20px;
  scrollbar-width: thin;
}
.welcome {
  margin: 8vh auto 0;
  max-width: 560px;
  text-align: center;
}
.welcome-lead {
  margin: 0 0 20px;
  font-size: 15px;
  line-height: 1.7;
  color: #b7c9c4;
}
.suggest-viewport {
  overflow: hidden;
  min-height: 108px;
}
.suggest-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}
.suggest-roll-enter-active,
.suggest-roll-leave-active {
  transition: transform 0.45s ease, opacity 0.45s ease;
}
.suggest-roll-enter-from {
  transform: translateY(22px);
  opacity: 0;
}
.suggest-roll-leave-to {
  transform: translateY(-22px);
  opacity: 0;
}
.suggest-row.compact {
  justify-content: flex-start;
  margin-bottom: 12px;
}
.chip {
  border: 1px solid rgba(159, 214, 196, 0.28);
  background: rgba(255, 255, 255, 0.06);
  color: #d7eee5;
  border-radius: 999px;
  padding: 10px 14px;
  font-size: 12px;
  font-weight: 650;
  text-align: left;
  cursor: pointer;
}
.chip:hover {
  background: rgba(159, 214, 196, 0.14);
  border-color: #9fd6c4;
}
.bubble-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: flex-start;
}
.bubble-row.mine {
  flex-direction: row-reverse;
}
.bubble-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(159, 214, 196, 0.22);
  color: #cfeee3;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
  flex: none;
}
.bubble-row.mine .bubble-icon {
  background: #cfeee3;
  color: #123041;
}
.bubble {
  max-width: min(92%, 680px);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(207, 238, 227, 0.14);
  border-radius: 18px;
  padding: 14px 16px;
}
.bubble-row.mine .bubble {
  background: rgba(207, 238, 227, 0.92);
  border-color: transparent;
  color: #123041;
}
.bubble-text {
  font-size: 15px;
  line-height: 1.75;
  overflow-wrap: anywhere;
}
.bubble-text :deep(.md-p) {
  margin: 0 0 0.55em;
}
.bubble-text :deep(.md-p:last-child),
.bubble-text :deep(.md-h:last-child) {
  margin-bottom: 0;
}
.bubble-text :deep(.md-h) {
  margin: 0.35em 0 0.55em;
}
.bubble-text :deep(.md-ul),
.bubble-text :deep(.md-ol) {
  margin: 0.35em 0 0.65em;
  padding-left: 1.35em;
}
.bubble-text :deep(li) {
  margin: 0.2em 0;
}
.bubble-text :deep(strong) {
  font-weight: 800;
  color: #e8fff6;
}
.bubble-text :deep(code) {
  font-size: 0.92em;
  padding: 0.05em 0.35em;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.08);
}
.bubble-meta {
  margin-top: 8px;
  font-size: 11px;
  color: #8eaaa2;
}
.bubble-row.mine .bubble-meta {
  color: #4d6b64;
}
.bubble-sources {
  margin-top: 8px;
  font-size: 12px;
  color: #9fd6c4;
  line-height: 1.5;
}
.thinking {
  margin: 8px 0 0 48px;
  font-size: 13px;
  color: #9fd6c4;
  font-weight: 650;
}
.composer {
  flex-shrink: 0;
  padding: 12px 16px 16px;
  border-top: 1px solid rgba(207, 238, 227, 0.1);
  background: rgba(8, 20, 30, 0.35);
}
.composer-box {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: end;
  padding: 12px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(207, 238, 227, 0.16);
}
.composer textarea {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 8px 6px;
  resize: none;
  min-height: 52px;
  max-height: 140px;
  font: inherit;
  font-size: 15px;
  line-height: 1.55;
  color: #f3faf7;
}
.composer textarea:focus {
  outline: none;
}
.composer textarea::placeholder {
  color: #8aa09a;
}
.send-btn {
  border: 0;
  border-radius: 14px;
  min-width: 72px;
  height: 44px;
  padding: 0 16px;
  background: #cfeee3;
  color: #123041;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
}
.send-btn:hover:not(:disabled) {
  background: #e4f7f0;
}
.send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.composer-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}
.linkish {
  border: 0;
  background: transparent;
  color: #9bb0aa;
  font-size: 12px;
  font-weight: 650;
  padding: 0;
  cursor: pointer;
}
.linkish:hover:not(:disabled) {
  color: #cfeee3;
}
.linkish:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.composer-hint {
  font-size: 11px;
  color: #7d918b;
}
.err {
  margin: 8px 0 0;
  color: #f0a399;
  font-size: 13px;
}
.ask-avatar {
  min-width: 0;
  min-height: 0;
  display: flex;
  align-items: stretch;
}
.ask-avatar-stage {
  width: 100%;
  border-radius: 24px;
  border: 1px solid rgba(207, 238, 227, 0.16);
  background: rgba(12, 28, 40, 0.42);
  backdrop-filter: blur(14px);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
  padding: 16px;
  display: flex;
  align-items: center;
}
.ask-avatar-stage :deep(.avatar-panel) {
  width: 100%;
  background: transparent;
  border: 0;
  box-shadow: none;
  padding: 0;
}
.ask-avatar-stage :deep(.avatar-scene) {
  height: min(42vh, 360px);
  background: radial-gradient(circle at 50% 35%, rgba(207, 238, 227, 0.28), rgba(24, 58, 70, 0.85) 70%);
  border-color: rgba(207, 238, 227, 0.18);
}
.ask-avatar-stage :deep(.avatar-status) {
  color: #e8f2ee;
}
.ask-avatar-stage :deep(.tiny) {
  color: #9fd6c4;
}
.ask-avatar-stage :deep(.player) {
  background: rgba(255, 255, 255, 0.08);
}
.ask-avatar-stage :deep(.player-sub) {
  color: #9bb0aa;
}
.ask-avatar-stage :deep(.link) {
  color: #cfeee3;
}
.ask-avatar-stage :deep(.speechbubble) {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(207, 238, 227, 0.14);
  color: #d7e8e2;
  min-height: 72px;
}
@media (max-width: 980px) {
  .ask-layout {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(0, 1fr) auto;
    padding: 64px 12px 12px;
    gap: 12px;
  }
  .ask-avatar {
    order: -1;
    max-height: 280px;
  }
  .ask-avatar-stage {
    padding: 10px;
  }
  .ask-avatar-stage :deep(.avatar-scene) {
    height: 150px;
  }
  .ask-avatar-stage :deep(.speechbubble) {
    min-height: 0;
    margin-top: 8px;
    padding: 8px 10px;
  }
}
@media (max-width: 720px) {
  .ask-exit {
    top: 12px;
    left: 12px;
  }
  .composer-hint {
    display: none;
  }
  .welcome {
    margin-top: 4vh;
  }
}
</style>
