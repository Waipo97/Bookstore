<script setup>
import { onMounted, ref } from 'vue'
import api, { formatError } from '@/api'
import AppModal from './AppModal.vue'

// Photo album of one book: view, add several photos at once, delete photos
const props = defineProps({ book: { type: Object, required: true } })
const emit = defineEmits(['close', 'changed'])

const photos = ref([])
const error = ref('')
const uploading = ref(false)
const fileInput = ref(null)
const viewing = ref(null) // photo opened in the big view

async function load() {
  const { data } = await api.get('/book-photos/', { params: { book: props.book.id, page_size: 200 } })
  photos.value = data.results
}
onMounted(load)

async function upload(e) {
  const files = [...e.target.files]
  if (!files.length) return
  uploading.value = true
  error.value = ''
  try {
    for (const file of files) {
      const body = new FormData()
      body.append('book', props.book.id)
      body.append('image', file)
      await api.post('/book-photos/', body)
    }
  } catch (err) {
    error.value = formatError(err)
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
    await load()
    emit('changed')
  }
}

async function remove(photo) {
  if (!confirm('Delete this photo?')) return
  await api.delete(`/book-photos/${photo.id}/`)
  await load()
  emit('changed')
}
</script>

<template>
  <AppModal :title="`Photo album: ${book.title}`" size="xl" @close="emit('close')">
    <div class="mb-3">
      <label class="form-label">Add photos (you can select several)</label>
      <input ref="fileInput" type="file" accept="image/*" multiple class="form-control" :disabled="uploading" @change="upload" />
    </div>
    <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
    <p v-if="!photos.length" class="text-muted mb-0">The album is empty.</p>
    <div class="row g-3">
      <div v-for="photo in photos" :key="photo.id" class="col-6 col-md-4 col-lg-3">
        <div class="card album-item h-100">
          <img :src="photo.image" :alt="photo.caption" @click="viewing = photo" />
          <div class="card-body p-2 d-flex justify-content-between align-items-center">
            <small class="text-truncate">{{ photo.caption || '—' }}</small>
            <button class="btn btn-sm btn-outline-danger" @click="remove(photo)"><i class="bi bi-trash"></i></button>
          </div>
        </div>
      </div>
    </div>
    <AppModal v-if="viewing" nested :title="viewing.caption || book.title" size="lg" @close="viewing = null">
      <img :src="viewing.image" :alt="viewing.caption" class="img-fluid d-block mx-auto" />
    </AppModal>
  </AppModal>
</template>
