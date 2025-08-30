<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SidebarMenu from '../components/SidebarMenu.vue'
import SelectButton from 'primevue/selectbutton'
import SplitButton from 'primevue/splitbutton'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Paginator from 'primevue/paginator'
import { getCookie, setCookie } from '../lib/cookies'
import { hasPermission } from '../lib/permissions'
import PersonEditor from '../components/contacts/Person.vue'
import SubjectEditor from '../components/contacts/Subject.vue'

const route = useRoute()
const router = useRouter()

// View toggle (large, small, list)
const COOKIE_KEY = 'ui_contacts_view'
const VALID_VIEWS = ['large','small','list']
const view = ref('large')
// Restore from cookie if valid
try {
  const v = getCookie(COOKIE_KEY)
  const val = (v || '').toString()
  if (VALID_VIEWS.includes(val)) view.value = val
} catch {}
const viewOptions = [
  { label: 'crop_landscape', value: 'large' },
  { label: 'view_cozy', value: 'small' },
  { label: 'table_rows', value: 'list' }
]

// Category filter (keep existing UX)
const filter = ref('All')
const filterOptions = [
  { label: 'All', value: 'All' },
  { label: 'Shepherds', value: 'Shepherds' },
  { label: 'Agency', value: 'Agency' },
  { label: 'Subjects', value: 'Subjects' },
]

// Data loading
const persons = ref([])
const subjects = ref([])
const loading = ref(false)

async function loadData() {
  loading.value = true
  try {
    const [pResp, sResp] = await Promise.all([
      fetch('/api/v1/persons/select'),
      fetch('/api/v1/subjects/select'),
    ])
    if (!pResp.ok) throw new Error('Failed to load persons')
    if (!sResp.ok) throw new Error('Failed to load subjects')
    const p = await pResp.json()
    const s = await sResp.json()
    persons.value = Array.isArray(p) ? p : []
    subjects.value = Array.isArray(s) ? s : []
  } finally {
    loading.value = false
  }
}

const contacts = computed(() => {
  const people = (persons.value || []).map(pr => {
    // persons/select already returns name, phone, email, photo_url, organization_name, is_shepherd, and telegram
    const isShep = !!pr.is_shepherd
    const subType = isShep ? 'Shepherds' : 'Agency'
    return {
      id: pr.id,
      kind: 'person',
      subType, // used for filter only
      name: pr.name || '',
      phone: pr.phone || '',
      email: pr.email || '',
      telegram: pr.telegram || '',
      photo_url: pr.photo_url || '/images/pfp-generic.png',
      organization_name: pr.organization_name || '',
      subLine: pr.organization_name || '',
    }
  })
  const subs = (subjects.value || []).map(sr => {
    const subLine = sr.has_subject_case ? 'Missing Person' : 'Related to Investigation'
    return {
      id: sr.id,
      kind: 'subject',
      subType: 'Subjects', // for filter only
      name: sr.name || ([sr.first_name, sr.last_name].filter(Boolean).join(' ').trim()),
      // Keep explicit name parts to enable correct last, first sorting
      first_name: sr.first_name || '',
      last_name: sr.last_name || '',
      phone: sr.phone || '',
      email: sr.email || '',
      dangerous: !!sr.dangerous,
      danger: sr.danger || '',
      photo_url: sr.photo_url || '/images/pfp-generic.png',
      subLine,
    }
  })
  return [...people, ...subs]
})

const search = ref('')

const canModify = computed(() => hasPermission('CONTACTS.MODIFY'))

const filteredContacts = computed(() => {
  const q = search.value.trim().toLowerCase()
  const f = filter.value
  return contacts.value
    .filter(c => f === 'All' || c.subType === f)
    .filter(c => {
      if (!q) return true
      return [c.name, c.phone, c.email].filter(Boolean).some(v => String(v).toLowerCase().includes(q))
    })
})

