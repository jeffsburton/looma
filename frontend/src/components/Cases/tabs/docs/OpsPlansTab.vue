<script setup>
import { ref, computed, onMounted, watch } from 'vue'
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
const expandedRows = ref({})

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

watch(() => props.caseId, () => { loadPlans() })

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
</script>

<template>
  <div class="p-2">
    <!-- Toolbar -->
    <div class="flex align-items-center gap-2 mb-3">
      <div class="ml-auto">
        <Button label="Add" icon="pi pi-plus" @click="startAdd" />
      </div>
    </div>

    <!-- New Plan form (Save/Cancel only visible for new records) -->
    <div v-if="adding" class="surface-card p-3 border-1 surface-border border-round mb-3">
      <div class="grid formgrid p-fluid gap-3">
        <div class="col-12 md:col-3">
          <FloatLabel variant="on" class="w-full">
            <Calendar id="new_date" v-model="newPlan.date" class="w-full" dateFormat="yy-mm-dd" />
            <label for="new_date">Date</label>
          </FloatLabel>
        </div>
        <div class="col-12 md:col-3">
          <FloatLabel variant="on" class="w-full">
            <Select id="new_op_type_id" v-model="newPlan.op_type_id" :options="opTypeOptions" optionLabel="label" optionValue="value" class="w-full" />
            <label for="new_op_type_id">Operation Type</label>
          </FloatLabel>
        </div>
        <div class="col-12 md:col-3">
          <FloatLabel variant="on" class="w-full">
            <Select id="new_responsible_agency_id" v-model="newPlan.responsible_agency_id" :options="organizationOptions" optionLabel="label" optionValue="value" class="w-full" />
            <label for="new_responsible_agency_id">Responsible Agency</label>
          </FloatLabel>
        </div>
        <div class="col-12 md:col-3">
          <FloatLabel variant="on" class="w-full">
            <InputText id="new_city" v-model="newPlan.city" class="w-full" />
            <label for="new_city">City</label>
          </FloatLabel>
        </div>
        <div class="col-12">
          <FloatLabel variant="on" class="w-full">
            <Textarea id="new_address" v-model="newPlan.address" class="w-full" autoResize rows="2" />
            <label for="new_address">Address</label>
          </FloatLabel>
        </div>
      </div>
      <div class="flex gap-2 justify-content-end mt-2">
        <Button label="Cancel" text @click="cancelAdd" />
        <Button label="Save" icon="pi pi-check" @click="createPlan" />
      </div>
    </div>

    <DataTable :value="plans" dataKey="id" v-model:expandedRows="expandedRows" size="small"  :loading="loading" class="w-full" @rowExpand="onRowExpand">
      <Column expander style="width:3rem" />
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

      <template #expansion="{ data }">
        <div class="surface-card p-3 border-1 surface-border border-round mb-2">
          <div class="grid formgrid p-fluid gap-3">
            <!-- Date & Team -->
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <Calendar id="date" v-model="edits[data.id].date" class="w-full" dateFormat="yy-mm-dd" @update:modelValue="v => queueSave(data, { date: v })" />
                <label for="date">Date</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <InputText id="team_id" v-model="edits[data.id].team_id" class="w-full" @update:modelValue="v => queueSave(data, { team_id: v })" />
                <label for="team_id">Team (id)</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <Select id="op_type_id" v-model="edits[data.id].op_type_id" :options="opTypeOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => queueSave(data, { op_type_id: v })"/>
                <label for="op_type_id">Operation Type</label>
              </FloatLabel>
            </div>

            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <InputText id="op_type_other" v-model="edits[data.id].op_type_other" class="w-full" @update:modelValue="v => queueSave(data, { op_type_other: v })" />
                <label for="op_type_other">Op Type (other)</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <Select id="responsible_agency_id" v-model="edits[data.id].responsible_agency_id" :options="organizationOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => queueSave(data, { responsible_agency_id: v })" />
                <label for="responsible_agency_id">Responsible Agency</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <Select id="subject_legal_id" v-model="edits[data.id].subject_legal_id" :options="subjLegalOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => queueSave(data, { subject_legal_id: v })"/>
                <label for="subject_legal_id">Subject Legal</label>
              </FloatLabel>
            </div>

            <!-- Locations -->
            <div class="col-12 md:col-6">
              <FloatLabel variant="on" class="w-full">
                <Textarea id="address" v-model="edits[data.id].address" class="w-full" autoResize rows="2" @update:modelValue="v => queueSave(data, { address: v })" />
                <label for="address">Address</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-6">
              <FloatLabel variant="on" class="w-full">
                <InputText id="city" v-model="edits[data.id].city" class="w-full" @update:modelValue="v => queueSave(data, { city: v })" />
                <label for="city">City</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-6">
              <FloatLabel variant="on" class="w-full">
                <Textarea id="vehicles" v-model="edits[data.id].vehicles" class="w-full" autoResize rows="2" @update:modelValue="v => queueSave(data, { vehicles: v })" />
                <label for="vehicles">Vehicles</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-6">
              <FloatLabel variant="on" class="w-full">
                <InputText id="residence_owner" v-model="edits[data.id].residence_owner" class="w-full" @update:modelValue="v => queueSave(data, { residence_owner: v })" />
                <label for="residence_owner">Residence Owner</label>
              </FloatLabel>
            </div>

            <!-- Threats -->
            <div class="col-12 md:col-2" v-for="(field, idx) in [
              ['threat_dogs_id','Dogs'],
              ['threat_cameras_id','Cameras'],
              ['threat_weapons_id','Weapons'],
              ['threat_drugs_id','Drugs'],
              ['threat_gangs_id','Gangs'],
              ['threat_assault_id','Assault'],
            ]" :key="idx">
              <FloatLabel variant="on" class="w-full">
                <Select :id="field[0]" v-model="edits[data.id][field[0]]" :options="ynuOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => queueSave(data, { [field[0]]: v })"/>
                <label :for="field[0]">Threat: {{ field[1] }}</label>
              </FloatLabel>
            </div>
            <div class="col-12">
              <FloatLabel variant="on" class="w-full">
                <Textarea id="threat_other" v-model="edits[data.id].threat_other" class="w-full" autoResize rows="2" @update:modelValue="v => queueSave(data, { threat_other: v })" />
                <label for="threat_other">Threat (other)</label>
              </FloatLabel>
            </div>

            <!-- Forecast -->
            <div class="col-12 md:col-12">
              <FloatLabel variant="on" class="w-full">
                <Textarea id="forecast" v-model="edits[data.id].forecast" class="w-full" autoResize rows="2" @update:modelValue="v => queueSave(data, { forecast: v })" />
                <label for="forecast">Forecast</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-3" v-for="(field, idx) in [
              ['temperature','Temperature'], ['humidity','Humidity'], ['precipitation','Precipitation'], ['uv_index','UV Index']
            ]" :key="'wx-' + idx">
              <FloatLabel variant="on" class="w-full">
                <InputText :id="field[0]" v-model="edits[data.id][field[0]]" class="w-full" @update:modelValue="v => queueSave(data, { [field[0]]: v })" />
                <label :for="field[0]">{{ field[1] }}</label>
              </FloatLabel>
            </div>
            <div class="col-12">
              <FloatLabel variant="on" class="w-full">
                <Textarea id="winds" v-model="edits[data.id].winds" class="w-full" autoResize rows="2" @update:modelValue="v => queueSave(data, { winds: v })" />
                <label for="winds">Winds</label>
              </FloatLabel>
            </div>

            <!-- Briefing / Locations / Comms -->
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <InputText id="briefing_time" v-model="edits[data.id].briefing_time" class="w-full" @update:modelValue="v => queueSave(data, { briefing_time: v })" />
                <label for="briefing_time">Briefing Time (HH:MM:SS)</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <Textarea id="rendevouz_location" v-model="edits[data.id].rendevouz_location" class="w-full" autoResize rows="2" @update:modelValue="v => queueSave(data, { rendevouz_location: v })" />
                <label for="rendevouz_location">Rendezvous Location</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <Textarea id="primary_location" v-model="edits[data.id].primary_location" class="w-full" autoResize rows="2" @update:modelValue="v => queueSave(data, { primary_location: v })" />
                <label for="primary_location">Primary Location</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <Select id="comms_channel_id" v-model="edits[data.id].comms_channel_id" :options="commsOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => queueSave(data, { comms_channel_id: v })"/>
                <label for="comms_channel_id">Comms Channel</label>
              </FloatLabel>
            </div>

            <!-- Emergency -->
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <InputText id="police_phone" v-model="edits[data.id].police_phone" class="w-full" @update:modelValue="v => queueSave(data, { police_phone: v })" />
                <label for="police_phone">Police Phone</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <InputText id="ems_phone" v-model="edits[data.id].ems_phone" class="w-full" @update:modelValue="v => queueSave(data, { ems_phone: v })" />
                <label for="ems_phone">EMS Phone</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-4">
              <FloatLabel variant="on" class="w-full">
                <Select id="hospital_er_id" v-model="edits[data.id].hospital_er_id" :options="hospitalOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => queueSave(data, { hospital_er_id: v })"/>
                <label for="hospital_er_id">Hospital ER</label>
              </FloatLabel>
            </div>

            <!-- Responsible roles -->
            <div class="col-12 md:col-4" v-for="(field, idx) in [
              ['resp_contact_at_door_id','Contact at Door'],
              ['resp_overwatch_id','Overwatch'],
              ['resp_navigation_id','Navigation'],
              ['resp_communications_id','Communications'],
              ['resp_safety_id','Safety'],
              ['resp_medical_id','Medical'],
            ]" :key="'resp-' + idx">
              <FloatLabel variant="on" class="w-full">
                <Select :id="field[0]" v-model="edits[data.id][field[0]]" :options="personOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => queueSave(data, { [field[0]]: v })"/>
                <label :for="field[0]">Responsible: {{ field[1] }}</label>
              </FloatLabel>
            </div>
          </div>

          <div class="flex justify-content-end mt-2 text-600 text-sm">
            <span v-if="saving[data.id]">Saving…</span>
          </div>

          <!-- Messages for this Ops Plan -->
          <div class="mt-3">
            <p class="text-600 mb-2">Ask questions or add updates related to this ops plan:</p>
            <Messages :caseId="caseId" filterByFieldName="ops_plan_id" :filterByFieldId="data.id" />
          </div>
        </div>
      </template>
    </DataTable>
  </div>
</template>

<style scoped>
.avatar-sm { width: 24px; height: 24px; border-radius: 999px; object-fit: cover; }
.name-clip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
