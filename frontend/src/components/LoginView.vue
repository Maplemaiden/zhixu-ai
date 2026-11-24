<script setup>
import { onMounted, ref } from "vue";
import { api } from "../api";

const props = defineProps({
  doLogin: { type: Function, required: true },
  doRegister: { type: Function, required: true },
});

const mode = ref("login");
const username = ref("demo");
const password = ref("demo123");
const displayName = ref("");
const loading = ref(false);
const error = ref("");
const demos = ref([]);

onMounted(async () => {
  try {
    const data = await api.demoAccounts();
    demos.value = data.accounts || [];
  } catch {
    demos.value = [
      { username: "demo", password: "demo123", display_name: "演示学生" },
      { username: "student", password: "student123", display_name: "体验学生" },
    ];
  }
});

function fillDemo(acc) {
  username.value = acc.username;
  password.value = acc.password;
  mode.value = "login";
  error.value = "";
}

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    if (mode.value === "login") {
      await props.doLogin(username.value.trim(), password.value);
    } else {
      await props.doRegister(username.value.trim(), password.value, displayName.value.trim());
    }
  } catch (e) {
    error.value = e?.message || "登录失败";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-brand">
        <div class="mark">知</div>
        <div>
          <h1>知序 AI</h1>
          <p>决策理论与方法 · 数字人助教</p>
        </div>
      </div>

      <div class="tabs">
        <button type="button" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button type="button" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <form class="form" @submit.prevent="submit">
        <label>
          <span>账号</span>
          <input v-model="username" autocomplete="username" placeholder="账号" required />
        </label>
        <label v-if="mode === 'register'">
          <span>显示名（可选）</span>
          <input v-model="displayName" placeholder="如：王同学" />
        </label>
        <label>
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            placeholder="密码"
            required
          />
        </label>
        <p v-if="error" class="err">{{ error }}</p>
        <button class="submit" type="submit" :disabled="loading">
          {{ loading ? "请稍候…" : mode === "login" ? "进入学习" : "注册并进入" }}
        </button>
      </form>

      <div class="demo-box">
        <div class="demo-title">演示账号（一键填入）</div>
        <button
          v-for="acc in demos"
          :key="acc.username"
          type="button"
          class="demo-chip"
          @click="fillDemo(acc)"
        >
          {{ acc.username }} / {{ acc.password }}
          <small>{{ acc.display_name }}</small>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 24px 14px;
  background:
    radial-gradient(ellipse 80% 60% at 20% 10%, rgba(102, 88, 223, 0.18), transparent 55%),
    radial-gradient(ellipse 70% 50% at 90% 80%, rgba(74, 180, 160, 0.14), transparent 50%),
    linear-gradient(160deg, #f4f5fb 0%, #e9ecf8 45%, #f7f3ee 100%);
}
.login-card {
  width: min(420px, 100%);
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(36, 37, 59, 0.08);
  border-radius: 22px;
  padding: 28px 26px 24px;
  box-shadow: 0 18px 50px rgba(36, 37, 59, 0.08);
}
.login-brand {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 22px;
}
.mark {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: #24253b;
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 20px;
}
.login-brand h1 {
  margin: 0;
  font-size: 22px;
  color: #24253b;
}
.login-brand p {
  margin: 4px 0 0;
  color: #6b7290;
  font-size: 13px;
}
.tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  background: #eef0f8;
  padding: 4px;
  border-radius: 12px;
  margin-bottom: 18px;
}
.tabs button {
  border: 0;
  background: transparent;
  padding: 10px;
  border-radius: 10px;
  color: #6b7290;
  cursor: pointer;
  font-weight: 600;
}
.tabs button.active {
  background: #fff;
  color: #24253b;
  box-shadow: 0 1px 4px rgba(36, 37, 59, 0.08);
}
.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #5a617c;
}
.form input {
  border: 1px solid #d8dceb;
  border-radius: 12px;
  padding: 11px 12px;
  font-size: 15px;
  outline: none;
  background: #fff;
}
.form input:focus {
  border-color: #6658df;
  box-shadow: 0 0 0 3px rgba(102, 88, 223, 0.12);
}
.submit {
  margin-top: 4px;
  border: 0;
  border-radius: 12px;
  padding: 12px;
  background: #6658df;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}
.submit:disabled {
  opacity: 0.65;
  cursor: wait;
}
.err {
  margin: 0;
  color: #c0392b;
  font-size: 13px;
}
.demo-box {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px dashed #d8dceb;
}
.demo-title {
  font-size: 12px;
  color: #8a91ab;
  margin-bottom: 8px;
}
.demo-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
  text-align: left;
  border: 1px solid #e2e6f2;
  background: #f7f8fc;
  border-radius: 12px;
  padding: 10px 12px;
  margin-bottom: 8px;
  cursor: pointer;
  color: #24253b;
  font-weight: 600;
}
.demo-chip small {
  margin-top: 2px;
  color: #8a91ab;
  font-weight: 500;
}
.demo-chip:hover {
  border-color: #6658df;
}
</style>
