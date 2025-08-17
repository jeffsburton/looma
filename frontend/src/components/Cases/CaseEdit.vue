<script setup>
import { ref, computed, defineAsyncComponent } from 'vue'

// Top-level tabs config
const tabs = [
  { key: 'intake', label: 'Intake', icon: 'arrows_input' },
  { key: 'social', label: 'Social Media', icon: 'photo_camera' },
  { key: 'timeline', label: 'Timeline', icon: 'calendar_month' },
  { key: 'files', label: 'Files', icon: 'folder_open' },
  { key: 'activity', label: 'Activity', icon: 'skateboarding' },
  { key: 'messages', label: 'Messages', icon: 'chat_bubble' }
]

const active = ref('intake')
const activeIndex = computed(() => tabs.findIndex(t => t.key === active.value))

// Lazy imports for tab components
const IntakeTab = defineAsyncComponent(() => import('./tabs/IntakeTab.vue'))
const SocialMediaTab = defineAsyncComponent(() => import('./tabs/SocialMediaTab.vue'))
const TimelineTab = defineAsyncComponent(() => import('./tabs/TimelineTab.vue'))
const FilesTab = defineAsyncComponent(() => import('./tabs/FilesTab.vue'))
const ActivityTab = defineAsyncComponent(() => import('./tabs/ActivityTab.vue'))
const MessagesTab = defineAsyncComponent(() => import('./tabs/MessagesTab.vue'))
</script>

<template>
  <div class="case-edit panel">
    <!-- Top Tabs -->
    <div class="tabs surface-card border-round p-1 mb-2">
      <div class="flex gap-1 wrap">
        <button
          v-for="t in tabs"
          :key="t.key"
          class="p-2 border-round flex align-items-center gap-2 cursor-pointer tab-btn"
          :class="{ active: t.key === active, inactive: t.key !== active }"
          @click="active = t.key"
        >
          <span class="material-symbols-outlined">{{ t.icon }}</span>
          <span class="label">{{ t.label }}</span>
        </button>
      </div>
    </div>

    <!-- Active Tab Content -->
    <div class="surface-card border-round p-2 flex-1 overflow-auto">
      <KeepAlive>
        <Suspense>
          <component
            :is="active === 'intake' ? IntakeTab
                  : active === 'social' ? SocialMediaTab
                  : active === 'timeline' ? TimelineTab
                  : active === 'files' ? FilesTab
                  : active === 'activity' ? ActivityTab
                  : MessagesTab"
          />
          <template #fallback>
            <div class="p-3 text-600">Loading...</div>
          </template>
        </Suspense>
      </KeepAlive>
    </div>
  </div>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; height: 100%; }
.tabs { position: sticky; top: 0; z-index: 1; }
.tab-btn { background: transparent; border: 1px solid transparent; }
.tab-btn:hover { background: var(--p-surface-100, #f5f5f5); }
.tab-btn.active { background: var(--p-primary-100, #fbd5d5); color: var(--p-primary-800, #1D3B52); border-color: var(--p-primary-200, #C9DFEE); }
.tab-btn.inactive { color: var(--p-text-color, inherit); }
.wrap { flex-wrap: wrap; }
</style>
