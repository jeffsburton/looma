<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import api from '@/lib/api'
import FloatLabel from 'primevue/floatlabel'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Calendar from 'primevue/calendar'
import Messages from '@/components/Messages.vue'

const route = useRoute()
const router = useRouter()

const props = defineProps({
  caseId: { type: [String, Number], required: true },
})

// Helpers to safely encode ids in path (mirror FilesTab/TasksEdit)
function safeEncode(id) {
  const s = String(id ?? '')
  if (/%[0-9a-fA-F]{2}/.test(s)) return s
  try { return encodeURIComponent(s) } catch { return s }
}
function casePathId(id) {
  const s = String(id ?? '')
  return safeEncode(s)
}

const caseNumber = computed(() => String(route.params.caseNumber || ''))
const rawOpsPlanId = computed(() => String(route.params.rawOpsPlanId || ''))
const isCreate = computed(() => rawOpsPlanId.value === 'new')

const loading = ref(false)
const saving = ref(false)
const error = ref('')

// Reference options and people (mirrors OpsPlansTab)
const opTypeOptions = ref([]) // OP_TYPE
const subjLegalOptions = ref([]) // OP_SUB_LEG
const ynuOptions = ref([]) // YNU
const commsOptions = ref([]) // OP_COMMS
const hospitalOptions = ref([])
const organizationOptions = ref([])

const personOptions = ref([])

async function loadPersonsOnce() {
  try {
    const { data } = await api.get('/api/v1/persons/select', { params: { shepherds: true, non_shepherds: true } })
    const arr = Array.isArray(data) ? data : []
    personOptions.value = arr.map(p => ({ label: p.name || 'Unknown', value: p.id, photo_url: p.photo_url || '/images/pfp-generic.png' }))
  } catch (_) {
    personOptions.value = []
  }
}

async function loadRef(code, target) {
  try {
    const { data } = await api.get(`/api/v1/reference/${encodeURIComponent(code)}/values`)
    const arr = Array.isArray(data) ? data : []
    target.value = arr.map(rv => ({ label: rv.name || rv.code || '—', value: rv.id }))
  } catch (_) {
    target.value = []
  }
}

async function loadHospitals() {
  try {
    const { data } = await api.get('/api/v1/hospital-ers')
    hospitalOptions.value = (Array.isArray(data) ? data : []).map(er => ({ label: `${er.name}${er.city ? ` — ${er.city}` : ''}`, value: er.id }))
  } catch (_) {
    hospitalOptions.value = []
  }
}

async function loadOrganizations() {
  try {
    const { data } = await api.get('/api/v1/organizations')
    organizationOptions.value = (Array.isArray(data) ? data : []).map(o => ({ label: o.name || '—', value: o.id }))
  } catch (_) {
    organizationOptions.value = []
  }
}

