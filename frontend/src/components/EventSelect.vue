<script setup>
import { ref, watch, computed } from 'vue'
import Select from 'primevue/select'

const props = defineProps({
  modelValue: { type: String, default: '' }, // opaque event id
  placeholder: { type: String, default: 'Select event' },
  disabled: { type: Boolean, default: false },
  filter: { type: Boolean, default: true },
  allowNone: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue', 'change'])

const selectedId = ref(props.modelValue || '')
watch(() => props.modelValue, (v) => { selectedId.value = v || '' })
watch(selectedId, (v) => { emit('update:modelValue', v); emit('change', v) })

const options = ref([])
const loading = ref(false)

async function loadOptions() {
  loading.value = true
  try {
    const resp = await fetch('/api/v1/events')
    if (!resp.ok) throw new Error('Failed to load events')
    const all = await resp.json()
    const active = (all || []).filter(e => !e.inactive)
    const mapped = active.map(e => ({ id: e.id, name: e.name }))
    if (props.allowNone) {
      options.value = [{ id: '', name: 'None' }, ...mapped]
    } else {
      options.value = mapped
    }
  } finally {
    loading.value = false
  }
}

loadOptions()

const selectedOption = computed(() => options.value.find(o => o.id === selectedId.value))
</script>

<template>
  <Select
    v-model="selectedId"
    :options="options"
    optionLabel="name"
    optionValue="id"
    :filter="filter"
    :loading="loading"
    :placeholder="placeholder"
    class="w-full"
    :disabled="disabled"
  >
    <template #value="{ value, placeholder }">
      <span v-if="selectedOption">{{ selectedOption.name }}</span>
      <span v-else>{{ placeholder }}</span>
    </template>
  </Select>
</template>

<style scoped>
</style>
