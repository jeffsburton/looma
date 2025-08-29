<script setup>
import { ref, watch, computed } from 'vue'
import Select from 'primevue/select'

const props = defineProps({
  modelValue: { type: String, default: '' }, // opaque person id
  shepherds: { type: Boolean, default: true },
  nonShepherds: { type: Boolean, default: true },
  placeholder: { type: String, default: 'Add team member' },
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
  if (!props.shepherds && !props.nonShepherds) {
    options.value = []
    return
  }
  loading.value = true
  try {
    const qs = new URLSearchParams({ shepherds: String(!!props.shepherds), non_shepherds: String(!!props.nonShepherds) })
    const resp = await fetch(`/api/v1/persons/select?${qs.toString()}`)
    if (!resp.ok) throw new Error('Failed to load people')
    options.value = await resp.json()
  } finally {
    loading.value = false
  }
}

watch(() => [props.shepherds, props.nonShepherds], loadOptions, { immediate: true })

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
    :disabled="disabled || (!shepherds && !nonShepherds)"
  >
    <template #option="{ option }">
      <div class="flex align-items-center gap-2 w-full">
        <img :src="option.photo_url" :alt="option.name" class="avatar" />
        <div class="min-w-0 flex-1">
          <!-- First row: name and, for shepherds, the team avatar group on the right -->
          <div class="flex align-items-center w-full">
            <div class="text-900 name-clip flex-1">{{ option.name }}</div>
            <div v-if="option.is_shepherd && option.team_photo_urls?.length" class="flex align-items-center gap-1 ml-2 team-pfps">
              <img v-for="(u, idx) in option.team_photo_urls" :key="idx" :src="u" class="team-avatar" alt="team" />
            </div>
          </div>
          <!-- Second row (only for non-shepherds): organization name -->
          <div v-if="!option.is_shepherd && option.organization_name" class="text-600 text-xs">{{ option.organization_name }}</div>
        </div>
      </div>
    </template>
    <template #value="{ value, placeholder }">
      <div v-if="selectedOption" class="flex align-items-center gap-2 w-full">
        <img :src="selectedOption.photo_url" :alt="selectedOption.name" class="avatar" />
        <div class="min-w-0 flex-1">
          <div class="flex align-items-center w-full">
            <div class="text-900 name-clip flex-1">{{ selectedOption.name }}</div>
            <div v-if="selectedOption.is_shepherd && selectedOption.team_photo_urls?.length" class="flex align-items-center gap-1 ml-2 team-pfps">
              <img v-for="(u, idx) in selectedOption.team_photo_urls" :key="idx" :src="u" class="team-avatar" alt="team" />
            </div>
          </div>
          <div v-if="!selectedOption.is_shepherd && selectedOption.organization_name" class="text-600 text-xs">{{ selectedOption.organization_name }}</div>
        </div>
      </div>
      <span v-else>{{ placeholder }}</span>
    </template>
  </Select>
</template>

<style scoped>
.avatar { width: 28px; height: 28px; border-radius: 999px; object-fit: cover; }
.team-avatar { width: 18px; height: 18px; border-radius: 999px; object-fit: cover; }
.name-clip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.team-pfps { flex-shrink: 0; }
</style>
