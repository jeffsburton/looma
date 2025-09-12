<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import api from '../../../lib/api'
import PersonSelect from '../../PersonSelect.vue'
import RefSelect from '../../RefSelect.vue'
import ToggleSwitch from 'primevue/toggleswitch'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import Badge from 'primevue/badge'
import InputText from 'primevue/inputtext'

const route = useRoute()
const router = useRouter()

const caseNumber = computed(() => String(route.params.caseNumber || ''))
const subjectCaseRawId = computed(() => String(route.params.rawSubjectId || ''))
const isCreate = computed(() => subjectCaseRawId.value === 'new')

const loading = ref(false)
const error = ref('')

// subject-case model (link row)
const sc = ref({
  id: '', // opaque subject_case id
  raw_id: '',
  subject_id: '', // opaque subject id
  relationship_id: null,
  relationship_code: '',
  relationship_other: '',
  legal_guardian: false,
  notes: '',
  rule_out: false,
  subject: null, // nested subject for display
})

function goBack() {
  router.replace({ name: 'case-detail', params: { caseNumber: caseNumber.value, tab: 'contacts', subtab: 'subjects' } })
}

async function load() {
  if (isCreate.value) {
    // Creation mode: do not load anything
    return
  }
  if (!subjectCaseRawId.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/subject/${encodeURIComponent(subjectCaseRawId.value)}`)
    const r = data || {}
    sc.value = {
      id: r.id,
      raw_id: r.raw_id,
      subject_id: r?.subject?.id || '',
      relationship_id: r.relationship_id || null,
      relationship_code: r.relationship_code || '',
      relationship_other: r.relationship_other || '',
      legal_guardian: !!r.legal_guardian,
      notes: r.notes || '',
      rule_out: !!r.rule_out,
      subject: r.subject || null,
    }
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load subject link.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

const creating = ref(false)

async function onCreateSave() {
  error.value = ''
  if (!sc.value.subject_id || String(sc.value.subject_id).trim() === '') {
    error.value = 'Please select a person to add as subject.'
    return
  }
  creating.value = true
  try {
    const payload = {
      subject_id: sc.value.subject_id,
      relationship_id: sc.value.relationship_id || null,
      relationship_other: (sc.value.relationship_other || '').trim() || null,
      legal_guardian: !!sc.value.legal_guardian,
      notes: (sc.value.notes || '').trim() || null,
    }
    await api.post(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/subjects`, payload)
    // After successful creation return to list view; SubjectsTab watcher reloads list
    goBack()
  } catch (e) {
    console.error(e)
    error.value = 'Failed to create investigatory subject.'
  } finally {
    creating.value = false
  }
}

function telHref(val) {
  if (!val) return ''
  const digits = String(val).trim().replace(/[^+\d]/g, '')
  return `tel:${digits}`
}

function mailtoHref(val) {
  if (!val) return ''
  const s = String(val).trim()
  return `mailto:${s}`
}

