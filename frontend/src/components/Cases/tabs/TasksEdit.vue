<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import api from '@/lib/api'
import { hasPermission } from '@/lib/permissions'
import FloatLabel from 'primevue/floatlabel'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import Messages from '@/components/Messages.vue'

const route = useRoute()
const router = useRouter()

const props = defineProps({
  caseId: { type: [String, Number], required: true }
})

const canCreate = computed(() => hasPermission('TASKS.CREATE'))
const canComplete = computed(() => hasPermission('TASKS.COMPLETE'))

const caseNumber = computed(() => String(route.params.caseNumber || ''))
const rawTaskId = computed(() => String(route.params.rawTaskId || ''))
const isCreate = computed(() => rawTaskId.value === 'new')

const loading = ref(false)
const saving = ref(false)
const error = ref('')

// People map for displaying "Assigned by"
const personMap = ref({})
const personsLoaded = ref(false)
function getPerson(id) {
  if (!id) return null
  return personMap.value[id] || null
}
async function loadPersonsOnce() {
  if (personsLoaded.value) return
  try {
    const { data } = await api.get('/api/v1/persons/select', { params: { shepherds: true, non_shepherds: true } })
    const arr = Array.isArray(data) ? data : []
    const map = {}
    for (const p of arr) {
      if (p && p.id) {
        map[p.id] = { id: p.id, name: p.name || 'Unknown', photo_url: p.photo_url || '/images/pfp-generic.png' }
      }
    }
    personMap.value = map
  } finally {
    personsLoaded.value = true
  }
}

// Task model
const form = ref({
  id: '',
  assigned_by_id: '',
  title: '',
  description: '',
  response: '',
  ready_for_review: false,
  completed: false,
})

function goBack() {
  router.replace({ name: 'case-detail', params: { caseNumber: caseNumber.value, tab: 'tasks' } })
}

async function load() {
  if (isCreate.value) {
    return
  }
  if (!rawTaskId.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/tasks/${encodeURIComponent(rawTaskId.value)}`)
    const r = data || {}
    form.value = {
      id: r.id,
      assigned_by_id: r.assigned_by_id || '',
      title: r.title || '',
      description: r.description || '',
      response: r.response || '',
      ready_for_review: !!r.ready_for_review,
      completed: !!r.completed,
    }
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load task.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => { await Promise.all([loadPersonsOnce(), load()]) })

async function onCreateSave() {
  error.value = ''
  const title = (form.value.title || '').trim()
  if (!title) {
    error.value = 'Please enter a title.'
    return
  }
  saving.value = true
  try {
    const payload = {
      title,
      description: form.value.description || '',
    }
    await api.post(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/tasks`, payload)
    goBack()
  } catch (e) {
    console.error(e)
    error.value = 'Failed to create task.'
  } finally {
    saving.value = false
  }
}

async function patch(payload) {
  if (!form.value.id) return
  try {
    await api.patch(`/api/v1/cases/${encodeURIComponent(caseNumber.value)}/tasks/${encodeURIComponent(form.value.id)}`, payload)
  } catch (e) {
    console.error(e)
    error.value = 'Failed to update task.'
    throw e
  }
}


async function onBlurTitle() {
  if (!canCreate.value) return
  try {
    await patch({ title: form.value.title || '' })
  } catch (_) {}
}

async function onBlurDesc() {
  if (!canCreate.value) return
  try {
    await patch({ description: form.value.description || '' })
  } catch (_) {}
}

async function onBlurResponse() {
  try {
    await patch({ response: form.value.response || '' })
  } catch (_) {}
}

async function onToggleReady(v) {
  try {
    await patch({ ready_for_review: !!v })
  } catch (_) {}
}

