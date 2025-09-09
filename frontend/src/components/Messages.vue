<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import Popover from 'primevue/popover'
import InputText from 'primevue/inputtext'
import ToggleSwitch from 'primevue/toggleswitch'
import api from '@/lib/api'
import { gMessageCounts, gMessageEvents } from '@/lib/messages_ws'
import { createClientLogger } from '@/lib/util'
import FileUpload from '@/components/common/FileUpload.vue'

const props = defineProps({
  caseId: { type: [String, Number], required: false },
  // Optional filters: when both provided, backend will filter on the matching field
  filterByFieldName: { type: String, required: false, default: null }, // one of: 'rfi_id','ops_plan_id','task_id'
  filterByFieldId: { type: String, required: false, default: null },    // encrypted id for the field
})

const log = createClientLogger('Messages')


const loading = ref(false)
const sending = ref(false)
const error = ref('')
const messages = ref([]) // [{ id, case_id, written_by_id, message, reply_to_id, rule_out, created_at, updated_at, writer_name, seen, reaction, reply_to_text, is_mine, writer_photo_url, my_photo_url }]

// Search state
const searchQuery = ref('')

const _lastUnseenCount = ref(0);

// Scrolling
const listEl = ref(null)
const didInitialScroll = ref(false)

function getScrollableParent(el) {
  try {
    let cur = el
    while (cur) {
      const style = window.getComputedStyle(cur)
      const oy = style ? style.overflowY : ''
      const ox = style ? style.overflowX : ''
      const canScrollY = (oy === 'auto' || oy === 'scroll') && cur.scrollHeight > cur.clientHeight
      const canScrollX = (ox === 'auto' || ox === 'scroll') && cur.scrollWidth > cur.clientWidth
      if (canScrollY || canScrollX) return cur
      cur = cur.parentElement
    }
  } catch (_) { /* noop */ }
  return document.scrollingElement || document.documentElement
}

async function initialScrollIfNeeded() {
  if (didInitialScroll.value) return
  await nextTick()
  const list = listEl.value
  if (!list) return
  const container = getScrollableParent(list)
  log.debug('scroll container', container)
  // Find first unseen within the list content
  const firstUnseen = list.querySelector('.row[data-unseen="true"]')

  log.debug('initialScrollIfNeeded firstUnseen', firstUnseen)

  if (firstUnseen) {
    try {
      firstUnseen.scrollIntoView({ behavior: 'auto', block: 'center' })
    } catch (_) {
      // Fallback: manual scroll relative to container
      const rect = firstUnseen.getBoundingClientRect()
      const crect = container.getBoundingClientRect()
      container.scrollTop += (rect.top - crect.top) - (crect.height / 2)
    }
  } else {
    // No unseen: scroll to bottom of the actual scroll container
    container.scrollTop = container.scrollHeight
    // As some containers require scrollHeight - clientHeight, ensure max
    if (container.scrollTop === 0 && container.scrollHeight > container.clientHeight) {
      container.scrollTop = container.scrollHeight - container.clientHeight
    }
    log.debug('scrollTop after', container.scrollTop, container.scrollHeight, 'clientHeight', container.clientHeight)
  }
  didInitialScroll.value = true
}

// Observe global unseen counts for this case
const unseenCountForCase = computed(() => {
  const cid = String(props.caseId || '')
  if (!cid) return 0
  const key = `count_${cid}`
  const m = gMessageCounts.value || {}
  return Number(m[key] || 0)
})

// Composer state
const composer = ref('')
const replyingTo = ref(null) // { id, message, writer_name }
const showUploader = ref(false)

// Lightbox for attachments (match FilesTab behavior)
const showLightbox = ref(false)
const lightboxItem = ref(null)

