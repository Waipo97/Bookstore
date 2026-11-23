<script setup>
import { computed, onBeforeMount } from 'vue'
import { useCrud, useEditor } from '@/composables/useCrud'
import AppModal from '@/components/AppModal.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import SortTh from '@/components/SortTh.vue'
import StatsPanel from '@/components/StatsPanel.vue'
import UserFilter from '@/components/UserFilter.vue'

const crud = useCrud('genres', { fields: ['name', 'description'], ordering: 'name' })
const { items, count, page, pageSize, stats, loading, error, filters, ordering } = crud
const editor = useEditor(crud, () => ({ name: '', description: '' }))
const { showForm, editingId, form, formError, saving } = editor

onBeforeMount(crud.reload)

const cards = computed(() =>
  stats.value
    ? [
        { label: 'Genres', value: stats.value.total },
        { label: 'Books in these genres', value: stats.value.books_total },
        { label: 'Avg books per genre', value: stats.value.avg_books_per_genre },
        { label: 'Most books in one genre', value: stats.value.max_books_in_genre },
      ]
    : [],
)
const breakdown = computed(() => ({
  title: 'Top genres by number of books',
  rows: (stats.value?.top_genres || []).map((g) => ({ label: g.name, value: g.books })),
}))
</script>

<template>
  <PageHeader title="Genres" icon="bi-tags" @add="editor.openAdd" @export="crud.exportExcel" @clear="crud.clearFilters">
    <UserFilter v-model="filters.user" />
  </PageHeader>

  <StatsPanel :cards="cards" :breakdown="breakdown" />
  <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>

  <div class="card">
    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead>
          <tr>
            <SortTh field="id" label="#" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="name" label="Name" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="description" label="Description" :ordering="ordering" @sort="crud.sort" />
            <th></th>
          </tr>
          <tr class="table-filters">
            <th></th>
            <th><input v-model="filters.name" class="form-control form-control-sm" placeholder="Name" /></th>
            <th><input v-model="filters.description" class="form-control form-control-sm" placeholder="Description" /></th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.name }}</td>
            <td class="text-muted">{{ item.description }}</td>
            <td class="text-end text-nowrap">
              <button class="btn btn-sm btn-success me-1" @click="editor.openEdit(item)"><i class="bi bi-pen-fill"></i></button>
              <button class="btn btn-sm btn-danger" @click="editor.onRemove(item, `genre “${item.name}”`)"><i class="bi bi-x"></i></button>
            </td>
          </tr>
          <tr v-if="!items.length && !loading">
            <td colspan="4" class="text-center text-muted py-4">Nothing found</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-footer"><PaginationBar :page="page" :count="count" :page-size="pageSize" @change="crud.changePage" /></div>
  </div>

  <AppModal v-if="showForm" :title="editingId ? 'Edit genre' : 'New genre'" @close="showForm = false">
    <form id="genre-form" @submit.prevent="editor.submit">
      <div class="alert alert-danger py-2" v-if="formError">{{ formError }}</div>
      <div class="mb-3">
        <label class="form-label">Name</label>
        <input v-model="form.name" class="form-control" required maxlength="100" />
      </div>
      <div class="mb-3">
        <label class="form-label">Description</label>
        <textarea v-model="form.description" class="form-control" rows="3"></textarea>
      </div>
    </form>
    <template #footer>
      <button class="btn btn-secondary" @click="showForm = false">Close</button>
      <button class="btn btn-primary" type="submit" form="genre-form" :disabled="saving">Save</button>
    </template>
  </AppModal>
</template>
