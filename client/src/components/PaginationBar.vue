<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, required: true },
  count: { type: Number, required: true },
  pageSize: { type: Number, required: true },
})
const emit = defineEmits(['change'])

const pages = computed(() => Math.max(1, Math.ceil(props.count / props.pageSize)))
// show a window of page numbers around the current one
const visible = computed(() => {
  const from = Math.max(1, Math.min(props.page - 2, pages.value - 4))
  const to = Math.min(pages.value, from + 4)
  return Array.from({ length: to - from + 1 }, (_, i) => from + i)
})
</script>

<template>
  <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
    <div class="text-muted small">Total: {{ count }}</div>
    <ul class="pagination pagination-sm mb-0">
      <li class="page-item" :class="{ disabled: page <= 1 }">
        <button class="page-link" @click="emit('change', page - 1)">&laquo;</button>
      </li>
      <li v-if="visible[0] > 1" class="page-item">
        <button class="page-link" @click="emit('change', 1)">1</button>
      </li>
      <li v-for="p in visible" :key="p" class="page-item" :class="{ active: p === page }">
        <button class="page-link" @click="emit('change', p)">{{ p }}</button>
      </li>
      <li v-if="visible[visible.length - 1] < pages" class="page-item">
        <button class="page-link" @click="emit('change', pages)">{{ pages }}</button>
      </li>
      <li class="page-item" :class="{ disabled: page >= pages }">
        <button class="page-link" @click="emit('change', page + 1)">&raquo;</button>
      </li>
    </ul>
  </div>
</template>