// For card views: sort by last name, then first name
function parseNameParts(item) {
  // Prefer explicit subject fields if present
  const hasSubjectNames = item && item.kind === 'subject' && (item.first_name || item.last_name)
  if (hasSubjectNames) {
    return [String(item.first_name || '').trim(), String(item.last_name || '').trim()]
  }
  const full = String(item?.name || '').trim()
  if (!full) return ['', '']
  const parts = full.split(/\s+/)
  if (parts.length === 1) {
    return ['', parts[0]] // first='', last=only token treats single token as last name for sorting consistency
  }
  const last = parts[parts.length - 1]
  const first = parts.slice(0, -1).join(' ')
  return [first, last]
}

const sortedFilteredContacts = computed(() => {
  const arr = filteredContacts.value || []
  return [...arr].sort((a, b) => {
    const [af, al] = parseNameParts(a)
    const [bf, bl] = parseNameParts(b)
    const lastCmp = String(al).localeCompare(String(bl), undefined, { sensitivity: 'base' })
    if (lastCmp !== 0) return lastCmp
    return String(af).localeCompare(String(bf), undefined, { sensitivity: 'base' })
  })
})

// Pagination state for card views
const firstLarge = ref(0)
const rowsLarge = ref(10)
const firstSmall = ref(0)
const rowsSmall = ref(25)

function onPageLarge(e) {
  firstLarge.value = e.first
  rowsLarge.value = e.rows
}
function onPageSmall(e) {
  firstSmall.value = e.first
  rowsSmall.value = e.rows
}

const pagedLargeContacts = computed(() => {
  const start = Math.min(firstLarge.value, Math.max(0, (sortedFilteredContacts.value.length - 1)))
  const end = start + rowsLarge.value
  return sortedFilteredContacts.value.slice(start, end)
})
const pagedSmallContacts = computed(() => {
  const start = Math.min(firstSmall.value, Math.max(0, (sortedFilteredContacts.value.length - 1)))
  const end = start + rowsSmall.value
  return sortedFilteredContacts.value.slice(start, end)
})

// Reset page when filters/search/view change
watch(() => [view.value, filter.value, search.value, sortedFilteredContacts.value.length], () => {
  if (view.value === 'large') firstLarge.value = 0
  if (view.value === 'small') firstSmall.value = 0
})

// Edit overlay state (via route query)
const isEditMode = computed(() => !!route.query.contact)
const editModel = ref({ kind: 'person', subType: 'Shepherds', id: null, first_name: '', last_name: '', phone: '', email: '', telegram: '', organization_id: '', dangerous: false, danger: '' })
const contentRef = ref(null)
const savedScrollTop = ref(0)

function openAdd(type) {
  if (!canModify.value) return
  // type: 'shepherd'|'agency'|'subject'
  const params = { ...route.query, contact: 'new', type }
  router.replace({ name: 'contacts', query: params })
}

function openEdit(item) {
  if (!canModify.value) return
  const id = item?.id || ''
  const type = item?.kind === 'subject' ? 'subject' : (item?.subType === 'Agency' ? 'agency' : 'shepherd')
  router.replace({ name: 'contacts', query: { ...route.query, contact: id, type } })
}

function goToListAndRestore() {
  const { contact, ...rest } = route.query
  router.replace({ name: 'contacts', query: { ...rest } })
}

async function onCreated() {
  await loadData()
  goToListAndRestore()
}

