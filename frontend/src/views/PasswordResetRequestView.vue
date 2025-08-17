<script setup>
import { ref } from 'vue'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import FloatLabel from 'primevue/floatlabel'
import Message from 'primevue/message'

const toast = useToast()
const email = ref('')
const loading = ref(false)
const submitted = ref(false)

const handlePasswordResetRequest = async () => {
  if (!email.value) {
    toast.add({
      severity: 'warn',
      summary: 'Email Required',
      detail: 'Please enter your email address',
      life: 3000
    })
    return
  }

  loading.value = true
  try {
    const apiModule = await import('../lib/api')
    const api = apiModule.default
    const res = await api.post('/api/v1/auth/password-reset/request', { email: email.value })

    if (res.status === 200) {
      submitted.value = true
      toast.add({
        severity: 'success',
        summary: 'Reset Link Sent',
        detail: 'If an account exists with that email, we\'ve sent you a reset link',
        life: 5000
      })
    }
  } catch (error) {
    const status = error?.response?.status
    if (status === 404) {
      toast.add({
        severity: 'warn',
        summary: 'Email Not Found',
        detail: 'We could not find an account with that email address.',
        life: 4000
      })
    } else {
      console.error('Password reset request failed:', error)
      toast.add({
        severity: 'error',
        summary: 'Request Failed',
        detail: 'Failed to send reset link. Please try again.',
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
        <div class="text-center">Reset Password</div>
      </template>

      <template #content>
        <div v-if="!submitted">
          <p class="text-color-secondary mb-4 text-center">
            Enter your email address and we'll send you a link to reset your password.
          </p>

          <form @submit.prevent="handlePasswordResetRequest" class="flex flex-column gap-4">
            <FloatLabel>
              <InputText
                  id="email"
                  v-model="email"
                  type="email"
                  class="w-full"
              />
              <label for="email">Email Address</label>
            </FloatLabel>

            <Button
                type="submit"
                label="Send Reset Link"
                class="w-full"
                :loading="loading"
            />
          </form>
        </div>

        <div v-else class="text-center">
          <Message severity="success" :closable="false" class="mb-4">
            <i class="pi pi-check-circle mr-2"></i>
            Reset link sent successfully!
          </Message>
          <p class="text-color-secondary mb-4">
            Check your email for the password reset link. It may take a few minutes to arrive.
          </p>
          <Button
              label="Send Another Link"
              severity="secondary"
              @click="submitted = false"
              class="w-full"
          />
        </div>

        <div class="text-center mt-4">
          <span class="text-sm text-color-secondary">Remember your password? </span>
          <router-link to="/login" class="text-primary font-medium text-sm">Sign in here</router-link>
        </div>
      </template>
    </Card>
  </div>
</template>