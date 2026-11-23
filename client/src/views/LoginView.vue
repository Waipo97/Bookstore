<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { formatError } from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const mode = ref('login') // 'login' | 'register'
const username = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  busy.value = true
  error.value = ''
  try {
    if (mode.value === 'login') await auth.login(username.value, password.value)
    else await auth.register(username.value, password.value)
    router.push(route.query.next || '/')
  } catch (e) {
    error.value = formatError(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="row justify-content-center mt-5">
    <div class="col-12 col-sm-8 col-md-5 col-lg-4">
      <div class="card shadow-sm">
        <div class="card-body p-4">
          <h1 class="h4 mb-1 text-center"><i class="bi bi-book-half me-2"></i>Bookstore</h1>
          <p class="text-muted text-center mb-4">{{ mode === 'login' ? 'Sign in to continue' : 'Create an account' }}</p>
          <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
          <form @submit.prevent="submit">
            <div class="form-floating mb-3">
              <input id="username" v-model="username" class="form-control" placeholder="Username" autocomplete="username" required />
              <label for="username">Username</label>
            </div>
            <div class="form-floating mb-3">
              <input id="password" v-model="password" type="password" class="form-control" placeholder="Password" :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" required />
              <label for="password">Password</label>
            </div>
            <button class="btn btn-primary w-100" :disabled="busy">{{ mode === 'login' ? 'Sign in' : 'Register' }}</button>
          </form>
          <div class="text-center mt-3 small">
            <a v-if="mode === 'login'" href="#" @click.prevent="mode = 'register'; error = ''">No account? Register</a>
            <a v-else href="#" @click.prevent="mode = 'login'; error = ''">Already registered? Sign in</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