// Populate editModel on route or data change
watch(
  () => [route.query.contact, route.query.type, contacts.value],
  async () => {
    const q = route.query.contact
    const t = String(route.query.type || '')
    if (!q) return
    if (q === 'new') {
      if (t === 'subject') {
        editModel.value = { kind: 'subject', subType: 'Subjects', id: null, first_name: '', last_name: '', phone: '', email: '', telegram: '', organization_id: null, dangerous: false, danger: '' }
      } else if (t === 'agency') {
        editModel.value = { kind: 'person', subType: 'Agency', id: null, first_name: '', last_name: '', phone: '', email: '', telegram: '', organization_id: null, dangerous: false, danger: '' }
      } else {
        editModel.value = { kind: 'person', subType: 'Shepherds', id: null, first_name: '', last_name: '', phone: '', email: '', telegram: '', organization_id: 1, dangerous: false, danger: '' }
      }
      await nextTick()
      return
    }
    // existing
    const item = contacts.value.find(x => String(x.id) === String(q))
    if (item) {
      if (item.kind === 'subject') {
        // Load full subject details
        try {
          const resp = await fetch('/api/v1/subjects')
          if (resp.ok) {
            const arr = await resp.json()
            const s = (arr || []).find(x => String(x.id) === String(item.id))
            if (s) editModel.value = { kind: 'subject', subType: 'Subjects', id: s.id, first_name: s.first_name || '', last_name: s.last_name || '', phone: s.phone || '', email: s.email || '', telegram: '', organization_id: '', dangerous: !!s.dangerous, danger: s.danger || '' }
          }
        } catch {}
      } else {
        // Load full person details
        try {
          const resp = await fetch('/api/v1/persons')
          if (resp.ok) {
            const arr = await resp.json()
            const p = (arr || []).find(x => String(x.id) === String(item.id))
            if (p) editModel.value = { kind: 'person', subType: item.subType, id: p.id, first_name: p.first_name || '', last_name: p.last_name || '', phone: p.phone || '', email: p.email || '', telegram: item.telegram || '', organization_id: (p.organization_id == null ? null : p.organization_id), dangerous: false, danger: '' }
          }
        } catch {}
      }
    }
    await nextTick()
  },
  { immediate: true }
)

// Save/restore scroll like Teams
watch(isEditMode, async (val, oldVal) => {
  const el = contentRef.value
  if (!el) return
  if (val && !oldVal) {
    savedScrollTop.value = el.scrollTop
  } else if (!val && oldVal) {
    await nextTick()
    el.scrollTop = savedScrollTop.value || 0
  }
})

