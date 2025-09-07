<script setup>
import { ref, watch, computed } from 'vue'
import ToggleSwitch from 'primevue/toggleswitch'
import FloatLabel from 'primevue/floatlabel'
import DatePicker from 'primevue/datepicker'
import RefSelect from '../../../RefSelect.vue'
import Fieldset from "primevue/fieldset";

// Props: models for case and disposition (optional to keep backwards compatible)
const props = defineProps({
  caseModel: { type: Object, default: () => ({}) },
  dispositionModel: { type: Object, default: () => ({}) },
  // New: accept caseId so this tab can self-load when used under CoreTab
  caseId: { type: [String, Number], default: '' },
})
const emit = defineEmits(['update:caseModel','update:dispositionModel'])

// Local mirrors
const mCase = ref({ ...(props.caseModel || {}) })
const mDisp = ref({
  shepherds_contributed_intel: !!props.dispositionModel?.shepherds_contributed_intel,
  date_found: props.dispositionModel?.date_found || null,
  scope_id: props.dispositionModel?.scope_id != null ? String(props.dispositionModel.scope_id) : '',
  class_id: props.dispositionModel?.class_id != null ? String(props.dispositionModel.class_id) : '',
  status_id: props.dispositionModel?.status_id != null ? String(props.dispositionModel.status_id) : '',
  living_id: props.dispositionModel?.living_id != null ? String(props.dispositionModel.living_id) : '',
  found_by_id: props.dispositionModel?.found_by_id != null ? String(props.dispositionModel.found_by_id) : '',
  // for code reconciliation if parent provides
  scope_code: props.dispositionModel?.scope_code || '',
  class_code: props.dispositionModel?.class_code || '',
  status_code: props.dispositionModel?.status_code || '',
  living_code: props.dispositionModel?.living_code || '',
  found_by_code: props.dispositionModel?.found_by_code || '',
})

// Date adapter to ensure Date type works with DatePicker (accepts ISO or Date)
function toDateOrNull(v) {
  if (!v) return null
  const d = v instanceof Date ? v : new Date(v)
  return isNaN(d.getTime()) ? null : d
}

const dateFound = computed({
  get(){ return toDateOrNull(mDisp.value?.date_found) },
  set(v){ mDisp.value.date_found = v instanceof Date ? v.toISOString().slice(0,10) : (v || null) }
})

// Sync from props
let syncing = false

// Load initial data when caseId is provided (decoupled mode)
async function loadFromCaseId(id) {
  const cid = String(id || '')
  if (!cid) return
  try {
    syncing = true
    const apiModule = await import('../../../../lib/api')
    const { data } = await apiModule.default.get(`/api/v1/cases/${encodeURIComponent(cid)}/by-id`)
    const c = data?.case || {}
    mCase.value = {
      id: c.id || null,
      subject_id: c.subject_id || null,
      case_number: c.case_number || '',
      date_intake: c.date_intake || null,
      inactive: !!c.inactive,
    }
    const disp = data?.disposition || {}
    mDisp.value = {
      shepherds_contributed_intel: !!disp.shepherds_contributed_intel,
      date_found: disp.date_found || null,
      scope_id: disp.scope_id != null ? String(disp.scope_id) : '',
      class_id: disp.class_id != null ? String(disp.class_id) : '',
      status_id: disp.status_id != null ? String(disp.status_id) : '',
      living_id: disp.living_id != null ? String(disp.living_id) : '',
      found_by_id: disp.found_by_id != null ? String(disp.found_by_id) : '',
      scope_code: disp.scope_code || '',
      class_code: disp.class_code || '',
      status_code: disp.status_code || '',
      living_code: disp.living_code || '',
      found_by_code: disp.found_by_code || '',
    }
  } catch (e) {
    console.error('Failed to load status data by case id', e)
  } finally {
    queueMicrotask(() => { syncing = false })
  }
}

watch(() => props.caseId, (v) => { if (v) loadFromCaseId(v) }, { immediate: true })

watch(() => props.caseModel, (v) => {
  syncing = true
  mCase.value = { ...(v || {}) }
  queueMicrotask(() => { syncing = false })
}, { deep: true })
watch(() => props.dispositionModel, (v) => {
  syncing = true
  const d = v || {}
  mDisp.value = {
    shepherds_contributed_intel: !!d.shepherds_contributed_intel,
    date_found: d.date_found || null,
    scope_id: d.scope_id != null ? String(d.scope_id) : '',
    class_id: d.class_id != null ? String(d.class_id) : '',
    status_id: d.status_id != null ? String(d.status_id) : '',
    living_id: d.living_id != null ? String(d.living_id) : '',
    found_by_id: d.found_by_id != null ? String(d.found_by_id) : '',
    scope_code: d.scope_code || '',
    class_code: d.class_code || '',
    status_code: d.status_code || '',
    living_code: d.living_code || '',
    found_by_code: d.found_by_code || '',
  }
  queueMicrotask(() => { syncing = false })
}, { deep: true })

// Emit up
watch(mCase, (v) => { if (!syncing) emit('update:caseModel', v) }, { deep: true })
watch(mDisp, (v) => { if (!syncing) emit('update:dispositionModel', v) }, { deep: true })
// Exploitation toggles
const exploitOptions = ref([])
const exploitSelected = ref({}) // { opaqueRefId: boolean }
let exploitLoaded = false
let exploitSaveTimer = null