async function onToggleCompleted(v) {
  if (!canComplete.value) return
  try {
    await patch({ completed: !!v })
  } catch (_) {}
}
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center gap-2 mb-3">
      <button class="icon-button" @click="goBack" title="Back">
        <span class="material-symbols-outlined">arrow_back</span>
      </button>
      <div class="text-lg font-semibold">{{ isCreate ? 'Add Task' : 'Edit Task' }}</div>
    </div>

    <div v-if="error" class="p-error mb-2">{{ error }}</div>

    <div class="surface-card border-round p-3">
      <div v-if="loading && !isCreate" class="text-600">Loading...</div>
      <template v-else-if="isCreate">
        <div class="grid formgrid p-fluid gap-3">
          <div class="col-12 md:col-6">
            <FloatLabel variant="on">
              <InputText id="title" v-model="form.title" class="w-full" />
              <label for="title">Title</label>
            </FloatLabel>
          </div>
          <div class="col-12">
            <FloatLabel variant="on">
              <Textarea id="desc" v-model="form.description" class="w-full" autoResize rows="3" />
              <label for="desc">Description</label>
            </FloatLabel>
          </div>
        </div>
        <div class="flex justify-content-end gap-2 mt-3">
          <button class="p-button p-component p-button-text" type="button" @click="goBack"><span class="p-button-label">Cancel</span></button>
          <button class="p-button p-component" type="button" @click="onCreateSave" :disabled="saving || !(form.title && form.title.trim())"><span class="p-button-icon pi pi-check mr-1"></span><span class="p-button-label">Save</span></button>
        </div>
      </template>
      <template v-else-if="form && form.id">
        <!-- Read-only Assigned By display at top -->
        <div class="flex align-items-center gap-2 mb-3">
          <img :src="getPerson(form.assigned_by_id)?.photo_url || '/images/pfp-generic.png'" alt="pfp" class="avatar-sm" />
          <div class="text-900 font-medium">Assigned by: {{ getPerson(form.assigned_by_id)?.name || 'Unknown' }}</div>
        </div>
        <div class="grid formgrid p-fluid gap-3">
          <div class="col-12 md:col-6">
            <FloatLabel variant="on">
              <InputText id="titleEdit" v-model="form.title" class="w-full" :disabled="!canCreate" @blur="onBlurTitle" />
              <label for="titleEdit">Title</label>
            </FloatLabel>
          </div>
          <div class="col-12">
            <FloatLabel variant="on">
              <Textarea id="descEdit" v-model="form.description" class="w-full" autoResize rows="3" :disabled="!canCreate" @blur="onBlurDesc" />
              <label for="descEdit">Description</label>
            </FloatLabel>
          </div>
          <div class="col-12">
            <FloatLabel variant="on">
              <Textarea id="respEdit" v-model="form.response" class="w-full" autoResize rows="3" @blur="onBlurResponse" />
              <label for="respEdit">Response</label>
            </FloatLabel>
          </div>
          <div class="col-12 md:col-6 flex align-items-center gap-2">
            <ToggleSwitch id="rfr" v-model="form.ready_for_review" @update:modelValue="onToggleReady" />
            <label for="rfr">Ready for review</label>
          </div>
          <div class="col-12 md:col-6 flex align-items-center gap-2">
            <ToggleSwitch id="completed" v-model="form.completed" :disabled="!canComplete" @update:modelValue="onToggleCompleted" />
            <label for="completed">Completed</label>
          </div>
        </div>
        <div class="mt-3">
          <p>Ask questions, provide updates here:</p>
          <Messages :caseId="props.caseId" filterByFieldName="task_id" :filterByFieldId="form.id" />
        </div>
      </template>
      <div v-else class="p-2 text-600">Not found</div>
    </div>
  </div>
</template>

<style scoped>
.icon-button { background: transparent; border: none; padding: .25rem; cursor: pointer; border-radius: 4px; }
.icon-button:hover { background: rgba(0,0,0,0.04); }
.avatar-sm { width: 24px; height: 24px; border-radius: 999px; object-fit: cover; }
</style>
