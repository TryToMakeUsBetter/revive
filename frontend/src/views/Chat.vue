<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const sessionKey = 'revive.chatSessionId'
const sessionId = (() => {
  let s = localStorage.getItem(sessionKey)
  if (!s) {
    s = `web-${Math.random().toString(36).slice(2, 10)}-${Date.now()}`
    localStorage.setItem(sessionKey, s)
  }
  return s
})()

const messages = ref([])
const input = ref('')
const sending = ref(false)
const error = ref(null)
const scroller = ref(null)

async function scrollToBottom() {
  await nextTick()
  if (scroller.value) {
    scroller.value.scrollTop = scroller.value.scrollHeight
  }
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return
  error.value = null
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  sending.value = true
  await scrollToBottom()
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message: text }),
    })
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}))
      throw new Error(detail.detail || `HTTP ${res.status}`)
    }
    const data = await res.json()
    for (const reply of data.replies || []) {
      messages.value.push({ role: 'assistant', content: reply })
    }
  } catch (e) {
    error.value = String(e.message || e)
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

async function resetSession() {
  if (!confirm('清空对话历史？')) return
  try {
    await fetch(`/api/chat/reset?session_id=${encodeURIComponent(sessionId)}`, {
      method: 'POST',
    })
  } catch {}
  messages.value = []
  error.value = null
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

onMounted(scrollToBottom)
</script>

<template>
  <main class="page">
    <header class="bar">
      <button class="back" @click="router.back()">← 返回</button>
      <span class="title">调试对话</span>
      <button class="reset" @click="resetSession">清空</button>
    </header>

    <div class="messages" ref="scroller">
      <div v-if="!messages.length" class="empty">
        在下方输入消息开始对话
      </div>
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="row"
        :class="m.role"
      >
        <div class="bubble">{{ m.content }}</div>
      </div>
      <div v-if="sending" class="row assistant">
        <div class="bubble typing">
          <span /><span /><span />
        </div>
      </div>
    </div>

    <p v-if="error" class="error">出错了：{{ error }}</p>

    <footer class="composer">
      <textarea
        v-model="input"
        @keydown="handleKey"
        :disabled="sending"
        placeholder="输入消息，Enter 发送，Shift+Enter 换行"
        rows="1"
      />
      <button class="send" @click="send" :disabled="sending || !input.trim()">
        发送
      </button>
    </footer>
  </main>
</template>

<style scoped>
.page {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 720px;
  margin: 0 auto;
  width: 100%;
}

.bar {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
}

.back, .reset {
  background: none;
  border: none;
  font-size: 14px;
  color: #2563eb;
  cursor: pointer;
  padding: 6px 4px;
}

.title {
  flex: 1;
  text-align: center;
  font-weight: 600;
  font-size: 16px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f9fafb;
}

.empty {
  margin: auto;
  color: #9ca3af;
  font-size: 14px;
}

.row {
  display: flex;
}

.row.user {
  justify-content: flex-end;
}

.row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.row.user .bubble {
  background: #2563eb;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.row.assistant .bubble {
  background: #fff;
  color: #1f2937;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 4px;
}

.typing {
  display: inline-flex;
  gap: 4px;
  padding: 14px;
}

.typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9ca3af;
  animation: blink 1.2s infinite ease-in-out;
}

.typing span:nth-child(2) {
  animation-delay: 0.15s;
}

.typing span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes blink {
  0%, 80%, 100% { opacity: 0.3; }
  40% { opacity: 1; }
}

.error {
  color: #dc2626;
  font-size: 13px;
  text-align: center;
  margin: 0;
  padding: 8px;
  background: #fef2f2;
  border-top: 1px solid #fee2e2;
}

.composer {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
  background: #fff;
}

textarea {
  flex: 1;
  resize: none;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  padding: 10px 12px;
  font: inherit;
  font-size: 15px;
  line-height: 1.4;
  max-height: 160px;
  outline: none;
}

textarea:focus {
  border-color: #2563eb;
}

.send {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.send:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
</style>
