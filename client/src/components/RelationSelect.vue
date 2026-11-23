<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '@/api'

// Dropdown for a foreign key with a search box (tables can have thousands of rows).
//   modelValue – selected id,  label – text of the already selected object
const props = defineProps({
  modelValue: { type: [Number, String, null], default: null },
  resource: { type: String, required: true },
  labelKey: { type: String, default: 'name' },
  label: { type: String, default: '' },
  caption: { type: String, default: '' },
  required: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const search = ref('')
const options = ref([])
const selectedLabel = ref(props.label)

async function load() {
  const { data } = await api.get(`/${props.resource}/`, {
    params: { search: search.value, page_size: 20 },
  })
  options.value = data.results.map((r) => ({ id: r.id, label: r[props.labelKey] }))
}
onMounted(load)

let timer
function onSearch() {
  clearTimeout(timer)
  timer = setTimeout(load, 300)
}

// always keep the selected object in the list, even if it is not in the search result
const merged = computed(() => {
  const list = [...options.value]
  if (props.modelValue && !list.some((o) => o.id === Number(props.modelValue))) {
    list.unshift({ id: Number(props.modelValue), label: selectedLabel.value || `#${props.modelValue}` })
  }
  return list
})

function onChange(e) {
  const id = e.target.value ? Number(e.target.value) : null
  selectedLabel.value = merged.value.find((o) => o.id === id)?.label || ''
  emit('update:modelValue', id)
}
</script>

<template>
  <div>
    <label class="form-label">{{ caption }}</label>
    <input
      v-model="search"
      type="search"
      class="form-control form-control-sm mb-1"
      placeholder="Type to search..."
      @input="onSearch"
    />
    <select class="form-select" :required="required" :value="modelValue ?? ''" @change="onChange">
      <option value="">---------</option>
      <option v-for="o in merged" :key="o.id" :value="o.id">{{ o.label }}</option>
    </select>
  </div>
</template>
