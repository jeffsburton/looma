<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import SelectButton from 'primevue/selectbutton'
import { getCookie, setCookie } from '../lib/cookies'

import CaseProfilesLarge from '../components/Cases/CaseProfilesLarge.vue'
import CaseProfilesSmall from '../components/Cases/CaseProfilesSmall.vue'
import CaseProfilesList from '../components/Cases/CaseProfilesList.vue'

const userEmail = ref('')
const userName = ref('')

const COOKIE_KEY = 'ui_cases_view'
const VALID_VIEWS = ['large','small','list']
const view = ref('large')
const viewOptions = [
  { label: 'crop_landscape', value: 'large' },
  { label: 'view_cozy', value: 'small' },
  { label: 'list', value: 'list' }
]

const cases = ref([
  {
    name: 'Kendrick Owen', age: 16, missingDays: 33, caseNumber: 'C-1001',
    photoUrl: '/images/sample_faces/1.png',
    guardians: [{ name: 'John Owen', phone: '702-382-9283' }, { name: 'Moira Owen', phone: '702-392-5818' }],
    leContact: { name: 'Peter Jorgensen', phone: '630-928-3928' },
    agencyContact: { name: 'Angela Consejo', phone: '290-938-1858' }
  },
  {
    name: 'Jasmine Jackson', age: 14, missingDays: 12, caseNumber: 'C-1002',
    photoUrl: '/images/sample_faces/2.png',
    guardians: [{ name: 'Keisha Butler', phone: '702-382-9283' }],
    leContact: { name: 'Axl Pendergast', phone: '908-329-3398' },
    agencyContact: { name: 'Kendra Smith', phone: '714-392-8583' }
  },
  {
    name: 'Chaz Hernandez', age: 17, missingDays: 71, caseNumber: 'C-1003',
    photoUrl: '/images/sample_faces/3.png',
    guardians: [{ name: 'Jesus Hernandez', phone: '702-583-3928' }, { name: 'Maria Hernandez', phone: '698-382-3858' }],
    leContact: { name: 'Brent Lowe', phone: '668-382-5831' },
    agencyContact: { name: 'Ursula Lequinn', phone: '734-392-8581' }
  },
  {
    name: 'Tanya Rider', age: 16, missingDays: 25, caseNumber: 'C-1004',
    photoUrl: '/images/sample_faces/4.png',
    guardians: [{ name: 'Wesley Kendrick', phone: '702-838-2293' }, { name: 'Felicia Sutter', phone: '702-983-0382' }],
    leContact: { name: 'Penelope Yoder', phone: '630-382-0392' },
    agencyContact: { name: 'Janet Orf', phone: '849-392-3902' }
  }
])

onMounted(() => {
  // Restore user info
  userEmail.value = localStorage.getItem('user_email') || 'user@example.com'
  userName.value = localStorage.getItem('user_name') || 'User'
  // Restore view from cookie if present and valid
  try {
    const saved = getCookie(COOKIE_KEY)
    if (saved && VALID_VIEWS.includes(saved)) {
      view.value = saved
    }
  } catch (_) { /* noop */ }
})

// Persist view changes (mirror Sidebar cookie logic: 1 year, Lax)
watch(view, (v) => {
  try {
    if (VALID_VIEWS.includes(v)) {
      setCookie(COOKIE_KEY, v, { maxAge: 60 * 60 * 24 * 365, sameSite: 'Lax' })
    }
  } catch (_) { /* noop */ }
})
</script>

<template>
  <div class="min-h-screen surface-50">

    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Cases'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <!-- Toolbar with SelectButton -->
          <div class="flex align-items-center justify-content-between gap-2 pb-2">
            <div class="text-xl font-semibold">Cases</div>
            <SelectButton v-model="view" :options="viewOptions" optionValue="value" optionLabel="label">
              <template #option="{ option }">
                <span class="material-symbols-outlined">{{ option.label }}</span>
              </template>
            </SelectButton>
          </div>

          <!-- Content panel -->
          <div class="surface-card border-round p-2 flex-1 overflow-auto">
            <CaseProfilesLarge v-if="view === 'large'" :cases="cases" />
            <CaseProfilesSmall v-else-if="view === 'small'" :cases="cases" />
            <CaseProfilesList v-else :cases="cases" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
