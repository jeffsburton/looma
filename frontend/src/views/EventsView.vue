<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dialog from 'primevue/dialog'
import Calendar from 'primevue/calendar'
import Checkbox from 'primevue/checkbox'
import RefSelect from '../components/RefSelect.vue'
import { hasPermission } from '../lib/permissions'

const events = ref([])
const loading = ref(false)
const filterText = ref('')

const editDialogVisible = ref(false)
const editModel = reactive({
  id: null,
  name: '',
  city: '',
  state_id: '',
  state_code: '',
  start: null,
  end: null,
  inactive: false,
})

const canModify = computed(() => hasPermission('EVENTS.MODIFY'))

// Validation state
const errors = reactive({
  name: '',
})
const validationMessage = ref('')

function clearErrors() {
  for (const k of Object.keys(errors)) errors[k] = ''
  validationMessage.value = ''
}

function validate() {
  clearErrors()
  let ok = true
  if (!editModel.name || !String(editModel.name).trim()) {
    errors.name = 'Name is required.'
    ok = false
  }
  if (!ok) {
    validationMessage.value = 'Please correct the highlighted fields.'
  }
  return ok
}

const filteredEvents = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  if (!q) return events.value
  return events.value.filter((o) => [o.name, o.city, o.state_code].some((v) => (v || '').toLowerCase().includes(q)))
})

async function fetchEvents() {
  loading.value = true
  try {
    const resp = await fetch('/api/v1/events')
    if (!resp.ok) throw new Error('Failed to load events')
    events.value = await resp.json()
  } finally {
    loading.value = false
  }
}

function openAdd() {
  Object.assign(editModel, { id: null, name: '', city: '', state_id: '', state_code: '', start: null, end: null, inactive: false })
  clearErrors()
  editDialogVisible.value = true
}

function openEdit(row) {
  Object.assign(editModel, { ...row })
  clearErrors()
  editDialogVisible.value = true
}

async function saveEdit() {
  if (!validate()) return
  const payload = {
    id: editModel.id || undefined,
    name: editModel.name,
    city: editModel.city || '',
    state_id: editModel.state_id || null,
    start: editModel.start || null,
    end: editModel.end || null,
    inactive: !!editModel.inactive,
  }
  const isNew = !editModel.id
  const url = isNew ? '/api/v1/events' : `/api/v1/events/${encodeURIComponent(editModel.id)}`
  const method = isNew ? 'POST' : 'PUT'
  const resp = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err?.detail || 'Save failed')
  }
  editDialogVisible.value = false
  await fetchEvents()
}

onMounted(async () => {
  await fetchEvents()
})
</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Events'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <div class="flex align-items-center justify-content-between gap-2 pb-2">
            <div class="text-xl font-semibold">Events</div>
          </div>

          <div class="surface-card border-round p-2 flex-1 overflow-auto">
            <div class="flex align-items-center justify-content-between mb-2 gap-2">
              <div />
              <div class="flex gap-2">
                <span class="p-input-icon-left">
                  <i class="pi pi-search" />
                  <InputText v-model="filterText" placeholder="Filter..." />
                </span>
                <Button v-if="canModify" label="Add" icon="pi pi-plus" @click="openAdd" />
              </div>
            </div>

            <DataTable
              :value="filteredEvents"
              dataKey="id"
              :loading="loading"
              paginator
              :rows="10"
              :rowsPerPageOptions="[10,20,50]"
              removableSort
              class="p-datatable-sm"
            >
              <Column field="name" header="Name" sortable></Column>
              <Column field="city" header="City" sortable></Column>
              <Column field="state_code" header="State" sortable></Column>
              <Column field="start" header="Start" sortable>
                <template #body="{ data }">
                  <span>{{ data.start || '' }}</span>
                </template>
              </Column>
              <Column field="end" header="End" sortable>
                <template #body="{ data }">
                  <span>{{ data.end || '' }}</span>
                </template>
              </Column>
              <Column field="inactive" header="Inactive" sortable>
                <template #body="{ data }">
                  <i v-if="data.inactive" class="pi pi-check" />
                </template>
              </Column>
              <Column header="Actions" style="width:8rem">
                <template #body="{ data }">
                  <Button v-if="canModify" icon="pi pi-pencil" size="small" text @click="openEdit(data)" />
                </template>
              </Column>
            </DataTable>

            <Dialog v-model:visible="editDialogVisible" modal header="Event" :style="{ width: '600px' }">
              <div class="flex flex-column gap-3">
                <div v-if="validationMessage" class="text-red-600 text-sm">{{ validationMessage }}</div>
                <div class="flex gap-2">
                  <div class="flex-1">
                    <label class="block mb-1 text-sm">Name</label>
                    <InputText v-model="editModel.name" :class="['w-full', errors.name && 'p-invalid']" />
                    <small v-if="errors.name" class="p-error text-red-600">{{ errors.name }}</small>
                  </div>
                </div>
                <div class="flex gap-2">
                  <div class="flex-1">
                    <label class="block mb-1 text-sm">City</label>
                    <InputText v-model="editModel.city" class="w-full" />
                  </div>
                  <div class="flex-1">
                    <label class="block mb-1 text-sm">State</label>
                    <RefSelect v-model="editModel.state_id" code="STATE" :currentCode="editModel.state_code" :add="false" placeholder="Select state..." />
                  </div>
                </div>
                <div class="flex gap-2">
                  <div class="flex-1">
                    <label class="block mb-1 text-sm">Start</label>
                    <Calendar v-model="editModel.start" dateFormat="yy-mm-dd" showIcon iconDisplay="input" />
                  </div>
                  <div class="flex-1">
                    <label class="block mb-1 text-sm">End</label>
                    <Calendar v-model="editModel.end" dateFormat="yy-mm-dd" showIcon iconDisplay="input" />
                  </div>
                </div>
                <div class="flex gap-2 align-items-center">
                  <Checkbox inputId="inactive" v-model="editModel.inactive" :binary="true" />
                  <label for="inactive">Inactive</label>
                </div>
                <div class="flex justify-content-end gap-2">
                  <Button label="Cancel" text @click="editDialogVisible = false" />
                  <Button v-if="canModify" label="Save" icon="pi pi-check" @click="saveEdit" />
                </div>
              </div>
            </Dialog>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
