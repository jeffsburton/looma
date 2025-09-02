<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dialog from 'primevue/dialog'
import ToggleSwitch from 'primevue/toggleswitch'
import FloatLabel from "primevue/floatlabel";

const quals = ref([])
const loading = ref(false)
const filterText = ref('')

const editDialogVisible = ref(false)
const editModel = reactive({
  id: null,
  name: '',
  description: '',
  inactive: false,
})

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

const filtered = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  if (!q) return quals.value
  return quals.value.filter((r) => [r.name, r.description].some((v) => (v || '').toLowerCase().includes(q)))
})

async function fetchQualifications() {
  loading.value = true
  try {
    const resp = await fetch('/api/v1/qualifications')
    if (!resp.ok) throw new Error('Failed to load qualifications')
    quals.value = await resp.json()
  } finally {
    loading.value = false
  }
}

function openAdd() {
  Object.assign(editModel, { id: null, name: '', description: '', inactive: false })
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
    description: editModel.description || null,
    inactive: !!editModel.inactive,
  }
  const isNew = !editModel.id
  const url = isNew ? '/api/v1/qualifications' : `/api/v1/qualifications/${encodeURIComponent(editModel.id)}`
  const method = isNew ? 'POST' : 'PUT'
  const resp = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err?.detail || 'Save failed')
  }
  editDialogVisible.value = false
  await fetchQualifications()
}

onMounted(async () => {
  await fetchQualifications()
})
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center justify-content-between mb-2 gap-2">
      <h3 class="m-0">Qualifications</h3>
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

    <Dialog v-model:visible="editDialogVisible" modal header="Qualification" :style="{ width: '600px' }">
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
              <label for="q-description" class="block mb-1 text-sm">Description</label>
              <textarea id="q-description" v-model="editModel.description" rows="4" class="w-full p-inputtext"></textarea>
            </FloatLabel>
          </div>
          <div class="flex align-items-center gap-2" style="width: 12rem">
            <label class="mb-0 text-sm">Inactive</label>
            <ToggleSwitch v-model="editModel.inactive" />
          </div>
        </div>
        <div class="flex justify-content-end gap-2">
          <Button label="Cancel" text @click="editDialogVisible = false" />
          <Button label="Save" icon="pi pi-check" @click="saveEdit" />
        </div>
      </div>
    </Dialog>
  </div>
</template>
