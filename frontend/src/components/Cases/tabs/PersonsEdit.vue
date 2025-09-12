<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import PersonPanel from '../../contacts/Person.vue'
import api from '../../../lib/api'

const props = defineProps({
  caseId: { type: [String, Number], default: '' },
})

const route = useRoute()
const router = useRouter()

const caseNumber = computed(() => String(route.params.caseNumber || ''))
const rawId = computed(() => String(route.params.rawPersonId || ''))

const loading = ref(false)
const error = ref('')
const model = ref(null)

function goBack() {
  router.replace({ name: 'case-detail', params: { caseNumber: caseNumber.value, tab: 'contacts', subtab: 'persons' } })
}

function extractRawId(obj) {
  return obj?.raw_id || obj?.rawId || obj?.id_raw || obj?.raw || null
}

async function resolveOpaqueIdFromCaseList() {
  if (!props.caseId || !rawId.value) return null
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/persons`
    const { data } = await api.get(url)
    const arr = data || []
    const needle = String(rawId.value)
    const found = arr.find(r => {
      const p = r?.person || {}
      const rid = extractRawId(p)
      return rid && String(rid) === needle
    })
    return found?.person?.id || null
  } catch (e) {
    console.error(e)
    return null
  }
}

async function load() {
  const id = rawId.value
  if (!id) return
  loading.value = true
  error.value = ''
  try {
    let opaqueId = await resolveOpaqueIdFromCaseList()
    if (!opaqueId) {
      // Fallback: try direct by raw id if supported
      opaqueId = id
    }
    const { data } = await api.get(`/api/v1/persons/${encodeURIComponent(String(opaqueId))}`)
    const p = data || {}
    model.value = {
      id: p.id,
      first_name: p.first_name,
      last_name: p.last_name,
      phone: p.phone,
      email: p.email,
      telegram: p.telegram,
      organization_id: p.organization_id,
    }
  } catch (e) { 
    console.error(e)
    error.value = 'Failed to load person.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function onEdited() {
  goBack()
}
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center gap-2 mb-3">
      <button class="icon-button" @click="goBack" title="Back">
        <span class="material-symbols-outlined">arrow_back</span>
      </button>
      <div class="text-lg font-semibold">Edit Person</div>
    </div>
    <div v-if="error" class="p-error mb-2">{{ error }}</div>
    <div class="surface-card border-round p-2">
      <PersonPanel v-if="model" v-model="model" :isNew="false" :canModify="true" @updated="onEdited" @avatarChanged="onEdited" />
      <div v-else class="p-2 text-600">{{ loading ? 'Loading...' : 'Not found' }}</div>
    </div>
  </div>
</template>

<style scoped>
.icon-button { background: transparent; border: none; padding: .25rem; cursor: pointer; border-radius: 4px; }
.icon-button:hover { background: rgba(0,0,0,0.04); }
</style>
