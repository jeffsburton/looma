<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import FloatLabel from 'primevue/floatlabel'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import Messages from '@/components/Messages.vue'
import api from '@/lib/api'
import { hasPermission } from '@/lib/permissions'
import UnseenMessageCount from "@/components/common/UnseenMessageCount.vue";
import { useRoute } from 'vue-router'


const props = defineProps({
  caseId: { type: [String, Number], required: true }
})

// Permissions
const canCreate = computed(() => hasPermission('TASKS.CREATE'))
const canComplete = computed(() => hasPermission('TASKS.COMPLETE'))

// Filters
const showCompleted = ref(false) // default off per requirements

// Data
const loading = ref(false)
const tasks = ref([])

// Expanded rows map for DataTable row expansion
const expandedRows = ref({})

const route = useRoute()

// Client-side filter for completed
const displayedTasks = computed(() => {
  const arr = Array.isArray(tasks.value) ? tasks.value : []
  return showCompleted.value ? arr : arr.filter(t => !t.completed)
})

// Lightweight people cache for display of "Assigned by" and for Dropdown options
const personMap = ref({})
const personOptions = ref([])
const personsLoaded = ref(false)

async function loadPersonsOnce() {
  if (personsLoaded.value) return
  try {
    const { data } = await api.get('/api/v1/persons/select', { params: { shepherds: true, non_shepherds: true } })
    const map = {}
    const arr = Array.isArray(data) ? data : []
    for (const p of arr) {
      if (p && p.id) {
        map[p.id] = {
          id: p.id,
          name: p.name || 'Unknown',
          photo_url: p.photo_url || '/images/pfp-generic.png',
        }
      }
    }
    personMap.value = map
    personOptions.value = Object.values(map).map(p => ({ label: p.name, value: p.id }))
  } finally {
    personsLoaded.value = true
  }
}

function getPerson(opaqueId) {
  if (!opaqueId) return null
  return personMap.value[opaqueId] || null
}

onMounted(() => { loadPersonsOnce() })

async function loadTasks() {
  loading.value = true
  try {
    const params = {}
    // Always load the full list; completion filtering is handled client-side
    const { data } = await api.get(`/api/v1/cases/${props.caseId}/tasks`, { params })
    tasks.value = Array.isArray(data) ? data : []

    // Handle deep-link to a specific task by raw id
    const rawTaskId = route.params.rawTaskId ? String(route.params.rawTaskId) : null
    if (rawTaskId) {
      try {
        const { data: target } = await api.get(`/api/v1/cases/${props.caseId}/tasks/${encodeURIComponent(rawTaskId)}`)
        if (target && target.id) {
          // Ensure completed tasks are visible if needed
          if (target.completed && !showCompleted.value) {
            showCompleted.value = true
            await nextTick()
          }
          // Expand the row for this task in DataTable
          const val = target.id
          expandedRows.value = { ...(expandedRows.value || {}), [val]: true }
          await nextTick()
          // Scroll to the row/title cell
          try {
            const el = document.querySelector(`[data-task-id="${val}"]`)
            if (el && el.scrollIntoView) {
              el.scrollIntoView({ behavior: 'smooth', block: 'center' })
            }
          } catch (_) { /* noop */ }
        }
      } catch (e) {
        // ignore if not found or access denied
      }
    }
  } finally {
    loading.value = false
  }
}

watch(() => [props.caseId], loadTasks, { immediate: true })

// Ensure edit buffers exist when rows become expanded (programmatic or user)
watch(expandedRows, (val) => {
  if (!val) return
  for (const [id, isOpen] of Object.entries(val)) {
    if (!isOpen) continue
    const task = tasks.value.find(t => String(t.id) === String(id))
    if (task && !task._isNew) ensureEdit(task)
  }
}, { deep: true })

// New task creation state (now used inside expansion)
const adding = ref(false)
const newTitle = ref('')
const newDescription = ref('')
const newRowId = ref('')

async function createNewTask() {
  const title = (newTitle.value || '').trim()
  if (!title) return // do not create until name has something in it
  try {
    const payload = { title, description: newDescription.value || '' }
    await api.post(`/api/v1/cases/${props.caseId}/tasks`, payload)
  } finally {
    // Regardless of success/failure, reset UI; errors will surface via global handler
    removeNewRow()
    await loadTasks()
  }
}

function removeNewRow() {
  if (!newRowId.value) return
  const idx = tasks.value.findIndex(t => t.id === newRowId.value)
  if (idx >= 0) tasks.value.splice(idx, 1)
  const expanded = { ...(expandedRows.value || {}) }
  delete expanded[newRowId.value]
  expandedRows.value = expanded
  adding.value = false
  newTitle.value = ''
  newDescription.value = ''
  newRowId.value = ''
}

