<script setup>
import { ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Image from 'primevue/image'

const props = defineProps({
  cases: { type: Array, default: () => [] }
})

const filters = ref({
  global: { value: null, matchMode: 'contains' },
  name: { value: null, matchMode: 'contains' },
  caseNumber: { value: null, matchMode: 'contains' },
  age: { value: null, matchMode: 'equals' },
  missingDays: { value: null, matchMode: 'gte' }
})

const rows = ref(10)
</script>

<template>
  <div class="panel">
    <DataTable
      :value="cases"
      paginator
      :rows="rows"
      :rowsPerPageOptions="[10,20,50]"
      filterDisplay="menu"
      :filters="filters"
      removableSort
      dataKey="caseNumber"
      :globalFilterFields="['name','caseNumber','age','missingDays']"
      tableStyle="min-width: 40rem"
      class="w-full"
    >
      <template #header>
        <div class="flex justify-content-between align-items-center">
          <span class="text-lg font-bold">Cases</span>
          <span class="p-input-icon-left">
            <i class="pi pi-search" />
            <input type="text" class="p-inputtext p-component" v-model="filters.global.value" placeholder="Search..."/>
          </span>
        </div>
      </template>



      <Column header="Image" style="width: 80px">
        <template #body="{ data }">
          <Image :src="data.photoUrl" alt="thumb" imageClass="w-3rem h-3rem border-round object-cover" preview />
        </template>
      </Column>
      <Column field="name" header="Name" sortable filter filterPlaceholder="Search by name" />
      <Column field="caseNumber" header="Case #" sortable filter filterPlaceholder="Search by case #" />
      <Column field="age" header="Age" sortable filter dataType="numeric" />
      <Column field="missingDays" header="Days Missing" sortable filter dataType="numeric" />
    </DataTable>
  </div>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; height: 100%; }
</style>
