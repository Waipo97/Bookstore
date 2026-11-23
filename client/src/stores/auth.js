import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import api from '@/api'

// Store with the information about the logged in user
export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const ready = ref(false) // have we already asked the backend who we are?
  const users = ref([]) // only filled for superusers (used by the "user" filter)

  const isAuthenticated = computed(() => !!user.value?.is_authenticated)
  const isSuperuser = computed(() => !!user.value?.is_superuser)

  async function fetchMe() {
    // this request also makes Django set the csrftoken cookie
    const { data } = await api.get('/auth/me/')
    user.value = data
    ready.value = true
    if (data.is_superuser) await fetchUsers()
  }

  async function fetchUsers() {
    const { data } = await api.get('/users/')
    users.value = data
  }

  async function login(username, password) {
    const { data } = await api.post('/auth/login/', { username, password })
    user.value = data
    if (data.is_superuser) await fetchUsers()
  }

  async function register(username, password) {
    const { data } = await api.post('/auth/register/', { username, password })
    user.value = data
  }

  async function logout() {
    await api.post('/auth/logout/')
    user.value = { is_authenticated: false }
    users.value = []
  }

  function reset() {
    user.value = { is_authenticated: false }
  }

  return { user, ready, users, isAuthenticated, isSuperuser, fetchMe, login, register, logout, reset }
})
