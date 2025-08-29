<script setup>
import { ref, watch, computed } from 'vue'
import AvatarCropper from 'vue-avatar-cropper'
import 'cropperjs/dist/cropper.css'
import Button from 'primevue/button'

const props = defineProps({
  kind: { type: String, default: 'team' }, // 'team' | 'person' | 'subject'
  id: { type: String, required: true }, // opaque id
  label: { type: String, default: 'Change' },
  size: { type: Number, default: 48 },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['changed'])

const showCropper = ref(false)
const cacheBust = ref(0)

const uploadUrl = computed(() => `/api/v1/${props.kind}s/${encodeURIComponent(props.id)}/profile_pic`)
const previewUrl = computed(() => `/api/v1/media/pfp/${props.kind}/${encodeURIComponent(props.id)}?t=${cacheBust.value}`)

async function handleUploaded({ response }) {
  try {
    // Attempt to parse JSON to ensure success
    if (response) {
      // Force preview refresh
      cacheBust.value = Date.now()
      emit('changed')
    }
  } catch (e) {
    // ignore
  } finally {
    showCropper.value = false
  }
}
</script>

<template>
  <div class="flex align-items-center gap-2">
    <img :src="previewUrl" alt="Avatar" :style="{ width: size + 'px', height: size + 'px' }" class="avatar-img" />
    <div>
      <Button :label="label" icon="pi pi-image" size="small" :disabled="disabled" @click="showCropper = true" />
      <AvatarCropper
        v-model="showCropper"
        :upload-url="uploadUrl"
        :output-options="{ width: 512, height: 512 }"
        :labels="{ submit: 'Upload', cancel: 'Cancel' }"
        @uploaded="handleUploaded"
      />
    </div>
  </div>
</template>

<style scoped>
.avatar-img { object-fit: cover; border-radius: 50%; }
</style>
