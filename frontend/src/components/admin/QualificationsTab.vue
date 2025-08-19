<script setup>
import { ref, onMounted } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useToast } from 'primevue/usetoast'

const toast = useToast()

const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const editingRows = ref([])

function makeKeyFromId(id) {
  return id ? String(id) : `tmp_${Math.random().toString(36).slice(2)}`
}

async function load() {
  loading.value = true
  try {
    const res = await fetch('/api/v1/admin/qualifications')
    if (!res.ok) throw new Error('Failed to load qualifications')
    const data = await res.json()
    rows.value = data.map((r) => ({ ...r, _key: makeKeyFromId(r.id) }))
  } catch (e) {
    console.error(e)
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load qualifications', life: 3000 })
  } finally {
    loading.value = false
  }
}

async function saveRow(row) {
  saving.value = true
  try {
    const payload = [
      {
        id: row.id || null,
        name: row.name || '',
        code: row.code || null,
      },
    ]
    const res = await fetch('/api/v1/admin/qualifications', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error('Save failed')
    const [saved] = await res.json()
    // Merge returned values back into the row (including new id)
    row.id = saved.id
    row.name = saved.name
    row.code = saved.code
    row._key = makeKeyFromId(saved.id)
    toast.add({ severity: 'success', summary: 'Saved', detail: 'Qualification saved', life: 1500 })
  } catch (e) {
    console.error(e)
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to save', life: 3000 })
  } finally {
    saving.value = false
  }
}

function onRowEditSave(e) {
  const { newData, index } = e
  // apply the edited data back to the rows and persist
  rows.value[index] = newData
  saveRow(rows.value[index])
}

function addNew() {
  rows.value = [
    { id: null, name: '', code: '', _key: makeKeyFromId(null) },
    ...rows.value,
  ]
}

onMounted(load)
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center justify-content-between mb-2">
      <h3 class="m-0">Qualifications</h3>
      <div class="flex gap-2">
        <Button label="Add" icon="pi pi-plus" @click="addNew" :disabled="loading || saving" />
      </div>
    </div>

    <DataTable
      v-model:editingRows="editingRows"
      :value="rows"
      :loading="loading"
      dataKey="_key"
      editMode="row"
      @row-edit-save="onRowEditSave"
      :pt="{
        table: { style: 'width: 100%' },
        column: {
          bodycell: ({ state }) => ({
            // Make rows more compact; keep a touch more room while editing
            style: state['d_editing']
              ? 'padding-top: 0.5rem; padding-bottom: 0.5rem'
              : 'padding-top: 0.25rem; padding-bottom: 0.25rem'
          })
        }
      }"
      size="small"
    >
      <Column field="name" header="Name" style="width: 60%">
        <template #editor="{ data, field }">
          <InputText v-model="data[field]" placeholder="Name" class="w-full" />
        </template>
      </Column>
      <Column field="code" header="Code" style="width: 30%">
        <template #editor="{ data, field }">
          <InputText v-model="data[field]" placeholder="Code" class="w-full" />
        </template>
      </Column>
      <Column :rowEditor="true" style="width: 10%; min-width: 8rem" bodyStyle="text-align:center" />
    </DataTable>
  </div>
</template>

<style scoped>
/* Compact rows */
:deep(.p-datatable .p-datatable-thead > tr > th),
:deep(.p-datatable .p-datatable-tbody > tr > td) {
  padding-top: 0.25rem !important;
  padding-bottom: 0.25rem !important;
}

/* Horizontal dividers only */
:deep(.p-datatable .p-datatable-thead > tr > th) {
  border-top: 0 !important;
  border-left: 0 !important;
  border-right: 0 !important;
  border-bottom: 1px solid #e5e7eb !important;
}

:deep(.p-datatable .p-datatable-tbody > tr > td) {
  border-top: 0 !important;
  border-left: 0 !important;
  border-right: 0 !important;
  border-bottom: 1px solid #e5e7eb !important;
}

/* Remove footer borders if any */
:deep(.p-datatable .p-datatable-tfoot > tr > td) {
  border: 0 !important;
}
</style>
