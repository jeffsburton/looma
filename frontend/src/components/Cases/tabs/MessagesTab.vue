<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'

// Simple in-memory messages. Later this can come from an API/store
const me = {
  id: 'me',
  name: 'You',
  avatar: 'https://avatars.githubusercontent.com/u/9919?s=40&v=4' // neutral placeholder
}

const participants = [
  { id: 'p1', name: 'Tom P', avatar: 'https://i.pravatar.cc/40?img=12' },
  { id: 'p2', name: 'Amy Pernie', avatar: 'https://i.pravatar.cc/40?img=32' },
  { id: 'p3', name: 'Rick Minchew', avatar: 'https://i.pravatar.cc/40?img=56' },
  { id: 'p4', name: 'Ruth Grambush', avatar: 'https://i.pravatar.cc/40?img=5' },
  { id: 'p5', name: 'Jenny Harp-Hoyt', avatar: 'https://i.pravatar.cc/40?img=25' },
  { id: 'p6', name: 'Mason Hoyt', avatar: 'https://i.pravatar.cc/40?img=18' }
]

function d(dateStr) { return new Date(dateStr) }

const messages = ref([
  { id: 1, from: 'p1', text: 'All in !\n❤️🇺🇸', at: d('2025-08-16T13:58:00') },
  { id: 2, from: 'p2', text: "I'm in\n❤️🇺🇸", at: d('2025-08-16T13:58:30') },
  { id: 3, from: 'p3', text: "I'm available, minus any unforeseen issues.\n❤️🇺🇸", at: d('2025-08-16T14:51:00') },
  { id: 4, from: 'p4', text: "So sorry for the delay in response time. We are still waiting for baby's arrival as she seems to be in no rush and is past her due date 😕\nBen and I most likely won't be able to help out with it being so close to the search and trying to coordinate child care", at: d('2025-08-16T13:29:00') },
  { id: 5, from: 'p5', text: 'Unfortunately I will have limited availability that week.', at: d('2025-08-16T13:32:00') },
  { id: 6, from: 'p6', text: 'Hoping to be available 2 days out of the week due to work constraints. @C2RShepherd I can explain more in detail offline.', at: d('2025-08-16T13:41:00') }
])

const composer = ref('')
const listEl = ref(null)

const groups = computed(() => {
  // Group by date (YYYY-MM-DD)
  const byDate = new Map()
  for (const m of messages.value.slice().sort((a, b) => a.at - b.at)) {
    const key = m.at.toISOString().slice(0, 10)
    if (!byDate.has(key)) byDate.set(key, [])
    byDate.get(key).push(m)
  }
  return Array.from(byDate.entries()).map(([key, arr]) => ({ key, date: new Date(key), items: arr }))
})

function senderFor(id) {
  if (id === me.id) return me
  return participants.find(p => p.id === id) || { id, name: 'Unknown', avatar: '' }
}

function fmtTime(date) {
  return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function fmtDate(date) {
  return date.toLocaleDateString([], { month: 'long', day: 'numeric' })
}

async function sendMessage() {
  const text = composer.value.trim()
  if (!text) return
  messages.value.push({ id: Date.now(), from: me.id, text, at: new Date() })
  composer.value = ''
  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  if (!listEl.value) return
  listEl.value.scrollTop = listEl.value.scrollHeight
}

onMounted(() => {
  scrollToBottom()
})
</script>
<template>
  <div class="chat-tab">
    <div class="header p-3">
      <div class="text-lg font-semibold flex align-items-center gap-2">
        <span class="material-symbols-outlined">chat_bubble</span>
        <span>Messages</span>
      </div>
    </div>

    <!-- Messages List -->
    <div class="list" ref="listEl">
      <div v-for="group in groups" :key="group.key" class="date-group">
        <div class="date-chip">{{ fmtDate(group.date) }}</div>
        <div v-for="m in group.items" :key="m.id" class="row">
          <img class="avatar" :src="senderFor(m.from).avatar" :alt="senderFor(m.from).name" />
          <div class="bubble">
            <div class="sender">{{ senderFor(m.from).name }}</div>
            <div class="text" v-html="m.text.replace(/\n/g, '<br>')" />
            <div class="time">{{ fmtTime(m.at) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Composer -->
    <div class="composer p-2">
      <Textarea v-model="composer" autoResize rows="1" placeholder="Type a message" class="flex-1" />
      <Button label="Send" icon="pi pi-send" @click="sendMessage" :disabled="!composer.trim()" />
    </div>
  </div>
</template>

<style scoped>
.chat-tab { display: flex; flex-direction: column; height: 100%; }
.header { border-bottom: 1px solid var(--p-surface-200, #e5e7eb); }
.list { flex: 1; overflow: auto; padding: 0 12px 12px 12px; background: var(--p-surface-0, #fff); }
.row { display: flex; gap: 8px; padding: 8px 4px; align-items: flex-start; }
.avatar { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; flex: 0 0 36px; background: #ddd; }
.bubble { position: relative; max-width: 680px; border: 1px solid var(--p-surface-300, #d1d5db); background: var(--p-surface-0, #fff); border-radius: 12px; padding: 8px 12px 6px 12px; box-shadow: 0 1px 1px rgba(0,0,0,0.04); }
.sender { font-weight: 600; margin-bottom: 4px; }
.text { white-space: pre-wrap; word-break: break-word; }
.time { text-align: right; font-size: 0.8rem; color: var(--p-text-color, #6b7280); margin-top: 4px; }

.date-group { padding-top: 8px; }
.date-chip { display: inline-block; margin: 8px auto; padding: 4px 10px; border-radius: 999px; border: 1px solid var(--p-surface-300, #d1d5db); background: var(--p-surface-50, #f9fafb); font-size: 0.85rem; color: var(--p-text-color, #374151); position: sticky; top: 6px; z-index: 1; align-self: center; }

.composer { display: flex; gap: 8px; align-items: flex-end; border-top: 1px solid var(--p-surface-200, #e5e7eb); background: var(--p-surface-0, #fff); }
:deep(textarea) { width: 100%; }
</style>
