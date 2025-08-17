<script setup>
import { ref, computed, onMounted } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import SelectButton from 'primevue/selectbutton'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

// Filter options
const filter = ref('All')
const filterOptions = [
  { label: 'All', value: 'All' },
  { label: 'Shepherds', value: 'Shepherds' },
  { label: 'Agency', value: 'Agency' },
  { label: 'Related to Investigations', value: 'Related to Investigations' }
]

// Sample contacts data (can later be replaced with API)
const contacts = ref([
  { agency: 'Shepherds International', name: 'Angela Consejo', phone: '290-938-1858', email: 'acons@shepherds.org', category: 'Shepherds' },
  { agency: 'Metro PD', name: 'Peter Jorgensen', phone: '630-928-3928', email: 'pjorgensen@metropd.gov', category: 'Agency' },
  { agency: 'Clark County CPS', name: 'Kendra Smith', phone: '714-392-8583', email: 'ksmith@clarkcps.gov', category: 'Agency' },
  { agency: 'Community Watch', name: 'Brent Lowe', phone: '668-382-5831', email: 'brent.lowe@example.com', category: 'Related to Investigations' },
  { agency: 'Shepherds North', name: 'Ursula LeGuin', phone: '734-392-8581', email: 'ursula@shep-north.org', category: 'Shepherds' }
])

const search = ref('')

const filteredContacts = computed(() => {
  const q = search.value.trim().toLowerCase()
  const f = filter.value
  return contacts.value.filter((c) => {
    const matchFilter = f === 'All' || c.category === f
    if (!matchFilter) return false
    if (!q) return true
    return [c.agency, c.name, c.phone, c.email]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q))
  })
})

onMounted(() => {
  // Future hook for loading contacts from API if needed
})
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
              <Button label="Add" icon="pi pi-plus" severity="primary" />
              <span class="text-600 hidden sm:block">Filter:</span>
              <SelectButton v-model="filter" :options="filterOptions" optionLabel="label" optionValue="value" />
            </div>
          </div>

          <!-- Content panel -->
          <div class="surface-card border-round p-2 flex-1 overflow-auto">
            <!-- Search -->
            <div class="flex align-items-center gap-2 mb-2">
              <span class="material-symbols-outlined text-600">search</span>
              <InputText v-model="search" placeholder="Search contacts..." class="w-20rem max-w-full" />
            </div>

            <!-- Table -->
            <DataTable :value="filteredContacts" dataKey="email" stripedRows size="small" class="w-full">
              <Column field="agency" header="Agency" sortable></Column>
              <Column field="name" header="Name" sortable></Column>
              <Column field="phone" header="Phone"></Column>
              <Column field="email" header="Email"></Column>
            </DataTable>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