async function loadMessages() {
  if (!props.caseId) { messages.value = []; return }
  loading.value = true
  error.value = ''
  try {
    let url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages`
    if (props.filterByFieldName && props.filterByFieldId) {
      const usp = new URLSearchParams()
      usp.set('filter_by_field_name', String(props.filterByFieldName))
      usp.set('filter_by_field_id', String(props.filterByFieldId))
      url += `?${usp.toString()}`
    }
    const { data } = await api.get(url)
    messages.value = Array.isArray(data) ? data : []
    log.debug('messages loaded', messages.value)

    console.log(messages.value)
    await nextTick()
    await observeUnseenRows()
    await initialScrollIfNeeded()
  } catch (e) {
    log.error(e)
    error.value = 'Failed to load messages.'
  } finally {
    loading.value = false
  }
}

function startReply(m) {
  if (!m || m.is_mine) return
  replyingTo.value = { id: m.id, message: m.message, writer_name: m.writer_name }
}

function isWithinFirstHour(m) {
  try {
    const created = new Date(m.created_at)
    const ageMs = Date.now() - created.getTime()
    return ageMs <= 60 * 60 * 1000
  } catch (_) { return false }
}

async function deleteMessage(m) {
  if (!props.caseId || !m?.id) return
  try {
    await api.delete(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages/${encodeURIComponent(String(m.id))}`)
    const idx = messages.value.findIndex(x => String(x.id) === String(m.id))
    if (idx >= 0) messages.value.splice(idx, 1)
  } catch (e) {
    log.error(e)
  }
}

async function toggleRuleOut(m) {
  if (!props.caseId || !m?.id) return
  try {
    const next = !Boolean(m.rule_out)
    const { data } = await api.patch(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages/${encodeURIComponent(String(m.id))}`, { rule_out: next })
    m.rule_out = Boolean((data && data.rule_out) ?? next)
  } catch (e) {
    log.error(e)
  }
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

async function onUploadedFromComposer(uploaded) {
  try {
    if (!uploaded || !uploaded.id || !props.caseId) return
    sending.value = true
    const payload = { message: '', reply_to_id: replyingTo.value ? String(replyingTo.value.id) : null, file_id: String(uploaded.id) }
    if (props.filterByFieldName && props.filterByFieldId) {
      payload.filter_by_field_name = String(props.filterByFieldName)
      payload.filter_by_field_id = String(props.filterByFieldId)
    }
    const { data } = await api.post(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages`, payload)
    const myPhoto = (messages.value.find(x => x?.my_photo_url)?.my_photo_url) || '/images/pfp-generic.png'
    messages.value.push({ ...data, seen: true, is_mine: true, my_photo_url: myPhoto })
    showUploader.value = false
    replyingTo.value = null
    await nextTick()
    try {
      const list = listEl.value
      if (list) {
        const container = getScrollableParent(list)
        if (container?.scrollTo) {
          container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
        } else {
          container.scrollTop = container.scrollHeight
        }
      }
    } catch (_) { /* noop */ }
  } catch (e) {
    log.error(e)
  } finally {
    sending.value = false
  }
}

