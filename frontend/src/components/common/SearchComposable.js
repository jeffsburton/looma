// composables/useSearchable.js
import { inject, onMounted, onUnmounted } from 'vue'

export function useSearchable(componentId, searchMethods) {
  const searchAPI = inject('searchAPI')

  if (!searchAPI) {
    //console.warn('useSearchable used outside of SearchWrapper')
    return
  }

  onMounted(() => {
    searchAPI.register(componentId, searchMethods)
  })

  onUnmounted(() => {
    searchAPI.unregister(componentId)
  })
}