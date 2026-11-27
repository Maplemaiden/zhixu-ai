<script setup>
import { onMounted, ref, watch } from "vue";
import { api } from "../api";
import { course } from "../data/catalog.js";

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
const showPassword = ref(false);
const FALLBACK_DEMOS = [
  { username: "demo", password: "demo123", display_name: "演示学生" },
  { username: "student", password: "student123", display_name: "体验学生" },
];
const demos = ref(FALLBACK_DEMOS);

onMounted(async () => {
  try {
    const data = await api.demoAccounts();
    if (data.accounts?.length) demos.value = data.accounts;
  } catch {
    demos.value = FALLBACK_DEMOS;
  }
});

function fillDemo(acc) {
  username.value = acc.username;
  password.value = acc.password;
  mode.value = "login";
  error.value = "";
}

/** 把后端 Pydantic / JSON 报错翻成可读中文 */
function friendlyError(e, fallback) {
  const raw = String(e?.message || "");
  if (raw.trim().startsWith("[")) {
    try {
      const arr = JSON.parse(raw);
      const map = {
        string_too_short: (f) => (f.includes("username") ? "账号至少 2 个字符" : "密码太短，请至少 6 位"),
        string_too_long: () => "输入内容过长",
        value_error: () => "输入格式不正确",
        missing: () => "请填写必填项",
      };
      const msgs = arr.map((it) => {
        const f = (it.loc || []).join(".");
        const label = f.includes("username") ? "账号" : f.includes("password") ? "密码" : f || "输入项";
        const fn = map[it.type];
        return fn ? fn(f) : `${label}：${it.msg || "格式不正确"}`;
      });
      if (msgs.length) return [...new Set(msgs)].join("；");
    } catch {
      /* 落到下面 */
    }
    return fallback;
  }
  if (/[\u4e00-\u9fa5]/.test(raw)) return raw;
  if (/Invalid|incorrect/i.test(raw)) return "账号或密码不正确";
  return raw || fallback;
}

watch(mode, () => {
  error.value = "";
});

