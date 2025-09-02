<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Checkbox from 'primevue/checkbox'
import FloatLabel from 'primevue/floatlabel'
import Button from 'primevue/button'
import AvatarEditor from '../../components/common/AvatarEditor.vue'

const props = defineProps({
  modelValue: { type: Object, required: true }, // { id?, first_name, last_name, phone, email, telegram, organization_id }
  isNew: { type: Boolean, default: false },
  canModify: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue','create','cancel','updated','avatarChanged'])

const m = ref({ ...props.modelValue })
// guard to avoid feedback loops when syncing from parent
let syncingFromParent = false
watch(() => props.modelValue, (val) => {
  syncingFromParent = true
  m.value = { ...val }
  // allow reactive chain to settle before re-enabling child emissions
  queueMicrotask(() => { syncingFromParent = false })
}, { deep: true })
watch(m, (val) => {
  if (syncingFromParent) return
  emit('update:modelValue', val)
}, { deep: true })

// Organizations
const orgs = ref([])
const loadingOrgs = ref(false)
async function fetchOrganizations() {
  loadingOrgs.value = true
  try {
    const resp = await fetch('/api/v1/organizations')
    if (resp.ok) {
      orgs.value = await resp.json()
      // Auto-select Called2Rescue (organization.id=1) when creating a Shepherd
      // The organizations API returns opaque ids, so map by name.
      try {
        const isCreating = !!props.isNew
        const wantsShepherd = String(m.value?.subType || '').toLowerCase() === 'shepherds' || m.value?.organization_id === 1
        const notAlreadyOpaque = typeof m.value?.organization_id === 'number' || m.value?.organization_id === 1
        if (isCreating && wantsShepherd) {
          const c2r = (orgs.value || []).find(o => String(o.name).trim().toLowerCase() === 'called2rescue')
          if (c2r && c2r.id) {
            m.value.organization_id = c2r.id
          }
        }
      } catch {}
    }
  } finally { loadingOrgs.value = false }
}

onMounted(() => { fetchOrganizations() })

// Helpers for links
function telHref(val) {
  if (!val) return ''
  const digits = String(val).trim().replace(/[^+\d]/g, '')
  return `tel:${digits}`
}
function mailtoHref(val) {
  if (!val) return ''
  return `sendto:${String(val).trim()}`
}
function telegramHref(val) {
  if (!val) return ''
  const t = String(val).trim()
  if (/^https?:\/\//i.test(t)) return t
  const handle = t.replace(/^@+/, '')
  return `https://t.me/${handle}`
}

// Auto-update for existing
let timer = null
async function updateExisting() {
  const payload = {
    id: m.value.id,
    first_name: m.value.first_name,
    last_name: m.value.last_name,
    phone: m.value.phone || null,
    email: m.value.email || null,
    telegram: m.value.telegram || null,
    organization_id: m.value.organization_id || null,
  }
  // Backend expects PATCH with opaque person id in the path
  const idPart = String(m.value.id ?? '').trim()
  const url = `/api/v1/persons/${encodeURIComponent(idPart)}`
  const resp = await fetch(url, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    // swallow to avoid blocking typing; parent can surface error if desired
    console.error('Failed to update person')
  } else {
    emit('updated')
  }
}

watch(() => ({...m.value}), (val) => {
  if (props.isNew) return
  if (!props.canModify) return
  if (!m.value.id) return
  if (syncingFromParent) return
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => { updateExisting() }, 400)
}, { deep: true })

async function onCreate() {
  const payload = {
    first_name: (m.value.first_name || '').trim(),
    last_name: (m.value.last_name || '').trim(),
    phone: m.value.phone || null,
    email: m.value.email || null,
    telegram: m.value.telegram || null,
    organization_id: m.value.organization_id || null,
  }
  const resp = await fetch('/api/v1/persons', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    console.error('Failed to create person')
    return
  }
  let created = null
  try { created = await resp.json() } catch {}
  emit('create', created)
}

const canEdit = computed(() => props.canModify)
</script>

<template>
  <div class="flex flex-column gap-3" style="max-width:600px;">
    <div v-if="m.id && canEdit" class="flex align-items-center gap-2">
      <label class="block mb-1 text-sm" style="min-width: 100px;">Profile Picture</label>
      <AvatarEditor kind="person" :id="m.id" :size="48" @changed="$emit('avatarChanged')" />
    </div>

    <div class="grid" style="grid-template-columns: 1fr 1fr; gap: .75rem;">
      <div>
          <FloatLabel variant="on">
            <label class="block mb-1 text-sm">First Name</label>
            <InputText v-if="canEdit" v-model="m.first_name" class="w-full" />
          </FloatLabel>
      </div>
      <div>
          <FloatLabel variant="on">
            <label class="block mb-1 text-sm">Last Name</label>
            <InputText v-if="canEdit" v-model="m.last_name" class="w-full" />
          </FloatLabel>
      </div>
    </div>

    <div>
      <template v-if="canEdit">
        <div class="flex align-items-center gap-2">
          <template v-if="m.phone">
            <a :href="telHref(m.phone)" class="icon" title="Call" @click.stop>
              <span>📞</span>
            </a>
          </template>
          <template v-else>
            <span class="icon">📞</span>
          </template>
          <FloatLabel variant="on">
            <label class="block mb-1 text-sm">Phone</label>
            <InputText v-model="m.phone" class="w-full" />
          </FloatLabel>
        </div>
      </template>
      <template v-else>
        <a v-if="m.phone" :href="telHref(m.phone)" class="link-row"><span class="icon">📞</span><span class="text">{{ m.phone }}</span></a>
        <span v-else class="text-600">—</span>
      </template>
    </div>

    <div>
      <template v-if="canEdit">
        <div class="flex align-items-center gap-2">
          <template v-if="m.email">
            <a :href="mailtoHref(m.email)" class="icon" title="Email" @click.stop>
              <span>✉️</span>
            </a>
          </template>
          <template v-else>
            <span class="icon">✉️</span>
          </template>
          <FloatLabel variant="on">
            <label class="block mb-1 text-sm">Email</label>
            <InputText v-model="m.email" class="w-full" />
          </FloatLabel>
        </div>
      </template>
      <template v-else>
        <a v-if="m.email" :href="mailtoHref(m.email)" class="link-row"><span class="icon">✉️</span><span class="text">{{ m.email }}</span></a>
        <span v-else class="text-600">—</span>
      </template>
    </div>

    <div>
      <template v-if="canEdit">
        <div class="flex align-items-center gap-2">
          <template v-if="m.telegram">
            <a :href="telegramHref(m.telegram)" class="icon" title="Telegram" target="_blank" rel="noopener noreferrer" @click.stop>
              <span>🗨️</span>
            </a>
          </template>
          <template v-else>
            <span class="icon">🗨️</span>
          </template>
          <FloatLabel variant="on">
            <label class="block mb-1 text-sm">Telegram</label>
            <InputText v-model="m.telegram" class="w-full" />
          </FloatLabel>
        </div>
      </template>
      <template v-else>
        <a v-if="m.telegram" :href="telegramHref(m.telegram)" target="_blank" rel="noopener" class="link-row"><span class="icon">🗨️</span><span class="text">{{ m.telegram }}</span></a>
        <span v-else class="text-600">—</span>
      </template>
    </div>

    <div>
      <FloatLabel variant="on">
        <Select v-if="canEdit" v-model="m.organization_id" :options="orgs" optionLabel="name" optionValue="id" :loading="loadingOrgs" class="w-full" />
        <label class="block mb-1 text-sm">Organization</label>
      </FloatLabel>
    </div>

    <div v-if="isNew" class="flex justify-content-end gap-2">
      <Button label="Cancel" text @click="$emit('cancel')" />
      <Button v-if="canEdit" label="Create" icon="pi pi-check" @click="onCreate" />
    </div>
  </div>
</template>

<style scoped>
.link-row { display: inline-flex; align-items: center; gap: .35rem; text-decoration: none; color: inherit; }
.link-row:hover .text { text-decoration: underline; }
.icon { width: 1em; display: inline-flex; align-items: center; justify-content: center; }
a.icon, a.icon:hover, a.icon:focus { text-decoration: none; color: inherit; }
</style>
