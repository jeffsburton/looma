<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dialog from 'primevue/dialog'
import ToggleSwitch from 'primevue/toggleswitch'
import RefSelect from '../RefSelect.vue'
import FloatLabel from 'primevue/floatlabel'

const hospitals = ref([])
const loading = ref(false)
const filterText = ref('')
const states = ref([])

const editDialogVisible = ref(false)
const editModel = reactive({
  id: null,
  name: '',
  address: '',
  city: '',
  state_id: '',
  zip_code: '',
  phone: '',
  inactive: false,
})

// Validation state
const errors = reactive({
  name: '',
  address: '',
  city: '',
  state_id: '',
  zip_code: '',
  phone: ''
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
  if (!editModel.address || !String(editModel.address).trim()) {
    errors.address = 'Address is required.'
    ok = false
  }
  if (!editModel.city || !String(editModel.city).trim()) {
    errors.city = 'City is required.'
    ok = false
  }
  if (!editModel.state_id) {
    errors.state_id = 'State is required.'
    ok = false
  }
  if (!editModel.zip_code || !String(editModel.zip_code).trim()) {
    errors.zip_code = 'Zip is required.'
    ok = false
  }
  if (!editModel.phone || !String(editModel.phone).trim()) {
    errors.phone = 'Phone is required.'
    ok = false
  } else {
    const digits = String(editModel.phone).replace(/\D+/g, '')
    if (digits.length < 10 || digits.length > 15) {
      errors.phone = 'Enter a valid phone number (10-15 digits).'
      ok = false
    }
  }
  if (!ok) {
    validationMessage.value = 'Please correct the highlighted fields.'
  }
  return ok
}

const filteredHospitals = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  if (!q) return hospitals.value
  return hospitals.value.filter((h) =>
    [h.name, h.address, h.city, h.zip_code, h.phone].some((v) => (v || '').toLowerCase().includes(q))
  )
})

async function fetchStates() {
  const resp = await fetch('/api/v1/states')
  if (!resp.ok) throw new Error('Failed to load states')
  const data = await resp.json()
  // Map to {label, value}
  states.value = data.map((s) => ({ label: `${s.code} - ${s.name}`, value: s.id, code: s.code, name: s.name }))
}

async function fetchHospitals() {
  loading.value = true
  try {
    const resp = await fetch('/api/v1/hospital-ers')
    if (!resp.ok) throw new Error('Failed to load hospitals')
    hospitals.value = await resp.json()
  } finally {
    loading.value = false
  }
}

function openAdd() {
  Object.assign(editModel, { id: null, name: '', address: '', city: '', state_id: '', zip_code: '', phone: '', inactive: false })
  clearErrors()
  editDialogVisible.value = true
}

function openEdit(row) {
  // Assign all fields from the row first
  Object.assign(editModel, { ...row })
  // Because opaque ids are probabilistic (Fernet), remap state_id to the exact
  // token used by the options list by matching on the stable state_code.
  if (row?.state_code && Array.isArray(states.value) && states.value.length) {
    const match = states.value.find((s) => s.code === row.state_code)
    if (match) {
      editModel.state_id = match.value
    }
  }
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
    address: editModel.address,
    city: editModel.city,
    state_id: editModel.state_id,
    zip_code: editModel.zip_code,
    phone: editModel.phone,
    inactive: !!editModel.inactive,
  }
  const isNew = !editModel.id
  const url = isNew ? '/api/v1/hospital-ers' : `/api/v1/hospital-ers/${encodeURIComponent(editModel.id)}`
  const method = isNew ? 'POST' : 'PUT'
  const resp = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err?.detail || 'Save failed')
  }
  editDialogVisible.value = false
  await fetchHospitals()
}

onMounted(async () => {
  await Promise.all([fetchStates(), fetchHospitals()])
})
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center justify-content-between mb-2 gap-2">
      <h3 class="m-0">ER's/Trauma Centers</h3>
      <div class="flex gap-2">
        <span class="p-input-icon-left">
          <i class="pi pi-search" />
          <InputText v-model="filterText" placeholder="Filter..." />
        </span>
        <Button label="Add" icon="pi pi-plus" @click="openAdd" />
      </div>
    </div>

    <DataTable
      :value="filteredHospitals"
      dataKey="id"
      :loading="loading"
      paginator
      :rows="10"
      :rowsPerPageOptions="[10,20,50]"
      removableSort
      class="p-datatable-sm"
    >
      <Column field="name" header="Name" sortable></Column>
      <Column field="address" header="Address" sortable></Column>
      <Column field="city" header="City" sortable></Column>
      <Column field="state_code" header="State" sortable></Column>
      <Column field="zip_code" header="Zip" sortable style="width:8rem"></Column>
      <Column field="phone" header="Phone" sortable style="width:12rem"></Column>
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

    <Dialog v-model:visible="editDialogVisible" modal header="Hospital" :style="{ width: '600px' }">
      <div class="flex flex-column gap-3 mt-1">
        <div v-if="validationMessage" class="text-red-600 text-sm">{{ validationMessage }}</div>
        <div class="flex gap-2">
          <div class="flex-1">
            <FloatLabel variant="on">
              <InputText id="h-name" v-model="editModel.name" :class="['w-full', errors.name && 'p-invalid']" />
              <label for="h-name">Name</label>
            </FloatLabel>
            <small v-if="errors.name" class="p-error text-red-600">{{ errors.name }}</small>
          </div>
        </div>
        <div class="flex gap-2">
          <div class="flex-1">
            <FloatLabel variant="on">
              <InputText id="h-address" v-model="editModel.address" :class="['w-full', errors.address && 'p-invalid']" />
              <label for="h-address">Address</label>
            </FloatLabel>
            <small v-if="errors.address" class="p-error text-red-600">{{ errors.address }}</small>
          </div>
        </div>
        <div class="flex gap-2">
          <div class="flex-1">
            <FloatLabel variant="on">
              <label class="block mb-1 text-sm">City</label>
              <InputText v-model="editModel.city" :class="['w-full', errors.city && 'p-invalid']" />
            </FloatLabel>
            <small v-if="errors.city" class="p-error text-red-600">{{ errors.city }}</small>
          </div>
          <div class="flex-1">
            <FloatLabel variant="on">
              <RefSelect v-model="editModel.state_id" code="STATE" :currentCode="editModel.state_code" :add="false" :class="['w-full', errors.state_id && 'p-invalid']" />
              <label class="block mb-1 text-sm">State</label>
            </FloatLabel>
            <small v-if="errors.state_id" class="p-error text-red-600">{{ errors.state_id }}</small>
          </div>
          <div class="flex-1">
            <FloatLabel variant="on">
              <label class="block mb-1 text-sm">Zip</label>
              <InputText v-model="editModel.zip_code" :class="['w-full', errors.zip_code && 'p-invalid']" />
            </FloatLabel>
            <small v-if="errors.zip_code" class="p-error text-red-600">{{ errors.zip_code }}</small>
          </div>
        </div>
        <div class="flex gap-2">
          <div class="flex-1">
            <FloatLabel variant="on">
              <label class="block mb-1 text-sm">Phone</label>
              <InputText v-model="editModel.phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="e.g., (555) 123-4567" :class="['w-full', errors.phone && 'p-invalid']" />
            </FloatLabel>
            <small v-if="errors.phone" class="p-error text-red-600">{{ errors.phone }}</small>
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
