// 开发：走 Vite 代理 /api → 8001；打包后与后端同域，直接打根路径
const BASE = import.meta.env.DEV ? "/api" : "";

let authToken = "";

export function setAuthToken(token) {
  authToken = token || "";
}

export function getAuthToken() {
  return authToken;
}

const FIELD_LABELS = {
  username: "账号",
  password: "密码",
  display_name: "显示名",
  question: "问题",
  alpha: "折中系数 α",
  probs: "状态概率",
  weights: "属性权重",
  payoffs: "收益表",
  matrix: "决策矩阵",
};

export function formatApiError(detail, statusText = "请求失败") {
  if (!detail) return statusText || "请求失败";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const msgs = detail.map((it) => {
      const loc = (it?.loc || []).filter((x) => x !== "body");
      const fieldKey = loc[0] || "";
      const label = FIELD_LABELS[fieldKey] || loc.join(".") || "输入项";
      const t = it?.type || "";
      if (t === "string_too_short") {
        if (fieldKey === "username") return "账号至少 2 个字符";
        if (fieldKey === "password") return "密码太短，请至少 6 位";
        return `${label}长度不足`;
      }
      if (t === "string_too_long") return `${label}内容过长`;
      if (t === "missing") return `请填写${label}`;
      if (t.includes("float") || t.includes("int") || t.includes("number")) {
        return `${label}请输入有效数字`;
      }
      if (t === "less_than_equal" || t === "greater_than_equal" || t === "less_than" || t === "greater_than") {
        if (fieldKey === "alpha") return "折中系数 α 须在 0～1 之间";
        return `${label}超出允许范围`;
      }
      const rawMsg = String(it?.msg || "").replace(/^Value error,\s*/i, "");
      return rawMsg ? `${label}：${rawMsg}` : `${label}格式不正确`;
    });
    const uniq = [...new Set(msgs.filter(Boolean))];
    if (uniq.length) return uniq.join("；");
  }
  return typeof detail === "object" ? JSON.stringify(detail) : String(detail);
}

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(formatApiError(data.detail, res.statusText));
  }
  return data;
}

export const api = {
  health: () => request("/health"),
  login: (username, password) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  register: (username, password, display_name = "") =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password, display_name }),
    }),
  me: () => request("/auth/me"),
  logout: () => request("/auth/logout", { method: "POST" }),
  demoAccounts: () => request("/auth/demo_accounts"),
  listNotes: (methodId) =>
    request(methodId ? `/notes?method_id=${encodeURIComponent(methodId)}` : "/notes"),
  createNote: (body) =>
    request("/notes", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateNote: (id, body) =>
    request(`/notes/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  deleteNote: (id) => request(`/notes/${id}`, { method: "DELETE" }),
  stepCard: (id = "expected_value") => request(`/teach/step_card/${id}`),
  lessonReading: (id = "expected_value") => request(`/teach/reading/${id}`),
  ask: (question, methodId = "expected_value", extra = {}) =>
    request("/teach/ask", {
      method: "POST",
      signal: extra.signal,
      body: JSON.stringify({
        question,
        method_id: methodId,
        section: extra.section ?? null,
        section_label: extra.sectionLabel ?? null,
        history: extra.history ?? [],
      }),
    }),
  classify: (question) =>
    request("/teach/classify", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  computeEV: (payload) =>
    request("/compute/expected_value", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  computeUncertainty: (payload) =>
    request("/compute/uncertainty", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  computeMadm: (payload) =>
    request("/compute/madm", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listQuiz: (methodId = "expected_value") => request(`/quiz/${methodId}`),
  grade: (body) =>
    request("/quiz/grade", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
