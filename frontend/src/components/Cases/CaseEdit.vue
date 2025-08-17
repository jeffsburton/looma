<script setup>
import { ref, computed, defineAsyncComponent } from 'vue'

// Top-level tabs config
const tabs = [
  { key: 'intake', label: 'Core', icon: 'article' },
  { key: 'social', label: 'Social Media', icon: 'photo_camera' },
  { key: 'timeline', label: 'Timeline', icon: 'calendar_month' },
  { key: 'files', label: 'Files', icon: 'folder_open' },
  { key: 'activity', label: 'Activity', icon: 'skateboarding' },
  { key: 'messages', label: 'Messages', icon: 'chat_bubble' }
]

const active = ref('intake')
const activeIndex = computed(() => tabs.findIndex(t => t.key === active.value))

// TEMP subject photo (to be wired to actual case subject data)
const subjectPhotoUrl = ref('/images/sample_faces/1.png')
const photoError = ref(false)
function onImgError() { photoError.value = true }

// TEMP subject core details (to be wired to actual case subject data)
const subjectName = ref('Kendrick Owen')
const subjectAge = ref(16)
const dateMissing = ref('2025-07-03')

// Computed: days missing since dateMissing (in whole days)
const daysMissing = computed(() => {
  const raw = dateMissing.value
  if (!raw) return null
  const d = new Date(raw)
  if (isNaN(d.getTime())) return null
  // Normalize both dates to UTC midnight to avoid timezone/daylight issues
  const missingUTC = Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())
  const now = new Date()
  const todayUTC = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())
  const diffMs = todayUTC - missingUTC
  const days = Math.floor(diffMs / 86400000)
  return Math.max(0, days)
})

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
    <!-- Subject Row -->
    <div class="subject-row surface-card border-round p-2 mb-2">
      <div class="flex align-items-center gap-2">
        <div class="pfp-wrapper">
          <img v-if="!photoError" :src="subjectPhotoUrl" alt="subject" class="pfp" @error="onImgError" />
          <div v-else class="pfp pfp-fallback flex align-items-center justify-content-center">
            <span class="material-symbols-outlined">person</span>
          </div>
        </div>
        <div class="min-w-0">
          <div class="subject-name text-xl font-semibold">{{ subjectName }}</div>
          <div class="subject-meta text-sm text-color-secondary">
            Age {{ subjectAge }} • Missing since {{ dateMissing }}
            <template v-if="daysMissing !== null">
              ({{ daysMissing }} day<span v-if="daysMissing !== 1">s</span>)
            </template>
          </div>
        </div>
      </div>
    </div>

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

/* PFP styles */
.pfp { width: 40px; height: 40px; border-radius: 9999px; object-fit: cover; display: block; border: 2px solid var(--p-surface-200, #e5e7eb); }
.pfp-fallback { width: 40px; height: 40px; border-radius: 9999px; background: var(--p-surface-200, #e5e7eb); color: var(--p-text-color, #6b7280); }
.pfp-wrapper { flex: 0 0 auto; }
</style>
