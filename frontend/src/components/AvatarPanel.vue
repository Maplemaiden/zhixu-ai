<script setup>
import { renderRichText } from "../utils/renderRichText";

defineProps({
  speaking: { type: Boolean, default: false },
  paused: { type: Boolean, default: false },
  line: { type: String, default: "" },
  supported: { type: Boolean, default: true },
  sectionLabel: { type: String, default: "" },
  /** 首页等场景：压扁播放区与字幕，形象区不变 */
  compact: { type: Boolean, default: false },
});

defineEmits(["play", "pause", "resume", "stop", "prev", "next"]);
</script>

<template>
  <aside class="avatar-panel card" :class="{ compact }">
    <div class="avatar-scene" :class="{ speaking: speaking && !paused }">
      <div class="figure">
        <div class="hair" />
        <div class="face">
          <span class="eye l" /><span class="eye r" />
          <span class="mouth" />
        </div>
        <div class="body" />
      </div>
      <div class="wave" aria-hidden="true"><i /><i /><i /><i /><i /></div>
    </div>

    <div class="avatar-status">
      <div><span class="online-dot" />知知 · 在线</div>
      <span class="tiny">{{ sectionLabel || (speaking ? (paused ? "已暂停" : "讲解中") : "待命") }}</span>
    </div>

    <slot name="extra" />

    <div class="player">
      <div class="player-buttons">
        <button class="player-btn" type="button" title="上一段" @click="$emit('prev')">‹</button>
        <button
          v-if="!speaking || paused"
          class="player-btn main"
          type="button"
          title="播放"
          @click="paused ? $emit('resume') : $emit('play')"
        >
          ▶
        </button>
        <button v-else class="player-btn main" type="button" title="暂停" @click="$emit('pause')">❚❚</button>
        <button class="player-btn" type="button" title="下一段" @click="$emit('next')">›</button>
      </div>
      <div class="player-sub">
        <span>{{ supported ? "浏览器语音播报" : "仅字幕模式" }}</span>
        <button class="link" type="button" @click="$emit('stop')">停止</button>
      </div>
    </div>

    <div
      class="speechbubble"
      v-html="renderRichText(line || '知知', { math: true })"
    />
  </aside>
</template>

