<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import Password from 'primevue/password'
import Button from 'primevue/button'
import FloatLabel from 'primevue/floatlabel'
import Message from 'primevue/message'

const props = defineProps({
  token: {
    type: String,
    default: null
  }
})

const route = useRoute()
const router = useRouter()
const toast = useToast()

const token = ref(props.token || route.params.token || route.query.token)
const loading = ref(false)
const success = ref(false)

const form = ref({
  password: '',
  confirmPassword: ''
})

const errors = ref({})

const validateForm = () => {
  errors.value = {}

  if (!form.value.password) {
    errors.value.password = 'Password is required'
  } else if (form.value.password.length < 6) {
    errors.value.password = 'Password must be at least 6 characters'
  }

  if (form.value.password !== form.value.confirmPassword) {
    errors.value.confirmPassword = 'Passwords do not match'
  }

  return Object.keys(errors.value).length === 0
}

const handlePasswordReset = async () => {
  if (!validateForm()) return

  loading.value = true
  try {
    const apiModule = await import('../lib/api')
    const api = apiModule.default

    const res = await api.post('/api/v1/auth/password-reset/reset', {
      token: token.value,
      new_password: form.value.password,
    })

    if (res.status === 200) {
      success.value = true
      toast.add({
        severity: 'success',
        summary: 'Password Reset Successful',
        detail: 'Your password has been updated successfully',
        life: 3000
      })

      // Redirect after 3 seconds
      setTimeout(() => {
        router.push({
          name: 'login',
          query: { message: 'Password reset successful! Please log in with your new password.' }
        })
      }, 3000)
    }
  } catch (error) {
    const status = error?.response?.status
    if (status === 400) {
      toast.add({
        severity: 'warn',
        summary: 'Invalid or Expired Token',
        detail: 'The reset token is invalid or has expired. Please request a new link.',
        life: 4000
      })
    } else {
      console.error('Password reset failed:', error)
      toast.add({
        severity: 'error',
        summary: 'Reset Failed',
        detail: 'Unable to reset password. Please try again.',
        life: 3000
      })
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex align-items-center justify-content-center min-h-screen p-4">
    <Card class="w-full max-w-md">
      <template #title>
        <div class="text-center">Set New Password</div>
      </template>

      <template #content>
        <div v-if="!token" class="text-center">
          <Message severity="error" :closable="false" class="mb-4">
            <i class="pi pi-exclamation-triangle mr-2"></i>
            Invalid or missing reset token
          </Message>
          <p class="text-color-secondary mb-4">
            Please request a new password reset link.
          </p>
          <router-link to="/password-reset">
            <Button label="Request New Reset" class="w-full" />
          </router-link>
        </div>

        <div v-else-if="success" class="text-center">
          <Message severity="success" :closable="false" class="mb-4">
            <i class="pi pi-check-circle mr-2"></i>
            Password updated successfully!
          </Message>
          <p class="text-color-secondary">
            Redirecting you to the login page...
          </p>
        </div>

        <form v-else @submit.prevent="handlePasswordReset" class="flex flex-column gap-4">
          <div class="flex flex-column gap-2">
            <FloatLabel>
              <Password
                  id="password"
                  v-model="form.password"
                  class="w-full"
                  inputClass="w-full"
                  :class="{ 'p-invalid': errors.password }"
                  toggleMask
                  :feedback="true"
              />
              <label for="password">New Password</label>
            </FloatLabel>
            <small v-if="errors.password" class="p-error">{{ errors.password }}</small>
          </div>

          <div class="flex flex-column gap-2">
            <FloatLabel>
              <Password
                  id="confirmPassword"
                  v-model="form.confirmPassword"
                  class="w-full"
                  inputClass="w-full"
                  :class="{ 'p-invalid': errors.confirmPassword }"
                  :feedback="false"
                  toggleMask
              />
              <label for="confirmPassword">Confirm New Password</label>
            </FloatLabel>
            <small v-if="errors.confirmPassword" class="p-error">{{ errors.confirmPassword }}</small>
          </div>

          <Button
              type="submit"
              label="Update Password"
              class="w-full"
              :loading="loading"
          />
        </form>
      </template>
    </Card>
  </div>
</template>