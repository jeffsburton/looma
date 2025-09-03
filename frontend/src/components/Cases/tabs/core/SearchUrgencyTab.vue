<script setup>
import { ref, watch, computed } from 'vue'
import Fieldset from 'primevue/fieldset'
import FloatLabel from 'primevue/floatlabel'
import RefSelect from '../../../RefSelect.vue'

const props = defineProps({
  caseId: { type: String, default: '' },
})

// Local model stores opaque ref_value ids for each category
const m = ref({
  age_id: '',
  physical_condition_id: '',
  medical_condition_id: '',
  personal_risk_id: '',
  online_risk_id: '',
  family_risk_id: '',
  behavioral_risk_id: '',
})

const serverScore = ref(null) // last score saved on server
let hydrated = false
let saveTimer = null

// Reference value maps for sort_order lookups by opaque id
const sortMaps = ref({ SU_AGE: {}, SU_FIT: {}, SU_MED: {}, SU_RISK: {}, SU_ONL: {}, SU_FAM: {}, SU_BE: {} })

async function loadSortMap(code) {
  const resp = await fetch(`/api/v1/reference/${encodeURIComponent(code)}/values`, { headers: { 'Accept': 'application/json' } })
  if (!resp.ok) return
  const data = await resp.json()
  const map = {}
  for (const o of data) {
    map[String(o.id)] = o.sort_order != null ? Number(o.sort_order) : 0
  }
  sortMaps.value[code] = map
}

async function loadAllSortMaps() {
  await Promise.all([
    loadSortMap('SU_AGE'),
    loadSortMap('SU_FIT'),
    loadSortMap('SU_MED'),
    loadSortMap('SU_RISK'),
    loadSortMap('SU_ONL'),
    loadSortMap('SU_FAM'),
    loadSortMap('SU_BE'),
  ])
}

function sumOrNull(vals) {
  return vals.every(v => typeof v === 'number') ? vals.reduce((a,b)=>a+b,0) : null
}

const localScore = computed(() => {
  // Compute using sort_order values of current selections; if any missing map or selection, return null
  const age = sortMaps.value.SU_AGE[String(m.value.age_id)]
  const fit = sortMaps.value.SU_FIT[String(m.value.physical_condition_id)]
  const med = sortMaps.value.SU_MED[String(m.value.medical_condition_id)]
  const prs = sortMaps.value.SU_RISK[String(m.value.personal_risk_id)]
  const onl = sortMaps.value.SU_ONL[String(m.value.online_risk_id)]
  const fam = sortMaps.value.SU_FAM[String(m.value.family_risk_id)]
  const beh = sortMaps.value.SU_BE[String(m.value.behavioral_risk_id)]
  const vals = [age, fit, med, prs, onl, fam, beh]
  if (vals.some(v => v === undefined)) return null
  return sumOrNull(vals.map(v => (typeof v === 'number' ? v : 0)))
})

const complete = computed(() => [
  m.value.age_id,
  m.value.physical_condition_id,
  m.value.medical_condition_id,
  m.value.personal_risk_id,
  m.value.online_risk_id,
  m.value.family_risk_id,
  m.value.behavioral_risk_id,
].every(v => !!v))

const displayScore = computed(() => localScore.value ?? serverScore.value)

const advisory = computed(() => {
  const score = displayScore.value
  if (score == null) return 'Select one option for each category to calculate the total.'
  if (score >= 7 && score <= 12) return 'Urgent Response'
  if (score >= 13 && score <= 17) return 'Measured Response'
  if (score >= 18 && score <= 23) return 'Evaluate and Investigate'
  return ''
})

watch(() => props.caseId, (v) => { if (v) init(); }, { immediate: true })

async function init(){
  hydrated = false
  await loadAllSortMaps()
  await load()
  hydrated = true
}