async function loadExploitation() {
  try {
    // load options
    const { getReferenceValues } = await import('../../../../lib/referenceValues')
    const opts = await getReferenceValues('EXPLOIT')
    exploitOptions.value = opts
    // load selected for this case
    const caseId = mCase.value?.id
    if (caseId) {
      try {
        const apiModule = await import('../../../../lib/api')
        const { data } = await apiModule.default.get(`/api/v1/cases/${encodeURIComponent(String(caseId))}/exploitation`)
        const ids = Array.isArray(data)
          ? data
          : (Array.isArray(data?.exploitation_ids) ? data.exploitation_ids : [])
        const codes = Array.isArray(data?.exploitation_codes) ? data.exploitation_codes : []
        const set = {}
        ids.forEach(id => { set[String(id)] = true })
        if (codes.length && Array.isArray(exploitOptions.value) && exploitOptions.value.length) {
          const codeSet = new Set(codes.map(c => String(c).toUpperCase()))
          for (const opt of exploitOptions.value) {
            const c = (opt?.code || '').toString().toUpperCase()
            if (c && codeSet.has(c)) {
              set[String(opt.id)] = true
            }
          }
        }
        exploitSelected.value = set
      } catch (e) {
        console.error('Failed to load exploitation', e)
      }
    }
  } finally {
    exploitLoaded = true
  }
}

watch(mCase, (v) => {
  // reload when switching cases
  exploitLoaded = false
  exploitOptions.value = []
  exploitSelected.value = {}
  if (v?.id) loadExploitation()
}, { deep: true, immediate: true })

function onToggleExploit(id, checked) {
  exploitSelected.value = { ...exploitSelected.value, [String(id)]: !!checked }
  if (exploitSaveTimer) clearTimeout(exploitSaveTimer)
  // do not save until initial load is complete
  if (!exploitLoaded) return
  exploitSaveTimer = setTimeout(saveExploitation, 600)
}

async function saveExploitation() {
  try {
    const caseId = mCase.value?.id
    if (!caseId) return
    const ids = Object.entries(exploitSelected.value)
      .filter(([, on]) => !!on)
      .map(([id]) => id)
    const apiModule = await import('../../../../lib/api')
    await apiModule.default.put(`/api/v1/cases/${encodeURIComponent(String(caseId))}/exploitation`, { exploitation_ids: ids })
  } catch (e) {
    console.error('Failed to save exploitation', e)
  }
}
</script>

<template>
  <div class="p-3">
    <div class="surface-card border-round p-3">
      <div class="row row-2">
        <div class="flex align-items-center gap-2">
          <ToggleSwitch :inputId="'shep-intel'" v-model="mDisp.shepherds_contributed_intel" />
          <label for="shep-intel">Shepherds Contributed Intel</label>
        </div>
        <div class="flex align-items-center gap-2">
          <ToggleSwitch :inputId="'case-inactive'" v-model="mCase.inactive" />
          <label for="case-inactive">Case Archived</label>
        </div>
      </div>

      <div class="row row-3 mt-2">
        <div>
          <FloatLabel variant="on">
            <DatePicker id="date-found" v-model="dateFound" date-format="yy-mm-dd" showIcon iconDisplay="input" class="w-full" />
            <label for="date-found">Date Found</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <RefSelect id="scope" code="SCOPE" v-model="mDisp.scope_id" :currentCode="mDisp.scope_code" />
            <label for="scope">Geographic Scope</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <RefSelect id="class" code="CASE_CLASS" v-model="mDisp.class_id" :currentCode="mDisp.class_code" />
            <label for="class">Case Classification</label>
          </FloatLabel>
        </div>
      </div>

      <div class="row row-3">
        <div>
          <FloatLabel variant="on">
            <RefSelect id="status" code="STATUS" v-model="mDisp.status_id" :currentCode="mDisp.status_code" />
            <label for="status">Case Status</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <RefSelect id="living" code="LIVING" v-model="mDisp.living_id" :currentCode="mDisp.living_code" />
            <label for="living">Victim Living</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <RefSelect id="found-by" code="FOUND_BY" v-model="mDisp.found_by_id" :currentCode="mDisp.found_by_code" />
            <label for="found-by">Found By</label>
          </FloatLabel>
        </div>
      </div>

      <div class="row row-1">
        <div>
          <Fieldset legend="Exploitation">
              <div v-for="opt in exploitOptions" :key="String(opt.id)" class="flex align-items-center gap-2 mb-2">
                <ToggleSwitch :inputId="`exp-${opt.id}`" :modelValue="!!exploitSelected[String(opt.id)]" @update:modelValue="(v) => onToggleExploit(opt.id, v)" />
                <label :for="`exp-${opt.id}`">{{ opt.name }}<span v-if="opt.code" class="text-600 ml-1">({{ opt.code }})</span></label>
              </div>
          </Fieldset>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.row { display: grid; gap: 1rem; margin-bottom: 1rem; grid-template-columns: 1fr; }
@media (min-width: 700px) {
  .row-1 { grid-template-columns: 1fr; }
  .row-2 { grid-template-columns: repeat(2, 1fr); }
  .row-3 { grid-template-columns: repeat(3, 1fr); }
  .row-4 { grid-template-columns: repeat(4, 1fr); }
}
</style>
