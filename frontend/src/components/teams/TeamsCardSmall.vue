<script setup>
import Button from 'primevue/button'

const props = defineProps({
  team: { type: Object, required: true },
  canModify: { type: Boolean, default: false }
})

const emit = defineEmits(['edit'])
</script>

<template>
  <div class="team-card p-2 border-1 surface-border border-round flex align-items-center justify-content-between gap-2">
    <div class="flex align-items-center gap-2">
      <img v-if="team.photo_url" :src="team.photo_url" :alt="team.name" class="avatar" />
      <button class="name-button" @click="emit('edit', team)">
        <span class="font-medium text-900">{{ team.name }}</span>
      </button>
      <span v-if="team.inactive" class="text-600 text-sm">(Inactive)</span>
    </div>
    <div class="text-700 text-sm">
      <span
        v-tooltip.top="(team.cases && team.cases.length) ? team.cases.map(c => c.name).join(', ') : ''"
      >{{ team.cases?.length || 0 }} cases</span>
      <span class="mx-1">•</span>
      <span
        v-tooltip.top="(team.members && team.members.length) ? team.members.map(m => m.name).join(', ') : ''"
      >{{ team.members?.length || 0 }} members</span>
    </div>
    <Button v-if="canModify" icon="pi pi-pencil" size="small" text @click="emit('edit', team)" />
  </div>
</template>

<style scoped>
.name-button { background: transparent; border: none; padding: 0; cursor: pointer; text-align: left; }
.avatar { width: 28px; height: 28px; border-radius: 999px; object-fit: cover; display: block; }
</style>
