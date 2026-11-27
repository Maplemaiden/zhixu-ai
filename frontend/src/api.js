// 开发：走 Vite 代理 /api → 8001；打包后与后端同域，直接打根路径
const BASE = import.meta.env.DEV ? "/api" : "";

let authToken = "";

export function setAuthToken(token) {
  authToken = token || "";
}

export function getAuthToken() {
  return authToken;
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
    const detail = data.detail || res.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
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
      body: JSON.stringify({
        question,
        method_id: methodId,
        section: extra.section ?? null,
        section_label: extra.sectionLabel ?? null,
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
