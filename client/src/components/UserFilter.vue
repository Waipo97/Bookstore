<script setup>
import { useAuthStore } from '@/stores/auth'

// "Filter by user" – only visible to superusers (normal users only see their own data anyway)
defineProps({ modelValue: { type: [String, Number], default: '' } })
defineEmits(['update:modelValue'])
const auth = useAuthStore()
</script>

<template>
  <select
    v-if="auth.isSuperuser"
    class="form-select form-select-sm"
    style="width: auto"
    :value="modelValue"
    @change="$emit('update:modelValue', $event.target.value)"
  >
    <option value="">All users</option>
    <option v-for="u in auth.users" :key="u.id" :value="u.id">{{ u.username }}</option>
  </select>
</template>
