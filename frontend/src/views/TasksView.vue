<script setup>
import { ref } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'

// Simple sample tasks for three missing persons
const tasks = ref([
  {
    id: 't1',
    name: 'Kendrick Owen',
    photoUrl: '/images/sample_faces/1.png',
    title: 'Call guardian and confirm last known contacts',
    expanded: false,
    instructions: 'Call parent/guardian to confirm any new leads and verify last known contacts for the past 48 hours. Document any new names, places, or times mentioned.' ,
    response: ''
  },
  {
    id: 't2',
    name: 'Jasmine Jackson',
    photoUrl: '/images/sample_faces/2.png',
    title: 'Post updated flyer to social media groups',
    expanded: false,
    instructions: 'Share the updated flyer on the community and neighborhood social media groups. Include tip line and case number in the caption.',
    response: ''
  },
  {
    id: 't3',
    name: 'Chaz Hernandez',
    photoUrl: '/images/sample_faces/3.png',
    title: 'Request nearby camera footage from businesses',
    expanded: false,
    instructions: 'Visit or call businesses within a 4-block radius to request exterior camera footage for the relevant timeframe. Note which locations agreed and contact details.',
    response: ''
  }
])

function toggleExpand(item) {
  item.expanded = !item.expanded
}

function markDone(item) {
  // Minimal behavior: mark as done by collapsing and clearing response
  item.expanded = false
}
</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Tasks'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <div class="flex align-items-center justify-content-between gap-2 pb-2">
            <div class="text-xl font-semibold">Tasks</div>
          </div>

          <div class="surface-card border-round p-0 flex-1 overflow-auto">
            <div class="tasks-list">
              <div v-for="item in tasks" :key="item.id" class="task-block">
                <div class="task-row">
                  <Button text rounded @click="toggleExpand(item)" class="expand-btn"
                          :aria-label="item.expanded ? 'Collapse task' : 'Expand task'">
                    <span class="material-symbols-outlined">{{ item.expanded ? 'expand_less' : 'expand_more' }}</span>
                  </Button>
                  <img class="avatar" :src="item.photoUrl" :alt="item.name" />
                  <div class="meta">
                    <div class="title">{{ item.title }}</div>
                    <div class="sub">{{ item.name }}</div>
                  </div>
                </div>

                <div v-show="item.expanded" class="details">
                  <div class="instructions">
                    <div class="heading">Instructions</div>
                    <div class="body">{{ item.instructions }}</div>
                  </div>
                  <div class="response">
                    <div class="heading">Response</div>
                    <Textarea v-model="item.response" autoResize rows="3" placeholder="Type your response or notes" class="w-full" />
                  </div>
                  <div class="actions">
                    <Button label="Done" icon="pi pi-check" @click="markDone(item)" />
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
.tasks-list { padding: 8px; }
.task-row { display: flex; align-items: center; gap: 10px; padding: 8px; border-bottom: 1px solid var(--p-surface-200, #e5e7eb); }
.avatar { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; background: #ddd; }
.meta .title { font-weight: 600; }
.meta .sub { font-size: 0.9rem; color: var(--p-text-color, #6b7280); }
.details { padding: 8px 12px 12px 56px; border-bottom: 1px solid var(--p-surface-200, #e5e7eb); background: var(--p-surface-0, #fff); }
.instructions .heading, .response .heading { font-weight: 600; margin-bottom: 4px; }
.instructions .body { margin-bottom: 8px; white-space: pre-wrap; }
.response :deep(textarea) { width: 100%; }
.actions { margin-top: 8px; display: flex; gap: 8px; }
</style>
