<script setup>
import { computed } from 'vue'
import OverlayBadge from 'primevue/overlaybadge'
import { gMessageCounts } from '@/lib/messages_ws'

const props = defineProps({
  // Name of the table/category to target counts for
  // null/undefined => global total ("count")
  TableName: { type: String, default: null },
  // Encrypted ids (strings). All are optional and may be null/empty.
  CaseId: { type: [String, Number], default: null },
  RfiId: { type: [String, Number], default: null },
  OpsPlanId: { type: [String, Number], default: null },
  TaskId: { type: [String, Number], default: null },
  // Presentation props
  showZero: { type: Boolean, default: false },
  max: { type: Number, default: 99 },
  severity: { type: String, default: 'info' },
  size: { type: String, default: 'small' }, // 'small' | 'normal'
  ariaLabel: { type: String, default: '' },
  badgeOnly: { type: Boolean, default: false },
})

function toStr(v) {
  if (v === null || v === undefined) return ''
  const s = String(v)
  return s.trim()
}

const keys = computed(() => {
  const t = props.TableName ? String(props.TableName).trim().toLowerCase() : ''
  const caseId = toStr(props.CaseId)
  const rfiId = toStr(props.RfiId)
  const opsPlanId = toStr(props.OpsPlanId)
  const taskId = toStr(props.TaskId)

  // Default: global messages count
  if (!t) return ['count']

  if (t === 'case') {
    if (!caseId) return []
    return [`count_${caseId}`]
  }

  if (t === 'rfi') {
    if (!rfiId && !caseId) return ['count_rfis']
    if (!rfiId && caseId) return [`count_rfis_${caseId}`]
    if (rfiId && caseId) return [`count_rfis_${caseId}_${rfiId}`]
    return []
  }

  if (t === 'ops_plan' || t === 'opsplan' || t === 'ops-plans' || t === 'ops_plans') {
    if (!opsPlanId && !caseId) return ['count_ops_plans']
    if (!opsPlanId && caseId) return [`count_ops_plans_${caseId}`]
    if (opsPlanId && caseId) return [`count_ops_plans_${caseId}_${opsPlanId}`]
    return []
  }

  if (t === 'task' || t === 'tasks') {
    if (!taskId && !caseId) return ['count_tasks']
    if (!taskId && caseId) return [`count_tasks_${caseId}`]
    if (taskId && caseId) return [`count_tasks_${caseId}_${taskId}`]
    return []
  }

  // Unknown table name -> nothing
  return []
})

const rawCount = computed(() => {
  const m = gMessageCounts.value || {}
  const arr = keys.value
  if (!arr || !arr.length) return 0
  return arr.reduce((sum, k) => sum + Number(m[k] || 0), 0)
})

const visible = computed(() => props.showZero || rawCount.value > 0)

const displayValue = computed(() => {
  const c = rawCount.value
  return c <= props.max ? String(c) : `${props.max}+`
})

const computedAria = computed(() => props.ariaLabel || `${rawCount.value} unread messages`)
</script>

<template>
  <template v-if="badgeOnly">
    <OverlayBadge
      v-if="visible"
      :value="displayValue"
      :severity="severity"
      :aria-label="computedAria"
      :size="size"
    >
      <span class="umc-badge-anchor"></span>
    </OverlayBadge>
  </template>
  <template v-else>
    <OverlayBadge
      v-if="visible"
      :value="displayValue"
      :severity="severity"
      :aria-label="computedAria"
      :size="size"
    >
      <slot />
    </OverlayBadge>
    <template v-else>
      <slot />
    </template>
  </template>
</template>

<style scoped>
.umc-badge-anchor { display: inline-block; width: 0.001px; height: 0.001px; }
</style>