async function sendMessage() {
  const text = composer.value.trim()
  if (!text || !props.caseId) return
  sending.value = true
  try {
    const payload = { message: text, reply_to_id: replyingTo.value ? String(replyingTo.value.id) : null }
    if (props.filterByFieldName && props.filterByFieldId) {
      payload.filter_by_field_name = String(props.filterByFieldName)
      payload.filter_by_field_id = String(props.filterByFieldId)
    }
    const { data } = await api.post(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages`, payload)
    // Append and reset composer
    const myPhoto = (messages.value.find(x => x?.my_photo_url)?.my_photo_url) || '/images/pfp-generic.png'
    messages.value.push({ ...data, seen: true, is_mine: true, my_photo_url: myPhoto })
    composer.value = ''
    replyingTo.value = null
    await nextTick()
    try {
      const list = listEl.value
      if (list) {
        const container = getScrollableParent(list)
        if (container?.scrollTo) {
          container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
        } else {
          container.scrollTop = container.scrollHeight
        }
      }
    } catch (_) { /* noop */ }
  } catch (e) {
    log.error(e)
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
    // Update my reaction
    const prev = m.reaction || null
    m.reaction = val || null
    // Adjust aggregated reactions locally for immediate UI feedback
    if (!Array.isArray(m.reactions)) m.reactions = []
    // Decrement previous emoji count
    if (prev) {
      const idx = m.reactions.findIndex(r => r.emoji === prev)
      if (idx >= 0) {
        m.reactions[idx].count = Math.max(0, Number(m.reactions[idx].count || 0) - 1)
        if (m.reactions[idx].count <= 0) {
          m.reactions.splice(idx, 1)
        }
      }
    }
    // Increment new emoji count
    if (val) {
      const idx2 = m.reactions.findIndex(r => r.emoji === val)
      if (idx2 >= 0) {
        m.reactions[idx2].count = Number(m.reactions[idx2].count || 0) + 1
      } else {
        m.reactions.push({ emoji: val, count: 1 })
      }
    }
  } catch (e) {
    log.error(e)
  } finally {
    if (emojiPanel.value?.hide) emojiPanel.value.hide()
    emojiTargetMessage.value = null
  }
}


watch(() => props.caseId, (val) => {
  didInitialScroll.value = false
  if (val) {
    loadMessages()
  } else {
    messages.value = []
  }
}, { immediate: true })

// Local filter for search
const filteredMessages = computed(() => {
  const q = (searchQuery.value || '').trim().toLowerCase()
  if (!q) return messages.value
  return messages.value.filter(m => {
    const parts = [
      (m.message || ''),
      (m.writer_name || ''),
      (m.file_name || ''),
      (m.reply_to_text || ''),
    ].join(' ').toLowerCase()
    return parts.includes(q)
  })
})

// Toggle search within composer
const showSearch = ref(false)
const searchInputEl = ref(null)
watch(() => showSearch.value, async (val) => {
  if (val) {
    await nextTick()
    try { searchInputEl.value?.focus?.() } catch (_) {}
  }
})

const groups = computed(() => {
  const byDate = new Map()
  const sorted = filteredMessages.value.slice().sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
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

function extensionIcon(name) {
  const n = String(name || '').toLowerCase()
  if (n.endsWith('.pdf')) return 'pi-file-pdf'
  if (/\.doc(x|m)?$|\.dot(x)?$/i.test(n)) return 'pi-file-word'
  if (/\.xls(x|m)?$|\.xlt(x)?$/i.test(n)) return 'pi-file-excel'
  if (/\.(png|jpg|jpeg|gif|bmp|webp|tif|tiff|svg)$/i.test(n)) return 'pi-image'
  return 'pi-file'
}

function downloadMessageFile(m) {
  try {
    const href = m?.file_url
    if (!href) return
    const a = document.createElement('a')
    a.href = href
    a.download = m?.file_name || 'download'
    a.rel = 'noopener'
    document.body.appendChild(a)
    a.click()
    a.remove()
  } catch (e) {
    try { window.open(m?.file_url, '_blank', 'noopener') } catch (_) {}
  }
}

function openLightbox(m) {
  try {
    if (!m) return
    lightboxItem.value = m
    showLightbox.value = true
  } catch (_) { /* noop */ }
}

function closeLightbox() {
  showLightbox.value = false
  lightboxItem.value = null
}

function onLightboxKeydown(e) {
  if (!showLightbox.value) return
  const key = e?.key || e?.code || ''
  if (key === 'Escape' || key === 'Esc') {
    e.preventDefault()
    closeLightbox()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onLightboxKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onLightboxKeydown)
})

// Fetch only the new/unseen messages for this case and append to the end
async function fetchAndAppendNewMessages() {
  const cid = String(props.caseId || '')
  if (!cid) return
  try {
    let url = `/api/v1/cases/messages/new_messages/case/${encodeURIComponent(cid)}`
    if (props.filterByFieldName && props.filterByFieldId) {
      const usp = new URLSearchParams()
      usp.set('filter_by_field_name', String(props.filterByFieldName))
      usp.set('filter_by_field_id', String(props.filterByFieldId))
      url += `?${usp.toString()}`
    }
    const { data } = await api.get(url)
    const arr = Array.isArray(data) ? data : []
    if (!arr.length) return
    const have = new Set(messages.value.map(m => String(m.id)))
    for (const m of arr) {
      if (!have.has(String(m.id))) {
        messages.value.push(m)
      }
      await observeUnseenRows();
    }
    // Do not scroll; leave position unchanged by requirement
  } catch (e) {
    // Silently ignore to avoid user disruption
    log.error(e)
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

// handle unseen rows
async function observeUnseenRows() {
  await nextTick();
  const nodes = Array.from(document.querySelectorAll('.row[data-unseen="true"]'));
  log.debug('observeUnseenRows', nodes);
  for (const node of nodes) {
    observer.observe(node);
  }

}

  // Create the observer
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // Your code here
        executeWhenVisible(entry);
      }
    });
  }, {
    threshold: 0.1, // Trigger when 10% visible
    rootMargin: '0px'
  });

async function executeWhenVisible(entry) {
  log.debug('Element is visible', entry);
  observer.unobserve(entry.target);
  let id = entry.target.getAttribute('data-mid');
  for (const m of messages.value) {
    if (String(m.id) === String(id)) {
      m.seen = true;
      m._fadingUnseen = true;
        try {
          await api.post(`/api/v1/cases/${encodeURIComponent(props.caseId)}/messages/mark_seen_up_to/${encodeURIComponent(String(m.id))}`)
        } catch (e) {
          log.error(e);
          // ignore API failure; local fade already shown
        }
      setTimeout(() => { m._fadingUnseen = false }, 20000);
    }
  }
}

// Listen for generic message changes via global event bus and refresh targeted message
const _onMessageChange = async (evt) => {
  try {
    const det = (evt && evt.detail) ? evt.detail : null
    if (!det) return
    const encCase = String(det.case_id || '')
    const encMid = String(det.message_id || '')
    if (!encCase || !encMid) return
    if (String(props.caseId || '') !== encCase) return
    // Find the message in current list
    const idx = messages.value.findIndex(m => String(m.id) === encMid)
    if (idx < 0) return
    // Fetch the complete message record
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/messages/${encodeURIComponent(encMid)}`
    try {
      const { data } = await api.get(url)
      if (data) {
        messages.value[idx] = data
      }
    } catch (err) {
      // On 404, remove the message locally (was deleted)
      try {
        const status = err && err.response && err.response.status
        if (status === 404) {
          messages.value.splice(idx, 1)
        }
      } catch (_) { /* noop */ }
    }
  } catch (_) { /* noop */ }
}

onMounted(() => {
  try { gMessageEvents?.addEventListener?.('message-change', _onMessageChange) } catch (_) { /* noop */ }
})

onBeforeUnmount(() => {
  try { gMessageEvents?.removeEventListener?.('message-change', _onMessageChange) } catch (_) { /* noop */ }
})

</script>

<template>
  <div class="chat-tab">

    <div v-if="error" class="p-2 text-red-600">{{ error }}</div>

    <!-- Messages List -->
    <div class="list" ref="listEl">
      <div v-for="group in groups" :key="group.key" class="date-group">
        <div class="date-chip">{{ fmtDate(group.date) }}</div>
        <div v-for="m in group.items" :key="m.id" class="row" :data-mid="m.id" :data-unseen="!m.seen" :class="{ unseen: (!!m._fadingUnseen && !m.is_mine) }">
          <div class="pfp left">
            <img v-if="!m.is_mine" :src="m.writer_photo_url || '/images/pfp-generic.png'" alt="pfp" class="avatar" />
          </div>
          <div class="bubble">
            <div v-if="m.reply_to_id && m.reply_to_text" class="reply-preview">
              <span class="material-symbols-outlined tiny">reply</span>
              <span class="ellipsis">{{ m.reply_to_text }}</span>
            </div>
            <div class="text" :class="{ 'ruled-out': !!m.rule_out }">{{ m.message }}</div>
            <div v-if="m.file_id" class="attachment mt-2">
              <template v-if="m.file_thumb">
                <img :src="m.file_thumb"
                     :alt="m.file_name || 'attachment'"
                     class="attachment-thumb"
                     @click="openLightbox(m)" />
              </template>
              <template v-else>
                <button class="attachment-file flex align-items-center gap-2"
                        @click="downloadMessageFile(m)"
                        :aria-label="'Download ' + (m.file_name || 'file')">
                  <i class="pi text-lg" :class="extensionIcon(m.file_name)"></i>
                  <span class="filename ellipsis">{{ m.file_name || 'file' }}</span>
                </button>
              </template>
            </div>
            <div class="footer flex align-items-center justify-content-between mt-1">
              <span class="left-info flex align-items-center gap-2">
                <span class="time">{{ fmtTime(m.created_at) }}</span>
                <span v-if="Array.isArray(m.reactions) && m.reactions.length" class="reactions-list flex align-items-center gap-1">
                  <span v-for="rg in m.reactions" :key="rg.emoji" class="reaction-pill">
                    <span class="emoji">{{ rg.emoji }}</span>
                    <span class="count-badge">{{ rg.count }}</span>
                  </span>
                </span>
              </span>
              <span v-if="!m.is_mine" class="actions flex align-items-center gap-2">
                <Button size="small" text @click="startReply(m)">
                  <span class="material-symbols-outlined">reply</span>
                </Button>
                <Button size="small" text @click="openEmojiPicker($event, m)">
                  <span v-if="m.reaction">{{ m.reaction }}</span>
                  <span v-else class="material-symbols-outlined">mood</span>
                </Button>
              </span>
              <span v-else class="actions flex align-items-center gap-2">
                <Button v-if="isWithinFirstHour(m)" size="small" text @click="deleteMessage(m)" :aria-label="'Delete message'">
                  <span class="material-symbols-outlined">delete</span>
                </Button>
                <Button v-else size="small" text @click="toggleRuleOut(m)" :aria-label="m.rule_out ? 'Undo rule out' : 'Rule out'">
                  <span class="material-symbols-outlined" v-if="m.rule_out">change_circle</span>
                  <span class="material-symbols-outlined" v-else>cancel</span>
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

      <!-- Toggleable Search above composer row -->
      <div v-if="showSearch" class="mb-2">
        <FloatLabel variant="on" class="w-full">
          <InputText id="msg-search" ref="searchInputEl" v-model="searchQuery" class="w-full" placeholder=" " />
          <label for="msg-search">Search messages</label>
        </FloatLabel>
      </div>

      <div class="composer-row w-full space-y-1">
        <template v-if="showUploader">
          <Button text @click="showSearch = !showSearch" class="shrink-0" :aria-label="showSearch ? 'Hide search' : 'Show search'">
            <i class="pi pi-search"></i>
          </Button>
          <Button text @click="showUploader = false" class="shrink-0" :aria-label="'Close uploader'">
            <span class="material-symbols-outlined">close</span>
          </Button>
          <FloatLabel variant="on" class="flex-1 min-w-0 align-content-center">
            <div class="w-full">
              <FileUpload :caseId="caseId" :singleFile="true" :rfi_id="(filterByFieldName === 'rfi_id' && filterByFieldId) ? String(filterByFieldId) : null" @uploaded="onUploadedFromComposer" />
            </div>
          </FloatLabel>
        </template>
        <template v-else>
          <Button text @click="showSearch = !showSearch" class="shrink-0" :aria-label="showSearch ? 'Hide search' : 'Show search'" variant="outlined">
            <span v-if="showSearch" class="material-symbols-outlined">search_off</span>
            <span v-else class="material-symbols-outlined">search</span>
          </Button>
          <Button text @click="showUploader = true" class="shrink-0" :aria-label="'Attach file'">
            <span class="material-symbols-outlined">attach_file</span>
          </Button>
          <FloatLabel variant="on" class="flex-1 min-w-0 align-content-center">
            <Textarea id="msg-input" v-model="composer" autoResize rows="1" class="w-full"
                      @keydown="onComposerKeydown"
                      @compositionstart="isComposing = true"
                      @compositionend="isComposing = false" />
            <label for="msg-input">Type a message</label>
          </FloatLabel>
          <Button label="Send" icon="pi pi-send" @click="sendMessage" :loading="sending" :disabled="!composer.trim()" class="shrink-0 align-content-center"/>
        </template>
      </div>
    </div>

    <Popover ref="emojiPanel">
      <div class="emoji-panel">
        <button v-for="e in emojiChoices" :key="e" class="emoji-btn" @click="chooseEmoji(e)">{{ e }}</button>
        <button class="emoji-btn clear" @click="chooseEmoji(null)">Clear</button>
      </div>
    </Popover>

    <!-- Lightbox Overlay (match FilesTab) -->
    <div v-if="showLightbox" class="lightbox" @click.self="closeLightbox">
      <button class="lightbox-close" type="button" @click="closeLightbox" aria-label="Close">
        <i class="pi pi-times"></i>
      </button>
      <div class="lightbox-center">
        <div class="lightbox-content">
          <template v-if="lightboxItem">
            <video v-if="lightboxItem.file_is_video" :src="lightboxItem.file_url" controls class="lightbox-media"></video>
            <img v-else-if="lightboxItem.file_is_image" :src="lightboxItem.file_url" alt="preview" class="lightbox-media" />
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-tab { display: flex; flex-direction: column; height: 100%; min-height: 0; }
.header {  top: 0; z-index: 6; border-bottom: 1px solid var(--p-surface-200, #e5e7eb); background: var(--p-surface-0, #fff); }
.list { flex: 1; overflow: auto; padding: 0 12px 12px 12px; background: var(--p-surface-0, #fff); min-height: 0; }
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
.text.ruled-out { text-decoration: line-through; opacity: 0.8; }
.time { font-size: 0.8rem; color: var(--p-text-color, #6b7280); }
.reply-preview { font-size: 0.85rem; color: var(--p-text-color, #6b7280); padding: 4px 8px; border-left: 3px solid var(--p-surface-300, #d1d5db); margin: 4px 0; background: var(--p-surface-50, #f9fafb); border-radius: 6px; }
.reply-preview .tiny { font-size: 16px; vertical-align: middle; }
.ellipsis { display: inline-block; max-width: 520px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: bottom; }
.date-group { padding-top: 8px; }
.date-chip { display: inline-block; margin: 8px auto; padding: 4px 10px; border-radius: 999px; border: 1px solid var(--p-surface-300, #d1d5db); background: var(--p-surface-50, #f9fafb); font-size: 0.85rem; color: var(--p-text-color, #374151); position: sticky; top: 6px; z-index: 1; align-self: center; }
.actions :deep(.p-button) { padding: 2px 6px; }
.row.unseen .bubble { border-color: var(--p-primary-300, #93c5fd); border-width: 2px; box-shadow: 0 0 0 4px rgba(59,130,246,0.20); animation: unseenFade 20s ease-out forwards; }
@keyframes unseenFade { 0% { border-color: var(--p-primary-300, #93c5fd); box-shadow: 0 0 0 4px rgba(59,130,246,0.20); } 100% { border-color: var(--p-surface-300, #d1d5db); box-shadow: 0 1px 1px rgba(0,0,0,0.04); } }
.composer { position: sticky; bottom: 8px; z-index: 5; border-top: 1px solid var(--p-surface-200, #e5e7eb); background: var(--p-surface-0, #fff);  }
.composer-row { display: flex; gap: 8px; align-items: flex-end; }
.replying-chip { display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 999px; background: var(--p-surface-100, #f3f4f6); margin-bottom: 6px; }
.replying-chip .x { background: transparent; border: none; cursor: pointer; }
.reactions-list { display: inline-flex; gap: 6px; }
.reaction-pill { display: inline-flex; align-items: center; gap: 4px; background: var(--p-surface-100, #f3f4f6); border: 1px solid var(--p-surface-300, #d1d5db); border-radius: 999px; padding: 1px 6px; font-size: 0.8rem; }
.reaction-pill .count-badge { display: inline-block; min-width: 16px; padding: 0 4px; border-radius: 8px; background: var(--p-surface-200, #e5e7eb); color: var(--p-text-color, #374151); text-align: center; font-size: 0.72rem; }

/* Attachment styles */
.attachment { display: inline-block; }
.attachment-thumb { max-width: 160px; max-height: 120px; border-radius: 8px; border: 1px solid var(--p-surface-300, #d1d5db); cursor: pointer; object-fit: cover; }
.attachment-file { background: var(--p-surface-100, #f3f4f6); border: 1px solid var(--p-surface-300, #d1d5db); border-radius: 8px; padding: 4px 8px; cursor: pointer; }
.attachment-file:hover { background: var(--p-surface-50, #f9fafb); }
.filename { max-width: 360px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Lightbox (match FilesTab) */
.lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 1000; }
.lightbox-close { position: fixed; top: 12px; right: 12px; width: 40px; height: 40px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.4); background: rgba(0,0,0,0.4); color: #fff; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; z-index: 1001; }
.lightbox-close .pi { font-size: 18px; }
.lightbox-center { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; padding: 2vw; }
.lightbox-content { max-width: 80vw; max-height: 90vh; background: transparent; display: flex; align-items: center; justify-content: center; }
.lightbox-media { max-width: 80vw; max-height: 90vh; object-fit: contain; display: block; }


</style>
