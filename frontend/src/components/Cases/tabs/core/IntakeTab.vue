<script setup>
import { ref, watch, computed } from 'vue'
import InputText from 'primevue/inputtext'
import Fieldset from 'primevue/fieldset'
import FloatLabel from 'primevue/floatlabel'
import Calendar from 'primevue/calendar'
import Textarea from 'primevue/textarea'
import RefSelect from '../../../RefSelect.vue'

// Props: accept case and subject models; allow optional v-model style updates
const props = defineProps({
  caseModel: { type: Object, default: () => ({}) },
  subjectModel: { type: Object, default: () => ({}) },
  demographicsModel: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:caseModel','update:subjectModel','update:demographicsModel'])

// Debounced autosave for subject changes
let saveTimer = null
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
    sex_id: d.sex_id ?? '',
    race_id: d.race_id ?? '',
  }
}

syncDemoFromProps(props.demographicsModel)

// Guard to prevent emitting changes caused by syncing from props
let syncingFromProps = false

// Keep local mirrors in sync when parent props change (avoid unnecessary reassignments)
watch(() => props.caseModel, (v) => {
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
  syncingFromProps = true
  syncDemoFromProps(v)
  queueMicrotask(() => { syncingFromProps = false })
}, { deep: true })

watch(() => props.subjectModel, (v) => {
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

// Emit updates up to parent on changes (skip if originated from prop sync)
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
}, { deep: true })

watch(mSubject, (v) => {
  if (syncingFromProps) return
  emit('update:subjectModel', v)
  // debounce save to server
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

// Derived: age_when_missing display (non-editable)
const ageWhenMissingDisplay = computed(() => {
  const dob = mDemo.value?.date_of_birth
  if (!dob) return ''
  try {
    const d = new Date(dob)
    if (isNaN(d.getTime())) return ''
    const today = new Date()
    let age = today.getFullYear() - d.getFullYear()
    const m = today.getMonth() - d.getMonth()
    if (m < 0 || (m === 0 && today.getDate() < d.getDate())) age--
    return age >= 0 ? String(age) : ''
  } catch {
    return ''
  }
})
</script>

<template>
  <div class="p-3">
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
            <Calendar id="dob" v-model="mDemo.date_of_birth" date-format="yy-mm-dd" showIcon iconDisplay="input" class="w-full" />

            <label class="block text-sm mb-1" for="dob">Date of Birth</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <InputText id="age-missing" :value="ageWhenMissingDisplay" class="w-full" disabled />
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
          <label class="block text-sm mb-1" for="marks">Identifying Marks</label>
          <Textarea id="marks" v-model="mDemo.identifying_marks" rows="3" class="w-full" />
        </div>
      </div>

      <!-- Row 5: sex_id, race_id using RefSelect -->
      <div class="row row-2">
        <div>
          <label class="block text-sm mb-1" for="sex">Sex</label>
          <RefSelect id="sex" code="SEX" v-model="mDemo.sex_id" placeholder="Select sex..." />
        </div>
        <div>
          <label class="block text-sm mb-1" for="race">Race</label>
          <RefSelect id="race" code="RACE" v-model="mDemo.race_id" placeholder="Select race..." />
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
}
</style>
