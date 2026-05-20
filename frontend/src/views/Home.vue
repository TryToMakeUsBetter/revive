<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goChat() {
  router.push({ name: 'chat' })
}
</script>

<template>
  <main class="home">
    <div class="hero">
      <h1>Revive</h1>
      <p class="subtitle">一个轻量级对话助手</p>

      <section class="settings">
        <button class="setting-row" @click="goChat">
          <div class="setting-text">
            <div class="setting-title">开始对话</div>
            <div class="setting-desc">在网页里直接和助手聊天</div>
          </div>
          <span class="arrow">›</span>
        </button>
      </section>
    </div>
  </main>
</template>

<style scoped>
.home {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 80px 24px 48px;
}

.hero {
  width: 100%;
  max-width: 520px;
}

h1 {
  font-size: 32px;
  margin: 0 0 8px;
  font-weight: 600;
}

.subtitle {
  color: #6b7280;
  margin: 0 0 40px;
}

.settings h2 {
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6b7280;
  margin: 0 0 12px 4px;
  font-weight: 500;
}

.setting-row {
  width: 100%;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  font: inherit;
  color: inherit;
  text-align: left;
  transition: background 0.15s ease;
}

.setting-row:hover {
  background: #f9fafb;
}

.setting-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-title {
  font-size: 16px;
  font-weight: 500;
}

.setting-desc {
  font-size: 13px;
  color: #6b7280;
}

.arrow {
  font-size: 24px;
  color: #9ca3af;
  line-height: 1;
}
</style>
