<script setup>
import { ref, computed, defineAsyncComponent, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'

const props = defineProps({
  caseNumber: { type: [String, Number], required: true },
  tab: { type: String, default: 'core' },
  subtab: { type: String, default: 'intake' },
})

const router = useRouter()
const route = useRoute()

const active = ref('core')
const intakeSubActive = ref('intake')
const filesSubActive = ref('images')
const VALID_TABS = ['core','contacts','social','timeline','files','activity','messages']
const VALID_FILES_SUBTABS = ['images','ops','intel','rfis','eod','flyer','other']

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

// Keep subtab in sync with prop for intake/files based on active tab
watch(
  () => props.subtab,
  (val) => {
    const t = String(props.tab || active.value || 'core')
    let sub = String(val || (t === 'files' ? 'images' : 'intake'))
    if (t === 'files' && !VALID_FILES_SUBTABS.includes(sub)) sub = 'images'
    if (t === 'core') {
      if (intakeSubActive.value !== sub) intakeSubActive.value = sub
    } else if (t === 'files') {
      if (filesSubActive.value !== sub) filesSubActive.value = sub
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
      : (tab === 'files' ? (VALID_FILES_SUBTABS.includes(String(filesSubActive.value)) ? String(filesSubActive.value) : 'images') : undefined)
    const curSub = route.params.subtab ? String(route.params.subtab) : undefined
    // Only update if different to avoid redundant navigations
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

// When files subtab changes, update URL
watch(
  () => filesSubActive.value,
  (v) => {
    if (active.value !== 'files') return
    const caseNumber = String(props.caseNumber || '')
    const tab = 'files'
    const subtab = String(v || 'images')
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

// Models to pass to Intake/Core tabs
const caseModel = ref({})
const subjectModel = ref({})
const demographicsModel = ref({})
const managementModel = ref({})
const patternOfLifeModel = ref({})
const dispositionModel = ref({})

// Keep header subjectName reactive to edits in IntakeTab
watch(subjectModel, (s) => {
  const nicks = s?.nicknames && String(s.nicknames).trim() ? ` "${String(s.nicknames).trim()}"` : ''
  subjectName.value = `${s?.first_name || ''}${nicks} ${s?.last_name || ''}`.trim()
}, { deep: true })

async function loadCase() {
  const num = String(props.caseNumber || '')
  if (!num) return
  try {
    const resp = await fetch(`/api/v1/cases/by-number/${encodeURIComponent(num)}`, { credentials: 'include', headers: { 'Accept': 'application/json' } })
    if (!resp.ok) throw new Error('Failed to load case')
    const data = await resp.json()
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

    // Models for tabs
    const mgmt = data.management || {}
    managementModel.value = {
      consent_sent: !!mgmt.consent_sent,
      consent_returned: !!mgmt.consent_returned,
      flyer_complete: !!mgmt.flyer_complete,
      ottic: !!mgmt.ottic,
      csec_id: mgmt.csec_id ?? null,
      missing_status_id: mgmt.missing_status_id ?? null,
      classification_id: mgmt.classification_id ?? null,
      requested_by_id: mgmt.requested_by_id ?? null,
      csec_code: mgmt.csec_code || '',
      missing_status_code: mgmt.missing_status_code || '',
      classification_code: mgmt.classification_code || '',
      requested_by_code: mgmt.requested_by_code || '',
      ncic_case_number: mgmt.ncic_case_number || '',
      ncmec_case_number: mgmt.ncmec_case_number || '',
      le_case_number: mgmt.le_case_number || '',
      le_24hour_contact: mgmt.le_24hour_contact || '',
      ss_case_number: mgmt.ss_case_number || '',
      ss_24hour_contact: mgmt.ss_24hour_contact || '',
      jpo_case_number: mgmt.jpo_case_number || '',
      jpo_24hour_contact: mgmt.jpo_24hour_contact || '',
    }

    demographicsModel.value = {
      // keep as primitives (Calendar in child will convert date to Date)
      date_of_birth: dem.date_of_birth || null,
      age_when_missing: dem.age_when_missing ?? null,
      height: dem.height || '',
      weight: dem.weight || '',
      hair_color: dem.hair_color || '',
      hair_length: dem.hair_length || '',
      eye_color: dem.eye_color || '',
      identifying_marks: dem.identifying_marks || '',
      sex_id: dem.sex_id ?? '',
      race_id: dem.race_id ?? '',
      sex_code: dem.sex_code || '',
      race_code: dem.race_code || '',
    }

    const pol = data.pattern_of_life || {}
    patternOfLifeModel.value = {
      school: pol.school || '',
      grade: pol.grade || '',
      missing_classes: !!pol.missing_classes,
      school_laptop: !!pol.school_laptop,
      school_laptop_taken: !!pol.school_laptop_taken,
      school_address: pol.school_address || '',
      employed: !!pol.employed,
      employer: pol.employer || '',
      work_hours: pol.work_hours || '',
      employer_address: pol.employer_address || '',
      confidants: pol.confidants || '',
    }

    subjectModel.value = {
      id: s.id || null,
      first_name: s.first_name || '',
      last_name: s.last_name || '',
      middle_name: s.middle_name || '',
      nicknames: s.nicknames || '',
    }
    const c = data.case || {}
    caseModel.value = {
      id: c.id || null,
      subject_id: s.id || null,
      case_number: c.case_number || num,
      date_intake: c.date_intake || null,
      inactive: !!c.inactive,
    }

    const disp = data.disposition || {}
    dispositionModel.value = {
      shepherds_contributed_intel: !!disp.shepherds_contributed_intel,
      date_found: disp.date_found || null,
      scope_id: disp.scope_id ?? null,
      class_id: disp.class_id ?? null,
      status_id: disp.status_id ?? null,
      living_id: disp.living_id ?? null,
      found_by_id: disp.found_by_id ?? null,
      scope_code: disp.scope_code || '',
      class_code: disp.class_code || '',
      status_code: disp.status_code || '',
      living_code: disp.living_code || '',
      found_by_code: disp.found_by_code || '',
    }
    photoError.value = false
  } catch (e) {
    console.error(e)
  }
}

loadCase()

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

// Lazy imports for tab components
import IntakeTab from './tabs/CoreTab.vue'
const ContactsTab = defineAsyncComponent(() => import('./tabs/ContactsTab.vue'))
const SocialMediaTab = defineAsyncComponent(() => import('./tabs/SocialMediaTab.vue'))
const TimelineTab = defineAsyncComponent(() => import('./tabs/TimelineTab.vue'))
import FilesTab from './tabs/FilesTab.vue'
const ActivityTab = defineAsyncComponent(() => import('./tabs/ActivityTab.vue'))
const MessagesTab = defineAsyncComponent(() => import('./tabs/MessagesTab.vue'))

import OverlayBadge from 'primevue/overlaybadge'
import api from '../../lib/api'

const messagesUnseenCount = ref(0)
async function refreshMessagesUnseenCount() {
  try {
    const cid = String(caseModel.value.id || '')
    if (!cid) { messagesUnseenCount.value = 0; return }
    const { data } = await api.get(`/api/v1/cases/${encodeURIComponent(cid)}/messages/unseen_count`)
    messagesUnseenCount.value = Number(data?.count || 0)
  } catch (e) {
    console.error(e)
  }
}

watch(() => caseModel.value.id, () => { refreshMessagesUnseenCount() })
watch(() => active.value, (v) => { if (v === 'messages') refreshMessagesUnseenCount() })
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
    <Tabs :value="active" @update:value="(v) => (active = v)">
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
        <Tab value="files">
          <span class="material-symbols-outlined">folder_open</span>
          <span class="ml-1">Files</span>
        </Tab>
        <Tab value="messages">
          <template v-if="messagesUnseenCount > 0">
            <OverlayBadge :value="String(messagesUnseenCount)">
              <div class="flex align-items-center">
                <span class="material-symbols-outlined">chat_bubble</span>
                <span class="ml-1">Messages</span>
              </div>
            </OverlayBadge>
          </template>
          <template v-else>
            <div class="flex align-items-center">
              <span class="material-symbols-outlined">chat_bubble</span>
              <span class="ml-1">Messages</span>
            </div>
          </template>
        </Tab>
      </TabList>

    <!-- Tab Panels -->
    <TabPanels>
      <TabPanel value="core">
        <div class="surface-card border-round pt-1 px-2 pb-2 flex-1 ">
          <Suspense>
            <IntakeTab
              :subtab="intakeSubActive"
              @update:subtab="(v) => (intakeSubActive = v)"
              v-model:caseModel="caseModel"
              v-model:subjectModel="subjectModel"
              v-model:demographicsModel="demographicsModel"
              v-model:managementModel="managementModel"
              v-model:patternOfLifeModel="patternOfLifeModel"
              v-model:dispositionModel="dispositionModel"
            />
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
            <SocialMediaTab :caseId="caseModel.id" :primarySubject="{ id: subjectModel.id, first_name: subjectModel.first_name, last_name: subjectModel.last_name }" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </div>
      </TabPanel>
      <TabPanel value="timeline">
        <div class="surface-card border-round p-2 flex-1 ">
          <Suspense>
            <TimelineTab :caseId="caseModel.id" :primarySubject="{ id: subjectModel.id, first_name: subjectModel.first_name, last_name: subjectModel.last_name }" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </div>
      </TabPanel>
      <TabPanel value="files">
        <div class="surface-card border-round pt-1 px-2 pb-2 flex-1 ">
          <Suspense>
            <FilesTab :caseId="caseModel.id" :subtab="filesSubActive" @update:subtab="(v) => (filesSubActive = v)" />
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
            <MessagesTab :caseId="caseModel.id" @unseen-count="(n) => (messagesUnseenCount = Number(n||0))" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </div>
      </TabPanel>
    </TabPanels>
    </Tabs>
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
