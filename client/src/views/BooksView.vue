<script setup>
import { computed, onBeforeMount, ref } from 'vue'
import api from '@/api'
import { useCrud, useEditor } from '@/composables/useCrud'
import AppModal from '@/components/AppModal.vue'
import ImageInput from '@/components/ImageInput.vue'
import ImageThumb from '@/components/ImageThumb.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import PhotoAlbum from '@/components/PhotoAlbum.vue'
import RelationSelect from '@/components/RelationSelect.vue'
import SortTh from '@/components/SortTh.vue'
import StatsPanel from '@/components/StatsPanel.vue'
import UserFilter from '@/components/UserFilter.vue'

const crud = useCrud('books', {
  fields: ['title', 'author', 'genre', 'price', 'pages', 'published_year', 'in_stock', 'cover'],
  fileFields: ['cover'],
  ordering: 'title',
})
const { items, count, page, pageSize, stats, loading, error, filters, ordering } = crud
const editor = useEditor(crud, () => ({
  title: '', author: null, author_name: '', genre: null, price: '0.00', pages: 0,
  published_year: null, in_stock: true, cover: null,
}))
const { showForm, editingId, form, formError, saving } = editor

// genres are few, so they are loaded once for the filter and for the form
const genres = ref([])
onBeforeMount(async () => {
  crud.reload()
  const { data } = await api.get('/genres/', { params: { page_size: 1000 } })
  genres.value = data.results
})

const currentCover = computed(() => (typeof form.value.cover === 'string' ? form.value.cover : null))
const newCover = computed({
  get: () => (form.value.cover instanceof File ? form.value.cover : null),
  set: (file) => (form.value.cover = file),
})

const albumBook = ref(null) // book whose photo album is open

const money = (v) => Number(v).toFixed(2)
const cards = computed(() =>
  stats.value
    ? [
        { label: 'Books', value: stats.value.total },
        { label: 'Avg price', value: money(stats.value.avg_price) },
        { label: 'Cheapest', value: money(stats.value.min_price) },
        { label: 'Most expensive', value: money(stats.value.max_price) },
        { label: 'Pages (total)', value: stats.value.total_pages },
        { label: 'In stock', value: `${stats.value.in_stock} / ${stats.value.total}` },
      ]
    : [],
)
const breakdown = computed(() => ({
  title: 'Top genres (books, avg price)',
  rows: (stats.value?.by_genre || []).map((g) => ({ label: g.genre, value: `${g.books} · ${money(g.avg_price)}` })),
}))
</script>