onMounted(async () => {
  await loadData()
})
// Persist view changes to cookie
watch(view, (val) => {
  try {
    if (!VALID_VIEWS.includes(val)) return
    setCookie(COOKIE_KEY, val, { maxAge: 60 * 60 * 24 * 365, sameSite: 'Lax' })
  } catch {}
})
// Helpers for contact links
function telHref(val) {
  if (!val) return ''
  // Keep digits, plus, and leading +, strip spaces/formatting
  const cleaned = String(val).trim()
  // remove all spaces and parentheses/dashes
  const digits = cleaned.replace(/[^+\d]/g, '')
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
</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Contacts'" />
        </div>

        <!-- Main -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <!-- Toolbar -->
          <div class="flex align-items-center justify-content-between gap-2 pb-2">
            <div class="text-xl font-semibold">Contacts</div>
            <div class="flex align-items-center gap-2">
              <!-- Category filter -->
              <span class="text-600 hidden sm:block">Filter:</span>
              <SelectButton v-model="filter" :options="filterOptions" optionLabel="label" optionValue="value" />
              <!-- View toggle -->
              <SelectButton v-model="view" :options="viewOptions" optionValue="value" optionLabel="label">
                <template #option="{ option }">
                  <span class="material-symbols-outlined">{{ option.label }}</span>
                </template>
              </SelectButton>
              <!-- Add split button -->
              <SplitButton v-if="canModify" label="Add" icon="pi pi-plus" :model="[
                { label: 'Shepherd', command: () => openAdd('shepherd') },
                { label: 'Agency Personnel', command: () => openAdd('agency') },
                { label: 'Investigatory Subject', command: () => openAdd('subject') },
              ]" />
            </div>
          </div>

          <!-- Content panel -->
          <div ref="contentRef" class="surface-card border-round p-2 flex-1 overflow-auto">
            <!-- List mode -->
            <template v-if="!isEditMode">
              <div v-if="view === 'large'">
                <div class="cards-grid cards-grid-large">
                  <div v-for="c in pagedLargeContacts" :key="c.kind + ':' + c.id" class="card-large" :class="{ 'can-edit': canModify }" @click="canModify ? openEdit(c) : null">
                    <div class="flex gap-2">
                      <img :src="c.photo_url" alt="pfp" class="pfp pfp-lg" />
                      <div class="min-w-0 flex-1">
                        <div class="text-lg font-semibold name-clip">{{ c.name }}</div>
                        <div class="text-600 text-sm">{{ c.subLine }}</div>
                        <div class="text-sm mt-1 flex flex-column gap-1">
                          <div v-if="c.phone">
                            <a :href="telHref(c.phone)" @click.stop title="Call" class="link-row">
                              <span class="icon">📞</span>
                              <span class="text">{{ c.phone }}</span>
                            </a>
                          </div>
                          <div v-if="c.email">
                            <a :href="mailtoHref(c.email)" @click.stop title="Email" class="link-row">
                              <span class="icon">✉️</span>
                              <span class="text">{{ c.email }}</span>
                            </a>
                          </div>
                          <!-- Telegram for people only -->
                          <div v-if="c.kind === 'person' && c.telegram">
                            <a :href="telegramHref(c.telegram)" @click.stop title="Telegram" target="_blank" rel="noopener noreferrer" class="link-row">
                              <span class="icon">🗨️</span>
                              <span class="text">Telegram: {{ c.telegram }}</span>
                            </a>
                          </div>
                          <!-- Subject danger badge -->
                          <div v-if="c.kind === 'subject' && c.dangerous" class="flex align-items-center gap-2">
                            <Badge :value="c.danger" severity="danger" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <Paginator
                  class="mt-2 w-full"
                  :rows="rowsLarge"
                  :first="firstLarge"
                  :totalRecords="sortedFilteredContacts.length"
                  :rowsPerPageOptions="[10,25,50,100]"
                  @page="onPageLarge"
                />
              </div>
              <div v-else-if="view === 'small'">
                <div class="cards-grid cards-grid-small">
                  <div v-for="c in pagedSmallContacts" :key="c.kind + ':' + c.id" class="card-small" :class="{ 'can-edit': canModify }" @click="canModify ? openEdit(c) : null">
                    <img :src="c.photo_url" alt="pfp" class="pfp pfp-sm" />
                    <div class="min-w-0">
                      <div class="name-clip">{{ c.name }}</div>
                      <small class="text-600 block">{{ c.subLine }}</small>
                      <div v-if="c.kind === 'subject' && c.dangerous" class="mt-1">
                        <Badge :value="c.danger" severity="danger" />
                      </div>
                      <small v-if="c.phone" class="text-700 block">
                                            <a :href="telHref(c.phone)" @click.stop class="inline-link" title="Call">
                                              <span class="icon">📞</span>
                                              <span class="text">{{ c.phone }}</span>
                                            </a>
                                          </small>
                    </div>
                  </div>
                </div>
                <Paginator
                  class="mt-2 w-full"
                  :rows="rowsSmall"
                  :first="firstSmall"
                  :totalRecords="sortedFilteredContacts.length"
                  :rowsPerPageOptions="[10,25,50,100]"
                  @page="onPageSmall"
                />
              </div>
              <div v-else>
                <!-- Table -->
                <div class="flex align-items-center gap-2 mb-2">
                  <span class="material-symbols-outlined text-600">search</span>
                  <InputText v-model="search" placeholder="Search contacts..." class="w-20rem max-w-full" />
                </div>
                <DataTable :value="filteredContacts" dataKey="id" stripedRows size="small" class="w-full" :loading="loading" paginator :rows="25" :rowsPerPageOptions="[10,25,50,100]">
                  <Column header="" style="width:48px">
                    <template #body="{ data }">
                      <img :src="data.photo_url" class="pfp pfp-sm" />
                    </template>
                  </Column>
                  <Column field="name" header="Name" sortable>
                    <template #body="{ data }">
                      <span>{{ data.name }}</span>
                      <Badge v-if="data.kind === 'subject' && data.dangerous" :value="data.danger" severity="danger" class="ml-2" />
                    </template>
                  </Column>
                  <Column field="subLine" header="Organization" sortable></Column>
                  <Column field="phone" header="Phone">
                    <template #body="{ data }">
                      <template v-if="data.phone">
                        <a :href="telHref(data.phone)" title="Call" class="inline-link" @click.stop>
                          <span class="icon">📞</span>
                          <span class="text">{{ data.phone }}</span>
                        </a>
                      </template>
                    </template>
                  </Column>
                  <Column field="email" header="Email">
                    <template #body="{ data }">
                      <template v-if="data.email">
                        <a :href="mailtoHref(data.email)" title="Email" class="inline-link" @click.stop>
                          <span class="icon">✉️</span>
                          <span class="text">{{ data.email }}</span>
                        </a>
                      </template>
                    </template>
                  </Column>
                  <Column field="telegram" header="Telegram">
                    <template #body="{ data }">
                      <template v-if="data.telegram">
                        <a :href="telegramHref(data.telegram)" title="Telegram" class="inline-link" target="_blank" rel="noopener noreferrer" @click.stop>
                          <span class="icon">🗨️</span>
                          <span class="text">{{ data.telegram }}</span>
                        </a>
                      </template>
                    </template>
                  </Column>
                  <Column header="" style="width:1%">
                    <template #body="{ data }">
                      <Button v-if="canModify" icon="pi pi-pencil" text rounded @click.stop="openEdit(data)" />
                    </template>
                  </Column>
                </DataTable>
              </div>
            </template>

            <!-- Edit mode -->
            <template v-else>
              <div class="flex align-items-center gap-2 mb-3">
                <button class="icon-button" @click="goToListAndRestore" title="Back">
                  <span class="material-symbols-outlined">arrow_back</span>
                </button>
                <div class="text-lg font-semibold">{{ editModel.id ? 'Edit Contact' : 'New Contact' }}</div>
              </div>
              <div>
                <PersonEditor
                  v-if="editModel.kind === 'person'"
                  v-model="editModel"
                  :isNew="!editModel.id"
                  :canModify="canModify"
                  @create="onCreated"
                  @cancel="goToListAndRestore"
                  @updated="loadData"
                  @avatarChanged="loadData"
                />
                <SubjectEditor
                  v-else
                  v-model="editModel"
                  :isNew="!editModel.id"
                  :canModify="canModify"
                  @create="onCreated"
                  @cancel="goToListAndRestore"
                  @updated="loadData"
                  @avatarChanged="loadData"
                />
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cards-grid { display: grid; grid-auto-rows: minmax(0, auto); gap: .5rem; }
.cards-grid-large { grid-template-columns: 1fr; }
@media (min-width: 768px) { .cards-grid-large { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.cards-grid-small { grid-template-columns: 1fr; }
@media (min-width: 768px) { .cards-grid-small { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (min-width: 1100px) { .cards-grid-small { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
.card-large { padding: .5rem; border: 1px solid rgba(0,0,0,0.1); border-radius: .5rem; }
.card-large.can-edit { cursor: pointer; }
.card-large.can-edit:hover { background: rgba(0,0,0,0.03); }
.card-small { display: flex; align-items: center; gap: .5rem; padding: .5rem; border: 1px solid rgba(0,0,0,0.1); border-radius: .5rem; }
.card-small.can-edit { cursor: pointer; }
.card-small.can-edit:hover { background: rgba(0,0,0,0.03); }
.pfp { border-radius: 999px; object-fit: cover; }
.pfp-sm { width: 32px; height: 32px; }
.pfp-lg { width: 64px; height: 64px; }
.name-clip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.icon-button { background: transparent; border: none; padding: .25rem; cursor: pointer; border-radius: 4px; }
.icon-button:hover { background: rgba(0,0,0,0.04); }
/* link row styling for contact methods */
.link-row, .inline-link { display: inline-flex; align-items: center; gap: .35rem; text-decoration: none; color: inherit; }
.link-row:hover .text, .inline-link:hover .text { text-decoration: underline; }
.icon { width: 1em; display: inline-flex; align-items: center; justify-content: center; }
</style>
