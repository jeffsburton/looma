<script setup>
import { ref, computed, watch } from 'vue'
import Paginator from 'primevue/paginator'
import InputText from 'primevue/inputtext'
import InputGroup from 'primevue/inputgroup'
import InputGroupAddon from 'primevue/inputgroupaddon'
import Button from 'primevue/button'
import CaseProfileCardLarge from './CaseProfileCardLarge.vue'

const props = defineProps({
  cases: { type: Array, default: () => [] },
  rows: { type: Number, default: 10 }
})

const first = ref(0)
const onPage = (e) => { first.value = e.first }

// Search term
const searchTerm = ref('')

// Filter across all relevant properties of a case
const filteredCases = computed(() => {
  const q = searchTerm.value?.toString().toLowerCase().trim()
  if (!q) return props.cases
  return props.cases.filter((c) => {
    const parts = [
      c.name,
      c.caseNumber,
      c.age?.toString(),
      c.missingDays?.toString(),
      c.photoUrl,
      // guardians
      ...(Array.isArray(c.guardians) ? c.guardians.flatMap(g => [g?.name, g?.phone]) : []),
      // contacts
      c.leContact?.name, c.leContact?.phone,
      c.agencyContact?.name, c.agencyContact?.phone
    ].filter(Boolean).map(v => v.toString().toLowerCase())
    return parts.some(p => p.includes(q))
  })
})

// Reset to first page when search changes
watch(searchTerm, () => { first.value = 0 })

const pagedCases = computed(() => {
  const start = first.value
  const end = start + props.rows
  return filteredCases.value.slice(start, end)
})
</script>

<template>
  <div class="panel">
    <!-- Toolbar with search -->
    <div class=" p-2 pb-3 flex align-items-center justify-content-between gap-2">

      <InputGroup>
        <InputText v-model="searchTerm"  placeholder="Search cases" />
        <InputGroupAddon>
          <Button icon="pi pi-search" severity="secondary" variant="text" />
        </InputGroupAddon>
      </InputGroup>

    </div>

    <div class="cards">
      <CaseProfileCardLarge
        v-for="(c, i) in pagedCases"
        :key="i"
        :name="c.name"
        :age="c.age"
        :missing-days="c.missingDays"
        :photo-url="c.photoUrl || c.photo_url"
        :guardians="c.guardians"
        :le-contact="c.leContact"
        :agency-contact="c.agencyContact"
        :case-number="c.caseNumber || c.id"
        class="mb-2 flex-none"
      />
    </div>
    <div class="paginator">
      <Paginator
        :rows="rows"
        :totalRecords="filteredCases.length"
        :first="first"
        :rowsPerPageOptions="[10,20,50]"
        @page="onPage"
      />
    </div>
  </div>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; height: 100%; }
.cards { display: flex; flex-wrap: wrap; gap: .5rem; align-content: flex-start; }
.paginator { margin-top: auto; padding-top: .5rem; }
.toolbar :deep(.p-inputtext) { width: 18rem; }
</style>
