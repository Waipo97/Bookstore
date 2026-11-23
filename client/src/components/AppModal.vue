<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

// `nested` – the window is opened on top of another window
defineProps({
  title: { type: String, default: '' },
  size: { type: String, default: '' },
  nested: { type: Boolean, default: false },
})
const emit = defineEmits(['close'])
const el = ref(null)

// only the top-most window reacts to Esc
function onKey(e) {
  if (e.key !== 'Escape') return
  const dialogs = document.querySelectorAll('.modal.show')
  if (el.value === dialogs[dialogs.length - 1] || !el.value) emit('close')
}
onMounted(() => {
  document.body.classList.add('modal-open')
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  document.body.classList.remove('modal-open')
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <Teleport to="body">
    <div class="modal-backdrop fade show" :style="nested ? { zIndex: 1060 } : {}"></div>
    <div ref="el" class="modal fade show d-block" tabindex="-1" :style="nested ? { zIndex: 1065 } : {}" @mousedown.self="emit('close')">
      <div class="modal-dialog modal-dialog-scrollable" :class="size ? `modal-${size}` : ''">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ title }}</h5>
            <button type="button" class="btn-close" aria-label="Close" @click="emit('close')"></button>
          </div>
          <div class="modal-body"><slot /></div>
          <div v-if="$slots.footer" class="modal-footer"><slot name="footer" /></div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
