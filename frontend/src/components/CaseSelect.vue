<script setup>
import { ref, watch, computed } from 'vue'
import Select from 'primevue/select'

const props = defineProps({
  modelValue: { type: String, default: '' }, // opaque case id
  disabled: { type: Boolean, default: false },
  filter: { type: Boolean, default: true },
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
    const resp = await fetch('/api/v1/cases/select', { credentials: 'include', headers: { 'Accept': 'application/json' } })
    if (resp.status === 401) {
      options.value = []
      return
    }
    if (!resp.ok) throw new Error('Failed to load cases')
    options.value = await resp.json()
  } catch (_) {
    // silence in dropdown context
    options.value = []
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
    class="w-full"
    :disabled="disabled"
  >
    <template #option="{ option }">
      <div class="flex align-items-center gap-2 w-full">
        <img :src="option.photo_url" :alt="option.name" class="avatar" />
        <div class="text-900 name-clip">{{ option.name }}</div>
      </div>
    </template>
    <template #value="{ value }">
      <div v-if="selectedOption" class="flex align-items-center gap-2 w-full">
        <img :src="selectedOption.photo_url" :alt="selectedOption.name" class="avatar" />
        <div class="text-900 name-clip">{{ selectedOption.name }}</div>
      </div>
    </template>
  </Select>
</template>

<style scoped>
.avatar { width: 28px; height: 28px; border-radius: 999px; object-fit: cover; }
.name-clip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
