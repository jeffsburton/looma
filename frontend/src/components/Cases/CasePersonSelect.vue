<script setup>
import { ref, watch, computed } from 'vue'
import Select from 'primevue/select'

const props = defineProps({
  caseId: { type: String, required: true },
  modelValue: { default: '' }, // opaque subject id or null (Unknown)
  primarySubject: { // optional: { id, first_name, last_name }
    type: Object,
    default: null,
  },
  placeholder: { type: String, default: 'Select subject...' },
  disabled: { type: Boolean, default: false },
  filter: { type: Boolean, default: true },
})
const emit = defineEmits(['update:modelValue','change'])

const selected = ref(props.modelValue)
watch(() => props.modelValue, v => { selected.value = v })
watch(selected, v => { emit('update:modelValue', v); emit('change', v) })

const options = ref([])
const loading = ref(false)

function dedupeById(list) {
  const seen = new Set()
  const out = []
  for (const it of list) {
    const id = it?.id || ''
    if (id && !seen.has(id)) { seen.add(id); out.push(it) }
  }
  return out
}

async function load() {
  options.value = []
  if (!props.caseId) return
  loading.value = true
  try {
    // Load subjects linked via subject_case
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/subjects`
    const resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json' } })
    const arr = resp.ok ? (await resp.json()) : []
    const fromSC = (arr || []).map(r => ({ id: r?.subject?.id || '', name: `${r?.subject?.first_name || ''} ${r?.subject?.last_name || ''}`.trim() }))

    // Include primary subject if provided and not already present
    let prim = []
    if (props.primarySubject && props.primarySubject.id) {
      const nm = `${props.primarySubject.first_name || ''} ${props.primarySubject.last_name || ''}`.trim()
      prim = [{ id: props.primarySubject.id, name: nm || 'Subject' }]
    }

    const list = dedupeById([...fromSC, ...prim])
    // Add Unknown at the top
    const unknown = { id: null, name: 'Unknown' }
    options.value = [unknown, ...list]
  } catch (e) {
    console.error(e)
    options.value = [{ id: null, name: 'Unknown' }]
  } finally {
    loading.value = false
  }
}

watch(() => [props.caseId, props.primarySubject?.id, props.primarySubject?.first_name, props.primarySubject?.last_name], () => load(), { immediate: true })

const selectedOption = computed(() => options.value.find(o => o.id === selected.value))
</script>

<template>
  <Select
    v-model="selected"
    :options="options"
    :loading="loading"
    optionLabel="name"
    optionValue="id"
    :filter="filter"
    :placeholder="placeholder"
    class="w-20rem max-w-full"
    :disabled="disabled"
  />
</template>
