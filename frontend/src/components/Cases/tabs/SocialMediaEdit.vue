<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'

import RefSelect from '../../RefSelect.vue'
import PersonSelect from '../../PersonSelect.vue'
import api from '../../../lib/api'

const props = defineProps({
  caseId: { type: [String, Number], default: '' },
})

const router = useRouter()
const route = useRoute()

const caseNumber = computed(() => String(route.params.caseNumber || ''))
const rawSocialId = computed(() => String(route.params.rawSocialId || ''))
const isNew = computed(() => rawSocialId.value === 'new')

const loading = ref(false)
const error = ref('')

const model = ref({
  id: null,
  subject_id: null,
  platform_id: null,
  platform_code: '',
  platform_other: '',
  url: '',
  status_id: null,
  status_code: '',
  investigated_id: null,
  investigated_code: '',
  rule_out: false,
  notes: '',
  subject: null,
})

const aliases = ref([])
const aliasesLoading = ref(false)

function goBack() {
  router.replace({ name: 'case-detail', params: { caseNumber: caseNumber.value, tab: 'social' } })
}

function href(val) {
  const s = String(val || '').trim()
  if (!s) return ''
  if (/^https?:\/\//i.test(s)) return s
  return ''
}

async function loadExisting() {
  if (!props.caseId || !rawSocialId.value || isNew.value) return
  loading.value = true
  error.value = ''
  try {
    // Prefer direct fetch by raw id
    const directUrl = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media/${encodeURIComponent(String(rawSocialId.value))}`
    const direct = await api.get(directUrl)
    const data = direct?.data || null
    if (data) {
      model.value = { ...model.value, ...data }
      // derive subject_id from nested subject if not provided
      if (!model.value.subject_id && data.subject && data.subject.id) {
        model.value.subject_id = data.subject.id
      }
    } else {
      throw new Error('Not found')
    }
  } catch (e) {
    // Fallback: load list and try to find by either raw_id/rawId or id
    try {
      const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media`
      const resp = await api.get(url)
      const arr = resp?.data || []
      const found = arr.find(r => String(r.raw_id || r.rawId || r.id) === String(rawSocialId.value))
      if (found) {
        model.value = { ...model.value, ...found }
        if (!model.value.subject_id && found.subject && found.subject.id) {
          model.value.subject_id = found.subject.id
        }
      } else {
        throw new Error('Social media record not found')
      }
    } catch (e2) {
      console.error(e2)
      error.value = 'Failed to load social media record.'
    }
  } finally {
    loading.value = false
  }

  // Load aliases
  await loadAliases()
}

async function loadAliases() {
  if (!props.caseId || !model.value?.id) return
  aliasesLoading.value = true
  try {
    const aurl = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media/${encodeURIComponent(String(model.value.id))}/aliases`
    const aresp = await api.get(aurl)
    aliases.value = aresp?.data || []
  } catch (e) {
    console.error(e)
    aliases.value = []
  } finally {
    aliasesLoading.value = false
  }
}

async function patch(patchObj) {
  if (!props.caseId || !model.value?.id) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media/${encodeURIComponent(String(model.value.id))}`
    await api.patch(url, patchObj)
  } catch (e) {
    console.error(e)
    await loadExisting()
  }
}

async function addAlias() {
  if (!props.caseId || !model.value?.id) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media/${encodeURIComponent(String(model.value.id))}/aliases`
    await api.post(url, {})
  } catch (e) {
    console.error(e)
  } finally {
    await loadAliases()
  }
}

async function patchAlias(alias, patchObj) {
  if (!props.caseId || !model.value?.id || !alias?.id) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media/${encodeURIComponent(String(model.value.id))}/aliases/${encodeURIComponent(String(alias.id))}`
    await api.patch(url, patchObj)
  } catch (e) {
    console.error(e)
    await loadAliases()
  }
}

// New record save
const newModel = ref({
  subject_id: null,
  platform_id: null,
  platform_code: '',
  platform_other: '',
  url: '',
  status_id: null,
  status_code: '',
  investigated_id: null,
  investigated_code: '',
  rule_out: false,
  notes: '',
})

