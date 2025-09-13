<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ref, computed, onMounted } from 'vue'
import api from '../../../lib/api'

import FloatLabel from 'primevue/floatlabel'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import DatePicker from 'primevue/datepicker'
import RefSelect from '../../RefSelect.vue'
import { getLocaleDateFormat } from '../../../lib/util.js'

const route = useRoute()
const router = useRouter()

const caseNumber = computed(() => String(route.params.caseNumber || ''))
const activityId = computed(() => String(route.params.subtab || ''))

const loading = ref(false)
const error = ref('')

const ia = ref({
  id: '',
  date: null,
  what: '',
  source_id: null,
  source_other: '',
  findings: '',
  case_management: '',
  reported_to: null,
  reported_to_other: '',
  on_eod_report: false,
  rule_out: false,
  source_name: '',
  source_code: '',
  reported_to_name: '',
  reported_to_code: '',
})

function goBack() {
  router.replace({ path: `/cases/${encodeURIComponent(caseNumber.value)}/activity` })
}

async function load() {
  if (!caseNumber.value || !activityId.value) return
  loading.value = true
  error.value = ''
  try {
    const url = `/api/v1/cases/${encodeURIComponent(caseNumber.value)}/activity`
    const { data } = await api.get(url)
    const found = (data || []).find((r) => String(r.id) === String(activityId.value))
    if (!found) {
      error.value = 'Activity entry not found.'
      return
    }
    ia.value = { ...found }
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load activity entry.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function patch(payload) {
  if (!caseNumber.value || !activityId.value) return
  try {
    await api.patch(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/activity/${encodeURIComponent(activityId.value)}`, payload)
  } catch (e) {
    console.error(e)
    throw e
  }
}

async function onChangeDate() {
  try {
    await patch({ date: ia.value.date || null })
  } catch (e) {
    error.value = 'Failed to update date.'
  }
}

async function onChangeSource(v) {
  ia.value.source_id = v
  try {
    await patch({ source_id: v })
  } catch (e) {
    error.value = 'Failed to update source.'
  }
}

async function onCommitSourceOther(v) {
  ia.value.source_other = v || ''
  try {
    await patch({ source_other: v || null })
  } catch (e) {
    error.value = 'Failed to update source other.'
  }
}

async function onChangeReportedTo(v) {
  ia.value.reported_to = v
  try {
    await patch({ reported_to: v })
  } catch (e) {
    error.value = 'Failed to update reported to.'
  }
}

async function onCommitReportedToOther(v) {
  ia.value.reported_to_other = v || ''
  try {
    await patch({ reported_to_other: v || null })
  } catch (e) {
    error.value = 'Failed to update reported to other.'
  }
}

async function onBlurWhat() {
  try {
    await patch({ what: ia.value.what || null })
  } catch (e) {
    error.value = 'Failed to update what.'
  }
}

async function onBlurFindings() {
  try {
    await patch({ findings: ia.value.findings || null })
  } catch (e) {
    error.value = 'Failed to update findings.'
  }
}

async function onBlurCaseMgmt() {
  try {
    await patch({ case_management: ia.value.case_management || null })
  } catch (e) {
    error.value = 'Failed to update case management.'
  }
}

async function onToggleEod(v) {
  ia.value.on_eod_report = !!v
  try {
    await patch({ on_eod_report: !!v })
  } catch (e) {
    error.value = 'Failed to update EOD flag.'
  }
}

async function onToggleRuleOut(v) {
  ia.value.rule_out = !!v
  try {
    await patch({ rule_out: !!v })
  } catch (e) {
    error.value = 'Failed to update rule-out.'
  }
}
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center gap-2 mb-3">
      <button class="icon-button" @click="goBack" title="Back">
        <span class="material-symbols-outlined">arrow_back</span>
      </button>
      <div class="text-lg font-semibold">Edit Activity Entry</div>
    </div>
    <div v-if="error" class="p-error mb-2">{{ error }}</div>

    <div class="surface-card border-round p-3">
      <div v-if="loading" class="text-600">Loading...</div>
      <template v-else-if="ia && ia.id">
        <div class="form-grid">
          <div class="field w-12 md:w-2" style="min-width: 10px;max-width: 140px">
            <FloatLabel variant="on">
              <DatePicker :date-format="getLocaleDateFormat()" v-model="ia.date" class="w-full" @change="onChangeDate" />
              <label>Date</label>
            </FloatLabel>
          </div>

          <div class="field" style="min-width: 250px;max-width: 250px">
            <FloatLabel variant="on">
              <RefSelect
                code="ACT_SOURCE"
                v-model="ia.source_id"
                :currentCode="ia.source_code || ''"
                :otherValue="ia.source_other || ''"
                @update:otherValue="(v) => { ia.source_other = v }"
                @otherCommit="onCommitSourceOther"
                @change="onChangeSource"
              />
              <label>Source</label>
            </FloatLabel>
          </div>

          <div class="field" style="min-width: 250px;max-width: 250px">
            <FloatLabel variant="on">
              <RefSelect
                code="ACT_REP"
                v-model="ia.reported_to"
                :currentCode="ia.reported_to_code || ''"
                :otherValue="ia.reported_to_other || ''"
                @update:otherValue="(v) => { ia.reported_to_other = v }"
                @otherCommit="onCommitReportedToOther"
                @change="onChangeReportedTo"
              />
              <label>Reported To</label>
            </FloatLabel>
          </div>

          <div class="field w-12">
            <FloatLabel variant="on" class="w-full">
              <Textarea v-model="ia.what" autoResize rows="2" class="w-full" @blur="onBlurWhat" />
              <label>What</label>
            </FloatLabel>
          </div>

          <div class="field w-12">
            <FloatLabel variant="on" class="w-full">
              <Textarea v-model="ia.findings" autoResize rows="2" class="w-full" @blur="onBlurFindings" />
              <label>Findings</label>
            </FloatLabel>
          </div>

          <div class="field w-12">
            <FloatLabel variant="on" class="w-full">
              <Textarea v-model="ia.case_management" autoResize rows="2" class="w-full" @blur="onBlurCaseMgmt" />
              <label>Case Management</label>
            </FloatLabel>
          </div>

          <div class="field w-12">
            <div class="flex align-items-center gap-3">
              <div class="flex align-items-center gap-2 nowrap">
                <label class="text-sm text-600  text-right" style="max-width: 90px;">On EOD Report</label>
                <ToggleSwitch :modelValue="ia.on_eod_report" @update:modelValue="onToggleEod" />
              </div>
              <div class="flex align-items-center gap-2 nowrap">
                <label class="text-sm text-600  text-right" style="max-width: 70px;">Rule Out</label>
                <ToggleSwitch :modelValue="ia.rule_out" @update:modelValue="onToggleRuleOut" />
              </div>
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
.form-grid { display: flex; flex-wrap: wrap; gap: 0.25rem 0.5rem; }
.field { min-width: 12rem; }
@media (max-width: 640px) { .field { min-width: 100%; } }
</style>
