<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import api from '../../../lib/api'
import PersonSelect from '../../PersonSelect.vue'
import RefSelect from '../../RefSelect.vue'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import InputText from 'primevue/inputtext'

const props = defineProps({
  caseId: { type: [String, Number], default: '' },
})

const route = useRoute()
const router = useRouter()

const caseNumber = computed(() => String(route.params.caseNumber || ''))
const personCaseRawId = computed(() => String(route.params.rawPersonId || ''))
const isCreate = computed(() => personCaseRawId.value === 'new')

const loading = ref(false)
const error = ref('')

// person-case model (link row)
const pc = ref({
  id: '', // opaque person_case id
  raw_id: '',
  person_id: '', // opaque person id
  relationship_id: null,
  relationship_code: '',
  relationship_other: '',
  notes: '',
  person: null, // nested person for display
})

function goBack() {
  router.replace({ name: 'case-detail', params: { caseNumber: caseNumber.value, tab: 'contacts', subtab: 'persons' } })
}

async function load() {
  if (isCreate.value) {
    return
  }
  if (!personCaseRawId.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/person/${encodeURIComponent(personCaseRawId.value)}`)
    const r = data || {}
    pc.value = {
      id: r.id,
      raw_id: r.raw_id,
      person_id: r?.person?.id || '',
      relationship_id: r.relationship_id || null,
      relationship_code: r.relationship_code || '',
      relationship_other: r.relationship_other || '',
      notes: r.notes || '',
      person: r.person || null,
    }
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load person link.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

const creating = ref(false)

async function onCreateSave() {
  error.value = ''
  if (!pc.value.person_id || String(pc.value.person_id).trim() === '') {
    error.value = 'Please select a person.'
    return
  }
  creating.value = true
  try {
    const payload = {
      person_id: pc.value.person_id,
      relationship_id: pc.value.relationship_id || null,
      relationship_other: (pc.value.relationship_other || '').trim() || null,
      notes: (pc.value.notes || '').trim() || null,
    }
    await api.post(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/persons`, payload)
    goBack()
  } catch (e) {
    console.error(e)
    error.value = 'Failed to create agency person link.'
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
  if (!personCaseRawId.value) return
  try {
    await api.patch(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/persons/${encodeURIComponent(personCaseRawId.value)}`, payload)
  } catch (e) {
    console.error(e)
    throw e
  }
}

async function patchPerson(payload) {
  const pid = pc.value?.person?.id
  if (!pid) return
  try {
    await api.patch(`/api/v1/persons/${encodeURIComponent(String(pid))}`, payload)
  } catch (e) {
    console.error(e)
    throw e
  }
}

async function onBlurPhone() {
  try {
    await patchPerson({ phone: pc.value?.person?.phone || null })
  } catch (e) {
    error.value = 'Failed to update phone.'
  }
}

async function onBlurEmail() {
  try {
    await patchPerson({ email: pc.value?.person?.email || null })
  } catch (e) {
    error.value = 'Failed to update email.'
  }
}

async function onChangePerson(newId) {
  if (!newId || newId === pc.value.person_id) return
  try {
    await patch({ person_id: newId })
    await load()
  } catch (e) {
    error.value = 'Failed to update person.'
  }
}

async function onChangeRelationship(newId) {
  pc.value.relationship_id = newId
  try {
    await patch({ relationship_id: newId })
  } catch (e) {
    error.value = 'Failed to update relationship.'
  }
}

async function onCommitOther(other) {
  pc.value.relationship_other = other || ''
  try {
    await patch({ relationship_other: other || null })
  } catch (e) {
    error.value = 'Failed to update relationship other.'
  }
}

async function onBlurNotes() {
  try {
    await patch({ notes: pc.value.notes || null })
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
      <div class="text-lg font-semibold">{{ isCreate ? 'Add Agency Person' : 'Edit Agency Person' }}</div>
    </div>
    <div v-if="error" class="p-error mb-2">{{ error }}</div>
    <div class="surface-card border-round p-3">
      <div v-if="loading && !isCreate" class="text-600">Loading...</div>
      <template v-else-if="isCreate">
        <div class="flex-row">
          <FloatLabel variant="on" class="row field w-full">
            <PersonSelect v-model="pc.person_id" :shepherds="true" :agency="true" :subjects="false" />
            <label class="block mb-1">Person</label>
          </FloatLabel>

          <div class="flex gap-3 align-content-start mt-2">
            <FloatLabel class="field w-6  align-content-start" variant="on">
              <RefSelect
                code="PER_REL"
                v-model="pc.relationship_id"
                :currentCode="pc.relationship_code || ''"
                :otherValue="pc.relationship_other || ''"
                @update:otherValue="(v) => { pc.relationship_other = v }"
              />
              <label class="block mb-1">Relationship</label>
            </FloatLabel>
          </div>

          <FloatLabel variant="on" class="field w-12 md:w-12 mt-2">
            <Textarea inputId="notes" v-model="pc.notes" autoResize rows="3" class="w-full" />
            <label for="notes">Notes</label>
          </FloatLabel>

          <div class="flex justify-content-end gap-2 mt-3">
            <button class="p-button p-component p-button-text" type="button" @click="goBack"><span class="p-button-label">Cancel</span></button>
            <button class="p-button p-component" type="button" @click="onCreateSave" :disabled="creating"><span class="p-button-icon pi pi-check mr-1"></span><span class="p-button-label">Save</span></button>
          </div>
        </div>
      </template>
      <template v-else-if="pc && pc.id">
        <div class="flex-row">
          <FloatLabel variant="on" class="row field w-full">
            <PersonSelect v-model="pc.person_id" :shepherds="true" :agency="true" :subjects="false" @update:modelValue="onChangePerson" />
            <label class="block mb-1">Person</label>
          </FloatLabel>

          <!-- Person quick info and editing -->
          <div class="row field w-full">
            <div class="flex flex-column gap-3">
              <div class="grid" style="grid-template-columns: 1fr 1fr; gap: .75rem;">
                <template v-if="pc.person?.phone">
                  <a :href="telHref(pc.person.phone)" class="link-btn" @click.stop>
                    📞
                  </a>
                </template>
                <FloatLabel variant="on">
                  <InputText v-model="pc.person.phone" class="w-full" @blur="onBlurPhone" />
                  <label class="block mb-1">Phone</label>
                </FloatLabel>
                <template v-if="pc.person?.email">
                  <a :href="mailtoHref(pc.person.email)" class="link-btn" @click.stop>
                    ✉️
                  </a>
                </template>
                <FloatLabel variant="on">
                  <InputText v-model="pc.person.email" class="w-full" @blur="onBlurEmail" />
                  <label class="block mb-1">Email</label>
                </FloatLabel>
              </div>
            </div>
          </div>

          <div class="flex gap-3  align-content-start">
            <FloatLabel class="field w-6  align-content-start" variant="on">
              <RefSelect
                code="PER_REL"
                v-model="pc.relationship_id"
                :currentCode="pc.relationship_code || ''"
                :otherValue="pc.relationship_other || ''"
                @update:otherValue="(v) => { pc.relationship_other = v }"
                @otherCommit="onCommitOther"
                @change="onChangeRelationship"
              />
              <label class="block mb-1">Relationship</label>
            </FloatLabel>
          </div>

          <FloatLabel variant="on" class="field w-12 md:w-12">
            <Textarea inputId="notes" v-model="pc.notes" autoResize rows="3" class="w-full" @blur="onBlurNotes" />
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
</style>
