<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

// File picker with a preview. v-model is a File (new picture) or null;
// `current` is the URL of the picture that is already saved.
const props = defineProps({
  modelValue: { type: [File, null], default: null },
  current: { type: String, default: null },
  label: { type: String, default: 'Image' },
})
const emit = defineEmits(['update:modelValue'])

const preview = ref(null)
watch(
  () => props.modelValue,
  (file) => {
    if (preview.value) URL.revokeObjectURL(preview.value)
    preview.value = file ? URL.createObjectURL(file) : null
  },
)
onBeforeUnmount(() => preview.value && URL.revokeObjectURL(preview.value))

const shown = computed(() => preview.value || props.current)

function onChange(e) {
  emit('update:modelValue', e.target.files[0] || null)
}
</script>

<template>
  <div>
    <label class="form-label">{{ label }}</label>
    <input type="file" accept="image/*" class="form-control" @change="onChange" />
    <img v-if="shown" :src="shown" class="preview-img mt-2" alt="preview" />
  </div>
</template>
