<script setup>
import { ref, watch, onMounted, computed, nextTick } from 'vue'
import Dropdown from 'primevue/dropdown'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

const props = defineProps({
  code: { type: String, required: true },
  add: { type: Boolean, default: false },
  modelValue: { type: String, default: '' }, // opaque id of ref_value.id
  otherValue: { type: String, default: '' }, // value for OTH free text
  placeholder: { type: String, default: 'Select...' },
  disabled: { type: Boolean, default: false },
  filter: { type: Boolean, default: true },
  currentCode: { type: String, default: '' }, // stable code used to reconcile selection across requests
  showCode: { type: Boolean, default: true }, // controls whether the code is displayed next to the name
})
const emit = defineEmits(['update:modelValue', 'update:otherValue', 'change'])

const allOptions = ref([]) // raw list from API [{id, name, description, code, inactive}]
const loading = ref(false)

// Dropdown ref to focus the filter input on open
const ddRef = ref(null)

function focusFilter() {
  if (!props.filter) return

  const root = ddRef.value?.$el || null
  if (!root) return

  // Find the parent element with class 'p-select'
  const selectParent = root.closest('.p-select')
  if (!selectParent) return

  // Extract the number from the id (e.g., "pv_id_95" -> "95")
  const id = selectParent.id
  if (!id) return
  const match = id.match(/pv_id_(\d+)/)
  if (!match) return
  const number = match[1]

  // Find the overlay element using the extracted number
  const overlay = document.querySelector(`.p-select-overlay[pc${number}]`)
  if (!overlay) return

  const input = overlay.querySelector('input')
  if (!input) return
  input.focus()
}

const selectedId = ref(props.modelValue ? String(props.modelValue) : '')
watch(() => props.modelValue, (v) => { selectedId.value = v ? String(v) : '' })
watch(selectedId, (v) => { emit('update:modelValue', v); emit('change', v) })

const otherText = ref(props.otherValue)
watch(() => props.otherValue, (v) => { otherText.value = v })
watch(otherText, (v) => emit('update:otherValue', v))

const selectedOption = computed(() => {
  const sel = selectedId.value != null ? String(selectedId.value) : ''
  return allOptions.value.find(o => String(o.id) === sel)
})
const isOTH = computed(() => (selectedOption.value?.code || '').toUpperCase() === 'OTH')

const visibleOptions = computed(() => {
  // Hide inactive unless it is the selected option and build a combined label for filtering by name or code
  const sel = selectedId.value != null ? String(selectedId.value) : ''
  return allOptions.value
    .filter(o => !o.inactive || String(o.id) === sel)
    .map(o => ({
      ...o,
      _filterLabel: [o.name, o.code].filter(Boolean).join(' ')
    }))
})

async function loadOptions() {
  if (!props.code) return
  loading.value = true
  try {
    const resp = await fetch(`/api/v1/reference/${encodeURIComponent(props.code)}/values`)
    if (!resp.ok) throw new Error('Failed to load reference values')
    const data = await resp.json()
    allOptions.value = data
    // Reconcile selection when opaque id tokens don't match across responses
    const upperCode = (props.currentCode || '').toUpperCase().trim()
    const sel = selectedId.value != null ? String(selectedId.value) : ''
    const hasSelected = allOptions.value.some(o => String(o.id) === sel)
    if ((!hasSelected && upperCode) || (!sel && upperCode)) {
      const byCode = allOptions.value.find(o => (o.code || '').toUpperCase() === upperCode)
      if (byCode) {
        selectedId.value = byCode.id
      }
    }
  } finally {
    loading.value = false
  }
}

watch(() => props.code, () => { loadOptions() }, { immediate: true })

// Add-new dialog state
const addVisible = ref(false)
const newName = ref('')
const newCode = ref('')
const newDescription = ref('')
const addError = ref('')

function openAdd() {
  newName.value = ''
  newCode.value = ''
  newDescription.value = ''
  addError.value = ''
  addVisible.value = true
}

async function saveAdd() {
  addError.value = ''
  if (!newName.value.trim() || !newCode.value.trim()) {
    addError.value = 'Name and Code are required.'
    return
  }
  const payload = { name: newName.value.trim(), code: newCode.value.trim(), description: newDescription.value.trim() }
  const resp = await fetch(`/api/v1/reference/${encodeURIComponent(props.code)}/values`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    addError.value = err?.detail || 'Failed to add value'
    return
  }
  const created = await resp.json()
  addVisible.value = false
  await loadOptions()
  // select the newly created option
  selectedId.value = created.id
}

// Reconcile when currentCode changes and options are already loaded
watch(
  () => props.currentCode,
  (v) => {
    const upper = (v || '').toUpperCase().trim()
    if (!upper || !Array.isArray(allOptions.value) || !allOptions.value.length) return
    const sel = selectedId.value != null ? String(selectedId.value) : ''
    const hasSelected = allOptions.value.some(o => String(o.id) === sel)
    if (!hasSelected) {
      const byCode = allOptions.value.find(o => (o.code || '').toUpperCase() === upper)
      if (byCode) {
        selectedId.value = byCode.id
      }
    }
  }
)
</script>

<template>
  <div class="flex flex-column gap-2">
    <Dropdown
      ref="ddRef"
      v-model="selectedId"
      :options="visibleOptions"
      :loading="loading"
      optionLabel="_filterLabel"
      optionValue="id"
      :filter="filter"
      filterBy="name,code"
      :placeholder="placeholder"
      class="w-full"
      :disabled="disabled"
      @show="focusFilter"
    >
      <template #option="{ option }">
        <div :title="option.description || ''" class="flex align-items-center justify-content-between w-full">
          <span>{{ option.name }}</span>
          <small v-if="showCode && option.code" class="text-600 ml-2">{{ option.code }}</small>
        </div>
      </template>
      <template #value="{ placeholder }">
        <div v-if="selectedOption" class="flex align-items-center justify-content-between w-full">
          <span>{{ selectedOption.name }}</span>
          <small v-if="showCode && selectedOption.code" class="text-600 ml-2">{{ selectedOption.code }}</small>
        </div>
        <span v-else>{{ placeholder }}</span>
      </template>
      <template v-if="add" #footer>
        <div class="p-2 border-top-1 surface-border">
          <Button label="Add..." icon="pi pi-plus" size="small" text @click.stop.prevent="openAdd" />
        </div>
      </template>
    </Dropdown>

    <div v-if="isOTH" class="flex flex-column gap-1">
      <label class="text-sm">Please specify</label>
      <InputText v-model="otherText" :class="['w-full', !otherText && 'p-invalid']" />
      <small v-if="!otherText" class="p-error">This field is required.</small>
    </div>

    <Dialog v-model:visible="addVisible" modal header="Add Value" :style="{ width: '420px' }">
      <div class="flex flex-column gap-3">
        <div v-if="addError" class="p-error">{{ addError }}</div>
        <div>
          <label class="block text-sm mb-1">Name</label>
          <InputText v-model="newName" class="w-full" />
        </div>
        <div>
          <label class="block text-sm mb-1">Code</label>
          <InputText v-model="newCode" class="w-full" placeholder="e.g., ABC" />
        </div>
        <div>
          <label class="block text-sm mb-1">Description</label>
          <InputText v-model="newDescription" class="w-full" />
        </div>
        <div class="flex justify-content-end gap-2">
          <Button label="Cancel" text @click="addVisible=false" />
          <Button label="Save" icon="pi pi-check" @click="saveAdd" />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
/* minimal spacing tweaks */
</style>
