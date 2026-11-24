import { computed, ref } from "vue";
import { api, setAuthToken } from "../api";

const TOKEN_KEY = "zhixu_ai_auth_token";

const token = ref(localStorage.getItem(TOKEN_KEY) || "");
const user = ref(null);
const ready = ref(false);
const bootError = ref("");

setAuthToken(token.value);

export function useAuth() {
  const isLoggedIn = computed(() => !!token.value && !!user.value);

  async function bootstrap() {
    bootError.value = "";
    if (!token.value) {
      user.value = null;
      ready.value = true;
      return;
    }
    try {
      const data = await api.me();
      user.value = data.user;
    } catch {
      token.value = "";
      user.value = null;
      setAuthToken("");
      localStorage.removeItem(TOKEN_KEY);
    } finally {
      ready.value = true;
    }
  }

  async function login(username, password) {
    const data = await api.login(username, password);
    token.value = data.token;
    user.value = data.user;
    setAuthToken(data.token);
    localStorage.setItem(TOKEN_KEY, data.token);
    return data.user;
  }

  async function register(username, password, displayName = "") {
    const data = await api.register(username, password, displayName);
    token.value = data.token;
    user.value = data.user;
    setAuthToken(data.token);
    localStorage.setItem(TOKEN_KEY, data.token);
    return data.user;
  }

  async function logout() {
    try {
      await api.logout();
    } catch {
      /* ignore */
    }
    token.value = "";
    user.value = null;
    setAuthToken("");
    localStorage.removeItem(TOKEN_KEY);
  }

  return {
    token,
    user,
    ready,
    bootError,
    isLoggedIn,
    bootstrap,
    login,
    register,
    logout,
  };
}