async function saveNew() {
  if (!props.caseId) return
  loading.value = true
  error.value = ''
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media`
    const payload = { ...newModel.value }
    const resp = await api.post(url, payload)
    // After save, return to list
    goBack()
  } catch (e) {
    console.error(e)
    error.value = 'Failed to create social media record.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!isNew.value) {
    loadExisting()
  }
})
</script>

<template>
  <div class="p-2">
    <div class="flex align-items-center gap-2 mb-3">
      <button class="icon-button" @click="goBack" title="Back">
        <span class="material-symbols-outlined">arrow_back</span>
      </button>
      <div class="text-lg font-semibold">Edit Social Media</div>
    </div>

    <div v-if="error" class="p-error mb-2">{{ error }}</div>

    <template v-if="isNew">
      <div class="surface-card border-round p-2 flex flex-column gap-2">
        <FloatLabel variant="on" class="w-20rem max-w-full">
          <PersonSelect v-model="newModel.subject_id" :shepherds="false" :agency="false" :subjects="true" />
          <label>Person</label>
        </FloatLabel>

        <FloatLabel variant="on" class="w-20rem max-w-full">
          <RefSelect code="SM_PLATFORM" v-model="newModel.platform_id" :currentCode="newModel.platform_code || ''" :otherValue="newModel.platform_other || ''" @update:otherValue="(v) => { newModel.platform_other = v }" />
          <label>Platform</label>
        </FloatLabel>

        <FloatLabel variant="on" class="w-30rem max-w-full">
          <InputText v-model="newModel.url" class="w-full" />
          <label>URL</label>
        </FloatLabel>

        <FloatLabel variant="on" class="w-20rem max-w-full">
          <RefSelect code="SM_STAT" v-model="newModel.status_id" :currentCode="newModel.status_code || ''" />
          <label>Status</label>
        </FloatLabel>

        <FloatLabel variant="on" class="w-20rem max-w-full">
          <RefSelect code="SM_INV" v-model="newModel.investigated_id" :currentCode="newModel.investigated_code || ''" />
          <label>Investigated</label>
        </FloatLabel>

        <div class="flex align-items-center gap-2">
          <label class="text-sm text-600">Rule Out</label>
          <ToggleSwitch v-model="newModel.rule_out" />
        </div>

        <FloatLabel variant="on" class="w-30rem max-w-full">
          <Textarea v-model="newModel.notes" autoResize rows="3" class="w-full" />
          <label>Notes</label>
        </FloatLabel>

        <div class="flex gap-2 mt-2">
          <Button label="Save" icon="pi pi-check" @click="saveNew" :disabled="loading" />
          <Button label="Cancel" icon="pi pi-times" text @click="goBack" />
        </div>
      </div>
    </template>

    <template v-else>
      <div v-if="loading" class="p-2 text-600">Loading...</div>
      <div class="form-grid">
        <div class="field w-12 md:w-5">
          <FloatLabel variant="on" class="w-full">
            <PersonSelect v-model="model.subject_id" :shepherds="false" :agency="false" :subjects="true" @change="(v) => patch({ subject_id: v })" />
            <label>Person</label>
          </FloatLabel>
        </div>
        <div class="field w-12 md:w-4">
          <FloatLabel variant="on">
            <RefSelect
              code="SM_PLATFORM"
              v-model="model.platform_id"
              :currentCode="model.platform_code || ''"
              :otherValue="model.platform_other || ''"
              @update:otherValue="(v) => { model.platform_other = v }"
              @otherCommit="(v) => patch({ platform_other: v || null })"
              @change="(v) => patch({ platform_id: v })"
            />
            <label>Platform</label>
          </FloatLabel>
        </div>

        <div class="field w-12 md:w-7">
          <div class="flex align-items-center gap-2">
            <FloatLabel variant="on" class="flex-1">
              <InputText v-model="model.url" class="w-full" @change="() => patch({ url: model.url || null })" />
              <label>URL</label>
            </FloatLabel>
            <a class="link-btn" v-if="href(model.url)" :href="model.url" target="_blank" rel="noopener" title="Open">
              <span class="material-symbols-outlined">open_in_new</span>
            </a>
          </div>
        </div>

        <div class="field w-12 md:w-4">
          <FloatLabel variant="on">
            <RefSelect code="SM_STAT" v-model="model.status_id" :currentCode="model.status_code || ''" @change="(v) => patch({ status_id: v })" />
            <label>Status</label>
          </FloatLabel>
        </div>

        <div class="field w-12 md:w-6">
          <div class="flex align-items-end gap-2">
            <div class="flex-1">
              <FloatLabel variant="on" class="w-full">
                <RefSelect code="SM_INV" v-model="model.investigated_id" :currentCode="model.investigated_code || ''" @change="(v) => patch({ investigated_id: v })" />
                <label>Investigated</label>
              </FloatLabel>
            </div>
            <div class="flex align-items-center gap-2 nowrap">
              <label class="text-sm text-600">Rule Out</label>
              <ToggleSwitch v-model="model.rule_out" @update:modelValue="(v) => patch({ rule_out: v })" />
            </div>
          </div>
        </div>

        <div class="field w-11">
          <FloatLabel variant="on" class="w-full">
            <Textarea v-model="model.notes" autoResize rows="2" class="w-full" @change="() => patch({ notes: model.notes || null })" />
            <label>Notes</label>
          </FloatLabel>
        </div>
      </div>

      <div class="w-12">
        <div class="flex flex-column gap-2 p-2 border-1 surface-border border-round">
          <div class="text-sm text-600">Aliases</div>
          <div v-if="aliasesLoading" class="text-600 text-sm">Loading aliases...</div>
          <div class="flex form-grid" v-for="alias in aliases" :key="alias.id">
            <FloatLabel variant="on" class="flex-column w-3">
              <RefSelect
                code="SM_ALIAS"
                v-model="alias.alias_status_id"
                :currentCode="alias.alias_status_code || ''"
                @change="(v) => patchAlias(alias, { alias_status_id: v })"
              />
              <label>Status</label>
            </FloatLabel>
            <FloatLabel variant="on" class="flex-column w-4">
              <InputText v-model="alias.alias" class="w-full" @change="() => patchAlias(alias, { alias: alias.alias || null })" />
              <label>Alias</label>
            </FloatLabel>
            <FloatLabel variant="on" class="flex-column w-4">
              <PersonSelect v-model="alias.alias_owner_id" @change="(v) => patchAlias(alias, { alias_owner_id: v })" />
              <label>Owner</label>
            </FloatLabel>
          </div>
          <div class="flex">
            <Button label="Add Alias" size="small" icon="pi pi-plus" text @click="addAlias" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.form-grid { display: flex; flex-wrap: wrap; gap: 0.25rem 0.5rem; }
.field { min-width: 12rem; }
.icon-button { background: transparent; border: none; padding: .25rem; cursor: pointer; border-radius: 4px; }
.icon-button:hover { background: rgba(0,0,0,0.04); }
@media (max-width: 640px) { .field { min-width: 100%; } }
</style>
