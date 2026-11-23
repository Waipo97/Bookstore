<script setup>
import { computed, onBeforeMount } from 'vue'
import { useCrud, useEditor } from '@/composables/useCrud'
import AppModal from '@/components/AppModal.vue'
import ImageInput from '@/components/ImageInput.vue'
import ImageThumb from '@/components/ImageThumb.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import RelationSelect from '@/components/RelationSelect.vue'
import SortTh from '@/components/SortTh.vue'
import StatsPanel from '@/components/StatsPanel.vue'
import UserFilter from '@/components/UserFilter.vue'

const crud = useCrud('book-photos', {
  fields: ['book', 'image', 'caption'],
  fileFields: ['image'],
  ordering: '-id',
})
const { items, count, page, pageSize, stats, loading, error, filters, ordering } = crud
const editor = useEditor(crud, () => ({ book: null, book_title: '', image: null, caption: '' }))
const { showForm, editingId, form, formError, saving } = editor

onBeforeMount(crud.reload)

const currentImage = computed(() => (typeof form.value.image === 'string' ? form.value.image : null))
const newImage = computed({
  get: () => (form.value.image instanceof File ? form.value.image : null),
  set: (file) => (form.value.image = file),
})

const cards = computed(() =>
  stats.value
    ? [
        { label: 'Photos', value: stats.value.total },
        { label: 'Books with photos', value: stats.value.books_with_photos },
        { label: 'Avg photos per book', value: stats.value.avg_photos_per_book },
      ]
    : [],
)
const breakdown = computed(() => ({
  title: 'Books with the most photos',
  rows: (stats.value?.top_books || []).map((b) => ({ label: b.book, value: b.photos })),
}))
</script>

<template>
  <PageHeader title="Book photos" icon="bi-images" @add="editor.openAdd" @export="crud.exportExcel" @clear="crud.clearFilters">
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
            <th>Photo</th>
            <SortTh field="book_title" label="Book" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="caption" label="Caption" :ordering="ordering" @sort="crud.sort" />
            <th></th>
          </tr>
          <tr class="table-filters">
            <th></th>
            <th></th>
            <th><input v-model="filters.book_title" class="form-control form-control-sm" placeholder="Book" /></th>
            <th><input v-model="filters.caption" class="form-control form-control-sm" placeholder="Caption" /></th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.id }}</td>
            <td><ImageThumb :src="item.image" :title="item.caption || item.book_title" /></td>
            <td>{{ item.book_title }}</td>
            <td>{{ item.caption }}</td>
            <td class="text-end text-nowrap">
              <button class="btn btn-sm btn-success me-1" @click="editor.openEdit(item)"><i class="bi bi-pen-fill"></i></button>
              <button class="btn btn-sm btn-danger" @click="editor.onRemove(item, 'this photo')"><i class="bi bi-x"></i></button>
            </td>
          </tr>
          <tr v-if="!items.length && !loading">
            <td colspan="5" class="text-center text-muted py-4">Nothing found</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-footer"><PaginationBar :page="page" :count="count" :page-size="pageSize" @change="crud.changePage" /></div>
  </div>

  <AppModal v-if="showForm" :title="editingId ? 'Edit photo' : 'New photo'" @close="showForm = false">
    <form id="photo-form" @submit.prevent="editor.submit">
      <div class="alert alert-danger py-2" v-if="formError">{{ formError }}</div>
      <div class="mb-3">
        <RelationSelect v-model="form.book" resource="books" label-key="title" caption="Book" :label="form.book_title" required />
      </div>
      <div class="mb-3">
        <label class="form-label">Caption</label>
        <input v-model="form.caption" class="form-control" maxlength="200" />
      </div>
      <ImageInput v-model="newImage" :current="currentImage" label="Image" />
    </form>
    <template #footer>
      <button class="btn btn-secondary" @click="showForm = false">Close</button>
      <button class="btn btn-primary" type="submit" form="photo-form" :disabled="saving">Save</button>
    </template>
  </AppModal>
</template>