// Form model (mirrors OpsPlansTab's fields)
const form = ref({
  id: '',
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

function goBack() {
  router.replace({ name: 'case-detail', params: { caseNumber: caseNumber.value, tab: 'docs' } })
}

async function loadExisting() {
  if (isCreate.value) return
  if (!rawOpsPlanId.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/api/v1/cases/${casePathId(caseNumber.value)}/ops-plans/${encodeURIComponent(rawOpsPlanId.value)}`)
    const r = data || {}
    form.value = { ...form.value, ...r, id: r.id }
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load ops plan.'
  } finally {
    loading.value = false
  }
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
    loadExisting(),
  ])
})

async function onCreateSave() {
  error.value = ''
  saving.value = true
  try {
    const payload = { ...form.value }
    delete payload.id
    const { data } = await api.post(`/api/v1/cases/${casePathId(caseNumber.value)}/ops-plans`, payload)
    // After create, go back to list
    goBack()
  } catch (e) {
    console.error(e)
    error.value = 'Failed to create ops plan.'
  } finally {
    saving.value = false
  }
}

async function patch(payload) {
  if (!form.value.id) return
  try {
    await api.patch(`/api/v1/cases/${casePathId(caseNumber.value)}/ops-plans/${encodeURIComponent(form.value.id)}`, payload)
  } catch (e) {
    console.error(e)
    error.value = 'Failed to update ops plan.'
    throw e
  }
}

function onFieldChange(field, value) {
  form.value[field] = value
  if (!isCreate.value) {
    // Save on change for existing records
    patch({ [field]: value }).catch(() => {})
  }
}
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center gap-2 mb-3">
      <button class="icon-button" @click="goBack" title="Back">
        <span class="material-symbols-outlined">arrow_back</span>
      </button>
      <div class="text-lg font-semibold">{{ isCreate ? 'Add Ops Plan' : 'Edit Ops Plan' }}</div>
    </div>

    <div v-if="error" class="p-error mb-2">{{ error }}</div>

    <div class="surface-card border-round p-3">
      <div v-if="loading && !isCreate" class="text-600">Loading...</div>
      <template v-else>
        <div class="grid formgrid p-fluid gap-3">
          <!-- Date & Team -->
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <Calendar id="date" v-model="form.date" class="w-full" dateFormat="yy-mm-dd" @update:modelValue="v => onFieldChange('date', v)" />
              <label for="date">Date</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <InputText id="team_id" v-model="form.team_id" class="w-full" @update:modelValue="v => onFieldChange('team_id', v)" />
              <label for="team_id">Team (id)</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <Select id="op_type_id" v-model="form.op_type_id" :options="opTypeOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => onFieldChange('op_type_id', v)" />
              <label for="op_type_id">Operation Type</label>
            </FloatLabel>
          </div>

          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <InputText id="op_type_other" v-model="form.op_type_other" class="w-full" @update:modelValue="v => onFieldChange('op_type_other', v)" />
              <label for="op_type_other">Op Type (other)</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <Select id="responsible_agency_id" v-model="form.responsible_agency_id" :options="organizationOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => onFieldChange('responsible_agency_id', v)" />
              <label for="responsible_agency_id">Responsible Agency</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <Select id="subject_legal_id" v-model="form.subject_legal_id" :options="subjLegalOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => onFieldChange('subject_legal_id', v)" />
              <label for="subject_legal_id">Subject Legal</label>
            </FloatLabel>
          </div>

          <!-- Locations -->
          <div class="col-12 md:col-6">
            <FloatLabel variant="on" class="w-full">
              <Textarea id="address" v-model="form.address" class="w-full" autoResize rows="2" @update:modelValue="v => onFieldChange('address', v)" />
              <label for="address">Address</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-6">
            <FloatLabel variant="on" class="w-full">
              <InputText id="city" v-model="form.city" class="w-full" @update:modelValue="v => onFieldChange('city', v)" />
              <label for="city">City</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-6">
            <FloatLabel variant="on" class="w-full">
              <Textarea id="vehicles" v-model="form.vehicles" class="w-full" autoResize rows="2" @update:modelValue="v => onFieldChange('vehicles', v)" />
              <label for="vehicles">Vehicles</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-6">
            <FloatLabel variant="on" class="w-full">
              <InputText id="residence_owner" v-model="form.residence_owner" class="w-full" @update:modelValue="v => onFieldChange('residence_owner', v)" />
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
          ]" :key="'thr-' + idx">
            <FloatLabel variant="on" class="w-full">
              <Select :id="field[0]" v-model="form[field[0]]" :options="ynuOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => onFieldChange(field[0], v)" />
              <label :for="field[0]">Threat: {{ field[1] }}</label>
            </FloatLabel>
          </div>
          <div class="col-12">
            <FloatLabel variant="on" class="w-full">
              <Textarea id="threat_other" v-model="form.threat_other" class="w-full" autoResize rows="2" @update:modelValue="v => onFieldChange('threat_other', v)" />
              <label for="threat_other">Threat (other)</label>
            </FloatLabel>
          </div>

          <!-- Forecast -->
          <div class="col-12 md:col-12">
            <FloatLabel variant="on" class="w-full">
              <Textarea id="forecast" v-model="form.forecast" class="w-full" autoResize rows="2" @update:modelValue="v => onFieldChange('forecast', v)" />
              <label for="forecast">Forecast</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-3" v-for="(field, idx) in [
            ['temperature','Temperature'], ['humidity','Humidity'], ['precipitation','Precipitation'], ['uv_index','UV Index']
          ]" :key="'wx-' + idx">
            <FloatLabel variant="on" class="w-full">
              <InputText :id="field[0]" v-model="form[field[0]]" class="w-full" @update:modelValue="v => onFieldChange(field[0], v)" />
              <label :for="field[0]">{{ field[1] }}</label>
            </FloatLabel>
          </div>
          <div class="col-12">
            <FloatLabel variant="on" class="w-full">
              <Textarea id="winds" v-model="form.winds" class="w-full" autoResize rows="2" @update:modelValue="v => onFieldChange('winds', v)" />
              <label for="winds">Winds</label>
            </FloatLabel>
          </div>

          <!-- Briefing / Locations / Comms -->
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <InputText id="briefing_time" v-model="form.briefing_time" class="w-full" @update:modelValue="v => onFieldChange('briefing_time', v)" />
              <label for="briefing_time">Briefing Time (HH:MM:SS)</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <Textarea id="rendevouz_location" v-model="form.rendevouz_location" class="w-full" autoResize rows="2" @update:modelValue="v => onFieldChange('rendevouz_location', v)" />
              <label for="rendevouz_location">Rendezvous Location</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <Textarea id="primary_location" v-model="form.primary_location" class="w-full" autoResize rows="2" @update:modelValue="v => onFieldChange('primary_location', v)" />
              <label for="primary_location">Primary Location</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <Select id="comms_channel_id" v-model="form.comms_channel_id" :options="commsOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => onFieldChange('comms_channel_id', v)" />
              <label for="comms_channel_id">Comms Channel</label>
            </FloatLabel>
          </div>

          <!-- Emergency -->
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <InputText id="police_phone" v-model="form.police_phone" class="w-full" @update:modelValue="v => onFieldChange('police_phone', v)" />
              <label for="police_phone">Police Phone</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <InputText id="ems_phone" v-model="form.ems_phone" class="w-full" @update:modelValue="v => onFieldChange('ems_phone', v)" />
              <label for="ems_phone">EMS Phone</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-4">
            <FloatLabel variant="on" class="w-full">
              <Select id="hospital_er_id" v-model="form.hospital_er_id" :options="hospitalOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => onFieldChange('hospital_er_id', v)" />
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
              <Select :id="field[0]" v-model="form[field[0]]" :options="personOptions" optionLabel="label" optionValue="value" class="w-full" @update:modelValue="v => onFieldChange(field[0], v)" />
              <label :for="field[0]">Responsible: {{ field[1] }}</label>
            </FloatLabel>
          </div>
        </div>

        <div v-if="isCreate" class="flex justify-content-end gap-2 mt-3">
          <button class="p-button p-component p-button-text" type="button" @click="goBack"><span class="p-button-label">Cancel</span></button>
          <button class="p-button p-component" type="button" @click="onCreateSave" :disabled="saving"><span class="p-button-icon pi pi-check mr-1"></span><span class="p-button-label">Save</span></button>
        </div>

        <div v-else class="mt-3">
          <p class="text-600 mb-2">Ask questions or add updates related to this ops plan:</p>
          <Messages :caseId="props.caseId" filterByFieldName="ops_plan_id" :filterByFieldId="form.id" />
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.icon-button { background: transparent; border: none; padding: .25rem; cursor: pointer; border-radius: 4px; }
.icon-button:hover { background: rgba(0,0,0,0.04); }
</style>
