<script setup>
import Card from 'primevue/card'
import Image from 'primevue/image'
import { useRouter } from 'vue-router'

const props = defineProps({
  name: { type: String, required: true },
  age: { type: [String, Number], required: false, default: null },
  missingDays: { type: [String, Number], required: false, default: null },
  photoUrl: { type: String, required: true },
  caseNumber: { type: [String, Number], default: '' }
})

const router = useRouter()
function goToCase() {
  router.push({ name: 'case' })
}
</script>

<template>
  <Card class="case-profile-small clickable" @click="goToCase">
    <template #content>
      <div class="small-card">
        <Image :src="photoUrl" alt="profile" imageClass="thumb border-round" />
        <div class="meta">
          <div class="name truncate">{{ name }}</div>
          <div class="sub text-color-secondary text-sm">
            #{{ caseNumber }}<template v-if="age != null"> • {{ age }}y</template><template v-if="missingDays != null"> • {{ missingDays }}d missing</template>
          </div>
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.case-profile-small { width: 220px; }
.clickable { cursor: pointer; }
.small-card { display: flex; gap: .5rem; align-items: center; }
:deep(.p-card-body) { padding: .5rem; }
:deep(.thumb) {
  width: 56px; height: 56px;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  object-position: center;
}
.meta { min-width: 0; }
.name { font-weight: 600; }
.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }


</style>
