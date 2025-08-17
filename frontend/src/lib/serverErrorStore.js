import { reactive } from 'vue'

export const serverErrorState = reactive({
  visible: false,
  message: '',
  details: null
})

export function showServerError({ message, details } = {}) {
  serverErrorState.message = message || 'A server error occurred.'
  serverErrorState.details = details || null
  serverErrorState.visible = true
}

export function hideServerError() {
  serverErrorState.visible = false
}
