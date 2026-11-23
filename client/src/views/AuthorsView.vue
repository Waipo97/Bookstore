<script setup>
import { computed, onBeforeMount } from 'vue'
import { useCrud, useEditor } from '@/composables/useCrud'
import AppModal from '@/components/AppModal.vue'
import ImageInput from '@/components/ImageInput.vue'
import ImageThumb from '@/components/ImageThumb.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import SortTh from '@/components/SortTh.vue'
import StatsPanel from '@/components/StatsPanel.vue'
import UserFilter from '@/components/UserFilter.vue'

const crud = useCrud('authors', {
  fields: ['name', 'country', 'birth_year', 'photo'],
  fileFields: ['photo'],
  ordering: 'name',
})
const { items, count, page, pageSize, stats, loading, error, filters, ordering } = crud
// `photo` in the form is a File (new picture) or null; the saved one comes from the row
const editor = useEditor(crud, () => ({ name: '', country: '', birth_year: null, photo: null }))
const { showForm, editingId, form, formError, saving } = editor

onBeforeMount(crud.reload)

// when editing, `form.photo` still holds the URL string of the saved picture
const currentPhoto = computed(() => (typeof form.value.photo === 'string' ? form.value.photo : null))
const newPhoto = computed({
  get: () => (form.value.photo instanceof File ? form.value.photo : null),
  set: (file) => (form.value.photo = file || currentPhoto.value),
})

const cards = computed(() =>
  stats.value
    ? [
        { label: 'Authors', value: stats.value.total },
        { label: 'Countries', value: stats.value.countries },
        { label: 'Avg birth year', value: stats.value.avg_birth_year },
        { label: 'Oldest born', value: stats.value.oldest_birth_year },
        { label: 'Youngest born', value: stats.value.youngest_birth_year },
      ]
    : [],
)
const breakdown = computed(() => ({
  title: 'Top countries',
  rows: (stats.value?.top_countries || []).map((c) => ({ label: c.country, value: c.authors })),
}))
</script>

<template>
  <PageHeader title="Authors" icon="bi-person-lines-fill" @add="editor.openAdd" @export="crud.exportExcel" @clear="crud.clearFilters">
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
            <SortTh field="name" label="Full name" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="country" label="Country" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="birth_year" label="Birth year" :ordering="ordering" @sort="crud.sort" />
            <th></th>
          </tr>
          <tr class="table-filters">
            <th></th>
            <th></th>
            <th><input v-model="filters.name" class="form-control form-control-sm" placeholder="Name" /></th>
            <th><input v-model="filters.country" class="form-control form-control-sm" placeholder="Country" /></th>
            <th>
              <div class="d-flex gap-1">
                <input v-model="filters.birth_year_min" type="number" class="form-control form-control-sm" placeholder="from" />
                <input v-model="filters.birth_year_max" type="number" class="form-control form-control-sm" placeholder="to" />
              </div>
            </th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.id }}</td>
            <td><ImageThumb :src="item.photo" :title="item.name" /></td>
            <td>{{ item.name }}</td>
            <td>{{ item.country }}</td>
            <td>{{ item.birth_year }}</td>
            <td class="text-end text-nowrap">
              <button class="btn btn-sm btn-success me-1" @click="editor.openEdit(item)"><i class="bi bi-pen-fill"></i></button>
              <button class="btn btn-sm btn-danger" @click="editor.onRemove(item, `author “${item.name}” (their books are deleted too)`)"><i class="bi bi-x"></i></button>
            </td>
          </tr>
          <tr v-if="!items.length && !loading">
            <td colspan="6" class="text-center text-muted py-4">Nothing found</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-footer"><PaginationBar :page="page" :count="count" :page-size="pageSize" @change="crud.changePage" /></div>
  </div>

  <AppModal v-if="showForm" :title="editingId ? 'Edit author' : 'New author'" @close="showForm = false">
    <form id="author-form" @submit.prevent="editor.submit">
      <div class="alert alert-danger py-2" v-if="formError">{{ formError }}</div>
      <div class="mb-3">
        <label class="form-label">Full name</label>
        <input v-model="form.name" class="form-control" required maxlength="200" />
      </div>
      <div class="row mb-3">
        <div class="col">
          <label class="form-label">Country</label>
          <input v-model="form.country" class="form-control" maxlength="100" />
        </div>
        <div class="col">
          <label class="form-label">Birth year</label>
          <input v-model="form.birth_year" type="number" min="0" max="3000" class="form-control" />
        </div>
      </div>
      <ImageInput v-model="newPhoto" :current="currentPhoto" label="Photo" />
    </form>
    <template #footer>
      <button class="btn btn-secondary" @click="showForm = false">Close</button>
      <button class="btn btn-primary" type="submit" form="author-form" :disabled="saving">Save</button>
    </template>
  </AppModal>
</template>
