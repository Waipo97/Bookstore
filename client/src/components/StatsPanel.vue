<script setup>
// Statistics block shown next to the table.
//   cards:     [{ label, value }]
//   breakdown: { title, rows: [{ label, value }] } (optional top-5 list)
defineProps({
  cards: { type: Array, default: () => [] },
  breakdown: { type: Object, default: null },
})
</script>

<template>
  <div class="row g-2 mb-3">
    <div v-for="card in cards" :key="card.label" class="col-6 col-md-4 col-xl">
      <div class="card stat-card h-100">
        <div class="card-body py-2">
          <div class="text-muted small">{{ card.label }}</div>
          <div class="stat-value">{{ card.value }}</div>
        </div>
      </div>
    </div>
    <div v-if="breakdown && breakdown.rows.length" class="col-12 col-xl-4">
      <div class="card h-100">
        <div class="card-body py-2">
          <div class="text-muted small mb-1">{{ breakdown.title }}</div>
          <div v-for="row in breakdown.rows" :key="row.label" class="d-flex justify-content-between small">
            <span class="text-truncate me-2">{{ row.label }}</span>
            <strong>{{ row.value }}</strong>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
