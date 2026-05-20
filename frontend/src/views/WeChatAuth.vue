<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const status = ref('idle')
const hasQr = ref(false)
const error = ref(null)
const qrSrc = ref('')
const qrVersion = ref(0)

let pollTimer = null

const STATUS_TEXT = {
  idle: '准备中…',
  waiting_qr: '正在生成二维码…',
  waiting_scan: '请使用微信扫描下方二维码',
  scanned: '扫码成功，请在手机上确认登录',
  logged_in: '登录成功',
  failed: '登录失败',
}

async function startLogin() {
  error.value = null
  try {
    await fetch('/api/wechat/login/start', { method: 'POST' })
  } catch (e) {
    error.value = String(e)
  }
}

async function poll() {
  try {
    const res = await fetch('/api/wechat/status')
    const data = await res.json()
    status.value = data.status
    hasQr.value = data.has_qr
    error.value = data.error || null
    if (data.has_qr && data.qr_version !== qrVersion.value) {
      qrVersion.value = data.qr_version
      qrSrc.value = `/api/wechat/qr?v=${data.qr_version}`
    }
    if (!data.has_qr) {
      qrSrc.value = ''
      qrVersion.value = 0
    }
    if (data.status === 'logged_in' || data.status === 'failed') {
      stopPolling()
    }
  } catch (e) {
    error.value = String(e)
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(poll, 1500)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function retry() {
  qrSrc.value = ''
  qrVersion.value = 0
  hasQr.value = false
  status.value = 'waiting_qr'
  error.value = null
  await startLogin()
  startPolling()
}

onMounted(async () => {
  await startLogin()
  await poll()
  startPolling()
})

onBeforeUnmount(stopPolling)
</script>

<template>
  <main class="page">
    <header class="bar">
      <button class="back" @click="router.back()">← 返回</button>
      <span class="title">微信授权</span>
      <span class="spacer" />
    </header>

    <section class="card">
      <h2>{{ STATUS_TEXT[status] || status }}</h2>

      <div class="qr-box">
        <img
          v-if="hasQr && status !== 'logged_in'"
          :src="qrSrc"
          alt="WeChat QR"
          class="qr"
        />
        <div v-else-if="status === 'logged_in'" class="placeholder success">
          ✓
        </div>
        <div v-else class="placeholder loading">
          <div class="spinner" />
        </div>

        <div v-if="status === 'scanned'" class="overlay">已扫码，请在手机上确认</div>
      </div>

      <p v-if="error" class="error">出错了：{{ error }}</p>

      <div class="actions">
        <button v-if="status === 'failed'" class="primary" @click="retry">
          重试
        </button>
        <button v-else-if="status === 'logged_in'" class="primary" @click="router.push('/')">
          完成
        </button>
        <button v-else class="ghost" @click="retry">刷新二维码</button>
      </div>

      <p class="hint">使用微信扫描二维码以授权登录</p>
    </section>
  </main>
</template>

<style scoped>
.page {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 24px 48px;
}

.bar {
  width: 100%;
  max-width: 520px;
  display: flex;
  align-items: center;
  margin-bottom: 32px;
}

.back {
  background: none;
  border: none;
  font-size: 15px;
  color: #2563eb;
  cursor: pointer;
  padding: 8px 4px;
}

.title {
  flex: 1;
  text-align: center;
  font-weight: 600;
  font-size: 16px;
}

.spacer {
  width: 64px;
}

.card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 32px 24px;
  text-align: center;
}

h2 {
  margin: 0 0 24px;
  font-size: 18px;
  font-weight: 500;
  color: #1f2937;
}

.qr-box {
  position: relative;
  width: 240px;
  height: 240px;
  margin: 0 auto 24px;
  background: #f3f4f6;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #fff;
}

.placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder.success {
  font-size: 64px;
  color: #10b981;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #e5e7eb;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  color: #111827;
  padding: 0 16px;
  text-align: center;
}

.error {
  color: #dc2626;
  font-size: 13px;
  margin: 0 0 16px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.primary {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.primary:hover {
  background: #1d4ed8;
}

.ghost {
  background: transparent;
  color: #2563eb;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 24px;
  font-size: 14px;
  cursor: pointer;
}

.ghost:hover {
  background: #f9fafb;
}

.hint {
  font-size: 12px;
  color: #6b7280;
  margin: 0;
}
</style>