// Editing state per task (local copies)
const edits = ref({}) // id -> { description, response, ready_for_review, completed, assigned_by_id, title }

function ensureEdit(task) {
  if (!task?.id) return
  const id = task.id
  if (!edits.value[id]) {
    edits.value[id] = {
      assigned_by_id: task.assigned_by_id || '',
      title: task.title || '',
      description: task.description || '',
      response: task.response || '',
      ready_for_review: !!task.ready_for_review,
      completed: !!task.completed,
    }
  }
}

function onRowExpand(event) {
  const t = event?.data
  if (t) ensureEdit(t)
}

// Auto-save machinery
const saveTimers = ref({}) // id -> timer
const pendingPatches = ref({}) // id -> { field: value }

function queueSave(task, patch) {
  if (!task?.id) return
  const id = task.id
  // Merge patch
  pendingPatches.value[id] = { ...(pendingPatches.value[id] || {}), ...patch }

  // Permission gating per field (per requirements)
  const allowed = {}
  for (const [k, v] of Object.entries(pendingPatches.value[id])) {
    if (k === 'completed') {
      if (canComplete.value) allowed[k] = v
    } else if (k === 'title' || k === 'description' || k === 'assigned_by_id') {
      if (canCreate.value) allowed[k] = v
    } else {
      // response, ready_for_review, and any other fields allowed for all
      allowed[k] = v
    }
  }
  pendingPatches.value[id] = allowed

  // Debounce per task
  if (saveTimers.value[id]) {
    clearTimeout(saveTimers.value[id])
  }
  saveTimers.value[id] = setTimeout(async () => {
    const patchToSend = pendingPatches.value[id]
    delete pendingPatches.value[id]
    delete saveTimers.value[id]
    if (!patchToSend || Object.keys(patchToSend).length === 0) return
    try {
      const { data } = await api.patch(`/api/v1/cases/${props.caseId}/tasks/${id}`, patchToSend)
      // Update in list
      const idx = tasks.value.findIndex(t => t.id === id)
      if (idx >= 0) tasks.value[idx] = data
    } catch (_) {
      // handled globally
    }
  }, 500)
}

function startAdd() {
  // Insert a temporary row and expand it
  if (adding.value) return
  const id = `_new_${Date.now()}`
  newRowId.value = id
  const placeholder = {
    id,
    case_id: props.caseId,
    assigned_by_id: null,
    title: '',
    description: '',
    response: '',
    ready_for_review: false,
    completed: false,
    _isNew: true,
  }
  tasks.value = [placeholder, ...tasks.value]
  expandedRows.value = { ...(expandedRows.value || {}), [id]: true }
  adding.value = true
  newTitle.value = ''
  newDescription.value = ''
}

function cancelAdd() {
  removeNewRow()
}

</script>

