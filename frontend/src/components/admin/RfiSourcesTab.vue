<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dialog from 'primevue/dialog'
import ToggleSwitch from 'primevue/toggleswitch'
import PersonSelect from '../PersonSelect.vue'
import FloatLabel from "primevue/floatlabel";

const sources = ref([])
const loading = ref(false)
const filterText = ref('')

const editDialogVisible = ref(false)
const editModel = reactive({
  id: null,
  name: '',
  description: '',
  primary_id: '',
  backup_id: '',
  inactive: false,
})

// Validation state
const errors = reactive({
  name: '',
  description: '',
  primary_id: '',
  backup_id: '',
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
  if (!editModel.description || !String(editModel.description).trim()) {
    errors.description = 'Description is required.'
    ok = false
  }
  // primary and backup are optional for now since some persons may not be linked to accounts
  return ok
}

const filtered = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  if (!q) return sources.value
  return sources.value.filter((s) =>
    [s.name, s.description].some((v) => (v || '').toLowerCase().includes(q))
  )
})

async function fetchSources() {
  loading.value = true
  try {
    const resp = await fetch('/api/v1/rfi-sources')
    if (!resp.ok) throw new Error('Failed to load RFI sources')
    sources.value = await resp.json()
  } finally {
    loading.value = false
  }
}

function openAdd() {
  Object.assign(editModel, { id: null, name: '', description: '', primary_id: '', backup_id: '', inactive: false })
  clearErrors()
  editDialogVisible.value = true
}

function openEdit(row) {
  Object.assign(editModel, { ...row })
  clearErrors()
  editDialogVisible.value = true
}

async function saveEdit() {
  if (!validate()) {
    return
  }
  const payload = {
    id: editModel.id || undefined,
    name: editModel.name,
    description: editModel.description,
    primary_id: editModel.primary_id || null,
    backup_id: editModel.backup_id || null,
    inactive: !!editModel.inactive,
  }
  const isNew = !editModel.id
  const url = isNew ? '/api/v1/rfi-sources' : `/api/v1/rfi-sources/${encodeURIComponent(editModel.id)}`
  const method = isNew ? 'POST' : 'PUT'
  const resp = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err?.detail || 'Save failed')
  }
  editDialogVisible.value = false
  await fetchSources()
}

onMounted(async () => {
  await fetchSources()
})
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center justify-content-between mb-2 gap-2">
      <h3 class="m-0">RFI Sources</h3>
      <div class="flex gap-2">
        <span class="p-input-icon-left">
          <i class="pi pi-search" />
          <InputText v-model="filterText" placeholder="Filter..." />
        </span>
        <Button label="Add" icon="pi pi-plus" @click="openAdd" />
      </div>
    </div>

    <DataTable
      :value="filtered"
      dataKey="id"
      :loading="loading"
      paginator
      :rows="10"
      :rowsPerPageOptions="[10,20,50]"
      removableSort
      class="p-datatable-sm"
    >
      <Column field="name" header="Name" sortable></Column>
      <Column field="description" header="Description" sortable></Column>
      <Column field="primary_name" header="Primary" sortable></Column>
      <Column field="backup_name" header="Backup" sortable></Column>
      <Column header="Active" style="width:6rem" :sortable="true" :sortField="'inactive'">
        <template #body="{ data }">
          <span :class="data.inactive ? 'text-600' : 'text-green-600'">{{ data.inactive ? 'Inactive' : 'Active' }}</span>
        </template>
      </Column>
      <Column header="Actions" style="width:8rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" size="small" text @click="openEdit(data)" />
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="editDialogVisible" modal header="RFI Source" :style="{ width: '600px' }">
      <div class="flex flex-column gap-3 mt-1">
        <div v-if="validationMessage" class="text-red-600 text-sm">{{ validationMessage }}</div>
        <div class="flex gap-2">
          <div class="flex-1">
            <FloatLabel variant="on">
            <label class="block mb-1 text-sm">Name</label>
            <InputText v-model="editModel.name" :class="['w-full', errors.name && 'p-invalid']" />
            </FloatLabel>
            <small v-if="errors.name" class="p-error text-red-600">{{ errors.name }}</small>
          </div>
        </div>
        <div class="flex gap-2">
          <div class="flex-1">
            <FloatLabel variant="on">
            <label class="block mb-1 text-sm">Description</label>
            <InputText v-model="editModel.description" :class="['w-full', errors.description && 'p-invalid']" />
            </FloatLabel>
            <small v-if="errors.description" class="p-error text-red-600">{{ errors.description }}</small>
          </div>
        </div>
        <div class="flex gap-2">
          <div class="flex-1">
            <FloatLabel variant="on">
              <PersonSelect v-model="editModel.primary_id" />
              <label class="block mb-1 text-sm">Primary</label>
            </FloatLabel>
          </div>
        </div>
        <div class="flex gap-2">
          <div class="flex-1">
            <FloatLabel variant="on">
              <PersonSelect v-model="editModel.backup_id" />
              <label class="block mb-1 text-sm">Backup</label>
            </FloatLabel>
          </div>
        </div>
        <div class="flex align-items-center gap-2" style="width: 12rem">
          <label class="mb-0 text-sm">Inactive</label>
          <ToggleSwitch v-model="editModel.inactive" />
        </div>
        <div class="flex justify-content-end gap-2">
          <Button label="Cancel" text @click="editDialogVisible = false" />
          <Button label="Save" icon="pi pi-check" @click="saveEdit" />
        </div>
      </div>
    </Dialog>
  </div>
</template>
