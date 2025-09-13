<script setup>
import { ref, computed, watch, onMounted, defineAsyncComponent } from 'vue'
import Button from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import api from '@/lib/api'
import { hasPermission } from '@/lib/permissions'
import UnseenMessageCount from '@/components/common/UnseenMessageCount.vue'
import { useRoute, useRouter } from 'vue-router'

// Async edit component
const TasksEdit = defineAsyncComponent(() => import('./TasksEdit.vue'))

const props = defineProps({
  caseId: { type: [String, Number], required: true }
})

// Permissions
const canCreate = computed(() => hasPermission('TASKS.CREATE'))

// Filters
const showCompleted = ref(false) // default off per requirements

// Data
const loading = ref(false)
const tasks = ref([])

const route = useRoute()
const router = useRouter()

const caseNumber = computed(() => String(route.params.caseNumber || ''))

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
    const { data } = await api.get(`/api/v1/cases/${props.caseId}/tasks`)
    tasks.value = Array.isArray(data) ? data : []
  } finally {
    loading.value = false
  }
}

watch(() => props.caseId, () => { loadTasks() }, { immediate: true })

// When leaving edit mode (rawTaskId removed), reload list
watch(
  () => route.params.rawTaskId,
  (val, oldVal) => {
    if (oldVal && !val) {
      loadTasks()
    }
  }
)

function openEdit(row) {
  const id = row?.id
  if (!id) return
  const url = `/cases/${encodeURIComponent(String(caseNumber.value))}/tasks/${encodeURIComponent(String(id))}`
  router.push({ path: url })
}
</script>

<template>
  <div class="p-2">
    <template v-if="route.params.rawTaskId">
      <TasksEdit :caseId="String(caseId)" />
    </template>
    <template v-else>
      <!-- Toolbar: show completed toggle (Add moved below table) -->
      <div class="flex gap-2 align-items-center flex-wrap mb-3">
        <div class="flex align-items-center gap-2">
          <ToggleSwitch id="showCompleted" v-model="showCompleted" />
          <label for="showCompleted">Show completed</label>
        </div>
      </div>

      <!-- Tasks Table -->
      <DataTable :value="displayedTasks" dataKey="id" size="small" :loading="loading" class="w-full">
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
            <span class="text-900">{{ data.title }}</span>
          </template>
        </Column>
        <Column field="description" header="Description">
          <template #body="{ data }">
            <span>{{ data.description }}</span>
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
        <Column header="" style="width:1%">
          <template #body="{ data }">
            <Button icon="pi pi-pencil" text rounded @click.stop="openEdit(data)" />
          </template>
        </Column>
      </DataTable>
      <div class="flex justify-content-start mt-2">
        <Button v-if="canCreate" label="Add" icon="pi pi-plus" @click="() => router.push({ path: `/cases/${encodeURIComponent(String(caseNumber))}/tasks/new` })" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.avatar-sm { width: 24px; height: 24px; border-radius: 999px; object-fit: cover; }
.name-clip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
