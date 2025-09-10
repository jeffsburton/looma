// composables/useSearchable.js
import { inject, onMounted, onUnmounted, getCurrentInstance } from 'vue'

export function useSearchable(componentId, searchMethods) {
  const searchAPI = inject('searchAPI')

  if (!searchAPI) {
    //console.warn('useSearchable used outside of SearchWrapper')
    return
  }

  onMounted(() => {
    const instance = getCurrentInstance()
    // Pass instance as third arg for hierarchy traversal (backward compatible)
    searchAPI.register(componentId, searchMethods, instance)
  })

  onUnmounted(() => {
    searchAPI.unregister(componentId)
  })
}