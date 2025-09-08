<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import Popover from 'primevue/popover'
import api from '@/lib/api'
import { gMessageCounts } from '@/lib/messages_ws'

const props = defineProps({
  caseId: { type: [String, Number], required: false },
})


const loading = ref(false)
const sending = ref(false)
const error = ref('')
const messages = ref([]) // [{ id, case_id, written_by_id, message, reply_to_id, created_at, updated_at, writer_name, seen, reaction, reply_to_text, is_mine, writer_photo_url, my_photo_url }]

// Observe global unseen counts for this case
const unseenCountForCase = computed(() => {
  const cid = String(props.caseId || '')
  if (!cid) return 0
  const key = `count_${cid}`
  const m = gMessageCounts.value || {}
  return Number(m[key] || 0)
})

const _lastUnseenCount = ref(0)

// Composer state
const composer = ref('')
const replyingTo = ref(null) // { id, message, writer_name }
const listEl = ref(null)
const _userScrolled = ref(false)

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
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load messages.'
  } finally {
    loading.value = false
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

// Composition state for IME (to avoid sending while composing)
const isComposing = ref(false)

function onComposerKeydown(e) {
  try {
    if (!e) return
    // Only handle Enter presses
    if (e.key !== 'Enter') return
    // If composing via IME, do not act on Enter
    if (isComposing.value || e.isComposing) return
    // Allow Shift+Enter or Ctrl+Enter to insert newline
    if (e.shiftKey || e.ctrlKey) return
    // Otherwise, Enter sends
    e.preventDefault()
    if (sending.value) return
    const text = (composer.value || '').trim()
    if (!text) return
    // Send the message
    sendMessage()
  } catch (_) {
    // no-op
  }
}

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
  } catch (e) {
    console.error(e)
  } finally {
    sending.value = false
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


watch(() => props.caseId, (val) => {
  if (val) {
    loadMessages()
    // Reset last unseen baseline for new case
    _lastUnseenCount.value = unseenCountForCase.value
  } else {
    messages.value = []
    _lastUnseenCount.value = 0
  }
}, { immediate: true })

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

// Fetch only the new/unseen messages for this case and append to the end
async function fetchAndAppendNewMessages() {
  const cid = String(props.caseId || '')
  if (!cid) return
  try {
    const url = `/api/v1/cases/messages/new_messages/case/${encodeURIComponent(cid)}`
    const { data } = await api.get(url)
    const arr = Array.isArray(data) ? data : []
    if (!arr.length) return
    const have = new Set(messages.value.map(m => String(m.id)))
    for (const m of arr) {
      if (!have.has(String(m.id))) {
        messages.value.push(m)
      }
    }
    // Do not scroll; leave position unchanged by requirement
  } catch (e) {
    // Silently ignore to avoid user disruption
    console.error(e)
  }
}

// Watch unseen count and fetch new messages when it increases
watch(() => unseenCountForCase.value, (newVal, oldVal) => {
  // Establish baseline if needed
  if (_lastUnseenCount.value === 0 && oldVal === undefined) {
    _lastUnseenCount.value = Number(newVal || 0)
    return
  }
  if (!props.caseId) return
  if (Number(newVal || 0) > Number(_lastUnseenCount.value || 0)) {
    fetchAndAppendNewMessages()
  }
  _lastUnseenCount.value = Number(newVal || 0)
})

// Visibility-based mark-as-seen logic
const _io = ref(null)
const _observed = new Set()
const _visibility = new Map() // id(enc) -> ratio
const _markTimer = ref(null)
const _lastMarkedId = ref(null)

function _ensureObserver() {
  if (_io.value || !listEl.value) return
  _io.value = new IntersectionObserver((entries) => {
    for (const e of entries) {
      const id = e.target?.getAttribute('data-mid')
      if (!id) continue
      _visibility.set(String(id), e.isIntersecting ? e.intersectionRatio : 0)
    }
    _scheduleMarkSeenCheck()
  }, { root: listEl.value, threshold: [0, 0.25, 0.5, 0.75, 1] })
}

function _observeAllRows() {
  if (!_io.value || !listEl.value) return
  const nodes = listEl.value.querySelectorAll('.row[data-mid]')
  nodes.forEach(n => {
    const id = n.getAttribute('data-mid')
    if (id && !_observed.has(id)) {
      _io.value.observe(n)
      _observed.add(id)
    }
  })
}

function _onScroll() {
  _userScrolled.value = true
  _scheduleMarkSeenCheck()
}

function _scheduleMarkSeenCheck() {
  if (_markTimer.value) return
  _markTimer.value = setTimeout(_maybeMarkSeenUpTo, 400)
}

function _getFurthestVisibleId() {
  if (!listEl.value) return null
  const nodes = Array.from(listEl.value.querySelectorAll('.row[data-mid]'))
  let furthest = null
  for (const n of nodes) {
    const id = n.getAttribute('data-mid')
    if (!id) continue
    const m = messages.value.find(x => String(x.id) === String(id))
    if (!m || m.is_mine) continue
    const ratio = _visibility.get(String(id)) || 0
    if (ratio >= 0.5) furthest = id
  }
  return furthest
}

async function _maybeMarkSeenUpTo() {

  console.log("checking for viewing unseen messages...");

  _markTimer.value = null
  const cid = String(props.caseId || '')
  if (!cid) return
  const targetId = _getFurthestVisibleId()
  if (!targetId) return
  if (_lastMarkedId.value && String(targetId) === String(_lastMarkedId.value)) return
  _lastMarkedId.value = String(targetId)
  // Update local flags and start 20s fade immediately upon visibility
  const idxMap = new Map(messages.value.map((m, i) => [String(m.id), i]))
  const targetIdx = idxMap.get(String(targetId))
  if (typeof targetIdx === 'number') {
    for (let i = 0; i <= targetIdx; i++) {
      const m = messages.value[i]
      if (!m || m.is_mine) continue
      const wasUnseen = !m.seen
      if (wasUnseen) {
        m.seen = true
        m._fadingUnseen = true
        setTimeout(() => { m._fadingUnseen = false }, 20000)
      }
    }
  }
  try {
    await api.post(`/api/v1/cases/${encodeURIComponent(cid)}/messages/mark_seen_up_to/${encodeURIComponent(String(targetId))}`)
  } catch (e) {
    // ignore API failure; local fade already shown
  }
}

onMounted(async () => {
  await nextTick()
  _ensureObserver()
  _observeAllRows()
  window.addEventListener('resize', _scheduleMarkSeenCheck)
  const el = listEl.value
  if (el) el.addEventListener('scroll', _onScroll, { passive: true })
})

watch(messages, async () => {
  await nextTick()
  _ensureObserver()
  _observeAllRows()
  _scheduleMarkSeenCheck()
})

onBeforeUnmount(() => {
  try { if (_io.value) _io.value.disconnect() } catch {}
  _io.value = null
  _observed.clear()
  _visibility.clear()
  try { if (_markTimer.value) clearTimeout(_markTimer.value) } catch {}
  _markTimer.value = null
  const el = listEl.value
  if (el) {
    try { el.removeEventListener('scroll', _onScroll) } catch {}
  }
})
</script>

<template>
  <div class="chat-tab">

    <div v-if="error" class="p-2 text-red-600">{{ error }}</div>

    <!-- Messages List -->
    <div class="list" ref="listEl">
      <div v-for="group in groups" :key="group.key" class="date-group">
        <div class="date-chip">{{ fmtDate(group.date) }}</div>
        <div v-for="m in group.items" :key="m.id" class="row" :data-mid="m.id" :class="{ unseen: (!!m._fadingUnseen && !m.is_mine) }">
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
          <Textarea id="msg-input" v-model="composer" autoResize rows="1" class="w-full"
                    @keydown="onComposerKeydown"
                    @compositionstart="isComposing = true"
                    @compositionend="isComposing = false" />
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
.row.unseen .bubble { border-color: var(--p-primary-300, #93c5fd); border-width: 2px; box-shadow: 0 0 0 4px rgba(59,130,246,0.20); animation: unseenFade 20s ease-out forwards; }
@keyframes unseenFade { 0% { border-color: var(--p-primary-300, #93c5fd); box-shadow: 0 0 0 4px rgba(59,130,246,0.20); } 100% { border-color: var(--p-surface-300, #d1d5db); box-shadow: 0 1px 1px rgba(0,0,0,0.04); } }
.composer { border-top: 1px solid var(--p-surface-200, #e5e7eb); background: var(--p-surface-0, #fff); }
.composer-row { display: flex; gap: 8px; align-items: flex-end; }
.replying-chip { display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 999px; background: var(--p-surface-100, #f3f4f6); margin-bottom: 6px; }
.replying-chip .x { background: transparent; border: none; cursor: pointer; }
</style>
