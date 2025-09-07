<script setup>
import { ref, watch, computed, onMounted, nextTick } from 'vue'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Fieldset from 'primevue/fieldset'
import FloatLabel from 'primevue/floatlabel'
import DatePicker from 'primevue/datepicker'
import Textarea from 'primevue/textarea'
import RefSelect from '../../../RefSelect.vue'
import Checkbox from 'primevue/checkbox'

// Props: accept case and subject models; allow optional v-model style updates
const props = defineProps({
  caseModel: { type: Object, default: () => ({}) },
  subjectModel: { type: Object, default: () => ({}) },
  demographicsModel: { type: Object, default: () => ({}) },
  managementModel: { type: Object, default: () => ({}) },
  patternOfLifeModel: { type: Object, default: () => ({}) },
  // New: allow loading by caseId when provided (CoreTab will pass this)
  caseId: { type: [String, Number], default: '' },
})
const emit = defineEmits(['update:caseModel','update:subjectModel','update:demographicsModel','update:managementModel','update:patternOfLifeModel'])

// Debounced autosave for subject changes
let saveTimer = null
let saveDemoTimer = null
let saveMgmtTimer = null
let savePolTimer = null
// Prevent autosaves until component fully initialized
let autoSaveReady = false
// Track whether user has interacted with the form to avoid initial autosaves
const hasUserInteracted = ref(false)
onMounted(() => {
  // wait for initial render and any prop-driven syncing to settle
  nextTick(() => { autoSaveReady = true })
})



// Models to pass to Intake/Core tabs
const caseModel = ref({})
const subjectModel = ref({})
const demographicsModel = ref({})
const managementModel = ref({})
const patternOfLifeModel = ref({})

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


