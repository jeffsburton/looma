<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import Select from 'primevue/select'
import Button from 'primevue/button'
import SplitButton from 'primevue/splitbutton'
import Dialog from 'primevue/dialog'
import Badge from 'primevue/badge'
import api from '../lib/api'
import { hasPermission } from '../lib/permissions'
import PersonEditor from './contacts/Person.vue'
import SubjectEditor from './contacts/Subject.vue'

const props = defineProps({
  modelValue: { type: String, default: '' }, // opaque id (person or subject)
  shepherds: { type: Boolean, default: true }, // person records where organization_id = 1
  agency: { type: Boolean, default: true },    // person records where organization_id > 1
  subjects: { type: Boolean, default: false }, // subject records
  disabled: { type: Boolean, default: false },
  filter: { type: Boolean, default: true },
  caseNumber: { type: [String, Number], default: null },
  addButton: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue', 'change'])

const selectedId = ref(props.modelValue || '')
watch(() => props.modelValue, (v) => { selectedId.value = v || '' })
watch(selectedId, (v) => { emit('update:modelValue', v) })

const options = ref([])
const loading = ref(false)

async function loadOptions() {
  loading.value = true
  try {
    // If a caseNumber is provided, list only subjects linked to that case via subject_case
    const caseNum = props.caseNumber
    if (caseNum !== null && String(caseNum).trim() !== '') {
      try {
        const url = `/api/v1/cases/${encodeURIComponent(String(caseNum))}/subjects`
        const { data } = await api.get(url)
        const arr = Array.isArray(data) ? data : []
        options.value = arr.map(r => ({
          id: r?.subject?.id,
          name: `${r?.subject?.first_name || ''} ${r?.subject?.last_name || ''}`.trim() || 'Subject',
          photo_url: r?.subject?.photo_url,
          is_shepherd: false,
          organization_name: r?.relationship_name || '',
          team_photo_urls: [],
          dangerous: r?.subject?.dangerous,
          danger: r?.subject?.danger,
        }))
      } catch (e) {
        console.error(e)
        options.value = []
      }
      return
    }

    // If only subjects should be listed, skip loading persons entirely
    if (props.subjects && !props.shepherds && !props.agency) {
      try {
        const { data } = await api.get('/api/v1/subjects/select')
        const subs = Array.isArray(data) ? data : []
        options.value = (subs || []).map(s => ({
          id: s.id, // opaque subject id like subj:...
          name: s.name,
          photo_url: s.photo_url,
          is_shepherd: false,
          organization_name: s.has_subject_case ? 'Missing Person' : 'Related to Investigation',
          team_photo_urls: [],
          dangerous: s.dangerous,
          danger: s.danger,
        }))
      } catch (e) {
        options.value = []
      }
      return
    }

    // If neither shepherds nor agency requested, and subjects isn't sole true, nothing to load
    if (!props.shepherds && !props.agency && !props.subjects) {
      options.value = []
      return
    }

    // Fetch people according to shepherds/agency mapping (agency -> non_shepherds on server)
    if (props.shepherds || props.agency) {
      const qs = new URLSearchParams({ shepherds: String(!!props.shepherds), non_shepherds: String(!!props.agency) })
      const { data } = await api.get(`/api/v1/persons/select?${qs.toString()}`)
      const people = Array.isArray(data) ? data : []
      options.value = people
    } else {
      options.value = []
    }

    // Optionally include subjects in addition to people
    if (props.subjects) {
      try {
        const { data } = await api.get('/api/v1/subjects/select')
        const subs = Array.isArray(data) ? data : []
        const mapped = (subs || []).map(s => ({
          id: s.id, // opaque subject id like subj:...
          name: s.name,
          photo_url: s.photo_url,
          is_shepherd: false,
          organization_name: s.has_subject_case ? 'Missing Person' : 'Related to Investigation',
          team_photo_urls: [],
          dangerous: s.dangerous,
          danger: s.danger,
        }))
        options.value = [...options.value, ...mapped]
      } catch {}
    }
  } finally {
    loading.value = false
  }
}

watch(() => [props.shepherds, props.agency, props.subjects, props.caseNumber], loadOptions, { immediate: true })

const selectedOption = computed(() => options.value.find(o => o.id === selectedId.value))

// Permissions
const canModify = computed(() => hasPermission('CONTACTS.MODIFY'))

// Add overlay state
const addVisible = ref(false)
const addType = ref('person') // 'person' or 'subject'
const editorModel = ref({ kind: 'person', id: null, first_name: '', last_name: '', phone: '', email: '', telegram: '', organization_id: null, dangerous: false, danger: '' })

function openAddShepherd() {
  addType.value = 'person'
  editorModel.value = { kind: 'person', id: null, first_name: '', last_name: '', phone: '', email: '', telegram: '', organization_id: 1, dangerous: false, danger: '' }
  addVisible.value = true
}
function openAddAgency() {
  addType.value = 'person'
  editorModel.value = { kind: 'person', id: null, first_name: '', last_name: '', phone: '', email: '', telegram: '', organization_id: null, dangerous: false, danger: '' }
  addVisible.value = true
}
function openAddSubject() {
  addType.value = 'subject'
  editorModel.value = { kind: 'subject', id: null, first_name: '', last_name: '', phone: '', email: '', dangerous: false, danger: '' }
  addVisible.value = true
}

async function onCreated(created) {
  addVisible.value = false
  await loadOptions()
  // Try to select the newly created record if id is available
  const newId = created?.id
  if (newId) {
    selectedId.value = newId
    await nextTick()
  }
}
</script>

<template>
  <Select
    v-model="selectedId"
    :options="options"
    optionLabel="name"
    optionValue="id"
    :filter="filter"
    :loading="loading"
    class="w-full"
    :disabled="disabled || ((!subjects && !shepherds && !agency) && !(caseNumber !== null && String(caseNumber).trim() !== ''))"
    @update:modelValue="(v) => emit('change', v)"
  >
    <template #option="{ option }">
      <div class="flex align-items-center gap-2 w-full">
        <img :src="option.photo_url" :alt="option.name" class="avatar" />
        <div class="min-w-0 flex-1">
          <!-- First row: name and, for shepherds, the team avatar group on the right -->
          <div class="flex align-items-center w-full">
            <div class="text-900 name-clip flex-1">{{ option.name }}</div>
            <div v-if="option.dangerous"  class="flex align-items-center gap-1 ml-2 team-pfps"><Badge :value="option.danger" severity="danger" /></div>
            <div v-if="option.is_shepherd && option.team_photo_urls?.length" class="flex align-items-center gap-1 ml-2 team-pfps">
              <img v-for="(u, idx) in option.team_photo_urls" :key="idx" :src="u" class="team-avatar" alt="team" />
            </div>
          </div>
          <!-- Second row (only for non-shepherds): organization name -->
          <div v-if="!option.is_shepherd && option.organization_name" class="text-600 text-xs">{{ option.organization_name }}</div>
        </div>
      </div>
    </template>
    <template #value="{ value }">
      <div v-if="selectedOption" class="flex align-items-center gap-2 w-full">
        <img :src="selectedOption.photo_url" :alt="selectedOption.name" class="avatar" />
        <div class="min-w-0 flex-1">
          <div class="flex align-items-center w-full">
            <div class="text-900 name-clip flex-1">{{ selectedOption.name }}</div>
            <div v-if="selectedOption.dangerous"  class="flex align-items-center gap-1 ml-2 team-pfps"><Badge :value="selectedOption.danger" severity="danger" /></div>
            <div v-if="selectedOption.is_shepherd && selectedOption.team_photo_urls?.length" class="flex align-items-center gap-1 ml-2 team-pfps">
              <img v-for="(u, idx) in selectedOption.team_photo_urls" :key="idx" :src="u" class="team-avatar" alt="team" />
            </div>
          </div>
          <div v-if="!selectedOption.is_shepherd && selectedOption.organization_name" class="text-600 text-xs">{{ selectedOption.organization_name }}</div>
        </div>
      </div>
    </template>

    <template v-if="filter && canModify && addButton" #footer>
      <div class="p-2 border-top-1 surface-border flex justify-content-end">
        <Button v-if="subjects && !shepherds && !agency" label="Add" icon="pi pi-plus" size="small" text @click.stop.prevent="openAddSubject" />
        <Button v-else-if="shepherds && !agency && !subjects" label="Add" icon="pi pi-plus" size="small" text @click.stop.prevent="openAddShepherd" />
        <SplitButton
          v-else
          label="Add"
          icon="pi pi-plus"
          size="small"
          text
          :model="[
            ...(shepherds ? [{ label: 'Shepherd', command: openAddShepherd }] : []),
            ...(agency ? [{ label: 'Agency Personnel', command: openAddAgency }] : []),
            ...(subjects ? [{ label: 'Investigatory Subject', command: openAddSubject }] : []),
          ]"
        />
      </div>
    </template>
  </Select>

  <Dialog v-model:visible="addVisible" modal :header="addType === 'subject' ? 'New Investigatory Subject' : 'New Person'" :style="{ width: '640px' }">
    <div class="dialog-body-pad">
      <PersonEditor
        v-if="addType === 'person'"
        v-model="editorModel"
        :isNew="true"
        :canModify="canModify"
        @create="onCreated"
        @cancel="addVisible=false"
      />
      <SubjectEditor
        v-else
        v-model="editorModel"
        :isNew="true"
        :canModify="canModify"
        @create="onCreated"
        @cancel="addVisible=false"
      />
    </div>
  </Dialog>
</template>

<style scoped>
.avatar { width: 28px; height: 28px; border-radius: 999px; object-fit: cover; }
.team-avatar { width: 18px; height: 18px; border-radius: 999px; object-fit: cover; }
.name-clip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.team-pfps { flex-shrink: 0; }
.dialog-body-pad { padding-top: .5rem; }
</style>
