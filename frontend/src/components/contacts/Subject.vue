<script setup>
import { ref, computed, watch } from 'vue'
import InputText from 'primevue/inputtext'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import FloatLabel from 'primevue/floatlabel'
import AvatarEditor from '../../components/common/AvatarEditor.vue'

const props = defineProps({
  modelValue: { type: Object, required: true }, // { id?, first_name, last_name, phone, email, dangerous, danger }
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

// Auto-update for existing
let timer = null
function sanitizeId(raw) {
  const s = String(raw ?? '').trim()
  // take only leading digits or segment before a dot
  const beforeDot = s.split('.')[0]
  const digits = beforeDot.match(/^\d+/)?.[0] ?? beforeDot
  return digits
}
async function updateExisting() {
  const payload = {
    id: m.value.id,
    first_name: m.value.first_name,
    last_name: m.value.last_name,
    phone: m.value.phone || null,
    email: m.value.email || null,
    dangerous: !!m.value.dangerous,
    danger: m.value.dangerous ? (m.value.danger || null) : null,
  }
  // Backend expects PATCH with opaque subject id in the path
  const idPart = String(m.value.id ?? '').trim()
  const url = `/api/v1/subjects/${encodeURIComponent(idPart)}`
  const resp = await fetch(url, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    console.error('Failed to update subject')
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
    dangerous: !!m.value.dangerous,
    danger: m.value.dangerous ? (m.value.danger || null) : null,
  }
  const resp = await fetch('/api/v1/subjects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    console.error('Failed to create subject')
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
    <div class="text-600">Type: Investigatory Subject</div>

    <div v-if="m.id && canEdit" class="flex align-items-center gap-2">
      <label class="block mb-1 text-sm" style="min-width: 100px;">Profile Picture</label>
      <AvatarEditor kind="subject" :id="m.id" :size="48" @changed="$emit('avatarChanged')" />
    </div>

    <div class="grid" style="grid-template-columns: 1fr 1fr; gap: .75rem;">
      <div>
          <FloatLabel v-if="canEdit" variant="on">
            <label class="block mb-1 text-sm">First Name</label>
            <InputText v-if="canEdit" v-model="m.first_name" class="w-full" />
          </FloatLabel>
        <div v-else class="flex align-items-center gap-2"><span class="icon">👤</span> <span>{{ m.first_name }}</span></div>
      </div>
      <div>
          <FloatLabel v-if="canEdit" variant="on">
            <label class="block mb-1 text-sm">Last Name</label>
            <InputText v-if="canEdit" v-model="m.last_name" class="w-full" />
          </FloatLabel>
        <div v-else class="flex align-items-center gap-2"><span class="icon">👤</span> <span>{{ m.last_name }}</span></div>
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
        <label class="block mb-1 text-sm">Phone</label>
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
        <label class="block mb-1 text-sm">Email</label>
        <a v-if="m.email" :href="mailtoHref(m.email)" class="link-row"><span class="icon">✉️</span><span class="text">{{ m.email }}</span></a>
        <span v-else class="text-600">—</span>
      </template>
    </div>

    <div class="flex gap-2 align-items-center">
      <Checkbox inputId="dangerous" v-model="m.dangerous" :binary="true" :disabled="!canEdit" />
      <label for="dangerous">Dangerous</label>
    </div>

    <div v-if="m.dangerous">
      <FloatLabel v-if="canEdit" variant="on">
        <label class="block mb-1 text-sm">Danger</label>
        <InputText v-model="m.danger" class="w-full" />
      </FloatLabel>
      <div v-else class="flex align-items-center gap-2"><span class="icon">⚠️</span> <span>{{ m.danger || '—' }}</span></div>
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
