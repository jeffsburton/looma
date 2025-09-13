<script setup>
import { ref, computed, onMounted, watch, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import Calendar from 'primevue/calendar'
import UnseenMessageCount from '@/components/common/UnseenMessageCount.vue'
import Messages from '@/components/Messages.vue'
import api from '@/lib/api'

const OpsPlansEdit = defineAsyncComponent(() => import('./OpsPlansEdit.vue'))

// Props
const props = defineProps({
  caseId: { type: [String, Number], required: true }
})

// Helpers to safely encode ids in path (mirror FilesTab)
function safeEncode(id) {
  const s = String(id ?? '')
  if (/%[0-9a-fA-F]{2}/.test(s)) return s
  try { return encodeURIComponent(s) } catch { return s }
}
function casePathId(id) {
  const s = String(id ?? '')
  return safeEncode(s)
}

// Data
const loading = ref(false)
const plans = ref([])

// Routing for edit mode
const route = useRoute()
const router = useRouter()
const caseNumber = computed(() => String(route.params.caseNumber || ''))

// People cache for created_by and role selects
const personMap = ref({})
const personOptions = ref([])
const personsLoaded = ref(false)
async function loadPersonsOnce() {
  if (personsLoaded.value) return
  try {
    const { data } = await api.get('/api/v1/persons/select', { params: { shepherds: true, non_shepherds: true } })
    const arr = Array.isArray(data) ? data : []
    const map = {}
    const opts = []
    for (const p of arr) {
      if (p && p.id) {
        map[p.id] = { id: p.id, name: p.name || 'Unknown', photo_url: p.photo_url || '/images/pfp-generic.png' }
        opts.push({ label: p.name || 'Unknown', value: p.id, photo_url: p.photo_url || '/images/pfp-generic.png' })
      }
    }
    personMap.value = map
    personOptions.value = opts
  } finally {
    personsLoaded.value = true
  }
}
function getPerson(oid) { return oid ? (personMap.value[oid] || null) : null }

// Reference options
const opTypeOptions = ref([]) // OP_TYPE
const subjLegalOptions = ref([]) // OP_SUB_LEG
const ynuOptions = ref([]) // YNU
const commsOptions = ref([]) // OP_COMMS
const hospitalOptions = ref([])
const organizationOptions = ref([])

async function loadRef(code, target) {
  try {
    const { data } = await api.get(`/api/v1/reference/${encodeURIComponent(code)}/values`)
    const arr = Array.isArray(data) ? data : []
    target.value = arr.map(rv => ({ label: rv.name || rv.code || '—', value: rv.id }))
  } catch (e) {
    target.value = []
  }
}

async function loadHospitals() {
  try {
    const { data } = await api.get('/api/v1/hospital-ers')
    hospitalOptions.value = (Array.isArray(data) ? data : []).map(er => ({ label: `${er.name}${er.city ? ` — ${er.city}` : ''}`, value: er.id }))
  } catch (e) {
    hospitalOptions.value = []
  }
}

async function loadOrganizations() {
  try {
    const { data } = await api.get('/api/v1/organizations')
    organizationOptions.value = (Array.isArray(data) ? data : []).map(o => ({ label: o.name || '—', value: o.id }))
  } catch (e) {
    organizationOptions.value = []
  }
}

// Load ops plans
async function loadPlans() {
  if (!props.caseId) return
  loading.value = true
  try {
    const { data } = await api.get(`/api/v1/cases/${casePathId(props.caseId)}/ops-plans`)
    plans.value = Array.isArray(data) ? data : []
  } catch (e) {
    plans.value = []
  } finally {
    loading.value = false
  }
}

function onRowExpand(event) {
  const row = event?.data
  if (row) ensureEdit(row)
}

onMounted(async () => {
  await Promise.all([
    loadPersonsOnce(),
    loadRef('OP_TYPE', opTypeOptions),
    loadRef('OP_SUB_LEG', subjLegalOptions),
    loadRef('YNU', ynuOptions),
    loadRef('OP_COMMS', commsOptions),
    loadHospitals(),
    loadOrganizations(),
  ])
  await loadPlans()
})

watch(() => props.caseId, () => { loadPlans() }, { immediate: false })

// When leaving edit mode, reload list
watch(
  () => route.params.rawOpsPlanId,
  (val, oldVal) => {
    if (oldVal && !val) {
      loadPlans()
    }
  }
)

// Editing (existing rows): local copy per expanded row with debounced auto-save
const edits = ref({}) // id -> model copy
function ensureEdit(row) {
  if (!row?.id) return
  const id = row.id
  if (!edits.value[id]) {
    edits.value[id] = { ...row }
  }
}

function resetEdit(row) {
  if (!row?.id) return
  const id = row.id
  edits.value[id] = { ...plans.value.find(p => p.id === id) }
}

const saving = ref({})
const saveTimers = ref({})
const pendingPatches = ref({})

function queueSave(row, patch) {
  if (!row?.id || !props.caseId) return
  const id = row.id
  pendingPatches.value[id] = { ...(pendingPatches.value[id] || {}), ...patch }
  if (saveTimers.value[id]) clearTimeout(saveTimers.value[id])
  saveTimers.value[id] = setTimeout(async () => {
    const payload = pendingPatches.value[id]
    delete pendingPatches.value[id]
    delete saveTimers.value[id]
    if (!payload || Object.keys(payload).length === 0) return
    saving.value[id] = true
    try {
      const { data } = await api.patch(`/api/v1/cases/${casePathId(props.caseId)}/ops-plans/${encodeURIComponent(id)}`, payload)
      const idx = plans.value.findIndex(p => p.id === id)
      if (idx > -1) plans.value[idx] = data
      edits.value[id] = { ...data }
    } catch (e) { /* handled globally */ }
    finally { saving.value[id] = false }
  }, 500)
}

// New Plan creation
const adding = ref(false)
const newPlan = ref({
  date: null,
  team_id: null,
  op_type_id: null,
  op_type_other: '',
  responsible_agency_id: null,
  subject_legal_id: null,
  address: '',
  city: '',
  vehicles: '',
  residence_owner: '',
  threat_dogs_id: null,
  threat_cameras_id: null,
  threat_weapons_id: null,
  threat_drugs_id: null,
  threat_gangs_id: null,
  threat_assault_id: null,
  threat_other: '',
  forecast: '',
  temperature: null,
  humidity: null,
  precipitation: null,
  uv_index: null,
  winds: '',
  briefing_time: null,
  rendevouz_location: '',
  primary_location: '',
  comms_channel_id: null,
  police_phone: null,
  ems_phone: null,
  hospital_er_id: null,
  resp_contact_at_door_id: null,
  resp_overwatch_id: null,
  resp_navigation_id: null,
  resp_communications_id: null,
  resp_safety_id: null,
  resp_medical_id: null,
})

function startAdd() { adding.value = true }
function cancelAdd() { adding.value = false; newPlan.value = { ...newPlan.value, // reset fields
  date: null, team_id: null, op_type_id: null, op_type_other: '', responsible_agency_id: null, subject_legal_id: null,
  address: '', city: '', vehicles: '', residence_owner: '', threat_dogs_id: null, threat_cameras_id: null, threat_weapons_id: null, threat_drugs_id: null, threat_gangs_id: null, threat_assault_id: null, threat_other: '',
  forecast: '', temperature: null, humidity: null, precipitation: null, uv_index: null, winds: '', briefing_time: null, rendevouz_location: '', primary_location: '', comms_channel_id: null,
  police_phone: null, ems_phone: null, hospital_er_id: null, resp_contact_at_door_id: null, resp_overwatch_id: null, resp_navigation_id: null, resp_communications_id: null, resp_safety_id: null, resp_medical_id: null,
} }

async function createPlan() {
  if (!props.caseId) return
  try {
    const payload = { ...newPlan.value }
    const { data } = await api.post(`/api/v1/cases/${casePathId(props.caseId)}/ops-plans`, payload)
    // Prepend or append
    plans.value = [...plans.value, data]
    adding.value = false
    // Optionally expand new row
    expandedRows.value = { ...(expandedRows.value || {}), [data.id]: true }
    // Prepare edit copy for autosave
    edits.value[data.id] = { ...data }
  } catch (e) { /* handled globally */ }
}

// Display helpers
const displayOpType = (row) => {
  const other = String(row?.op_type_other || '').trim()
  if (other) return other
  const id = row?.op_type_id
  if (!id) return '—'
  const opt = (opTypeOptions.value || []).find(o => o.value === id)
  return opt?.label || '—'
}

function openEdit(row) {
  const id = row?.id
  if (!id) return
  const url = `/cases/${encodeURIComponent(String(caseNumber.value))}/docs/ops/${encodeURIComponent(String(id))}`
  console.log('openEdit', url)
  router.push({ path: url })
}
</script>

<template>
  <div class="p-2">
    <template v-if="route.params.rawOpsPlanId">
      <OpsPlansEdit :caseId="String(caseId)" />
    </template>
    <template v-else>
      <!-- Toolbar -->
      <div class="flex align-items-center gap-2 mb-3">
        <div class="ml-auto">
          <Button label="Add" icon="pi pi-plus" @click="() => router.push({ path: `/cases/${encodeURIComponent(String(caseNumber))}/docs/ops/new` })" />
        </div>
      </div>

      <DataTable :value="plans" dataKey="id" size="small" :loading="loading" class="w-full">
        <Column header="" style="width:48px">
          <template #body="{ data }">
            <UnseenMessageCount TableName="ops_plan" :CaseId="caseId" :OpsPlanId="data.id">
              <div class="flex align-items-center">
                <span class="material-symbols-outlined text-900">map_pin_review</span>
              </div>
            </UnseenMessageCount>
          </template>
        </Column>
        <Column header="Created by">
          <template #body="{ data }">
            <div class="flex align-items-center gap-2">
              <img :src="getPerson(data.created_by)?.photo_url || '/images/pfp-generic.png'" alt="pfp" class="avatar-sm" />
              <span class="text-900 font-medium name-clip">{{ getPerson(data.created_by)?.name || 'Unknown' }}</span>
            </div>
          </template>
        </Column>
        <Column header="Date">
          <template #body="{ data }">{{ data.date || '—' }}</template>
        </Column>
        <Column header="Op Type">
          <template #body="{ data }">{{ displayOpType(data) }}</template>
        </Column>
        <Column header="Address">
          <template #body="{ data }">{{ data.address || '—' }}</template>
        </Column>
        <Column header="" style="width:1%">
          <template #body="{ data }">
            <Button icon="pi pi-pencil" text rounded @click.stop="openEdit(data)" />
          </template>
        </Column>
      </DataTable>
    </template>
  </div>
</template>

<style scoped>
.avatar-sm { width: 24px; height: 24px; border-radius: 999px; object-fit: cover; }
.name-clip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
