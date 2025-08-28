<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import Dropdown from 'primevue/dropdown'

// A lightweight person selector that will evolve later.
// Emits/accepts an opaque person id (schema: person OPAQUE_MODEL).
const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Select person...' },
  disabled: { type: Boolean, default: false },
  filter: { type: Boolean, default: true },
})
const emit = defineEmits(['update:modelValue', 'change'])

const options = ref([])
const loading = ref(false)
const selected = ref(props.modelValue)
watch(() => props.modelValue, (v) => { selected.value = v })
watch(selected, (v) => { emit('update:modelValue', v); emit('change', v) })

const displayLabel = (p) => {
  const name = [p.first_name, p.last_name].filter(Boolean).join(' ')
  return name
}

const visibleOptions = computed(() => options.value.map(p => ({ ...p, _label: displayLabel(p) })))

async function loadPersons() {
  loading.value = true
  try {
    const resp = await fetch('/api/v1/persons')
    if (!resp.ok) throw new Error('Failed to load people')
    const data = await resp.json()
    options.value = data
  } finally {
    loading.value = false
  }
}

onMounted(loadPersons)
</script>

<template>
  <Dropdown
    v-model="selected"
    :options="visibleOptions"
    :loading="loading"
    optionLabel="_label"
    optionValue="id"
    :filter="filter"
    filterBy="first_name,last_name,email,phone"
    :placeholder="placeholder"
    class="w-full"
    :disabled="disabled"
  />
</template>
