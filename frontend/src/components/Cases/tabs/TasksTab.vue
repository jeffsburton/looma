<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'
import Accordion from 'primevue/accordion';
import AccordionPanel from 'primevue/accordionpanel';
import AccordionHeader from 'primevue/accordionheader';
import AccordionContent from 'primevue/accordioncontent';
import FloatLabel from 'primevue/floatlabel'
import Textarea from 'primevue/textarea'
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

// Track open panels for programmatic control
const openPanels = ref([])

const route = useRoute()

// Client-side filter for completed
const displayedTasks = computed(() => {
  const arr = Array.isArray(tasks.value) ? tasks.value : []
  return showCompleted.value ? arr : arr.filter(t => !t.completed)
})

// Lightweight people cache for display of "Assigned by"
const personMap = ref({})
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
          // Open the accordion panel for this task
          const val = target.id
          const set = new Set(openPanels.value || [])
          set.add(val)
          openPanels.value = Array.from(set)
          await nextTick()
          // Scroll to the panel
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

// New task creation state
const adding = ref(false)
const newTitle = ref('')
const newDescription = ref('')

async function createNewTask() {
  const title = (newTitle.value || '').trim()
  if (!title) return // do not create until name has something in it
  try {
    const payload = { title, description: newDescription.value || '' }
    await api.post(`/api/v1/cases/${props.caseId}/tasks`, payload)
    // Reset add state and refresh list
    adding.value = false
    newTitle.value = ''
    newDescription.value = ''
    // Prepend or reload
    await loadTasks()
    // Expand newly created by focusing search to its name if needed
  } catch (e) {
    // handled globally
  }
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

function onPanelOpen(idx) {
  // idx can be index or value depending on Accordion; try index against displayed list first
  let t = (Array.isArray(displayedTasks.value) && typeof idx === 'number') ? displayedTasks.value[idx] : null
  if (!t) {
    // Fallback: try to find by id/value
    t = tasks.value.find(x => x.id === idx)
  }
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

  // Permission gating per field
  const allowed = {}
  for (const [k, v] of Object.entries(pendingPatches.value[id])) {
    if (k === 'completed') {
      if (canComplete.value) allowed[k] = v
    } else {
      if (canCreate.value) allowed[k] = v
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
  adding.value = true
  newTitle.value = ''
  newDescription.value = ''
}

function cancelAdd() {
  adding.value = false
  newTitle.value = ''
  newDescription.value = ''
}


// ========================
// Search implementation
// ========================


import { useSearchable } from '../../common/SearchComposable'
async function search(query) {
  const hits = []
  const lowerQuery = String(query || '').toLowerCase()

  const all = Array.isArray(tasks.value) ? tasks.value : []
  for (const t of all) {
    if (!showCompleted.value && t.completed)
      continue
    const title = String(t.title || '')
    const desc = String(t.description || '')
    const resp = String(t.response || '')
    if (title.toLowerCase().includes(lowerQuery))
      hits.push({ id: `${t.id}`, part: 'title_hit' })
    if (desc.toLowerCase().includes(lowerQuery))
      hits.push({ id: `${t.id}`, part: 'description_hit' })
    if (resp.toLowerCase().includes(lowerQuery))
      hits.push({ id: `${t.id}`, part: 'response_hit' })
  }

  // If we have hits, ensure their panels are open and completed visibility is on when needed
  if (hits.length) {
    // Determine if any hit is on a completed task
    const set = new Set(openPanels.value || [])
    for (const h of hits) {
      const t = all.find(x => String(x.id) === String(h.id))
      if (t) {
        set.add(t.id)
      }
    }
    openPanels.value = Array.from(set)
  }

  return hits
}

async function showSearchHit(hit) {
  clearHighlights()
  const all = Array.isArray(tasks.value) ? tasks.value : []
  const target = all.find(t => String(t.id) === String(hit.id))

  if (target) {
    target[hit.part] = true
    // Ensure panel is open
    const set = new Set(openPanels.value || [])
    set.add(target.id)
    openPanels.value = Array.from(set)
    // If completed and hidden, reveal
    if (target.completed && !showCompleted.value) {
      showCompleted.value = true
      await nextTick()
    }
  }

  // Scroll to the hit element (field-level), fallback to the panel
  await nextTick()
  try {
    const id = String(hit.id)
    const part = String(hit.part || '')
    let el = document.querySelector(`[data-task-id="${id}"][data-part="${part}"]`)
    if (!el) {
      el = document.querySelector(`[data-task-id="${id}"]`)
    }
    if (el && el.scrollIntoView) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  } catch (_) { /* noop */ }
}

function clearHighlights() {
    const all = Array.isArray(tasks.value) ? tasks.value : []
    for (const t of all) {
      t.title_hit = t.description_hit = t.response_hit = false
    }
}

// Map child component instance uid -> task id
const childUidToTaskId = ref(new Map())

function makeMessagesRef(taskId) {
  return (comp) => {
    const uid = comp?.$?.uid
    if (uid != null) {
      childUidToTaskId.value.set(uid, taskId)
    }
  }
}

async function childHadSearchHit(data){
  const uid = data?.uid
  if (uid == null) return

  const taskId = childUidToTaskId.value.get(uid)
  if (taskId == null) return

  // Ensure panel is open
  const set = new Set(openPanels.value || [])
  set.add(taskId)
  openPanels.value = Array.from(set)

  // If the task is completed and currently hidden, reveal completed
  const t = (Array.isArray(tasks.value) ? tasks.value : []).find(x => String(x.id) === String(taskId))
  if (t?.completed && !showCompleted.value) {
    showCompleted.value = true
    await nextTick()
  }

  // Scroll into view for better UX
  await nextTick()
  try {
    const el = document.querySelector(`[data-task-id="${taskId}"]`)
    el?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
  } catch (_) { /* noop */ }
}

// Register this component as searchable
useSearchable("tasks_" + props.caseId, {
  search,
  showSearchHit,
  clearHighlights,
  childHadSearchHit
})




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

    <!-- New Task Form (only name and description) -->
    <div v-if="adding" class="surface-card p-3 border-1 surface-border border-round mb-3">
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

    <!-- Task list -->
    <Accordion multiple :lazy="false" v-model:value="openPanels" @tab-open="onPanelOpen">
      <AccordionPanel v-for="(t, idx) in displayedTasks" :key="t.id" :value="t.id" :data-task-id="t.id">
        <AccordionHeader >
          <div class="flex align-items-center gap-2">
            <UnseenMessageCount TableName="task" :CaseId="caseId" :TaskId="t.id">
              <div class="flex align-items-center">
                <span class="material-symbols-outlined text-900 font-medium">assignment</span>
              </div>
            </UnseenMessageCount>
            <span class="text-900 font-medium" :class="t.title_hit ? 'search_highlight' : ''" :data-task-id="t.id" data-part="title">{{ t.title }}</span>
            <span v-if="t.completed" class="material-symbols-outlined text-green-600" title="Completed">check_circle</span>
            <span v-else-if="t.ready_for_review" class="material-symbols-outlined text-yellow-200" title="Ready for review">hand_gesture</span>
          </div>
        </AccordionHeader>
        <AccordionContent>
          <div class="grid formgrid p-fluid gap-3 mt-3">
            <div class="col-12 md:col-6">
              <div class="flex align-items-center gap-2">
                <span class="text-700">Assigned by:</span>
                <img :src="getPerson(t.assigned_by_id)?.photo_url || '/images/pfp-generic.png'" alt="pfp" class="avatar-sm" />
                <span class="text-900 font-medium name-clip">{{ getPerson(t.assigned_by_id)?.name || 'Unknown' }}</span>
              </div>
            </div>
            <div class="col-12 md:col-6" v-if="false">
              <!-- Name field hidden for existing per requirements; kept here toggled off -->
              <FloatLabel variant="on">
                <InputText id="titleEdit" :modelValue="(edits[t.id]?.title ?? t.title)" @update:modelValue="val => { ensureEdit(t); edits[t.id].title = val; queueSave(t, { title: val }) }" :disabled="!canCreate" />
                <label for="titleEdit">Task name</label>
              </FloatLabel>
            </div>
            <div class="col-12" :class="t.description_hit ? 'search_highlight' : ''" :data-task-id="t.id" data-part="description">
              <FloatLabel variant="on">
                <Textarea id="descEdit" :modelValue="(edits[t.id]?.description ?? t.description)" @update:modelValue="val => { ensureEdit(t); edits[t.id].description = val; queueSave(t, { description: val }) }" class="w-full" autoResize rows="3" :disabled="!canCreate" />
                <label for="descEdit">Description</label>
              </FloatLabel>
            </div>
            <div class="col-12" :class="t.response_hit ? 'search_highlight' : ''" :data-task-id="t.id" data-part="response">
              <FloatLabel variant="on">
                <Textarea id="responseEdit" :modelValue="(edits[t.id]?.response ?? t.response)" @update:modelValue="val => { ensureEdit(t); edits[t.id].response = val; queueSave(t, { response: val }) }" class="w-full" autoResize rows="3" />
                <label for="responseEdit">Response</label>
              </FloatLabel>
            </div>
            <div class="col-12 md:col-6 flex gap-4">
              <div class="flex align-items-center gap-2 flex-1" v-if="!(edits[t.id]?.completed ?? t.completed)">
                  <ToggleSwitch id="rfrEdit" :modelValue="(edits[t.id]?.ready_for_review ?? t.ready_for_review)" @update:modelValue="val => { ensureEdit(t); edits[t.id].ready_for_review = val; queueSave(t, { ready_for_review: val }) }" :disabled="!canCreate" />
                  <label for="rfrEdit">Ready for review</label>
              </div>
              <div class="flex align-items-center gap-2 flex-1">
                  <ToggleSwitch id="completedEdit" :modelValue="(edits[t.id]?.completed ?? t.completed)" @update:modelValue="val => { ensureEdit(t); edits[t.id].completed = val; queueSave(t, { completed: val }) }" :disabled="!canComplete" />
                  <label for="completedEdit">Completed</label>
              </div>
            </div>
          </div>
          <!-- Messages: only for existing records -->
          <div class="mt-3">
            <p>Ask questions, provide updates here:</p>
            <Messages :caseId="props.caseId" filterByFieldName="task_id" :filterByFieldId="t.id" :ref="makeMessagesRef(t.id)" />
          </div>
        </AccordionContent>
      </AccordionPanel>
    </Accordion>
  </div>
</template>

<style scoped>
.avatar-sm { width: 24px; height: 24px; border-radius: 999px; object-fit: cover; }
.name-clip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.p-accordionheader { background-color: var(--p-primary-200) }
.p-accordionpanel:not(.p-disabled).p-accordionpanel-active > .p-accordionheader {  background-color: var(--p-primary-200)  }
.p-accordionpanel:not(.p-disabled):not(p-accordionpanel-active) > .p-accordionheader:hover {  background-color: var(--p-primary-300)  }

</style>