<template>
  <PageHeader title="Books" icon="bi-book" @add="editor.openAdd" @export="crud.exportExcel" @clear="crud.clearFilters">
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
            <th>Cover</th>
            <SortTh field="title" label="Title" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="author_name" label="Author" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="genre_name" label="Genre" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="price" label="Price" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="pages" label="Pages" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="published_year" label="Year" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="in_stock" label="In stock" :ordering="ordering" @sort="crud.sort" />
            <th>Album</th>
            <th></th>
          </tr>
          <tr class="table-filters">
            <th></th>
            <th></th>
            <th><input v-model="filters.title" class="form-control form-control-sm" placeholder="Title" /></th>
            <th><input v-model="filters.author_name" class="form-control form-control-sm" placeholder="Author" /></th>
            <th>
              <select v-model="filters.genre" class="form-select form-select-sm">
                <option value="">All</option>
                <option v-for="g in genres" :key="g.id" :value="g.id">{{ g.name }}</option>
              </select>
            </th>
            <th>
              <div class="d-flex gap-1">
                <input v-model="filters.price_min" type="number" class="form-control form-control-sm" placeholder="from" />
                <input v-model="filters.price_max" type="number" class="form-control form-control-sm" placeholder="to" />
              </div>
            </th>
            <th>
              <div class="d-flex gap-1">
                <input v-model="filters.pages_min" type="number" class="form-control form-control-sm" placeholder="from" />
                <input v-model="filters.pages_max" type="number" class="form-control form-control-sm" placeholder="to" />
              </div>
            </th>
            <th>
              <div class="d-flex gap-1">
                <input v-model="filters.year_min" type="number" class="form-control form-control-sm" placeholder="from" />
                <input v-model="filters.year_max" type="number" class="form-control form-control-sm" placeholder="to" />
              </div>
            </th>
            <th>
              <select v-model="filters.in_stock" class="form-select form-select-sm">
                <option value="">All</option>
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            </th>
            <th></th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.id }}</td>
            <td><ImageThumb :src="item.cover" :title="item.title" /></td>
            <td>{{ item.title }}</td>
            <td>{{ item.author_name }}</td>
            <td>{{ item.genre_name || '—' }}</td>
            <td>{{ money(item.price) }}</td>
            <td>{{ item.pages }}</td>
            <td>{{ item.published_year }}</td>
            <td>
              <span class="badge" :class="item.in_stock ? 'text-bg-success' : 'text-bg-secondary'">
                {{ item.in_stock ? 'Yes' : 'No' }}
              </span>
            </td>
            <td>
              <button class="btn btn-sm btn-outline-primary" @click="albumBook = item">
                <i class="bi bi-images"></i> {{ item.photos_count }}
              </button>
            </td>
            <td class="text-end text-nowrap">
              <button class="btn btn-sm btn-success me-1" @click="editor.openEdit(item)"><i class="bi bi-pen-fill"></i></button>
              <button class="btn btn-sm btn-danger" @click="editor.onRemove(item, `book “${item.title}”`)"><i class="bi bi-x"></i></button>
            </td>
          </tr>
          <tr v-if="!items.length && !loading">
            <td colspan="11" class="text-center text-muted py-4">Nothing found</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-footer"><PaginationBar :page="page" :count="count" :page-size="pageSize" @change="crud.changePage" /></div>
  </div>

  <PhotoAlbum v-if="albumBook" :book="albumBook" @close="albumBook = null" @changed="crud.fetchList" />

  <AppModal v-if="showForm" :title="editingId ? 'Edit book' : 'New book'" @close="showForm = false">
    <form id="book-form" @submit.prevent="editor.submit">
      <div class="alert alert-danger py-2" v-if="formError">{{ formError }}</div>
      <div class="mb-3">
        <label class="form-label">Title</label>
        <input v-model="form.title" class="form-control" required maxlength="255" />
      </div>
      <div class="row mb-3">
        <div class="col-md-6">
          <RelationSelect v-model="form.author" resource="authors" caption="Author" :label="form.author_name" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Genre</label>
          <select v-model="form.genre" class="form-select">
            <option :value="null">---------</option>
            <option v-for="g in genres" :key="g.id" :value="g.id">{{ g.name }}</option>
          </select>
        </div>
      </div>
      <div class="row mb-3">
        <div class="col">
          <label class="form-label">Price</label>
          <input v-model="form.price" type="number" step="0.01" min="0" class="form-control" required />
        </div>
        <div class="col">
          <label class="form-label">Pages</label>
          <input v-model="form.pages" type="number" min="0" class="form-control" required />
        </div>
        <div class="col">
          <label class="form-label">Year</label>
          <input v-model="form.published_year" type="number" min="0" max="3000" class="form-control" />
        </div>
      </div>
      <div class="form-check mb-3">
        <input id="in-stock" v-model="form.in_stock" type="checkbox" class="form-check-input" />
        <label for="in-stock" class="form-check-label">In stock</label>
      </div>
      <ImageInput v-model="newCover" :current="currentCover" label="Cover" />
    </form>
    <template #footer>
      <button class="btn btn-secondary" @click="showForm = false">Close</button>
      <button class="btn btn-primary" type="submit" form="book-form" :disabled="saving">Save</button>
    </template>
  </AppModal>
</template>
