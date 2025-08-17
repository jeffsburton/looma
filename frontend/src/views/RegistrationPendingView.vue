<script setup>
import Card from 'primevue/card'
import Button from 'primevue/button'
import { useRouter } from 'vue-router'

const router = useRouter()

const goToLogin = () => {
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="flex align-items-center justify-content-center min-h-screen p-4 surface-50">
    <Card class="w-full max-w-2xl shadow-4">
      <template #title>
        <div class="text-center text-3xl font-bold text-900">Registration Submitted</div>
        <div class="text-center text-600 text-base mt-2 mb-4">
          Thank you for registering. Your account has been created and is pending review by Called2Rescue.
          You will receive an email once your account has been approved and activated.
        </div>
      </template>

      <template #content>
        <div class="flex flex-column align-items-center gap-4 py-4">
          <div class="text-center text-700">
            You can return to the login page now and sign in once your account is activated.
          </div>
          <Button label="Return to Login" icon="pi pi-sign-in" @click="goToLogin" />
        </div>
      </template>
    </Card>
  </div>
</template>

<style scoped>
</style>