async function patch(payload) {
  if (!subjectCaseRawId.value) return
  try {
    await api.patch(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/subjects/${encodeURIComponent(subjectCaseRawId.value)}`, payload)
  } catch (e) {
    console.error(e)
    throw e
  }
}

async function patchSubject(payload) {
  const sid = sc.value?.subject?.id
  if (!sid) return
  try {
    await api.patch(`/api/v1/subjects/${encodeURIComponent(String(sid))}`, payload)
  } catch (e) {
    console.error(e)
    throw e
  }
}

async function onBlurPhone() {
  try {
    await patchSubject({ phone: sc.value?.subject?.phone || null })
  } catch (e) {
    error.value = 'Failed to update phone.'
  }
}

async function onBlurEmail() {
  try {
    await patchSubject({ email: sc.value?.subject?.email || null })
  } catch (e) {
    error.value = 'Failed to update email.'
  }
}

async function onToggleDangerous(v) {
  const val = !!v
  if (!sc.value.subject) return
  sc.value.subject.dangerous = val
  if (!val) {
    sc.value.subject.danger = null
  }
  try {
    await patchSubject({ dangerous: val, danger: val ? (sc.value.subject?.danger || null) : null })
  } catch (e) {
    error.value = 'Failed to update dangerous flag.'
  }
}

async function onBlurDanger() {
  try {
    await patchSubject({ danger: sc.value?.subject?.danger || null })
  } catch (e) {
    error.value = 'Failed to update danger.'
  }
}

async function onChangeSubject(newId) {
  if (!newId || newId === sc.value.subject_id) return
  try {
    await patch({ subject_id: newId })
    await load()
  } catch (e) {
    error.value = 'Failed to update person.'
  }
}

async function onChangeRelationship(newId) {
  sc.value.relationship_id = newId
  try {
    await patch({ relationship_id: newId })
  } catch (e) {
    error.value = 'Failed to update relationship.'
  }
}

async function onCommitOther(other) {
  sc.value.relationship_other = other || ''
  try {
    await patch({ relationship_other: other || null })
  } catch (e) {
    error.value = 'Failed to update relationship other.'
  }
}

async function onToggleGuardian(v) {
  sc.value.legal_guardian = !!v
  try {
    await patch({ legal_guardian: !!v })
  } catch (e) {
    error.value = 'Failed to update guardian.'
  }
}

async function onToggleRuleOut(v) {
  sc.value.rule_out = !!v
  try {
    await patch({ rule_out: !!v })
  } catch (e) {
    error.value = 'Failed to update rule-out.'
  }
}

async function onBlurNotes() {
  try {
    await patch({ notes: sc.value.notes || null })
  } catch (e) {
    error.value = 'Failed to update notes.'
  }
}
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center gap-2 mb-3">
      <button class="icon-button" @click="goBack" title="Back">
        <span class="material-symbols-outlined">arrow_back</span>
      </button>
      <div class="text-lg font-semibold">{{ isCreate ? 'Add Investigatory Subject' : 'Edit Investigatory Subject' }}</div>
    </div>
    <div v-if="error" class="p-error mb-2">{{ error }}</div>
    <div class="surface-card border-round p-3">
      <div v-if="loading && !isCreate" class="text-600">Loading...</div>
      <template v-else-if="isCreate">
        <div class="flex-row">
          <FloatLabel variant="on" class="row field w-full">
            <PersonSelect v-model="sc.subject_id" :shepherds="false" :agency="false" :subjects="true" />
            <label class="block mb-1">Person</label>
          </FloatLabel>

          <div class="flex gap-3 align-content-start mt-2">
            <FloatLabel class="field w-6  align-content-start" variant="on">
              <RefSelect
                code="SUB_REL"
                v-model="sc.relationship_id"
                :currentCode="sc.relationship_code || ''"
                :otherValue="sc.relationship_other || ''"
                @update:otherValue="(v) => { sc.relationship_other = v }"
              />
              <label class="block mb-1">Relationship</label>
            </FloatLabel>

            <div class="flex gap-2 nowrap w-3 align-items-center">
              <label class="mb-1">Legal Guardian</label>
              <ToggleSwitch :modelValue="sc.legal_guardian" @update:modelValue="(v) => sc.legal_guardian = !!v" />
            </div>
          </div>

          <FloatLabel variant="on" class="field w-12 md:w-12 mt-2">
            <Textarea inputId="notes" v-model="sc.notes" autoResize rows="3" class="w-full" />
            <label for="notes">Notes</label>
          </FloatLabel>

          <div class="flex justify-content-end gap-2 mt-3">
            <button class="p-button p-component p-button-text" type="button" @click="goBack"><span class="p-button-label">Cancel</span></button>
            <button class="p-button p-component" type="button" @click="onCreateSave" :disabled="creating"><span class="p-button-icon pi pi-check mr-1"></span><span class="p-button-label">Save</span></button>
          </div>
        </div>
      </template>
      <template v-else-if="sc && sc.id">
        <div class="flex-row">
          <FloatLabel variant="on" class="row field w-full">
            <PersonSelect v-model="sc.subject_id" :shepherds="false" :agency="false" :subjects="true" @update:modelValue="onChangeSubject" />
            <label class="block mb-1">Person</label>
          </FloatLabel>

          <!-- Subject quick info and editing -->
          <div class="row field w-full">
            <div class="flex flex-column gap-3">

              <!-- Editable subject fields -->
              <div class="grid" style="grid-template-columns: 1fr 1fr; gap: .75rem;">


                <template v-if="sc.subject?.phone">
                  <a :href="telHref(sc.subject.phone)" class="link-btn" @click.stop>
                    📞
                  </a>
                </template>
                <FloatLabel variant="on">
                  <InputText v-model="sc.subject.phone" class="w-full" @blur="onBlurPhone" />
                  <label class="block mb-1">Phone</label>
                </FloatLabel>
                <template v-if="sc.subject?.email">
                  <a :href="mailtoHref(sc.subject.email)" class="link-btn" @click.stop>
                    ✉️
                  </a>
                </template>
                <FloatLabel variant="on">
                  <InputText v-model="sc.subject.email" class="w-full" @blur="onBlurEmail" />
                  <label class="block mb-1">Email</label>
                </FloatLabel>
              </div>
              <div class="grid" style="grid-template-columns: 1fr 1fr; gap: .75rem;">
                <div class="flex gap-2 align-items-center">
                  <label class="mb-1">Dangerous</label>
                  <ToggleSwitch :modelValue="sc.subject?.dangerous || false" @update:modelValue="onToggleDangerous" />
                </div>
  
                <div v-if="sc.subject?.dangerous">
                  <FloatLabel variant="on" class="w-12">
                    <InputText v-model="sc.subject.danger" class="w-full" @blur="onBlurDanger" />
                    <label class="block mb-1">Danger</label>
                  </FloatLabel>
                </div>
                </div>
            </div>
          </div>

          <div class="flex gap-3  align-content-start">

            <FloatLabel class="field w-6  align-content-start" variant="on">

              <RefSelect
                code="SUB_REL"
                v-model="sc.relationship_id"
                :currentCode="sc.relationship_code || ''"
                :otherValue="sc.relationship_other || ''"
                @update:otherValue="(v) => { sc.relationship_other = v }"
                @otherCommit="onCommitOther"
                @change="onChangeRelationship"
              />
              <label class="block mb-1">Relationship</label>
            </FloatLabel>

            <div class="flex gap-2 nowrap w-3 align-items-center">
              <label class="mb-1">Legal Guardian</label>
              <ToggleSwitch :modelValue="sc.legal_guardian" @update:modelValue="onToggleGuardian" />
            </div>

            <div class="flex gap-2 nowrap w-3 align-items-center">
              <label class="mb-1">Rule Out</label>
              <ToggleSwitch :modelValue="sc.rule_out" @update:modelValue="onToggleRuleOut" />
            </div>
          </div>

          <FloatLabel variant="on" class="field w-12 md:w-12">
            <Textarea inputId="notes" v-model="sc.notes" autoResize rows="3" class="w-full" @blur="onBlurNotes" />
            <label for="notes">Notes</label>
          </FloatLabel>
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
