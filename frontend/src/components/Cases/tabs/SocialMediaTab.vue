<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import FloatLabel from 'primevue/floatlabel'
import InputText from 'primevue/inputtext'

import api from '../../../lib/api'
import SocialMediaEdit from './SocialMediaEdit.vue'

const props = defineProps({
  caseId: { type: [String, Number], default: '' },
  primarySubject: { type: Object, default: null },
})

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref('')
const rows = ref([])

// Helper: display only the part after the last '/'
function tailAfterLastSlash(val) {
  const raw = String(val || '').trim()
  if (!raw) return ''
  const noHash = raw.split('#')[0]
  const noQuery = noHash.split('?')[0]
  const trimmed = noQuery.replace(/\/+$/g, '')
  const idx = trimmed.lastIndexOf('/')
  if (idx >= 0) {
    const tail = trimmed.slice(idx + 1)
    return tail || trimmed
  }
  return trimmed
}

// Helper: detect platform (by other/name/code)
function detectPlatform(row) {
  const otherOrName = String((row?.platform_other && String(row.platform_other).trim())
    ? row.platform_other
    : (row?.platform_name || '')).toLowerCase()
  const code = String(row?.platform_code || '').toLowerCase()

  if (otherOrName.includes('facebook') || code === 'fb') return 'facebook'
  if (otherOrName.includes('instagram') || otherOrName.includes('insta') || code === 'ig') return 'instagram'
  if (otherOrName.includes('tiktok') || otherOrName.includes('tik') || otherOrName.includes('tok') || code === 'tik') return 'tiktok'
  if (otherOrName === 'x' || otherOrName.includes('twitter') || code === 'x') return 'x'
  if (otherOrName.includes('linkedin') || code === 'li') return 'linkedin'
  return ''
}

// Helper: PrimeVue icon class for known platforms
function platformIcon(row) {
  const plat = detectPlatform(row)
  if (plat === 'facebook') return 'pi-facebook'
  if (plat === 'instagram') return 'pi-instagram'
  if (plat === 'tiktok') return 'pi-tiktok'
  if (plat === 'x') return 'pi-twitter'
  if (plat === 'linkedin') return 'pi-linkedin'
  return ''
}

