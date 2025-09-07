<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import Popover from 'primevue/popover'
import api from '@/lib/api'

const props = defineProps({
  caseId: { type: [String, Number], required: false },
})

const emit = defineEmits(['unseen-count'])

const loading = ref(false)
const sending = ref(false)
const error = ref('')
const messages = ref([]) // [{ id, case_id, written_by_id, message, reply_to_id, created_at, updated_at, writer_name, seen, reaction, reply_to_text, is_mine, writer_photo_url, my_photo_url }]

// Composer state
const composer = ref('')
const replyingTo = ref(null) // { id, message, writer_name }
const listEl = ref(null)

async function loadMessages() {
  if (!props.caseId) { messages.value = []; return }
  loading.value = true
  error.value = ''
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages`
    const { data } = await api.get(url)
    messages.value = Array.isArray(data) ? data : []
    await nextTick()
    scrollToBottom()
    // After displaying, mark unseen as seen
    const unseenIds = messages.value.filter(m => !m.seen && !m.is_mine).map(m => String(m.id))
    if (unseenIds.length) {
      await api.post(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages/mark_seen`, { message_ids: unseenIds })
      // Refresh unseen count for badge
      await refreshUnseenCount()
      // Update local flags to avoid flicker
      for (const m of messages.value) if (!m.seen) m.seen = true
    }
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load messages.'
  } finally {
    loading.value = false
  }
}

async function refreshUnseenCount() {
  if (!props.caseId) { emit('unseen-count', 0); return }
  try {
    const { data } = await api.get(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages/unseen_count`)
    const count = Number(data?.count || 0)
    emit('unseen-count', count)
  } catch (e) {
    console.error(e)
  }
}

function scrollToBottom() {
  if (!listEl.value) return
  listEl.value.scrollTop = listEl.value.scrollHeight
}

function startReply(m) {
  if (!m || m.is_mine) return
  replyingTo.value = { id: m.id, message: m.message, writer_name: m.writer_name }
}

function clearReply() { replyingTo.value = null }

async function sendMessage() {
  const text = composer.value.trim()
  if (!text || !props.caseId) return
  sending.value = true
  try {
    const payload = { message: text, reply_to_id: replyingTo.value ? String(replyingTo.value.id) : null }
    const { data } = await api.post(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages`, payload)
    // Append and reset composer
    const myPhoto = (messages.value.find(x => x?.my_photo_url)?.my_photo_url) || '/images/pfp-generic.png'
    messages.value.push({ ...data, seen: true, is_mine: true, my_photo_url: myPhoto })
    composer.value = ''
    replyingTo.value = null
    await nextTick()
    scrollToBottom()
    // A new message might increase unseen for others but not for us; our badge remains based on server
    await refreshUnseenCount()
  } catch (e) {
    console.error(e)
  } finally {
    sending.value = false
  }
}

async function toggleReaction(m) {
  try {
    const next = m.reaction ? null : '👍'
    await api.post(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages/${encodeURIComponent(String(m.id))}/reaction`, { reaction: next })
    m.reaction = next
  } catch (e) {
    console.error(e)
  }
}

// Emoji picker support
const emojiPanel = ref(null)
const emojiTargetMessage = ref(null)
const emojiChoices = ['👍','❤️','🎉','🙏','😂','😮','😢','🔥','🚀','✅','❓']

function openEmojiPicker(event, m) {
  if (!m || m.is_mine) return
  emojiTargetMessage.value = m
  if (emojiPanel.value?.toggle) emojiPanel.value.toggle(event)
}

async function chooseEmoji(val) {
  const m = emojiTargetMessage.value
  if (!m) return
  try {
    await api.post(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages/${encodeURIComponent(String(m.id))}/reaction`, { reaction: val || null })
    m.reaction = val || null
  } catch (e) {
    console.error(e)
  } finally {
    if (emojiPanel.value?.hide) emojiPanel.value.hide()
    emojiTargetMessage.value = null
  }
}

watch(() => props.caseId, (val) => { if (val) { loadMessages(); refreshUnseenCount() } else { messages.value = []; emit('unseen-count', 0) } }, { immediate: true })

onMounted(() => { /* additional hooks if needed */ })

