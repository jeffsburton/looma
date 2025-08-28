<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dialog from 'primevue/dialog'
import RefSelect from '../RefSelect.vue'

const orgs = ref([])
const loading = ref(false)
const filterText = ref('')

const editDialogVisible = ref(false)
const editModel = reactive({
  id: null,
  name: '',
  state_id: '',
  state_code: '',
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

const filteredOrgs = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  if (!q) return orgs.value
  return orgs.value.filter((o) => [o.name, o.state_code].some((v) => (v || '').toLowerCase().includes(q)))
})

async function fetchOrganizations() {
  loading.value = true
  try {
    const resp = await fetch('/api/v1/organizations')
    if (!resp.ok) throw new Error('Failed to load organizations')
    orgs.value = await resp.json()
  } finally {
    loading.value = false
  }
}

function openAdd() {
  Object.assign(editModel, { id: null, name: '', state_id: '', state_code: '' })
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
    state_id: editModel.state_id || null,
  }
  const isNew = !editModel.id
  const url = isNew ? '/api/v1/organizations' : `/api/v1/organizations/${encodeURIComponent(editModel.id)}`
  const method = isNew ? 'POST' : 'PUT'
  const resp = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err?.detail || 'Save failed')
  }
  editDialogVisible.value = false
  await fetchOrganizations()
}

onMounted(async () => {
  await fetchOrganizations()
})
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center justify-content-between mb-2 gap-2">
      <h3 class="m-0">Organizations</h3>
      <div class="flex gap-2">
        <span class="p-input-icon-left">
          <i class="pi pi-search" />
          <InputText v-model="filterText" placeholder="Filter..." />
        </span>
        <Button label="Add" icon="pi pi-plus" @click="openAdd" />
      </div>
    </div>

    <DataTable
      :value="filteredOrgs"
      dataKey="id"
      :loading="loading"
      paginator
      :rows="10"
      :rowsPerPageOptions="[10,20,50]"
      removableSort
      class="p-datatable-sm"
    >
      <Column field="name" header="Name" sortable></Column>
      <Column field="state_code" header="State" sortable></Column>
      <Column header="Actions" style="width:8rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" size="small" text @click="openEdit(data)" />
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="editDialogVisible" modal header="Organization" :style="{ width: '520px' }">
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
            <label class="block mb-1 text-sm">State</label>
            <RefSelect v-model="editModel.state_id" code="STATE" :currentCode="editModel.state_code" :add="false" placeholder="Select state..." />
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