// Helper: final href for a row (existing https URL or guessed for known platforms)
function linkUrlForRow(row) {
  const s = String(row?.url || '').trim()
  if (!s) return ''
  if (/^https?:\/\//i.test(s)) return s
  const plat = detectPlatform(row)
  if (!plat) return ''
  const handle = s.replace(/^@+/, '').replace(/^\/+/, '')
  const base = plat === 'facebook' ? 'https://facebook.com/'
    : plat === 'instagram' ? 'https://instagram.com/'
    : plat === 'tiktok' ? 'https://tiktok.com/'
    : ''
  return base ? (base + handle) : ''
}

async function load() {
  if (!props.caseId) { rows.value = []; return }
  loading.value = true
  error.value = ''
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media`
    const resp = await api.get(url)
    const baseRows = resp?.data || []
    // initialize per-row pfp error flag
    rows.value = baseRows.map(r => ({ ...r, _pfpError: false }))
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load social media.'
    rows.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.caseId, () => { load() }, { immediate: true })

const caseNumber = computed(() => String(route.params.caseNumber || ''))
const isEditing = computed(() => !!route.params.rawSocialId)

function openEdit(row) {
  const raw = row?.raw_id || row?.rawId || row?.id
  if (!raw) return
  const cn = caseNumber.value
  const url = `/cases/${encodeURIComponent(String(cn))}/social/${encodeURIComponent(String(raw))}`
  console.log(url);
  router.push({ path: url})
}

function openAdd() {
  const cn = caseNumber.value
  router.push({ path: `/cases/${encodeURIComponent(String(cn))}/social/new` })
}

// Refresh a single row by raw id and splice into rows while preserving local flags
async function refreshRowByRawId(rawId) {
  try {
    const cid = String(props.caseId || '')
    if (!cid || !rawId) return
    const url = `/api/v1/cases/${encodeURIComponent(cid)}/social-media/${encodeURIComponent(String(rawId))}`
    const { data } = await api.get(url)
    if (!data) return

    // Find existing row by raw_id (preferred) or by id fallback
    const idx = rows.value.findIndex(r =>
      String(r.raw_id || r.rawId) === String(rawId) || String(r.id) === String(data.id)
    )
    const preserved = idx >= 0 ? { _pfpError: rows.value[idx]?._pfpError === true } : { _pfpError: false }
    if (idx >= 0) {
      rows.value.splice(idx, 1, { ...data, ...preserved })
    } else {
      // If not found (e.g., pagination/filter), optionally prepend
      rows.value = [{ ...data, ...preserved }, ...rows.value]
    }
  } catch (e) {
    console.error('Failed to refresh row', e)
  }
}

// When leaving edit mode (rawSocialId removed), refresh only that row
watch(
  () => route.params.rawSocialId,
  (val, oldVal) => {
    if (oldVal && !val) {
      if (String(oldVal) !== 'new') {
        refreshRowByRawId(String(oldVal))
      } else {
        // After creating a new item we don't know its id (POST returns ok only); reload list
        load()
      }
    }
  }
)
</script>

<template>
  <div class="p-2 flex flex-column gap-1">
    <template v-if="isEditing">
      <SocialMediaEdit :caseId="String(caseId)" />
    </template>
    <template v-else>
      <div class="flex align-items-center justify-content-between mb-2">
        <div class="text-base font-semibold">Social Media</div>
        <Button label="Add" icon="pi pi-plus" @click="openAdd" />
      </div>
      <div v-if="error" class="p-error mb-2">{{ error }}</div>
      <DataTable :value="rows" dataKey="id" stripedRows size="small" class="w-full" :loading="loading" :rows="25" paginator :rowsPerPageOptions="[10,25,50,100]">
        <Column header="Person">
          <template #body="{ data }">
            <div class="flex align-items-center gap-2" :style="data.rule_out ? 'text-decoration: line-through;' : ''">
              <img :src="data._pfpError ? '/images/pfp-generic.png' : (data.subject?.photo_url || '/images/pfp-generic.png')" class="pfp-sm" alt="pfp" @error="data._pfpError = true" />
              <span>{{ [data.subject?.first_name, data.subject?.last_name].filter(Boolean).join(' ') || 'Unknown' }}</span>
            </div>
          </template>
        </Column>
        <Column header="Platform">
          <template #body="{ data }">
            <span :style="data.rule_out ? 'text-decoration: line-through;' : ''" :title="(String(data.platform_other || '').trim().length > 0) ? data.platform_other : (data.platform_name || '—')">
              <template v-if="platformIcon(data)">
                <i class="pi" :class="platformIcon(data)" aria-hidden="true"></i>
              </template>
              <template v-else>
                {{ (String(data.platform_other || '').trim().length > 0) ? data.platform_other : (data.platform_name || '—') }}
              </template>
            </span>
          </template>
        </Column>
        <Column header="URL">
          <template #body="{ data }">
            <template v-if="linkUrlForRow(data)">
              <a :href="linkUrlForRow(data)" class="link-btn" target="_blank" rel="noopener" :style="data.rule_out ? 'text-decoration: line-through;' : ''">{{ tailAfterLastSlash(data.url) || data.url }}</a>
            </template>
            <template v-else>
              <span :style="data.rule_out ? 'text-decoration: line-through;' : ''">{{ tailAfterLastSlash(data.url) || data.url || '—' }}</span>
            </template>
          </template>
        </Column>
        <Column header="Status">
          <template #body="{ data }">
            <span :style="data.rule_out ? 'text-decoration: line-through;' : ''">{{ data.status_name || '—' }}</span>
          </template>
        </Column>
        <Column header="" style="width:1%">
          <template #body="{ data }">
            <Button icon="pi pi-pencil" text rounded @click.stop="openEdit(data)" />
          </template>
        </Column>
      </DataTable>
    </template>
  </div>
</template>

<style scoped>
.pfp-sm { width: 32px; height: 32px; border-radius: 999px; object-fit: cover; }
</style>