const groups = computed(() => {
  const byDate = new Map()
  const sorted = messages.value.slice().sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  for (const m of sorted) {
    const dt = new Date(m.created_at)
    const y = dt.getFullYear()
    const mo = dt.getMonth()
    const d = dt.getDate()
    const key = `${y}-${String(mo + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    if (!byDate.has(key)) byDate.set(key, { date: new Date(y, mo, d), items: [] })
    byDate.get(key).items.push(m)
  }
  return Array.from(byDate.entries()).map(([key, grp]) => ({ key, date: grp.date, items: grp.items }))
})

function fmtTime(date) { return new Date(date).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) }
function fmtDate(date) { return new Date(date).toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' }) }
</script>

<template>
  <div class="chat-tab">

    <div v-if="error" class="p-2 text-red-600">{{ error }}</div>

    <!-- Messages List -->
    <div class="list" ref="listEl">
      <div v-for="group in groups" :key="group.key" class="date-group">
        <div class="date-chip">{{ fmtDate(group.date) }}</div>
        <div v-for="m in group.items" :key="m.id" class="row" :class="{ unseen: !m.seen }">
          <div class="pfp left">
            <img v-if="!m.is_mine" :src="m.writer_photo_url || '/images/pfp-generic.png'" alt="pfp" class="avatar" />
          </div>
          <div class="bubble">
            <div v-if="m.reply_to_id && m.reply_to_text" class="reply-preview">
              <span class="material-symbols-outlined tiny">reply</span>
              <span class="ellipsis">{{ m.reply_to_text }}</span>
            </div>
            <div class="text">{{ m.message }}</div>
            <div class="footer flex align-items-center justify-content-between mt-1">
              <span class="time">{{ fmtTime(m.created_at) }}</span>
              <span v-if="!m.is_mine" class="actions flex align-items-center gap-2">
                <Button size="small" text @click="startReply(m)">
                  <span class="material-symbols-outlined">reply</span>
                </Button>
                <Button size="small" text @click="openEmojiPicker($event, m)">
                  <span v-if="m.reaction">{{ m.reaction }}</span>
                  <span v-else class="material-symbols-outlined">mood</span>
                </Button>
              </span>
            </div>
          </div>
          <div class="pfp right">
            <img v-if="m.is_mine" :src="m.my_photo_url || '/images/pfp-generic.png'" alt="me" class="avatar" />
          </div>
        </div>
      </div>
    </div>

    <!-- Composer -->
    <div class="composer p-2">
      <div v-if="replyingTo" class="replying-chip">
        <span class="material-symbols-outlined tiny">reply</span>
        <span>Replying to {{ replyingTo.writer_name }}: {{ replyingTo.message }}</span>
        <button class="x" @click="clearReply" aria-label="Cancel reply">×</button>
      </div>
      <div class="composer-row w-full space-y-1">
        <FloatLabel variant="on" class="flex-1 min-w-0 align-content-center">
          <Textarea id="msg-input" v-model="composer" autoResize rows="1" class="w-full" />
          <label for="msg-input">Type a message</label>
        </FloatLabel>
        <Button label="Send" icon="pi pi-send" @click="sendMessage" :loading="sending" :disabled="!composer.trim()" class="shrink-0 align-content-center"/>
      </div>
    </div>

    <Popover ref="emojiPanel">
      <div class="emoji-panel">
        <button v-for="e in emojiChoices" :key="e" class="emoji-btn" @click="chooseEmoji(e)">{{ e }}</button>
        <button class="emoji-btn clear" @click="chooseEmoji(null)">Clear</button>
      </div>
    </Popover>
  </div>
</template>

<style scoped>
.chat-tab { display: flex; flex-direction: column; height: 100%; }
.header { border-bottom: 1px solid var(--p-surface-200, #e5e7eb); }
.list { flex: 1; overflow: auto; padding: 0 12px 12px 12px; background: var(--p-surface-0, #fff); }
.row { display: grid; grid-template-columns: 40px 1fr 40px; gap: 8px; padding: 8px 4px; align-items: start; }
.pfp { width: 40px; height: 40px; }
.avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; background: var(--p-surface-200, #e5e7eb); border: 2px solid var(--p-surface-200, #e5e7eb); }
.left {position: relative; left: 15px; top: -5px; z-index: 1; }
.right {position: relative; left: -20px; top: -5px; z-index: 1; }
.bubble { position: relative; max-width: 100%; width: 100%; border: 1px solid var(--p-surface-300, #d1d5db); background: var(--p-surface-0, #fff); border-radius: 12px; padding: 8px 12px 6px 12px; box-shadow: 0 1px 1px rgba(0,0,0,0.04); }
.emoji-panel { display: flex; flex-wrap: wrap; gap: 6px; max-width: 260px; }
.emoji-btn { font-size: 20px; background: var(--p-surface-0, #fff); border: 1px solid var(--p-surface-300, #d1d5db); border-radius: 8px; padding: 4px 6px; cursor: pointer; }
.emoji-btn:hover { background: var(--p-surface-50, #f9fafb); }
.emoji-btn.clear { font-size: 12px; }
.sender { font-weight: 600; }
.text { white-space: pre-wrap; word-break: break-word; }
.time { font-size: 0.8rem; color: var(--p-text-color, #6b7280); }
.reply-preview { font-size: 0.85rem; color: var(--p-text-color, #6b7280); padding: 4px 8px; border-left: 3px solid var(--p-surface-300, #d1d5db); margin: 4px 0; background: var(--p-surface-50, #f9fafb); border-radius: 6px; }
.reply-preview .tiny { font-size: 16px; vertical-align: middle; }
.ellipsis { display: inline-block; max-width: 520px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: bottom; }
.date-group { padding-top: 8px; }
.date-chip { display: inline-block; margin: 8px auto; padding: 4px 10px; border-radius: 999px; border: 1px solid var(--p-surface-300, #d1d5db); background: var(--p-surface-50, #f9fafb); font-size: 0.85rem; color: var(--p-text-color, #374151); position: sticky; top: 6px; z-index: 1; align-self: center; }
.actions :deep(.p-button) { padding: 2px 6px; }
.row.unseen .bubble { border-color: var(--p-primary-300, #93c5fd); box-shadow: 0 0 0 2px rgba(59,130,246,0.15); }
.composer { border-top: 1px solid var(--p-surface-200, #e5e7eb); background: var(--p-surface-0, #fff); }
.composer-row { display: flex; gap: 8px; align-items: flex-end; }
.replying-chip { display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 999px; background: var(--p-surface-100, #f3f4f6); margin-bottom: 6px; }
.replying-chip .x { background: transparent; border: none; cursor: pointer; }
</style>