async function submit() {
  error.value = "";
  const u = username.value.trim();
  const p = password.value;
  if (mode.value === "register") {
    if (!u) {
      error.value = "请填写账号";
      return;
    }
    if (u.length < 2) {
      error.value = "账号至少 2 个字符";
      return;
    }
    if (!p) {
      error.value = "请填写密码";
      return;
    }
    if (p.length < 6) {
      error.value = "密码太短，请至少 6 位";
      return;
    }
  } else {
    if (!u) {
      error.value = "请填写账号";
      return;
    }
    if (!p) {
      error.value = "请填写密码";
      return;
    }
  }
  loading.value = true;
  try {
    if (mode.value === "login") {
      await props.doLogin(username.value.trim(), password.value);
    } else {
      await props.doRegister(username.value.trim(), password.value, displayName.value.trim());
    }
  } catch (e) {
    error.value = friendlyError(e, mode.value === "login" ? "登录失败" : "注册失败");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <section class="login-story" aria-label="产品介绍">
      <div class="story-brand">
        <span class="mark">知</span>
        <div>
          <strong>{{ course.assistant }}</strong>
          <span>{{ course.name }}</span>
        </div>
      </div>

      <h1>课后跟着知知，把决策课学成能追问的过程。</h1>
      <p class="story-lead">
        按讲听讲解、进实验台验算、做题追问，都在同一套学习台里。数字由程序算，知知只负责把步骤讲清楚。
      </p>

      <ul class="story-points">
        <li>
          <span class="pt-icon">01</span>
          <div>
            <b>一讲一个学习台</b>
            <span>按讲听讲义、对照课件，进度会留下来。</span>
          </div>
        </li>
        <li>
          <span class="pt-icon">02</span>
          <div>
            <b>实验台改参数看结果</b>
            <span>期望值、不确定型、多属性排序都走 Solver，不口算。</span>
          </div>
        </li>
        <li>
          <span class="pt-icon">03</span>
          <div>
            <b>带着课程上下文答疑</b>
            <span>课中追问或进答疑空间，都对着这门课的资料讲。</span>
          </div>
        </li>
      </ul>

      <div class="story-foot">
        <div class="zhizhi" aria-hidden="true">
          <i class="hair" />
          <i class="face">
            <i class="eye l" />
            <i class="eye r" />
            <i class="mouth" />
          </i>
          <i class="body" />
        </div>
        <div>
          <div class="story-teacher">主讲 {{ course.teacher }}</div>
          <div class="story-course">《{{ course.name }}》课后助教</div>
        </div>
      </div>
    </section>

    <section class="login-panel">
      <div class="login-card">
        <p class="panel-kicker">{{ mode === "login" ? "欢迎回来" : "创建账号" }}</p>
        <h2>{{ mode === "login" ? "登录后继续学习" : "注册后进入学习台" }}</h2>

        <div class="tabs" role="tablist">
          <button
            type="button"
            role="tab"
            :class="{ active: mode === 'login' }"
            :aria-selected="mode === 'login'"
            @click="mode = 'login'"
          >
            登录
          </button>
          <button
            type="button"
            role="tab"
            :class="{ active: mode === 'register' }"
            :aria-selected="mode === 'register'"
            @click="mode = 'register'"
          >
            注册
          </button>
        </div>

        <form class="form" @submit.prevent="submit">
          <label>
            <span>账号</span>
            <input
              v-model="username"
              autocomplete="username"
              placeholder="请输入账号"
              required
              @input="error = ''"
            />
          </label>
          <label v-if="mode === 'register'">
            <span>显示名<span class="optional">可选</span></span>
            <input
              v-model="displayName"
              placeholder="如：王同学"
              @input="error = ''"
            />
          </label>
          <label>
            <span>密码</span>
            <div class="pw-wrap">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
                placeholder="请输入密码"
                required
                @input="error = ''"
              />
              <button
                class="pw-toggle"
                type="button"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? "隐藏" : "显示" }}
              </button>
            </div>
          </label>
          <p v-if="error" class="err" role="alert">{{ error }}</p>
          <button class="submit" type="submit" :disabled="loading">
            {{ loading ? "请稍候…" : mode === "login" ? "进入学习" : "注册并进入" }}
          </button>
        </form>

        <div class="demo-box">
          <div class="demo-title">课程试用账号，点一下即可填入</div>
          <div class="demo-row">
            <button
              v-for="acc in demos"
              :key="acc.username"
              type="button"
              class="demo-chip"
              @click="fillDemo(acc)"
            >
              <b>{{ acc.display_name || acc.username }}</b>
              <small>{{ acc.username }}</small>
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100dvh;
  display: grid;
  grid-template-columns: minmax(280px, 1.05fr) minmax(320px, 0.95fr);
  background: #f5f6fa;
}
.login-story {
  position: relative;
  overflow: hidden;
  padding: 40px 44px 32px;
  color: #eef1fb;
  background:
    radial-gradient(ellipse 70% 50% at 12% 0%, rgba(139, 124, 245, 0.28), transparent 55%),
    radial-gradient(ellipse 55% 45% at 90% 88%, rgba(87, 194, 180, 0.18), transparent 50%),
    linear-gradient(165deg, #1b2038 0%, #242a48 58%, #1a1e32 100%);
  display: flex;
  flex-direction: column;
}
.login-story::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.55), transparent 78%);
  pointer-events: none;
}
.story-brand,
.login-story h1,
.story-lead,
.story-points,
.story-foot {
  position: relative;
}
.story-brand {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 36px;
}
.mark {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: #cfeee3;
  color: #18263f;
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 20px;
  flex-shrink: 0;
}
.story-brand strong {
  display: block;
  font-size: 16px;
  letter-spacing: 0.02em;
}
.story-brand > div span {
  display: block;
  margin-top: 2px;
  color: #9aa3c4;
  font-size: 12px;
}
.login-story h1 {
  margin: 0 0 14px;
  font-size: clamp(26px, 3.1vw, 36px);
  line-height: 1.28;
  font-weight: 760;
  max-width: 12em;
  letter-spacing: -0.02em;
}
.story-lead {
  margin: 0 0 28px;
  max-width: 36em;
  color: #c5cbe0;
  font-size: 14px;
  line-height: 1.75;
}
.story-points {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 14px;
}
.story-points li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.pt-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: rgba(215, 243, 234, 0.12);
  color: #d7f3ea;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 800;
  flex-shrink: 0;
}
.story-points b {
  display: block;
  font-size: 14px;
  font-weight: 700;
}
.story-points span {
  display: block;
  margin-top: 3px;
  color: #9aa3c4;
  font-size: 12px;
  line-height: 1.55;
}
.story-foot {
  margin-top: auto;
  padding-top: 36px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.story-teacher {
  font-size: 13px;
  font-weight: 700;
}
.story-course {
  margin-top: 2px;
  color: #9aa3c4;
  font-size: 12px;
}
.zhizhi {
  position: relative;
  width: 52px;
  height: 58px;
  flex-shrink: 0;
}
.zhizhi .hair {
  position: absolute;
  left: 8px;
  top: 2px;
  width: 36px;
  height: 22px;
  border-radius: 16px 16px 8px 8px;
  background: linear-gradient(145deg, #3a3f62, #2a2e4a);
}
.zhizhi .face {
  position: absolute;
  left: 12px;
  top: 12px;
  width: 28px;
  height: 30px;
  border-radius: 12px;
  background: linear-gradient(160deg, #fff0e3, #f9d9cb 50%, #eab7af);
}
.zhizhi .eye {
  position: absolute;
  top: 12px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #2a2d45;
}
.zhizhi .eye.l {
  left: 6px;
}
.zhizhi .eye.r {
  right: 6px;
}
.zhizhi .mouth {
  position: absolute;
  left: 50%;
  bottom: 7px;
  width: 8px;
  height: 3px;
  margin-left: -4px;
  border-radius: 4px;
  background: #9a6070;
}
.zhizhi .body {
  position: absolute;
  left: 14px;
  bottom: 0;
  width: 24px;
  height: 16px;
  border-radius: 10px 10px 4px 4px;
  background: #3d6b63;
}

.login-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 40px 28px;
  background:
    radial-gradient(ellipse 60% 40% at 80% 0%, rgba(102, 88, 223, 0.08), transparent 50%),
    #f5f6fa;
}
.login-card {
  width: min(400px, 100%);
}
.panel-kicker {
  margin: 0 0 6px;
  color: #6658df;
  font-size: 12px;
  font-weight: 750;
  letter-spacing: 0.06em;
}
.login-card h2 {
  margin: 0 0 22px;
  font-size: 24px;
  color: #20243a;
  letter-spacing: -0.02em;
}
.tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  background: #eceef6;
  padding: 4px;
  border-radius: 14px;
  margin-bottom: 20px;
}
.tabs button {
  border: 0;
  background: transparent;
  padding: 10px;
  border-radius: 11px;
  color: #6b7290;
  cursor: pointer;
  font-weight: 650;
  font-size: 14px;
}
.tabs button.active {
  background: #fff;
  color: #20243a;
  box-shadow: 0 1px 4px rgba(32, 36, 58, 0.08);
}
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form label {
  display: flex;
  flex-direction: column;
  gap: 7px;
  font-size: 13px;
  font-weight: 650;
  color: #5a617c;
}
.optional {
  margin-left: 8px;
  color: #9aa1b8;
  font-weight: 500;
  font-size: 12px;
}
.form input {
  width: 100%;
  border: 1px solid #d8dceb;
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 15px;
  outline: none;
  background: #fff;
  color: #20243a;
}
.form input:focus {
  border-color: #6658df;
  box-shadow: 0 0 0 3px rgba(102, 88, 223, 0.14);
}
.pw-wrap {
  position: relative;
}
.pw-wrap input {
  padding-right: 58px;
}
.pw-toggle {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  border: 0;
  background: transparent;
  color: #6658df;
  font-size: 12px;
  font-weight: 700;
  padding: 6px 8px;
}
.submit {
  margin-top: 4px;
  border: 0;
  border-radius: 12px;
  padding: 13px;
  background: #6658df;
  color: #fff;
  font-weight: 750;
  font-size: 15px;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(102, 88, 223, 0.22);
}
.submit:hover:not(:disabled) {
  background: #574be0;
}
.submit:disabled {
  opacity: 0.65;
  cursor: wait;
  box-shadow: none;
}
.err {
  margin: 0;
  color: #a65c42;
  font-size: 13px;
}
.demo-box {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid #e8eaf3;
}
.demo-title {
  font-size: 12px;
  color: #8a91ab;
  margin-bottom: 10px;
}
.demo-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.demo-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  text-align: left;
  border: 1px solid #e2e6f2;
  background: #fff;
  border-radius: 12px;
  padding: 10px 12px;
  cursor: pointer;
  color: #20243a;
}
.demo-chip b {
  font-size: 13px;
  font-weight: 700;
}
.demo-chip small {
  color: #8a91ab;
  font-size: 11px;
}
.demo-chip:hover {
  border-color: #cfc8f5;
  background: #f7f5ff;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
  }
  .login-story {
    padding: 28px 22px 24px;
    min-height: auto;
  }
  .login-story h1 {
    font-size: 26px;
    max-width: none;
  }
  .story-lead {
    margin-bottom: 18px;
  }
  .story-points {
    gap: 10px;
  }
  .story-foot {
    padding-top: 20px;
  }
  .login-panel {
    padding: 8px 18px 36px;
    place-items: start center;
  }
}
@media (max-width: 520px) {
  .demo-row {
    grid-template-columns: 1fr;
  }
}
</style>
