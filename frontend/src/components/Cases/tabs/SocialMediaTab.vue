<script setup>
import { ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'

// Local editable data model. In the future, lift to store/props/API as needed.
const nextId = ref(1)
const accounts = ref([
  // Start with one empty row to guide the user
  { id: nextId.value++, platform: null, handle: '', owner: '', private: false, active: true }
])

// Allowed platforms per requirement: Instagram, Facebook, TikTok
const platforms = [
  { label: 'Instagram', value: 'instagram' },
  { label: 'Facebook', value: 'facebook' },
  { label: 'TikTok', value: 'tiktok' }
]

function addRow() {
  accounts.value.push({ id: nextId.value++, platform: null, handle: '', owner: '', private: false, active: true })
}

function removeRow(rowId) {
  accounts.value = accounts.value.filter(a => a.id !== rowId)
  if (accounts.value.length === 0) addRow()
}

function normalizeHandle(h) {
  const s = (h || '').trim()
  if (!s) return ''
  // If full URL already, return as is
  if (/^https?:\/\//i.test(s)) return s
  // Strip leading @ if present
  return s.startsWith('@') ? s.slice(1) : s
}

function profileUrl(row) {
  const platform = row?.platform
  const raw = row?.handle
  if (!platform || !raw) return ''
  const h = normalizeHandle(raw)
  // If the handle was actually a URL, just return it
  if (/^https?:\/\//i.test(raw)) return raw
  switch (platform) {
    case 'instagram':
      return `https://www.instagram.com/${h}`
    case 'facebook':
      return `https://www.facebook.com/${h}`
    case 'tiktok':
      // TikTok uses @ in path; add it if user did not include @ originally
      return `https://www.tiktok.com/@${h}`
    default:
      return ''
  }
}
</script>

<template>
  <div class="p-3">
    <div class="text-lg font-semibold mb-3 flex align-items-center gap-2">
      <span class="material-symbols-outlined">photo_camera</span>
      <span>Social Media</span>
    </div>

    <div class="flex justify-content-end mb-2">
      <Button label="Add Account" icon="pi pi-plus" @click="addRow" size="small" />
    </div>

    <DataTable :value="accounts" dataKey="id" stripedRows size="small" class="shadow-1 border-round surface-card">
      <Column header="#" style="width:4rem">
        <template #body="{ index }">
          <span class="text-600">{{ index + 1 }}</span>
        </template>
      </Column>

      <Column field="platform" header="Platform" style="min-width:12rem">
        <template #body="{ data }">
          <Dropdown v-model="data.platform" :options="platforms" optionLabel="label" optionValue="value" placeholder="Select platform" class="w-full" />
        </template>
      </Column>

      <Column field="handle" header="Handle/User Name" style="min-width:16rem">
        <template #body="{ data }">
          <InputText v-model="data.handle" placeholder="@username or URL" class="w-full" />
        </template>
      </Column>

      <Column field="owner" header="Owner" style="min-width:12rem">
        <template #body="{ data }">
          <InputText v-model="data.owner" placeholder="Account owner" class="w-full" />
        </template>
      </Column>

      <Column field="private" header="Private" style="width:8rem; text-align:center" bodyClass="text-center">
        <template #body="{ data }">
          <div class="flex justify-content-center">
            <Checkbox v-model="data.private" :binary="true" :input-id="'priv-' + data.id" />
          </div>
        </template>
      </Column>

      <Column field="active" header="Active" style="width:8rem; text-align:center" bodyClass="text-center">
        <template #body="{ data }">
          <div class="flex justify-content-center">
            <Checkbox v-model="data.active" :binary="true" :input-id="'act-' + data.id" />
          </div>
        </template>
      </Column>

      <Column header="Open" style="width:6rem; text-align:center" bodyClass="text-center">
        <template #body="{ data }">
          <div class="flex justify-content-center">
            <a v-if="profileUrl(data)" :href="profileUrl(data)" target="_blank" rel="noopener" :title="'Open profile'">
              <span class="material-symbols-outlined">open_in_new</span>
            </a>
            <span v-else class="material-symbols-outlined text-300" title="Missing platform or handle">open_in_new</span>
          </div>
        </template>
      </Column>

      <Column header="" style="width:6rem">
        <template #body="{ data }">
          <Button icon="pi pi-trash" severity="danger" text rounded @click="removeRow(data.id)" />
        </template>
      </Column>
    </DataTable>
  </div>
</template>
