<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import api from '../../../lib/api'

import ToggleSwitch from 'primevue/toggleswitch'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import DatePicker from 'primevue/datepicker'

import PersonSelect from '../../PersonSelect.vue'
import RefSelect from '../../RefSelect.vue'
import { getLocaleDateFormat } from '../../../lib/util.js'

const route = useRoute()
const router = useRouter()

const caseNumber = computed(() => String(route.params.caseNumber || ''))
const timelineId = computed(() => String(route.params.subtab || ''))

const loading = ref(false)
const error = ref('')

const row = ref({
  id: '',
  date: null,
  time: null,
  who_id: null,
  who_name: null,
  where: '',
  details: '',
  rule_out: false,
  type_id: null,
  type_other: '',
  type_name: '',
  type_code: '',
  comments: '',
  questions: '',
})

function goBack() {
  router.replace({ path: `/cases/${encodeURIComponent(caseNumber.value)}/timeline` })
}

async function load() {
  if (!caseNumber.value || !timelineId.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/timeline`)
    const found = (data || []).find(r => String(r.id) === String(timelineId.value))
    if (!found) {
      error.value = 'Timeline item not found.'
      return
    }
    row.value = { ...found }
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load timeline item.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function fmtDate(val) {
  if (val == null || val === '') return null
  if (typeof val === 'string') return val
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return null
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  } catch { return null }
}
function fmtTime(val) {
  if (val == null || val === '') return null
  if (typeof val === 'string') return val
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return null
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    const ss = String(d.getSeconds()).padStart(2, '0')
    return `${hh}:${mm}:${ss}`
  } catch { return null }
}

async function patch(patch) {
  if (!timelineId.value || !caseNumber.value) return
  try {
    const payload = { ...patch }
    if (Object.prototype.hasOwnProperty.call(payload, 'date')) {
      payload.date = fmtDate(payload.date)
    }
    if (Object.prototype.hasOwnProperty.call(payload, 'time')) {
      payload.time = fmtTime(payload.time)
    }
    await api.patch(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/timeline/${encodeURIComponent(timelineId.value)}`, payload)
  } catch (e) {
    console.error(e)
    error.value = 'Failed to save changes.'
  }
}

async function onUpdateDate(v) {
  row.value.date = v || null
  await patch({ date: v || null })
}
async function onUpdateTime(v) {
  row.value.time = v || null
  await patch({ time: v || null })
}
async function onChangeWho(v) {
  row.value.who_id = v || null
  await patch({ who_id: v || null })
}
async function onChangeWhere() {
  await patch({ where: row.value.where || null })
}
async function onChangeType(v) {
  row.value.type_id = v || null
  await patch({ type_id: v || null })
}
async function onCommitTypeOther(v) {
  row.value.type_other = v || ''
  await patch({ type_other: v || null })
}
async function onChangeDetails() {
  await patch({ details: row.value.details || null })
}
async function onChangeComments() {
  await patch({ comments: row.value.comments || null })
}
async function onChangeQuestions() {
  await patch({ questions: row.value.questions || null })
}
async function onToggleRuleOut(v) {
  row.value.rule_out = !!v
  await patch({ rule_out: !!v })
}
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center gap-2 mb-3">
      <button class="icon-button" @click="goBack" title="Back">
        <span class="material-symbols-outlined">arrow_back</span>
      </button>
      <div class="text-lg font-semibold">Edit Timeline Item</div>
    </div>

    <div v-if="error" class="p-error mb-2">{{ error }}</div>
    <div class="surface-card border-round p-3">
      <div v-if="loading" class="text-600">Loading...</div>
      <template v-else-if="row && row.id">
        <div class="form-grid">
          <FloatLabel variant="on" class="field" style="max-width: 160px;">
            <DatePicker v-model="row.date" :date-format="getLocaleDateFormat()" @update:modelValue="onUpdateDate" />
            <label>Date</label>
          </FloatLabel>

          <FloatLabel variant="on" class="field" style="max-width: 160px;">
            <DatePicker v-model="row.time" timeOnly hourFormat="24" showTime @update:modelValue="onUpdateTime" />
            <label>Time</label>
          </FloatLabel>

          <FloatLabel variant="on" class="field" style="max-width: 280px;">
            <PersonSelect v-model="row.who_id" :caseNumber="caseNumber" :addButton="false" :filter="false" @change="onChangeWho" />
            <label>Who</label>
          </FloatLabel>

          <FloatLabel variant="on" class="field w-12">
            <Textarea v-model="row.where" class="w-full" @change="onChangeWhere" />
            <label>Where</label>
          </FloatLabel>

          <FloatLabel variant="on" class="field" style="max-width: 220px;">
            <RefSelect
              code="TL_TYPE"
              v-model="row.type_id"
              :currentCode="row.type_code || ''"
              :otherValue="row.type_other || ''"
              @update:otherValue="(v) => { row.type_other = v }"
              @otherCommit="onCommitTypeOther"
              @change="onChangeType"
            />
            <label>Type</label>
          </FloatLabel>

          <FloatLabel variant="on" class="field w-12">
            <Textarea v-model="row.details" class="w-full" @change="onChangeDetails" />
            <label>Details</label>
          </FloatLabel>

          <FloatLabel variant="on" class="field w-12">
            <Textarea v-model="row.comments" class="w-full" @change="onChangeComments" />
            <label>Comments</label>
          </FloatLabel>

          <FloatLabel variant="on" class="field w-12">
            <Textarea v-model="row.questions" class="w-full" @change="onChangeQuestions" />
            <label>Questions</label>
          </FloatLabel>

          <div class="field">
            <div class="flex align-items-center gap-2 nowrap">
              <label class="text-sm text-600">Rule Out</label>
              <ToggleSwitch :modelValue="row.rule_out" @update:modelValue="onToggleRuleOut" />
            </div>
          </div>
        </div>
      </template>
      <div v-else class="p-2 text-600">Not found</div>
    </div>
  </div>
</template>

<style scoped>
.icon-button { background: transparent; border: none; padding: .25rem; cursor: pointer; border-radius: 4px; }
.icon-button:hover { background: rgba(0,0,0,0.04); }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.field { display: flex; flex-direction: column; }
@media (max-width: 768px) { .form-grid { grid-template-columns: 1fr; } }
</style>
