<script setup>
// Title + buttons above every table
defineProps({ title: { type: String, required: true }, icon: { type: String, default: '' } })
defineEmits(['add', 'export', 'clear'])
</script>

<template>
  <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
    <h2 class="h4 mb-0"><i v-if="icon" class="bi me-2" :class="icon"></i>{{ title }}</h2>
    <div class="d-flex flex-wrap gap-2 align-items-center">
      <slot />
      <button class="btn btn-sm btn-outline-secondary" @click="$emit('clear')">
        <i class="bi bi-x-circle"></i> Clear filters
      </button>
      <button class="btn btn-sm btn-outline-success" @click="$emit('export')">
        <i class="bi bi-file-earmark-excel"></i> Export to Excel
      </button>
      <button class="btn btn-sm btn-primary" @click="$emit('add')"><i class="bi bi-plus-lg"></i> Add</button>
    </div>
  </div>
</template>
