import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

import AuthorsView from '@/views/AuthorsView.vue'
import BookPhotosView from '@/views/BookPhotosView.vue'
import BooksView from '@/views/BooksView.vue'
import GenresView from '@/views/GenresView.vue'
import LoginView from '@/views/LoginView.vue'
import OrdersView from '@/views/OrdersView.vue'

// One route (and one component) per backend model
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/books' },
    { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
    { path: '/genres', name: 'genres', component: GenresView },
    { path: '/authors', name: 'authors', component: AuthorsView },
    { path: '/books', name: 'books', component: BooksView },
    { path: '/book-photos', name: 'book-photos', component: BookPhotosView },
    { path: '/orders', name: 'orders', component: OrdersView },
  ],
})

// Everything except the login page needs authorisation
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.ready) await auth.fetchMe()
  if (to.meta.public) {
    return auth.isAuthenticated && to.name === 'login' ? { path: '/' } : true
  }
  if (!auth.isAuthenticated) return { name: 'login', query: { next: to.fullPath } }
  return true
})

export default router
