<script setup>
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { setUnauthorizedHandler } from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

// session expired while the page was open -> back to the login page
setUnauthorizedHandler(() => {
  auth.reset()
  router.push({ name: 'login' })
})

async function logout() {
  await auth.logout()
  router.push({ name: 'login' })
}

const links = [
  { to: '/books', label: 'Books', icon: 'bi-book' },
  { to: '/authors', label: 'Authors', icon: 'bi-person-lines-fill' },
  { to: '/genres', label: 'Genres', icon: 'bi-tags' },
  { to: '/book-photos', label: 'Photos', icon: 'bi-images' },
  { to: '/orders', label: 'Orders', icon: 'bi-cart' },
]
</script>

<template>
  <nav v-if="auth.isAuthenticated" class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
    <div class="container-fluid">
      <RouterLink class="navbar-brand" to="/"><i class="bi bi-book-half me-2"></i>Bookstore</RouterLink>
      <ul class="navbar-nav me-auto flex-row flex-wrap">
        <li v-for="l in links" :key="l.to" class="nav-item me-3">
          <RouterLink class="nav-link" :to="l.to"><i class="bi me-1" :class="l.icon"></i>{{ l.label }}</RouterLink>
        </li>
      </ul>
      <div class="d-flex align-items-center gap-2 text-white">
        <span class="small"><i class="bi bi-person-circle me-1"></i>{{ auth.user.username }}<span v-if="auth.isSuperuser" class="badge text-bg-warning ms-1">superuser</span></span>
        <!-- /admin is proxied to Django (see vite.config.js) -->
        <a class="btn btn-sm btn-outline-light" href="/admin/" target="_blank" rel="noopener"><i class="bi bi-gear"></i> Admin panel</a>
        <button class="btn btn-sm btn-outline-light" @click="logout"><i class="bi bi-box-arrow-right"></i> Log out</button>
      </div>
    </div>
  </nav>
  <main class="container-fluid pb-5 px-4"><RouterView /></main>
</template>

<style>
.navbar .nav-link.router-link-active {
  color: #fff;
  font-weight: 600;
}
</style>