<template>
  <div class="p-2">
    <!-- Toolbar: search, add (permission), show completed toggle -->
    <div class="flex gap-2 align-items-center flex-wrap mb-3">
      <div class="flex align-items-center gap-2">
          <ToggleSwitch id="showCompleted" v-model="showCompleted" />
          <label for="showCompleted">Show completed</label>
      </div>
      <div class="ml-auto flex align-items-center gap-2">
        <Button v-if="canCreate" label="Add" icon="pi pi-plus" @click="startAdd" />
      </div>
    </div>

    <!-- Tasks Table with Row Expansion -->
    <DataTable :value="displayedTasks" dataKey="id" v-model:expandedRows="expandedRows"
               size="small"  :loading="loading" class="w-full" @rowExpand="onRowExpand">
      <Column expander style="width: 3rem" />
      <Column header="" style="width:48px">
        <template #body="{ data }">
          <UnseenMessageCount TableName="task" :CaseId="caseId" :TaskId="data.id">
            <div class="flex align-items-center">
              <span class="material-symbols-outlined text-900 font-medium">assignment</span>
            </div>
          </UnseenMessageCount>
        </template>
      </Column>
      <Column header="Assigned by">
        <template #body="{ data }">
          <div class="flex align-items-center gap-2">
            <img :src="getPerson(data.assigned_by_id)?.photo_url || '/images/pfp-generic.png'" alt="pfp" class="avatar-sm" />
            <span class="text-900 font-medium name-clip">{{ getPerson(data.assigned_by_id)?.name || 'Unknown' }}</span>
          </div>
        </template>
      </Column>
      <Column field="title" header="Title">
        <template #body="{ data }">
          <span class="text-900" :class="data.title_hit ? 'search_highlight' : ''" :data-task-id="data.id" data-part="title">{{ data.title }}</span>
        </template>
      </Column>
      <Column field="description" header="Description">
        <template #body="{ data }">
          <span :class="data.description_hit ? 'search_highlight' : ''" :data-task-id="data.id" data-part="description">{{ data.description }}</span>
        </template>
      </Column>
      <Column header="Ready for review" style="width:160px">
        <template #body="{ data }">
          <span v-if="data.ready_for_review" class="material-symbols-outlined text-yellow-200" title="Ready for review">hand_gesture</span>
          <span v-else>—</span>
        </template>
      </Column>
      <Column header="Completed" style="width:130px">
        <template #body="{ data }">
          <span v-if="data.completed" class="material-symbols-outlined text-green-600" title="Completed">check_circle</span>
          <span v-else>—</span>
        </template>
      </Column>

      <template #expansion="slotProps">
        <div class="surface-card p-3 border-1 surface-border border-round mb-3">
          <div v-if="slotProps.data._isNew">
            <div class="grid formgrid p-fluid gap-3">
              <div class="col-12 md:col-6">
                <FloatLabel variant="on">
                  <InputText id="newTitle" v-model="newTitle" class="w-full" />
                  <label for="newTitle">Task name</label>
                </FloatLabel>
              </div>
              <div class="col-12">
                <FloatLabel variant="on">
                  <Textarea id="newDesc" v-model="newDescription" class="w-full" autoResize rows="3" />
                  <label for="newDesc">Description</label>
                </FloatLabel>
              </div>
            </div>
            <div class="flex gap-2 justify-content-end mt-2">
              <Button label="Cancel" text @click="cancelAdd" />
              <Button label="Create" icon="pi pi-check" @click="createNewTask" :disabled="!(newTitle && newTitle.trim())" />
            </div>
          </div>
          <div v-else>
            <div class="grid formgrid p-fluid gap-3">
              <div class="col-12 md:col-6">
                <FloatLabel variant="on">
                  <Dropdown id="assignedBy" class="w-full" :options="personOptions" optionLabel="label" optionValue="value"
                            v-model="edits[slotProps.data.id].assigned_by_id"
                            :disabled="!canCreate"
                            @change="queueSave(slotProps.data, { assigned_by_id: edits[slotProps.data.id].assigned_by_id })" />
                  <label for="assignedBy">Assigned by</label>
                </FloatLabel>
              </div>
              <div class="col-12 md:col-6">
                <FloatLabel variant="on">
                  <InputText id="titleEdit" class="w-full" v-model="edits[slotProps.data.id].title"
                             :disabled="!canCreate"
                             @input="queueSave(slotProps.data, { title: edits[slotProps.data.id].title })" />
                  <label for="titleEdit">Title</label>
                </FloatLabel>
              </div>
              <div class="col-12">
                <FloatLabel variant="on">
                  <Textarea id="descEdit" class="w-full" autoResize rows="3"
                            v-model="edits[slotProps.data.id].description"
                            :disabled="!canCreate"
                            @input="queueSave(slotProps.data, { description: edits[slotProps.data.id].description })" />
                  <label for="descEdit">Description</label>
                </FloatLabel>
              </div>
              <div class="col-12">
                <FloatLabel variant="on">
                  <Textarea id="respEdit" class="w-full" autoResize rows="3"
                            v-model="edits[slotProps.data.id].response"
                            @input="queueSave(slotProps.data, { response: edits[slotProps.data.id].response })" />
                  <label for="respEdit">Response</label>
                </FloatLabel>
              </div>
              <div class="col-12 md:col-6 flex align-items-center gap-2">
                <ToggleSwitch id="rfrEdit" v-model="edits[slotProps.data.id].ready_for_review"
                              @change="queueSave(slotProps.data, { ready_for_review: edits[slotProps.data.id].ready_for_review })" />
                <label for="rfrEdit">Ready for review</label>
              </div>
              <div class="col-12 md:col-6 flex align-items-center gap-2">
                <ToggleSwitch id="completedEdit" :disabled="!canComplete"
                              v-model="edits[slotProps.data.id].completed"
                              @change="queueSave(slotProps.data, { completed: edits[slotProps.data.id].completed })" />
                <label for="completedEdit">Completed</label>
              </div>
            </div>
            <div class="mt-3">
              <p>Ask questions, provide updates here:</p>
              <Messages :caseId="props.caseId" filterByFieldName="task_id" :filterByFieldId="slotProps.data.id" />
            </div>
          </div>
        </div>
      </template>
    </DataTable>
  </div>
</template>

<style scoped>
.avatar-sm { width: 24px; height: 24px; border-radius: 999px; object-fit: cover; }
.name-clip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.p-accordionheader { background-color: var(--p-primary-200) }
.p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader {  background-color: var(--p-primary-200)  }
.p-accordionpanel:not(.p-disabled):not(p-accordionpanel-active) > .p-accordionheader:hover {  background-color: var(--p-primary-300)  }

</style>
