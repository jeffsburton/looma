<script setup>
import { ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'

// Local editable data model. In the future, lift to store/props/API as needed.
const nextId = ref(1)
const accounts = ref([
  // Example starting row (empty). Users can add/remove rows.
  { id: nextId.value++, platform: null, handle: '', owner: '', private: false, active: true }
])

const platforms = [
  { label: 'Discord', value: 'Discord' },
  { label: 'Facebook', value: 'Facebook' },
  { label: 'Instagram', value: 'Instagram' },
  { label: 'LinkedIn', value: 'LinkedIn' },
  { label: 'Snapchat', value: 'Snapchat' }
]

function addRow() {
  accounts.value.push({ id: nextId.value++, platform: null, handle: '', owner: '', private: false, active: true })
}

function removeRow(rowId) {
  accounts.value = accounts.value.filter(a => a.id !== rowId)
  if (accounts.value.length === 0) {
    // Always keep at least one row to guide the user
    addRow()
  }
}
</script>

<template>
  <div class="p-3">
    <div class="text-lg font-semibold mb-3 flex align-items-center gap-2">
      <span class="material-symbols-outlined">share</span>
      <span>Intake • Social Media</span>
    </div>

    <div class="flex justify-content-end mb-2">
      <Button label="Add Account" icon="pi pi-plus" @click="addRow" size="small" />
    </div>

    <DataTable :value="accounts" dataKey="id" stripedRows size="small" class="shadow-1 border-round surface-card">
      <Column header="#" style="width:4rem">
        <template #body="{ index }">
          <span class="text-600">{{ index + 1 }}</span>
        </template>
      </Column>

      <Column field="platform" header="Platform" style="min-width:12rem">
        <template #body="{ data }">
          <Dropdown v-model="data.platform" :options="platforms" optionLabel="label" optionValue="value" placeholder="Select platform" class="w-full" />
        </template>
      </Column>

      <Column field="handle" header="Handle/User" style="min-width:14rem">
        <template #body="{ data }">
          <InputText v-model="data.handle" placeholder="@username or URL" class="w-full" />
        </template>
      </Column>

      <Column field="owner" header="Owner" style="min-width:12rem">
        <template #body="{ data }">
          <InputText v-model="data.owner" placeholder="Account owner" class="w-full" />
        </template>
      </Column>

      <Column field="private" header="Private" style="width:8rem; text-align:center" bodyClass="text-center">
        <template #body="{ data }">
          <div class="flex justify-content-center">
            <Checkbox v-model="data.private" :binary="true" :input-id="'priv-' + data.id" />
          </div>
        </template>
      </Column>

      <Column field="active" header="Active" style="width:8rem; text-align:center" bodyClass="text-center">
        <template #body="{ data }">
          <div class="flex justify-content-center">
            <Checkbox v-model="data.active" :binary="true" :input-id="'act-' + data.id" />
          </div>
        </template>
      </Column>

      <Column header="" style="width:6rem">
        <template #body="{ data }">
          <Button icon="pi pi-trash" severity="danger" text rounded @click="removeRow(data.id)" />
        </template>
      </Column>
    </DataTable>
  </div>
</template>