async function saveSubjectToServer(subj) {
  try {
    if (!subj?.id) return
    const payload = {
      first_name: subj.first_name || '',
      last_name: subj.last_name || '',
      middle_name: subj.middle_name || null,
      nicknames: subj.nicknames || null,
    }
    await fetch(`/api/v1/subjects/${encodeURIComponent(String(subj.id))}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload),
    })
  } catch (e) {
    console.error('Failed to save subject', e)
  }
}

async function saveDemographicsToServer(demo) {
  try {
    const caseId = mCase.value?.id || demo?.case_id || null
    if (!caseId) return
    const payload = {
      case_id: String(caseId),
      date_of_birth: demo?.date_of_birth instanceof Date ? demo.date_of_birth.toISOString().slice(0,10) : (demo?.date_of_birth || null),
      age_when_missing: demo?.age_when_missing != null ? Number(demo.age_when_missing) : null,
      height: demo?.height || '',
      weight: demo?.weight || '',
      hair_color: demo?.hair_color || '',
      hair_length: demo?.hair_length || '',
      eye_color: demo?.eye_color || '',
      identifying_marks: demo?.identifying_marks || '',
      sex_id: demo?.sex_id || null,
      race_id: demo?.race_id || null,
    }
    await fetch(`/api/v1/cases/${encodeURIComponent(String(caseId))}/demographics`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload),
    })
  } catch (e) {
    console.error('Failed to save demographics', e)
  }
}

async function savePatternOfLifeToServer(pol) {
  try {
    const caseId = mCase.value?.id || null
    if (!caseId) return
    const payload = {
      case_id: String(caseId),
      school: pol?.school || '',
      grade: pol?.grade || '',
      missing_classes: !!pol?.missing_classes,
      school_laptop: !!pol?.school_laptop,
      school_laptop_taken: !!pol?.school_laptop_taken,
      school_address: pol?.school_address || '',
      employed: !!pol?.employed,
      employer: pol?.employer || '',
      work_hours: pol?.work_hours || '',
      employer_address: pol?.employer_address || '',
      confidants: pol?.confidants || '',
    }
    await fetch(`/api/v1/cases/${encodeURIComponent(String(caseId))}/pattern-of-life`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload),
    })
  } catch (e) {
    console.error('Failed to save pattern of life', e)
  }
}

async function saveManagementToServer(mgmt) {
  try {
    const caseId = mCase.value?.id || null
    if (!caseId) return
    const payload = {
      case_id: String(caseId),
      consent_sent: !!mgmt?.consent_sent,
      consent_returned: !!mgmt?.consent_returned,
      flyer_complete: !!mgmt?.flyer_complete,
      ottic: !!mgmt?.ottic,
      csec_id: mgmt?.csec_id || null,
      missing_status_id: mgmt?.missing_status_id || null,
      classification_id: mgmt?.classification_id || null,
      requested_by_id: mgmt?.requested_by_id || null,
      ncic_case_number: mgmt?.ncic_case_number || '',
      ncmec_case_number: mgmt?.ncmec_case_number || '',
      le_case_number: mgmt?.le_case_number || '',
      le_24hour_contact: mgmt?.le_24hour_contact || '',
      ss_case_number: mgmt?.ss_case_number || '',
      ss_24hour_contact: mgmt?.ss_24hour_contact || '',
      jpo_case_number: mgmt?.jpo_case_number || '',
      jpo_24hour_contact: mgmt?.jpo_24hour_contact || '',
    }
    await fetch(`/api/v1/cases/${encodeURIComponent(String(caseId))}/management`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload),
    })
  } catch (e) {
    console.error('Failed to save case management', e)
  }
}

// Local mirrors for two-way binding within this component
const mCase = ref({ ...(props.caseModel || {}) })
const mSubject = ref({
  id: props.subjectModel?.id || null,
  first_name: props.subjectModel?.first_name || '',
  last_name: props.subjectModel?.last_name || '',
  middle_name: props.subjectModel?.middle_name || '',
  nicknames: props.subjectModel?.nicknames || '',
})

// Demographics local state (created on first edit if not present on server)
const mDemo = ref({
  id: null,
  case_id: null,
  date_of_birth: null,
  age_when_missing: null,
  height: '',
  weight: '',
  hair_color: '',
  hair_length: '',
  eye_color: '',
  identifying_marks: '',
  sex_id: '',
  race_id: '',
  sex_code: '',
  race_code: '',
})

// Initialize demographics from incoming prop
function toDateOrNull(v) {
  if (!v) return null
  const d = v instanceof Date ? v : new Date(v)
  return isNaN(d.getTime()) ? null : d
}

function syncDemoFromProps(src) {
  const d = src || {}
  mDemo.value = {
    id: d.id || null,
    case_id: (props.caseModel && props.caseModel.id) || d.case_id || null,
    date_of_birth: toDateOrNull(d.date_of_birth) || null,
    age_when_missing: d.age_when_missing ?? null,
    height: d.height || '',
    weight: d.weight || '',
    hair_color: d.hair_color || '',
    hair_length: d.hair_length || '',
    eye_color: d.eye_color || '',
    identifying_marks: d.identifying_marks || '',
    sex_id: d.sex_id != null ? String(d.sex_id) : '',
    race_id: d.race_id != null ? String(d.race_id) : '',
    sex_code: d.sex_code || '',
    race_code: d.race_code || '',
  }
}

syncDemoFromProps(props.demographicsModel)

// Pattern of Life local state
const mPol = ref({
  school: '',
  grade: '',
  missing_classes: false,
  school_laptop: false,
  school_laptop_taken: false,
  school_address: '',
  employed: false,
  employer: '',
  work_hours: '',
  employer_address: '',
  confidants: '',
})

function syncPolFromProps(src){
  const p = src || {}
  mPol.value = {
    school: p.school || '',
    grade: p.grade || '',
    missing_classes: !!p.missing_classes,
    school_laptop: !!p.school_laptop,
    school_laptop_taken: !!p.school_laptop_taken,
    school_address: p.school_address || '',
    employed: !!p.employed,
    employer: p.employer || '',
    work_hours: p.work_hours || '',
    employer_address: p.employer_address || '',
    confidants: p.confidants || '',
  }
}

syncPolFromProps(props.patternOfLifeModel)

// Case Management local state
const mMgmt = ref({
  consent_sent: false,
  consent_returned: false,
  flyer_complete: false,
  ottic: false,
  csec_id: '',
  missing_status_id: '',
  classification_id: '',
  requested_by_id: '',
  csec_code: '',
  missing_status_code: '',
  classification_code: '',
  requested_by_code: '',
  ncic_case_number: '',
  ncmec_case_number: '',
  le_case_number: '',
  le_24hour_contact: '',
  ss_case_number: '',
  ss_24hour_contact: '',
  jpo_case_number: '',
  jpo_24hour_contact: '',
})

function syncMgmtFromProps(src){
  const m = src || {}
  mMgmt.value = {
    consent_sent: !!m.consent_sent,
    consent_returned: !!m.consent_returned,
    flyer_complete: !!m.flyer_complete,
    ottic: !!m.ottic,
    csec_id: m.csec_id != null ? String(m.csec_id) : '',
    missing_status_id: m.missing_status_id != null ? String(m.missing_status_id) : '',
    classification_id: m.classification_id != null ? String(m.classification_id) : '',
    requested_by_id: m.requested_by_id != null ? String(m.requested_by_id) : '',
    csec_code: m.csec_code || '',
    missing_status_code: m.missing_status_code || '',
    classification_code: m.classification_code || '',
    requested_by_code: m.requested_by_code || '',
    ncic_case_number: m.ncic_case_number || '',
    ncmec_case_number: m.ncmec_case_number || '',
    le_case_number: m.le_case_number || '',
    le_24hour_contact: m.le_24hour_contact || '',
    ss_case_number: m.ss_case_number || '',
    ss_24hour_contact: m.ss_24hour_contact || '',
    jpo_case_number: m.jpo_case_number || '',
    jpo_24hour_contact: m.jpo_24hour_contact || '',
  }
}

syncMgmtFromProps(props.managementModel)

// Guard to prevent emitting changes caused by syncing from props
let syncingFromProps = false

// Load initial data when caseId is provided (decoupled mode)
async function loadFromCaseId(id) {
  const cid = String(id || '')
  if (!cid) return
  try {
    syncingFromProps = true
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
    const s = data?.subject || {}
    mSubject.value = {
      id: s.id || null,
      first_name: s.first_name || '',
      last_name: s.last_name || '',
      middle_name: s.middle_name || '',
      nicknames: s.nicknames || '',
    }
    syncDemoFromProps(data?.demographics || {})
    syncPolFromProps(data?.pattern_of_life || {})
    syncMgmtFromProps(data?.management || {})
  } catch (e) {
    console.error('Failed to load intake data by case id', e)
  } finally {
    // allow emits/saves after initial load
    queueMicrotask(() => { syncingFromProps = false })
  }
}

watch(() => props.caseId, (v) => { if (v) loadFromCaseId(v) }, { immediate: true })

// Keep local mirrors in sync when parent props change (avoid unnecessary reassignments)
watch(() => props.caseModel, (v) => {
  if (String(props.caseId || '')) return
  const next = { ...(v || {}) }
  const cur = mCase.value || {}
  const changed = JSON.stringify(next) !== JSON.stringify(cur)
  if (changed) {
    syncingFromProps = true
    mCase.value = next
    // ensure mDemo.case_id tracks case id for saves
    if (!mDemo.value) mDemo.value = {}
    mDemo.value.case_id = next?.id || null
    queueMicrotask(() => { syncingFromProps = false })
  }
}, { deep: true })

// Sync demographics when prop changes
watch(() => props.demographicsModel, (v) => {
  if (String(props.caseId || '')) return
  syncingFromProps = true
  syncDemoFromProps(v)
  queueMicrotask(() => { syncingFromProps = false })
}, { deep: true })

// Sync pattern of life when prop changes
watch(() => props.patternOfLifeModel, (v) => {
  if (String(props.caseId || '')) return
  syncingFromProps = true
  syncPolFromProps(v)
  queueMicrotask(() => { syncingFromProps = false })
}, { deep: true })

// Sync management when prop changes
watch(() => props.managementModel, (v) => {
  if (String(props.caseId || '')) return
  syncingFromProps = true
  syncMgmtFromProps(v)
  queueMicrotask(() => { syncingFromProps = false })
}, { deep: true })

watch(() => props.subjectModel, (v) => {
  if (String(props.caseId || '')) return
  const next = {
    id: v?.id || null,
    first_name: v?.first_name || '',
    last_name: v?.last_name || '',
    middle_name: v?.middle_name || '',
    nicknames: v?.nicknames || '',
  }
  const cur = mSubject.value || {}
  const changed = (
    next.id !== (cur.id || null) ||
    next.first_name !== (cur.first_name || '') ||
    next.last_name !== (cur.last_name || '') ||
    next.middle_name !== (cur.middle_name || '') ||
    next.nicknames !== (cur.nicknames || '')
  )
  if (changed) {
    syncingFromProps = true
    mSubject.value = next
    queueMicrotask(() => { syncingFromProps = false })
  }
}, { deep: true })

watch(mCase, (v) => {
  if (syncingFromProps) return
  emit('update:caseModel', v)
}, { deep: true })

watch(mDemo, (v) => {
  if (syncingFromProps) return
  emit('update:demographicsModel', {
    ...v,
    // Normalize date to ISO string for parent if it's a Date
    date_of_birth: v?.date_of_birth instanceof Date ? v.date_of_birth.toISOString().slice(0,10) : v?.date_of_birth || null,
  })
  if (!autoSaveReady || !hasUserInteracted.value) return
  if (saveDemoTimer) clearTimeout(saveDemoTimer)
  saveDemoTimer = setTimeout(() => saveDemographicsToServer(v), 700)
}, { deep: true })

// Emit pattern of life up to parent
watch(mPol, (v) => {
  if (syncingFromProps) return
  emit('update:patternOfLifeModel', v)
  if (!autoSaveReady || !hasUserInteracted.value) return
  if (savePolTimer) clearTimeout(savePolTimer)
  savePolTimer = setTimeout(() => savePatternOfLifeToServer(v), 700)
}, { deep: true })

// Emit management up to parent
watch(mMgmt, (v) => {
  if (syncingFromProps) return
  emit('update:managementModel', v)
  if (!autoSaveReady || !hasUserInteracted.value) return
  if (saveMgmtTimer) clearTimeout(saveMgmtTimer)
  saveMgmtTimer = setTimeout(() => saveManagementToServer(v), 700)
}, { deep: true })

watch(mSubject, (v) => {
  if (syncingFromProps) return
  emit('update:subjectModel', v)
  // debounce save to server (but only after user interaction and initial load)
  if (!autoSaveReady || !hasUserInteracted.value) return
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => saveSubjectToServer(v), 600)
}, { deep: true })

// Maintain rule: subject.id == case.subject_id
watch(() => mSubject.value.id, (id) => {
  if (!mCase.value) mCase.value = {}
  if (mCase.value.subject_id !== id) mCase.value.subject_id = id || null
})
watch(() => mCase.value?.subject_id, (sid) => {
  if ((mSubject.value.id || null) !== (sid || null)) mSubject.value.id = sid || null
})

// When DOB changes, recompute age_when_missing and update model
function computeAgeFromDob(dob) {
  if (!dob) return null
  try {
    const d = dob instanceof Date ? dob : new Date(dob)
    if (isNaN(d.getTime())) return null
    const today = new Date()
    let age = today.getFullYear() - d.getFullYear()
    const m = today.getMonth() - d.getMonth()
    if (m < 0 || (m === 0 && today.getDate() < d.getDate())) age--
    return age >= 0 ? age : null
  } catch {
    return null
  }
}

watch(() => mDemo.value?.date_of_birth, (dob) => {
  if (syncingFromProps) return
  const newAge = computeAgeFromDob(dob)
  // Only update if changed to avoid unnecessary saves
  if ((mDemo.value?.age_when_missing ?? null) !== (newAge ?? null)) {
    mDemo.value.age_when_missing = newAge
  }
})
// Computed date adapter for intake date on case
const intakeDate = computed({
  get() {
    return toDateOrNull(mCase.value?.date_intake) || null
  },
  set(v) {
    if (!mCase.value) mCase.value = {}
    if (v instanceof Date) {
      mCase.value.date_intake = v.toISOString().slice(0,10)
    } else if (!v) {
      mCase.value.date_intake = null
    } else {
      // attempt to coerce
      const d = new Date(v)
      mCase.value.date_intake = isNaN(d.getTime()) ? null : d.toISOString().slice(0,10)
    }
  }
})
</script>

<template>
  <div class="p-3" @input.capture="hasUserInteracted = true">
    <Fieldset legend="Missing Person">
      <div class="mp-grid">
        <div>
          <FloatLabel variant="on">
            <InputText id="mp-first" v-model="mSubject.first_name" class="w-full" />
            <label for="mp-first">First Name</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <InputText id="mp-middle" v-model="mSubject.middle_name" class="w-full" />
            <label for="mp-middle">Middle Name</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <InputText id="mp-last" v-model="mSubject.last_name" class="w-full" />
            <label for="mp-last">Last Name</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <InputText id="mp-nick" v-model="mSubject.nicknames" class="w-full" />
            <label for="mp-nick">Nickname(s)</label>
          </FloatLabel>
        </div>
      </div>
    </Fieldset>

    <Fieldset legend="Demographics" class="mt-3">
      <!-- Row 1: date_of_birth, age_when_missing (readonly) -->
      <div class="row row-2">
        <div>
          <FloatLabel variant="on">
            <DatePicker id="dob" v-model="mDemo.date_of_birth" date-format="yy-mm-dd" showIcon iconDisplay="input" class="w-full" />

            <label class="block text-sm mb-1" for="dob">Date of Birth</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <InputNumber id="age-missing" v-model="mDemo.age_when_missing" buttonLayout="horizontal" class="w-full" showButtons :min="0" :max="120">
                  <template #incrementbuttonicon>
                      <span class="pi pi-plus" />
                  </template>
                  <template #decrementbuttonicon>
                      <span class="pi pi-minus" />
                  </template>
            </InputNumber>
            <label for="age-missing">Age when missing</label>
          </FloatLabel>
        </div>
      </div>

      <!-- Row 2: height, weight -->
      <div class="row row-2">
        <div>
          <FloatLabel variant="on">
            <InputText id="height" v-model="mDemo.height" class="w-full" />
            <label for="height">Height</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <InputText id="weight" v-model="mDemo.weight" class="w-full" />
            <label for="weight">Weight</label>
          </FloatLabel>
        </div>
      </div>

      <!-- Row 3: hair_color, hair_length, eye_color -->
      <div class="row row-3">
        <div>
          <FloatLabel variant="on">
            <InputText id="hair-color" v-model="mDemo.hair_color" class="w-full" />
            <label for="hair-color">Hair Color</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <InputText id="hair-length" v-model="mDemo.hair_length" class="w-full" />
            <label for="hair-length">Hair Length</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <InputText id="eye-color" v-model="mDemo.eye_color" class="w-full" />
            <label for="eye-color">Eye Color</label>
          </FloatLabel>
        </div>
      </div>

      <!-- Row 4: identifying_marks (full width) -->
      <div class="row row-1">
        <div>
              <FloatLabel variant="on">
                <Textarea id="marks" v-model="mDemo.identifying_marks" rows="3" class="w-full" />
                <label class="block text-sm mb-1" for="marks">Identifying Marks</label>
              </FloatLabel>
        </div>
      </div>

      <!-- Row 5: sex_id, race_id using RefSelect -->
      <div class="row row-2">
        <div>
              <FloatLabel variant="on">
                <RefSelect id="sex" code="SEX" v-model="mDemo.sex_id" :currentCode="mDemo.sex_code" />
                <label for="sex">Sex</label>
              </FloatLabel>
        </div>
        <div>
              <FloatLabel variant="on">
                <RefSelect id="race" code="RACE" v-model="mDemo.race_id" :currentCode="mDemo.race_code" />
                <label for="race">Race</label>
              </FloatLabel>
        </div>
      </div>
    </Fieldset>

        <Fieldset legend="Case Management" class="mt-3">
          <!-- Row 0: C2R Case Number (read-only) and Intake Date (editable) -->
          <div class="row row-2">
            <div>
              <FloatLabel variant="on">
                <InputText id="cm-case-number" v-model="mCase.case_number" class="w-full" :readonly="true" />
                <label for="cm-case-number">C2R Case Number</label>
              </FloatLabel>
            </div>
            <div>
              <FloatLabel variant="on">
                <DatePicker id="cm-intake-date" v-model="intakeDate" date-format="yy-mm-dd" showIcon iconDisplay="input" class="w-full" />
                <label for="cm-intake-date">Intake Date</label>
              </FloatLabel>
            </div>
          </div>
          <!-- Row 1: consent_sent, consent_returned, flyer_complete -->
          <div class="row row-3">
            <div class="flex align-items-center gap-2">
              <Checkbox inputId="cm-consent-sent" v-model="mMgmt.consent_sent" :binary="true" />
              <label for="cm-consent-sent">Consent Sent</label>
            </div>
            <div class="flex align-items-center gap-2">
              <Checkbox inputId="cm-consent-returned" v-model="mMgmt.consent_returned" :binary="true" />
              <label for="cm-consent-returned">Consent Returned</label>
            </div>
            <div class="flex align-items-center gap-2">
              <Checkbox inputId="cm-flyer-complete" v-model="mMgmt.flyer_complete" :binary="true" />
              <label for="cm-flyer-complete">Flyer Complete</label>
            </div>
          </div>

          <!-- Row 2: csec_id, missing_status_id, classification_id, ottic -->
          <div class="row row-4">
            <div>
              <FloatLabel variant="on">
                <RefSelect id="cm-csec" code="CSEC" v-model="mMgmt.csec_id" :currentCode="mMgmt.csec_code" />
                <label class="block text-sm mb-1" for="cm-csec">CSEC</label>
              </FloatLabel>
            </div>
            <div>
              <FloatLabel variant="on">
                <RefSelect id="cm-mstat" code="MSTAT" v-model="mMgmt.missing_status_id" :currentCode="mMgmt.missing_status_code" />
                <label class="block text-sm mb-1" for="cm-mstat">Missing Status</label>
              </FloatLabel>
            </div>
            <div>
              <FloatLabel variant="on">
                <RefSelect id="cm-mclass" code="MCLASS" v-model="mMgmt.classification_id" :currentCode="mMgmt.classification_code" />
                <label class="block text-sm mb-1" for="cm-mclass">Classification</label>
              </FloatLabel>
            </div>
            <div class="flex align-items-center gap-2">
              <Checkbox inputId="cm-ottic" v-model="mMgmt.ottic" :binary="true" />
              <label for="cm-ottic">OTTIC</label>
            </div>
          </div>

          <!-- Row 3: ncic_case_number, ncmec_case_number -->
          <div class="row row-2">
            <div>
              <FloatLabel variant="on">
                <InputText id="cm-ncic" v-model="mMgmt.ncic_case_number" class="w-full" />
                <label for="cm-ncic">NCIC Case #</label>
              </FloatLabel>
            </div>
            <div>
              <FloatLabel variant="on">
                <InputText id="cm-ncmec" v-model="mMgmt.ncmec_case_number" class="w-full" />
                <label for="cm-ncmec">NCMEC Case #</label>
              </FloatLabel>
            </div>
          </div>

          <!-- Row 4: Law Enforcement -->
          <div class="row row-2">
            <div>
              <FloatLabel variant="on">
                <InputText id="cm-le-case" v-model="mMgmt.le_case_number" class="w-full" />
                <label for="cm-le-case">LE Case #</label>
              </FloatLabel>
            </div>
            <div>
              <FloatLabel variant="on">
                <InputText id="cm-le-24" v-model="mMgmt.le_24hour_contact" class="w-full" />
                <label for="cm-le-24">LE 24-hour Contact</label>
              </FloatLabel>
            </div>
          </div>

          <!-- Row 5: Social Services -->
          <div class="row row-2">
            <div>
              <FloatLabel variant="on">
                <InputText id="cm-ss-case" v-model="mMgmt.ss_case_number" class="w-full" />
                <label for="cm-ss-case">SS Case #</label>
              </FloatLabel>
            </div>
            <div>
              <FloatLabel variant="on">
                <InputText id="cm-ss-24" v-model="mMgmt.ss_24hour_contact" class="w-full" />
                <label for="cm-ss-24">SS 24-hour Contact</label>
              </FloatLabel>
            </div>
          </div>

          <!-- Row 6: Juvenile Probation Officer -->
          <div class="row row-2">
            <div>
              <FloatLabel variant="on">
                <InputText id="cm-jpo-case" v-model="mMgmt.jpo_case_number" class="w-full" />
                <label for="cm-jpo-case">JPO Case #</label>
              </FloatLabel>
            </div>
            <div>
              <FloatLabel variant="on">
                <InputText id="cm-jpo-24" v-model="mMgmt.jpo_24hour_contact" class="w-full" />
                <label for="cm-jpo-24">JPO 24-hour Contact</label>
              </FloatLabel>
            </div>
          </div>

          <!-- Row 7: Requested By -->
          <div class="row row-1">
            <div>
              <FloatLabel variant="on">
                <RefSelect id="cm-requested-by" code="REQ_BY" v-model="mMgmt.requested_by_id" :currentCode="mMgmt.requested_by_code" />
                <label for="cm-requested-by">Requested By</label>
              </FloatLabel>
            </div>
          </div>
        </Fieldset>

        <Fieldset legend="Pattern of Life" class="mt-3">
          <!-- Row 1: school, grade -->
          <div class="row row-2">
            <div>
              <FloatLabel variant="on">
                <InputText id="pol-school" v-model="mPol.school" class="w-full" />
                <label for="pol-school">School</label>
              </FloatLabel>
            </div>
            <div>
              <FloatLabel variant="on">
                <InputText id="pol-grade" v-model="mPol.grade" class="w-full" />
                <label for="pol-grade">Grade</label>
              </FloatLabel>
            </div>
          </div>

          <!-- Row 2: missing_classes, school_laptop, school_laptop_taken -->
          <div class="row row-3">
            <div class="flex align-items-center gap-2">
              <Checkbox inputId="pol-missing-classes" v-model="mPol.missing_classes" :binary="true" />
              <label for="pol-missing-classes">Missing Classes</label>
            </div>
            <div class="flex align-items-center gap-2">
              <Checkbox inputId="pol-school-laptop" v-model="mPol.school_laptop" :binary="true" />
              <label for="pol-school-laptop">School Laptop</label>
            </div>
            <div class="flex align-items-center gap-2" v-if="mPol.school_laptop">
              <Checkbox inputId="pol-school-laptop-taken" v-model="mPol.school_laptop_taken" :binary="true" />
              <label for="pol-school-laptop-taken">Laptop Taken</label>
            </div>
          </div>

          <!-- Row 3: school_address -->
          <div class="row row-1">
            <div>
              <FloatLabel variant="on">
                <Textarea id="pol-school-address" v-model="mPol.school_address" rows="2" class="w-full" />
                <label for="pol-school-address">School Address</label>
              </FloatLabel>
            </div>
          </div>

          <!-- Row 4: employed, employer, work_hours -->
          <div class="row row-3">
            <div class="flex align-items-center gap-2">
              <Checkbox inputId="pol-employed" v-model="mPol.employed" :binary="true" />
              <label for="pol-employed">Employed</label>
            </div>
            <div v-if="mPol.employed">
              <FloatLabel variant="on">
                <InputText id="pol-employer" v-model="mPol.employer" class="w-full" />
                <label for="pol-employer">Employer</label>
              </FloatLabel>
            </div>
            <div v-if="mPol.employed">
              <FloatLabel variant="on">
                <InputText id="pol-work-hours" v-model="mPol.work_hours" class="w-full" />
                <label for="pol-work-hours">Work Hours</label>
              </FloatLabel>
            </div>
          </div>

          <!-- Row 5: employer_address -->
          <div class="row row-1" v-if="mPol.employed">
            <div>
              <FloatLabel variant="on">
                <Textarea id="pol-employer-address" v-model="mPol.employer_address" rows="2" class="w-full" />
                <label for="pol-employer-address">Employer Address</label>
              </FloatLabel>
            </div>
          </div>

          <!-- Row 6: confidants -->
          <div class="row row-1">
            <div>
              <FloatLabel variant="on">
                <Textarea id="pol-confidants" v-model="mPol.confidants" rows="3" class="w-full" />
                <label for="pol-confidants">Confidants</label>
              </FloatLabel>
            </div>
          </div>
        </Fieldset>
      </div>
    </template>

    <style scoped>
    .mp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}
.row { display: grid; gap: 1rem; margin-bottom: 1rem; grid-template-columns: 1fr; }
/* On medium+ screens, enforce the desired columns per row */
@media (min-width: 700px) {
  .row-1 { grid-template-columns: 1fr; }
  .row-2 { grid-template-columns: repeat(2, 1fr); }
  .row-3 { grid-template-columns: repeat(3, 1fr); }
  .row-4 { grid-template-columns: repeat(4, 1fr); }
}
</style>
