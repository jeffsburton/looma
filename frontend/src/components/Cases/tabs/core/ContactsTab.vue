<script setup>
import { ref, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

// Temporary local data. In future, replace with props or API data.
const contacts = ref([
  { firstName: 'Jane', lastName: 'Doe', phone: '(555) 123-4567', email: 'jane.doe@example.com', organization: 'Acme Corp', relationship: 'Client' },
  { firstName: 'John', lastName: 'Smith', phone: '(555) 765-4321', email: 'john.smith@example.com', organization: 'Beta LLC', relationship: 'Witness' },
  { firstName: 'Alex', lastName: 'Johnson', phone: '(555) 111-2222', email: 'alex.j@example.com', organization: 'Gamma Org', relationship: 'Family' }
])

const search = ref('')

function add() {
  // Placeholder for future add-contact behavior (e.g., open dialog)
  // Kept minimal per issue request to add the button to the toolbar.
  console.debug('[ContactsTab] Add Contact clicked')
}

const filteredContacts = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return contacts.value
  return contacts.value.filter((c) => {
    return [
      c.firstName,
      c.lastName,
      c.phone,
      c.email,
      c.organization,
      c.relationship
    ]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q))
  })
})
</script>
<template>
  <div class="p-3">

    <div class="flex justify-content-between align-items-center mb-3">
      <div class="flex align-items-center gap-2">
        <span class="material-symbols-outlined text-600">search</span>
        <InputText v-model="search" placeholder="Search contacts..." class="w-20rem max-w-full" />
      </div>
      <Button label="Add Contact" icon="pi pi-plus" size="small" @click="add" />
    </div>

    <DataTable :value="filteredContacts" dataKey="email" stripedRows size="small" class="shadow-1 border-round surface-card">
      <Column field="firstName" header="First Name" sortable></Column>
      <Column field="lastName" header="Last Name" sortable></Column>
      <Column field="phone" header="Phone Number"></Column>
      <Column field="email" header="Email"></Column>
      <Column field="organization" header="Organization" sortable></Column>
      <Column field="relationship" header="Relationship" sortable></Column>
    </DataTable>
  </div>
</template>