<style scoped>
.card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.avatar-panel {
  padding: 17px;
}
.avatar-scene {
  height: 220px;
  background: radial-gradient(circle at 50% 35%, #f1edff 0%, #e8e7ff 54%, #dcdafa 100%);
  border: 1px solid #e8e4ff;
  border-radius: 19px;
  position: relative;
  overflow: hidden;
  display: grid;
  place-items: center;
}
.figure {
  position: relative;
  width: 120px;
  height: 160px;
}
.hair {
  position: absolute;
  left: 18px;
  top: 8px;
  width: 84px;
  height: 50px;
  border-radius: 40px 40px 18px 18px;
  background: linear-gradient(145deg, #343858, #242742);
}
.face {
  position: absolute;
  left: 28px;
  top: 28px;
  width: 64px;
  height: 72px;
  border-radius: 28px;
  background: linear-gradient(160deg, #fff0e3, #f9d9cb 50%, #eab7af);
}
.eye {
  position: absolute;
  top: 28px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #2a2d45;
}
.eye.l {
  left: 16px;
}
.eye.r {
  right: 16px;
}
.mouth {
  position: absolute;
  left: 50%;
  bottom: 18px;
  width: 16px;
  height: 5px;
  margin-left: -8px;
  border-radius: 8px;
  background: #9a6070;
  transform: scaleY(0.45);
}
.avatar-scene.speaking .mouth {
  animation: mouthTalk 0.22s ease-in-out infinite alternate;
}
@keyframes mouthTalk {
  from {
    transform: scaleY(0.35);
  }
  to {
    transform: scaleY(1.6);
  }
}
.body {
  position: absolute;
  left: 20px;
  bottom: 0;
  width: 80px;
  height: 70px;
  border-radius: 22px 22px 12px 12px;
  background: linear-gradient(160deg, #766bee, #4a48bb);
}
.wave {
  position: absolute;
  right: 14px;
  bottom: 12px;
  display: flex;
  gap: 3px;
  align-items: flex-end;
  height: 22px;
}
.wave i {
  width: 3px;
  height: 5px;
  border-radius: 3px;
  background: #726ce2;
  display: block;
}
.avatar-scene.speaking .wave i {
  animation: voicewave 0.65s infinite alternate;
}
.wave i:nth-child(2) {
  animation-delay: 0.1s;
}
.wave i:nth-child(3) {
  animation-delay: 0.2s;
}
.wave i:nth-child(4) {
  animation-delay: 0.08s;
}
@keyframes voicewave {
  from {
    height: 4px;
  }
  to {
    height: 18px;
  }
}
.avatar-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 14px 0 4px;
  font-size: 13px;
  font-weight: 700;
}
.online-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  background: #24b88b;
  border-radius: 50%;
  margin-right: 6px;
}
.tiny {
  font-size: 11px;
  color: var(--muted);
  font-weight: 600;
}
.player {
  padding: 14px;
  background: #f7f7fc;
  border-radius: 14px;
  margin-top: 10px;
}
.player-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
  align-items: center;
}
.player-btn {
  border: 0;
  background: #fff;
  border-radius: 10px;
  width: 37px;
  height: 37px;
  color: #5c5e8b;
}
.player-btn.main {
  background: var(--primary);
  color: #fff;
  width: 48px;
  height: 48px;
  border-radius: 14px;
}
/* 播放控件 hover —— 必须写在本组件内。
   App.vue 的 <style scoped> 会编译成 .player-btn[data-v-App]:hover，
   而这里的元素带的是 [data-v-AvatarPanel]，跨组件永不匹配（此前写错过两次）。 */
.player-btn:hover:not(:disabled) {
  background: #f0edff;
  border-color: #d8cffd;
  color: var(--primary);
}
.player-sub {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 11px;
  /* 原 #9397ae 在 #f7f7fc 上只有 2.70:1，提到 4.6:1 */
  color: #626a85;
}
.link {
  border: 0;
  background: transparent;
  color: var(--primary);
}
.speechbubble {
  background: #fff;
  border: 1px solid #ededf3;
  padding: 13px 15px;
  border-radius: 12px;
  font-size: 12px;
  /* 原 #777e96 在白底 4.03:1，提到 4.6:1 */
  color: #646b85;
  line-height: 1.7;
  margin-top: 12px;
  min-height: 64px;
  word-break: break-word;
}
.speechbubble :deep(.md-p) {
  margin: 0 0 6px;
}
.speechbubble :deep(.md-p:last-child) {
  margin-bottom: 0;
}
.speechbubble :deep(.md-ul),
.speechbubble :deep(.md-ol) {
  margin: 4px 0;
  padding-left: 1.2em;
}
.speechbubble :deep(.katex-display) {
  margin: 6px 0;
  overflow-x: auto;
}

.avatar-panel.compact {
  padding: 12px;
}
.avatar-panel.compact .avatar-status {
  margin: 8px 0 0;
  font-size: 12px;
}
.avatar-panel.compact .player {
  padding: 8px 10px;
  margin-top: 6px;
  border-radius: 10px;
}
.avatar-panel.compact .player-buttons {
  gap: 8px;
}
.avatar-panel.compact .player-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  font-size: 13px;
}
.avatar-panel.compact .player-btn.main {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  font-size: 12px;
}
.avatar-panel.compact .player-sub {
  margin-top: 6px;
  font-size: 10px;
}
.avatar-panel.compact .speechbubble {
  margin-top: 8px;
  padding: 8px 10px;
  min-height: 0;
  line-height: 1.45;
  font-size: 12px;
  border-radius: 10px;
}
</style>