async function load(){
  if (!props.caseId) return
  try {
    const resp = await fetch(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/search-urgency`, {
      headers: { 'Accept': 'application/json' },
      credentials: 'include',
    })
    if (resp.ok) {
      const data = await resp.json()
      m.value = {
        age_id: data.age_id || '',
        physical_condition_id: data.physical_condition_id || '',
        medical_condition_id: data.medical_condition_id || '',
        personal_risk_id: data.personal_risk_id || '',
        online_risk_id: data.online_risk_id || '',
        family_risk_id: data.family_risk_id || '',
        behavioral_risk_id: data.behavioral_risk_id || '',
      }
      serverScore.value = data.score ?? null
    } else {
      m.value = { ...m.value }
      serverScore.value = null
    }
  } catch (e) {
    console.error('Failed to load search urgency', e)
  }
}

watch(m, () => { queueSave() }, { deep: true })

function queueSave(){
  if (!props.caseId || !hydrated) return
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(save, 500)
}

async function save(){
  try {
    const payload = { ...m.value }
    const resp = await fetch(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/search-urgency`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload),
    })
    if (resp.ok) {
      const data = await resp.json().catch(() => ({}))
      // Update serverScore with returned score
      if (data && typeof data.score !== 'undefined') serverScore.value = data.score
    }
  } catch (e) {
    console.error('Failed to save search urgency', e)
  }
}
</script>

<template>
  <div class="p-3">
    <div class="surface-card border-round p-3">
      <Fieldset legend="Search Urgency Factors" class="mb-3">
        <div class="row row-2">
          <div>
            <FloatLabel variant="on">
              <RefSelect id="su-age" code="SU_AGE" v-model="m.age_id" />
              <label for="su-age">Age</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <RefSelect id="su-fit" code="SU_FIT" v-model="m.physical_condition_id" />
              <label for="su-fit">Physical Condition</label>
            </FloatLabel>
          </div>
        </div>
        <div class="row row-2">
          <div>
            <FloatLabel variant="on">
              <RefSelect id="su-med" code="SU_MED" v-model="m.medical_condition_id" />
              <label for="su-med">Medical Condition</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <RefSelect id="su-prs" code="SU_RISK" v-model="m.personal_risk_id" />
              <label for="su-prs">Personal Risk</label>
            </FloatLabel>
          </div>
        </div>
        <div class="row row-2">
          <div>
            <FloatLabel variant="on">
              <RefSelect id="su-onl" code="SU_ONL" v-model="m.online_risk_id" />
              <label for="su-onl">Online Risk</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <RefSelect id="su-fam" code="SU_FAM" v-model="m.family_risk_id" />
              <label for="su-fam">Family Risk</label>
            </FloatLabel>
          </div>
        </div>
        <div class="row row-1">
          <div>
            <FloatLabel variant="on">
              <RefSelect id="su-beh" code="SU_BE" v-model="m.behavioral_risk_id" />
              <label for="su-beh">Behavioral Risk</label>
            </FloatLabel>
          </div>
        </div>
      </Fieldset>

      <hr class="my-2" />

      <div class="flex align-items-center justify-content-between gap-3">
        <div>
          <div class="font-medium">Calculated Score: <span>{{ displayScore ?? '—' }}</span></div>
          <div class="text-600 text-sm">Calculated when all seven fields are selected.</div>
        </div>
        <div class="text-right">
          <div class="font-medium">Assessment</div>
          <div class="text-600">{{ advisory }}</div>
        </div>
      </div>

      <div class="mt-2 text-600 text-sm">
        Ranges: 7–12 Urgent Response; 13–17 Measured Response; 18–23 Evaluate and Investigate.
      </div>
    </div>
  </div>
</template>

<style scoped>
.row { display: grid; gap: 1rem; margin-bottom: 1rem; grid-template-columns: 1fr; }
@media (min-width: 700px) {
  .row-1 { grid-template-columns: 1fr; }
  .row-2 { grid-template-columns: repeat(2, 1fr); }
}
</style>
