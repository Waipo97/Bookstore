<script setup>
import { ref } from 'vue'
import AppModal from './AppModal.vue'

// A small picture; clicking it opens the big one in a modal window
defineProps({ src: { type: String, default: null }, title: { type: String, default: '' } })
const open = ref(false)
</script>

<template>
  <template v-if="src">
    <img :src="src" :alt="title" class="thumb" @click="open = true" />
    <AppModal v-if="open" nested :title="title" size="lg" @close="open = false">
      <img :src="src" :alt="title" class="img-fluid d-block mx-auto" />
    </AppModal>
  </template>
  <span v-else class="thumb-placeholder"><i class="bi bi-image"></i></span>
</template>
