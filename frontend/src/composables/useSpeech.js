import { ref } from "vue";

/** 浏览器中文 TTS：支持分步、暂停/继续、停止 */
export function useSpeech() {
  const speaking = ref(false);
  const paused = ref(false);
  const currentLine = ref("");
  const queue = ref([]);
  const index = ref(-1);
  const supported = typeof window !== "undefined" && "speechSynthesis" in window;
  /** cancel() 后立刻 speak()，Chrome 有时会把同一句读两遍；用代次作废过期回调 */
  let token = 0;
  let startTimer = null;

  function stop() {
    token += 1;
    if (startTimer) {
      clearTimeout(startTimer);
      startTimer = null;
    }
    if (supported) window.speechSynthesis.cancel();
    speaking.value = false;
    paused.value = false;
    currentLine.value = "";
    queue.value = [];
    index.value = -1;
  }

  function pause() {
    if (!supported || !speaking.value) return;
    window.speechSynthesis.pause();
    paused.value = true;
  }

  function resume() {
    if (!supported) return;
    window.speechSynthesis.resume();
    paused.value = false;
  }

  function speakLines(lines, { autoStart = true } = {}) {
    stop();
    const list = (lines || []).map((x) => String(x).trim()).filter(Boolean);
    queue.value = list;
    if (!list.length || !autoStart) return;
    const my = token;
    // 等 cancel 落定再开读，避开同一句入队两次
    startTimer = setTimeout(() => {
      startTimer = null;
      if (my !== token) return;
      playFrom(0);
    }, 80);
  }

  function playFrom(i) {
    const my = token;
    if (my !== token) return;
    if (!queue.value.length || i >= queue.value.length) {
      speaking.value = false;
      paused.value = false;
      currentLine.value = "";
      index.value = -1;
      return;
    }
    index.value = i;
    currentLine.value = queue.value[i];
    speaking.value = true;
    paused.value = false;

    if (!supported) {
      window.setTimeout(() => {
        if (my === token) playFrom(i + 1);
      }, 1600);
      return;
    }

    const u = new SpeechSynthesisUtterance(currentLine.value);
    u.lang = "zh-CN";
    u.rate = 1;
    const voice = window.speechSynthesis
      .getVoices()
      .find((v) => v.lang === "zh-CN" || v.lang?.toLowerCase().startsWith("zh"));
    if (voice) u.voice = voice;
    u.onend = () => {
      if (my !== token || paused.value) return;
      playFrom(i + 1);
    };
    u.onerror = (e) => {
      if (my !== token) return;
      const reason = e?.error || "";
      if (reason === "interrupted" || reason === "canceled" || reason === "cancelled") return;
      playFrom(i + 1);
    };
    window.speechSynthesis.speak(u);
  }

  function speakText(text) {
    speakLines([text]);
  }

  return {
    speaking,
    paused,
    currentLine,
    queue,
    index,
    supported,
    stop,
    pause,
    resume,
    speakLines,
    speakText,
  };
}
