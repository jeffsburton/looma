<script setup>
import { ref, computed, defineAsyncComponent, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import ProgressSpinner from 'primevue/progressspinner';

import CoreTab from './tabs/CoreTab.vue'
import ContactsTab from './tabs/ContactsTab.vue'
import SocialMediaTab from './tabs/SocialMediaTab.vue'
import TimelineTab from './tabs/TimelineTab.vue'
import DocsTab from './tabs/DocsTab.vue'
import ActivityTab from './tabs/ActivityTab.vue'
import TasksTab from './tabs/TasksTab.vue'
import Messages from '../Messages.vue'

import api from '../../lib/api'
import UnseenMessageCount from '../common/UnseenMessageCount.vue'

const props = defineProps({
  caseNumber: { type: [String, Number], required: true },
  tab: { type: String, default: 'core' },
  subtab: { type: String, default: 'intake' },
})


// Models to pass to Intake/Core tabs
const caseModel = ref({})
const subjectModel = ref({})

async function loadCase() {
  const num = String(props.caseNumber || '')
  if (!num) return
  try {
    const resp = await api.get(`/api/v1/cases/by-number/${encodeURIComponent(num)}`)
    const data = resp?.data || {}
    // Header
    const s = data.subject || {}
    const nicks = s.nicknames && String(s.nicknames).trim() ? ` "${String(s.nicknames).trim()}"` : ''
    subjectName.value = `${s.first_name || ''}${nicks} ${s.last_name || ''}`.trim()
    subjectPhotoUrl.value = (s.photo_url || '/images/pfp-generic.png')
    const dem = data.demographics || {}
    // Prefer age_when_missing
    subjectAge.value = dem.age_when_missing ?? null
    const circ = data.circumstances || {}
    dateMissing.value = circ.date_missing || null


    const c = data.case || {}
    caseModel.value = {
      id: c.id || null,
      subject_id: s.id || null,
      case_number: c.case_number || num,
      date_intake: c.date_intake || null,
      inactive: !!c.inactive,
    }
    photoError.value = false
  } catch (e) {
    console.error(e)
  }
}

loadCase()

const router = useRouter()
const route = useRoute()

const active = ref('core')
const intakeSubActive = ref('intake')
const docsSubActive = ref('files')
const VALID_TABS = ['core','contacts','social','timeline','docs','tasks','activity','messages']
const VALID_DOCS_SUBTABS = ['files','ops','intel','rfis','eod','flyer']

// Sync initial tab from route/prop and keep in sync
watch(
  () => props.tab,
  (val) => {
    let v = String(val || 'core')
    if (!VALID_TABS.includes(v)) v = 'core'
    if (active.value !== v) active.value = v
  },
  { immediate: true }
)

// Keep subtab in sync with prop for intake/docs based on active tab
watch(
  () => props.subtab,
  (val) => {
    const t = String(props.tab || active.value || 'core')
    let sub = String(val || (t === 'docs' ? 'files' : 'intake'))
    if (t === 'docs' && !VALID_DOCS_SUBTABS.includes(sub)) sub = 'files'
    if (t === 'core') {
      if (intakeSubActive.value !== sub) intakeSubActive.value = sub
    } else if (t === 'docs') {
      if (docsSubActive.value !== sub) docsSubActive.value = sub
    }
  },
  { immediate: true }
)

watch(
  () => active.value,
  (v) => {
    const tab = String(v || 'core')
    const caseNumber = String(props.caseNumber || '')
    const subtab = tab === 'core'
      ? String(intakeSubActive.value || 'intake')
      : (tab === 'docs' ? (VALID_DOCS_SUBTABS.includes(String(docsSubActive.value)) ? String(docsSubActive.value) : 'files') : undefined)
    const curSub = route.params.subtab ? String(route.params.subtab) : undefined
    const rawTaskId = route.params.rawTaskId ? String(route.params.rawTaskId) : undefined

    // When on Tasks tab with a deep-linked task, preserve the case-task route and rawTaskId
    if (tab === 'tasks') {
      if (rawTaskId) {
        if (route.name !== 'case-task' || String(route.params.caseNumber || '') !== caseNumber) {
          router.replace({ name: 'case-task', params: { caseNumber, rawTaskId } })
        }
        return
      }
      // No rawTaskId: ensure we're on the generic tasks route
      if (
        String(route.params.caseNumber || '') !== caseNumber ||
        String(route.params.tab || '') !== 'tasks' ||
        route.name !== 'case-detail'
      ) {
        router.replace({ name: 'case-detail', params: { caseNumber, tab: 'tasks' } })
      }
      return
    }

    // Default behavior for other tabs
    if (
      String(route.params.caseNumber || '') !== caseNumber ||
      String(route.params.tab || '') !== tab ||
      curSub !== subtab
    ) {
      router.replace({ name: 'case-detail', params: { caseNumber, tab, subtab } })
    }
  }
)

// When intake subtab changes, update URL
watch(
  () => intakeSubActive.value,
  (v) => {
    if (active.value !== 'core') return
    const caseNumber = String(props.caseNumber || '')
    const tab = 'core'
    const subtab = String(v || 'intake')
    const curSub = route.params.subtab ? String(route.params.subtab) : undefined
    if (curSub !== subtab) {
      router.replace({ name: 'case-detail', params: { caseNumber, tab, subtab } })
    }
  }
)

// When docs subtab changes, update URL
watch(
  () => docsSubActive.value,
  (v) => {
    if (active.value !== 'docs') return
    const caseNumber = String(props.caseNumber || '')
    const tab = 'docs'
    const subtab = String(v || 'files')
    const curSub = route.params.subtab ? String(route.params.subtab) : undefined
    if (curSub !== subtab) {
      router.replace({ name: 'case-detail', params: { caseNumber, tab, subtab } })
    }
  }
)

// Subject header reactive data (populated from API)
const subjectPhotoUrl = ref('/images/pfp-generic.png')
const photoError = ref(false)
function onImgError() { photoError.value = true }

const subjectName = ref('')
const subjectAge = ref(null)
const dateMissing = ref(null)

watch(() => props.caseNumber, () => { loadCase() })

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

</script>

<template>
  <div class="case-edit panel" v-if="caseModel.id">
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
            <template v-if="subjectAge !== null && subjectAge !== undefined">Age {{ subjectAge }}</template>
            <template v-if="(subjectAge !== null && subjectAge !== undefined) && dateMissing"> • </template>
            <template v-if="dateMissing">Missing since {{ dateMissing }}
              <template v-if="daysMissing !== null">
                ({{ daysMissing }} day<span v-if="daysMissing !== 1">s</span>)
              </template>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <Tabs :value="active" @update:value="(v) => (active = v)" :lazy="true">
      <TabList class="mb-1">
        <Tab value="core">
          <span class="material-symbols-outlined">article</span>
          <span class="ml-1">Core</span>
        </Tab>
        <Tab value="contacts">
          <span class="material-symbols-outlined">patient_list</span>
          <span class="ml-1">People</span>
        </Tab>
        <Tab value="social">
          <span class="material-symbols-outlined">share</span>
          <span class="ml-1">Social Media</span>
        </Tab>
        <Tab value="timeline">
          <span class="material-symbols-outlined">calendar_month</span>
          <span class="ml-1">Timeline</span>
        </Tab>
        <Tab value="activity">
          <span class="material-symbols-outlined">skateboarding</span>
          <span class="ml-1">Activity</span>
        </Tab>
        <Tab value="docs">
          <span class="material-symbols-outlined">folder_open</span>
          <span class="ml-1">Docs</span>
        </Tab>
        <Tab value="tasks">
          <UnseenMessageCount TableName="task" :CaseId="caseModel.id">
            <div class="flex align-items-center">
              <span class="material-symbols-outlined">list_alt_check</span>
              <span class="ml-1">Tasks</span>
            </div>
          </UnseenMessageCount>
        </Tab>
        <Tab value="messages">
          <UnseenMessageCount TableName="case" :CaseId="caseModel.id">
            <div class="flex align-items-center">
              <span class="material-symbols-outlined">chat_bubble</span>
              <span class="ml-1">Messages</span>
            </div>
          </UnseenMessageCount>
        </Tab>
      </TabList>

    <!-- Tab Panels -->
    <TabPanels>
      <TabPanel value="core">
        <div class="surface-card border-round pt-1 px-2 pb-2 flex-1 ">
          <Suspense>
            <CoreTab :caseId="caseModel.id" :subtab="intakeSubActive" @update:subtab="(v) => (intakeSubActive = v)"/>
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </div>
      </TabPanel>
      <TabPanel value="contacts">
        <div class="surface-card border-round pt-1 px-2 pb-2 flex-1 ">
          <Suspense>
            <ContactsTab :caseId="caseModel.id" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </div>
      </TabPanel>
      <TabPanel value="social">
        <div class="surface-card border-round pt-1 px-2 pb-2 flex-1 ">
          <Suspense>
            <SocialMediaTab :caseId="caseModel.id"  />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </div>
      </TabPanel>
      <TabPanel value="timeline">
        <div class="surface-card border-round p-2 flex-1 ">
          <Suspense>
            <TimelineTab :caseId="caseModel.id"  />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </div>
      </TabPanel>
      <TabPanel value="docs">
        <div class="surface-card border-round pt-1 px-2 pb-2 flex-1 ">
          <Suspense>
            <DocsTab :caseId="caseModel.id" :subtab="docsSubActive" @update:subtab="(v) => (docsSubActive = v)" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </div>
      </TabPanel>
      <TabPanel value="tasks">
        <div class="surface-card border-round p-2 flex-1 ">
          <Suspense>
            <TasksTab :caseId="caseModel.id" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </div>
      </TabPanel>
      <TabPanel value="activity">
        <div class="surface-card border-round p-2 flex-1 ">
          <Suspense>
            <ActivityTab :caseId="caseModel.id" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </div>
      </TabPanel>
      <TabPanel value="messages">
        <div class="surface-card border-round p-2 flex-1 ">
          <Suspense>
            <Messages :caseId="caseModel.id" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </div>
      </TabPanel>
    </TabPanels>
    </Tabs>
  </div>
  <div v-else class="p-3 text-600">
    <ProgressSpinner />
  </div>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; height: 100%; min-height: 0; overflow: hidden; }
:deep(.p-tabs) { display: flex; flex-direction: column; height: 100%; min-height: 0; }
:deep(.p-tabs .p-tabpanels) { flex: 1 1 auto; min-height: 0; overflow: auto; padding-bottom: 0px !important; }


.panel { display: flex; flex-direction: column; height: 100%; }

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
