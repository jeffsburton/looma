<script setup>
import Card from 'primevue/card'
import Image from 'primevue/image'
import Divider from 'primevue/divider'
import Tag from 'primevue/tag'
import { useRouter } from 'vue-router'

const props = defineProps({
  name: { type: String, required: true },
  age: { type: [String, Number], required: false, default: null },
  missingDays: { type: [String, Number], required: false, default: null },
  caseNumber: { type: [String, Number], default: '' },
  rawId: { type: [String, Number], default: '' },
  photoUrl: { type: String, required: true },
  guardians: { // array of { name, phone }
    type: Array,
    default: () => []
  },
  leContact: { // { name, phone }
    type: Object,
    default: () => ({})
  },
  agencyContact: { // { name, phone }
    type: Object,
    default: () => ({})
  }
})

const router = useRouter()
function goToCase() {
  const caseNum = String(props.caseNumber || '')
  if (!caseNum) return
  router.push({ name: 'case-detail', params: { caseNumber: caseNum, tab: 'core', subtab: 'intake' } })
}

</script>

<template>
  <Card class="youth-profile-card clickable" @click="goToCase">
      <template #header>
        <div class="case-header">Case {{ caseNumber }}</div>
      </template>
    <template #content>
      <div class="profile-card-body">
        <!-- Full-width header with name -->
        <div class="card-header">
          <h2 class="m-0"><span class="material-symbols-outlined name-icon" aria-hidden="true">work</span>{{ name }}<span class="age-after-name"><template v-if="age != null"> age {{ age }}</template><template v-if="missingDays != null">, missing {{missingDays}} days</template><template v-if="caseNumber">, {{ caseNumber }}</template></span></h2>
        </div>

        <!-- Two-panel layout below: photo (left) and text grid (right) -->
        <div class="grid flex-nowrap profile-grid">
          <!-- Photo on the left -->
          <div class="col-12 photo-col">
            <Image :src="photoUrl" alt="profile photo" imageClass="profile-photo border-round" />
          </div>

          <!-- Right content -->
          <div class="col-12 content-col">
            <!-- Table-like grid -->
            <div class="info-grid surface-card">

              <!-- Guardians -->
              <div class="row">
                <div class="cell label">Legal Guardians</div>
                <div class="cell value">
                  <div v-for="(g, i) in guardians" :key="i" class="guardian-item">
                    <div class="font-medium">{{ g.name }}</div>
                    <div class="text-color-secondary text-sm">{{ g.phone }}</div>
                  </div>
                </div>
              </div>

              <!-- LE Contact -->
              <div class="row">
                <div class="cell label">LE Contact</div>
                <div class="cell value">
                  <div class="font-medium">{{ leContact.name }}</div>
                  <div class="text-color-secondary text-sm">{{ leContact.phone }}</div>
                </div>
              </div>

              <!-- Agency Contact -->
              <div class="row">
                <div class="cell label">Agency Contact</div>
                <div class="cell value">
                  <div class="font-medium">{{ agencyContact.name }}</div>
                  <div class="text-color-secondary text-sm">{{ agencyContact.phone }}</div>
                </div>
              </div>

              <!-- Socials -->
              <div class="row">
                <div class="cell label">
                  <i class="pi pi-instagram"></i>&nbsp;
                  <i class="pi pi-tiktok"></i>&nbsp;
                  <i class="pi pi-facebook"></i>
                </div>
              </div>
            </div>

            <Divider class="hidden" />
          </div>
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.youth-profile-card {
  width: 500px;
  font-size: 0.9rem;
  line-height: 1.25;
}
.case-header { padding: .5rem 1rem; font-weight: 600; color: var(--p-primary-800, #1D3B52); }
.clickable { cursor: pointer; }
.youth-profile-card h2 { font-size: 1.3rem; }
.youth-profile-card :deep(.mb-3) { margin-bottom: .5rem !important; }
.youth-profile-card :deep(.p-card-body) {
  padding: 1rem;
  height: 100%;
}
.profile-card-body { display: flex; flex-direction: column; height: 100%; }
.card-header { margin-bottom: .25rem; }
.profile-grid { overflow: hidden; display: flex; flex: 1 1 auto; }
.photo-col { overflow: hidden; display: flex; align-items: center; justify-content: center; flex: 0 0 40%; max-width: 40%; }
:deep(.profile-photo) {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  object-position: center;
  display: block;
}
/* Table-like grid */
.info-grid {
  border: none;
  border-radius: 0;
  overflow: visible;
}
.row { display: grid; grid-template-columns: 2fr 3fr; }
.cell {
  padding: .5rem;
  border-bottom: none;
}
.label {
  text-align: right;
  background: transparent;
}
.value { background: transparent; }


@media (min-width: 768px) {
  /* responsive rules no longer needed for fixed card, keep for safety but overridden below */
}
.profile-grid > .col-12 { width: auto; }
.content-col { flex: 1 1 60%; max-width: 60%; overflow: hidden; display: flex; flex-direction: column; }
.age-after-name { font-size: .8rem; font-weight: normal; color: #6b7280; margin-left: .25rem; }
.name-icon.material-symbols-outlined { font-size: 1em; line-height: 1; vertical-align: -0.125em; margin-right: .35rem; }
</style>
