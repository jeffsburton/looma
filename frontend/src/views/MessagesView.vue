<script setup>
import { ref, computed, nextTick } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'

// Prototype data: three Missing Cases
const cases = ref([
  {
    id: 'm1',
    name: 'Kendrick Owen',
    photoUrl: '/images/sample_faces/1.png',
    expanded: false,
    // minimal sample conversation (2-3 bubbles)
    messages: [
      { id: 1, from: 'parent', name: 'John Owen', avatar: '/images/sample_faces/1.png', text: 'Any updates on the search around the park?', at: new Date('2025-08-16T10:10:00') },
      { id: 2, from: 'you', name: 'You', avatar: 'https://avatars.githubusercontent.com/u/9919?s=40&v=4', text: 'We have teams revisiting the area this afternoon.', at: new Date('2025-08-16T10:12:00') },
      { id: 3, from: 'parent', name: 'John Owen', avatar: '/images/sample_faces/1.png', text: 'Thank you. Please keep us posted.', at: new Date('2025-08-16T10:13:00') },
    ],
    composer: ''
  },
  {
    id: 'm2',
    name: 'Jasmine Jackson',
    photoUrl: '/images/sample_faces/2.png',
    expanded: false,
    messages: [
      { id: 1, from: 'parent', name: 'Keisha Butler', avatar: '/images/sample_faces/2.png', text: 'Saw the flyer shared on FB. Appreciate it.', at: new Date('2025-08-17T09:01:00') },
      { id: 2, from: 'you', name: 'You', avatar: 'https://avatars.githubusercontent.com/u/9919?s=40&v=4', text: 'We will post the updated one later today.', at: new Date('2025-08-17T09:02:00') }
    ],
    composer: ''
  },
  {
    id: 'm3',
    name: 'Chaz Hernandez',
    photoUrl: '/images/sample_faces/3.png',
    expanded: false,
    messages: [
      { id: 1, from: 'le', name: 'Det. Lowe', avatar: '/images/sample_faces/3.png', text: 'Checking new camera footage in the area.', at: new Date('2025-08-15T15:45:00') },
      { id: 2, from: 'you', name: 'You', avatar: 'https://avatars.githubusercontent.com/u/9919?s=40&v=4', text: 'Understood. Let us know anything actionable.', at: new Date('2025-08-15T15:47:00') }
    ],
    composer: ''
  }
])

function toggleExpand(item) {
  item.expanded = !item.expanded
  if (item.expanded) nextTick(() => scrollToBottom(item.id))
}

function fmtTime(date) {
  return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function listRefId(id) { return `list-${id}` }

function scrollToBottom(id) {
  const el = document.getElementById(listRefId(id))
  if (!el) return
  el.scrollTop = el.scrollHeight
}

function sendMessage(item) {
  const text = (item.composer || '').trim()
  if (!text) return
  item.messages.push({ id: Date.now(), from: 'you', name: 'You', avatar: 'https://avatars.githubusercontent.com/u/9919?s=40&v=4', text, at: new Date() })
  item.composer = ''
  nextTick(() => scrollToBottom(item.id))
}
</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Messages'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <div class="flex align-items-center justify-content-between gap-2 pb-2">
            <div class="text-xl font-semibold">Messages</div>
          </div>

          <div class="surface-card border-round p-0 flex-1 overflow-auto">
            <!-- List of Missing Cases -->
            <div class="cases-list">
              <div v-for="item in cases" :key="item.id" class="case-block">
                <div class="case-row">
                  <Button text rounded @click="toggleExpand(item)" class="expand-btn"
                          :aria-label="item.expanded ? 'Collapse' : 'Expand'">
                    <span class="material-symbols-outlined">{{ item.expanded ? 'expand_less' : 'expand_more' }}</span>
                  </Button>
                  <img class="avatar" :src="item.photoUrl" :alt="item.name" />
                  <div class="meta">
                    <div class="name">{{ item.name }}</div>
                  </div>
                </div>

                <!-- Expanded thread under its row -->
                <div v-show="item.expanded" class="thread">
                  <!-- Messages List (limited bubbles) -->
                  <div class="list" :id="listRefId(item.id)">
                    <div v-for="m in item.messages" :key="m.id" class="row">
                      <img class="avatar" :src="m.avatar" :alt="m.name" />
                      <div class="bubble">
                        <div class="sender">{{ m.name }}</div>
                        <div class="text">{{ m.text }}</div>
                        <div class="time">{{ fmtTime(m.at) }}</div>
                      </div>
                    </div>
                  </div>

                  <!-- Composer (like MessagesTab) -->
                  <div class="composer p-2">
                    <Textarea v-model="item.composer" autoResize rows="1" placeholder="Type a message" class="flex-1" />
                    <Button label="Send" icon="pi pi-send" @click="sendMessage(item)" :disabled="!(item.composer||'').trim()" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cases-list { padding: 8px; }
.case-row { display: flex; align-items: center; gap: 10px; padding: 8px; border-bottom: 1px solid var(--p-surface-200, #e5e7eb); }
.avatar { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; background: #ddd; }
.meta .name { font-weight: 600; }
.thread { border-bottom: 1px solid var(--p-surface-200, #e5e7eb); background: var(--p-surface-0, #fff); }

/* Chat list styling mirroring MessagesTab */
.list { padding: 8px 12px; background: var(--p-surface-0, #fff); }
.row { display: flex; gap: 8px; padding: 6px 4px; align-items: flex-start; }
.bubble { position: relative; max-width: 680px; border: 1px solid var(--p-surface-300, #d1d5db); background: var(--p-surface-0, #fff); border-radius: 12px; padding: 8px 12px 6px 12px; box-shadow: 0 1px 1px rgba(0,0,0,0.04); }
.sender { font-weight: 600; margin-bottom: 4px; }
.text { white-space: pre-wrap; word-break: break-word; }
.time { text-align: right; font-size: 0.8rem; color: var(--p-text-color, #6b7280); margin-top: 4px; }

.composer { display: flex; gap: 8px; align-items: flex-end; border-top: 1px solid var(--p-surface-200, #e5e7eb); background: var(--p-surface-0, #fff); }
</style>
