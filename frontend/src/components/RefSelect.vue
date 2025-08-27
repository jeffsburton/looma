<script setup>
import { ref, watch, onMounted, computed } from 'vue'
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
})
const emit = defineEmits(['update:modelValue', 'update:otherValue', 'change'])

const allOptions = ref([]) // raw list from API [{id, name, description, code, inactive}]
const loading = ref(false)

const selectedId = ref(props.modelValue)
watch(() => props.modelValue, (v) => { selectedId.value = v })
watch(selectedId, (v) => { emit('update:modelValue', v); emit('change', v) })

const otherText = ref(props.otherValue)
watch(() => props.otherValue, (v) => { otherText.value = v })
watch(otherText, (v) => emit('update:otherValue', v))

const selectedOption = computed(() => allOptions.value.find(o => o.id === selectedId.value))
const isOTH = computed(() => (selectedOption.value?.code || '').toUpperCase() === 'OTH')

const visibleOptions = computed(() => {
  // Hide inactive unless it is the selected option
  const sel = selectedId.value
  return allOptions.value.filter(o => !o.inactive || o.id === sel)
})

async function loadOptions() {
  if (!props.code) return
  loading.value = true
  try {
    const resp = await fetch(`/api/v1/reference/${encodeURIComponent(props.code)}/values`)
    if (!resp.ok) throw new Error('Failed to load reference values')
    const data = await resp.json()
    allOptions.value = data
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
</script>

<template>
  <div class="flex flex-column gap-2">
    <Dropdown
      v-model="selectedId"
      :options="visibleOptions"
      :loading="loading"
      optionLabel="name"
      optionValue="id"
      :filter="filter"
      :placeholder="placeholder"
      class="w-full"
      :disabled="disabled"
    >
      <template #option="{ option }">
        <div :title="option.description || ''" class="flex align-items-center justify-content-between w-full">
          <span>{{ option.name }}</span>
          <small v-if="option.code" class="text-600 ml-2">{{ option.code }}</small>
        </div>
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
