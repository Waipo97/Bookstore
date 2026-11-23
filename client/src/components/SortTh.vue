<script setup>
// Clickable table header that shows the current sort direction
defineProps({
  field: { type: String, required: true },
  label: { type: String, required: true },
  ordering: { type: String, default: '' },
})
defineEmits(['sort'])
</script>

<template>
  <th class="sortable" @click="$emit('sort', field)">
    {{ label }}
    <i v-if="ordering === field" class="bi bi-caret-up-fill small"></i>
    <i v-else-if="ordering === '-' + field" class="bi bi-caret-down-fill small"></i>
  </th>
</template>
