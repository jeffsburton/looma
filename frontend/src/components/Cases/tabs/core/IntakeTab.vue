<script setup>
import { ref, watch } from 'vue'
import InputText from 'primevue/inputtext'
import Fieldset from 'primevue/fieldset'
import FloatLabel from 'primevue/floatlabel'

// Props: accept case and subject models; allow optional v-model style updates
const props = defineProps({
  caseModel: { type: Object, default: () => ({}) },
  subjectModel: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:caseModel','update:subjectModel'])

// Local mirrors for two-way binding within this component
const mCase = ref({ ...(props.caseModel || {}) })
const mSubject = ref({
  id: props.subjectModel?.id || null,
  first_name: props.subjectModel?.first_name || '',
  last_name: props.subjectModel?.last_name || '',
  middle_name: props.subjectModel?.middle_name || '',
  nicknames: props.subjectModel?.nicknames || '',
})

// Keep local mirrors in sync when parent props change
watch(() => props.caseModel, (v) => { mCase.value = { ...(v || {}) } }, { deep: true })
watch(() => props.subjectModel, (v) => {
  mSubject.value = {
    id: v?.id || null,
    first_name: v?.first_name || '',
    last_name: v?.last_name || '',
    middle_name: v?.middle_name || '',
    nicknames: v?.nicknames || '',
  }
}, { deep: true })

// Emit updates up to parent on changes
watch(mCase, (v) => emit('update:caseModel', v), { deep: true })
watch(mSubject, (v) => emit('update:subjectModel', v), { deep: true })

// Maintain rule: subject.id == case.subject_id
watch(() => mSubject.value.id, (id) => {
  if (!mCase.value) mCase.value = {}
  if (mCase.value.subject_id !== id) mCase.value.subject_id = id || null
})
watch(() => mCase.value?.subject_id, (sid) => {
  if ((mSubject.value.id || null) !== (sid || null)) mSubject.value.id = sid || null
})
</script>

<template>
  <div class="p-3">
    <Fieldset legend="Missing Person">
      <div class="mp-grid">
        <div>
          <FloatLabel variant="on">
            <InputText id="mp-first" v-model="mSubject.first_name" class="w-full" />
            <label for="mp-first">First Name</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <InputText id="mp-middle" v-model="mSubject.middle_name" class="w-full" />
            <label for="mp-middle">Middle Name</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <InputText id="mp-last" v-model="mSubject.last_name" class="w-full" />
            <label for="mp-last">Last Name</label>
          </FloatLabel>
        </div>
        <div>
          <FloatLabel variant="on">
            <InputText id="mp-nick" v-model="mSubject.nicknames" class="w-full" />
            <label for="mp-nick">Nickname(s)</label>
          </FloatLabel>
        </div>
      </div>
    </Fieldset>
  </div>
</template>

<style scoped>
.mp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}
</style>
