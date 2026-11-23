<script setup>
import { computed, onBeforeMount } from 'vue'
import { useCrud, useEditor } from '@/composables/useCrud'
import AppModal from '@/components/AppModal.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import RelationSelect from '@/components/RelationSelect.vue'
import SortTh from '@/components/SortTh.vue'
import StatsPanel from '@/components/StatsPanel.vue'
import UserFilter from '@/components/UserFilter.vue'

const STATUSES = [
  { value: 'new', label: 'New', badge: 'text-bg-primary' },
  { value: 'paid', label: 'Paid', badge: 'text-bg-success' },
  { value: 'shipped', label: 'Shipped', badge: 'text-bg-info' },
  { value: 'cancelled', label: 'Cancelled', badge: 'text-bg-secondary' },
]
const statusInfo = (value) => STATUSES.find((s) => s.value === value) || { label: value, badge: 'text-bg-light' }

const crud = useCrud('orders', {
  fields: ['book', 'customer_name', 'quantity', 'status'],
  ordering: '-created_at',
})
const { items, count, page, pageSize, stats, loading, error, filters, ordering } = crud
const editor = useEditor(crud, () => ({ book: null, book_title: '', customer_name: '', quantity: 1, status: 'new' }))
const { showForm, editingId, form, formError, saving } = editor

onBeforeMount(crud.reload)

const money = (v) => Number(v).toFixed(2)
const date = (v) => new Date(v).toLocaleString()

const cards = computed(() =>
  stats.value
    ? [
        { label: 'Orders', value: stats.value.total },
        { label: 'Books ordered', value: stats.value.total_quantity },
        { label: 'Avg quantity', value: stats.value.avg_quantity },
        { label: 'Revenue (no cancelled)', value: money(stats.value.revenue) },
      ]
    : [],
)
const breakdown = computed(() => ({
  title: 'Orders by status',
  rows: (stats.value?.by_status || []).map((s) => ({ label: statusInfo(s.status).label, value: s.orders })),
}))
</script>

<template>
  <PageHeader title="Orders" icon="bi-cart" @add="editor.openAdd" @export="crud.exportExcel" @clear="crud.clearFilters">
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
            <SortTh field="customer_name" label="Customer" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="book_title" label="Book" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="quantity" label="Qty" :ordering="ordering" @sort="crud.sort" />
            <th>Total</th>
            <SortTh field="status" label="Status" :ordering="ordering" @sort="crud.sort" />
            <SortTh field="created_at" label="Created" :ordering="ordering" @sort="crud.sort" />
            <th></th>
          </tr>
          <tr class="table-filters">
            <th></th>
            <th><input v-model="filters.customer_name" class="form-control form-control-sm" placeholder="Customer" /></th>
            <th><input v-model="filters.book_title" class="form-control form-control-sm" placeholder="Book" /></th>
            <th>
              <div class="d-flex gap-1">
                <input v-model="filters.quantity_min" type="number" class="form-control form-control-sm" placeholder="from" />
                <input v-model="filters.quantity_max" type="number" class="form-control form-control-sm" placeholder="to" />
              </div>
            </th>
            <th></th>
            <th>
              <select v-model="filters.status" class="form-select form-select-sm">
                <option value="">All</option>
                <option v-for="s in STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
              </select>
            </th>
            <th>
              <div class="d-flex gap-1">
                <input v-model="filters.created_from" type="date" class="form-control form-control-sm" />
                <input v-model="filters.created_to" type="date" class="form-control form-control-sm" />
              </div>
            </th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.customer_name }}</td>
            <td>{{ item.book_title }}</td>
            <td>{{ item.quantity }}</td>
            <td>{{ money(item.total_price) }}</td>
            <td><span class="badge" :class="statusInfo(item.status).badge">{{ statusInfo(item.status).label }}</span></td>
            <td class="text-nowrap">{{ date(item.created_at) }}</td>
            <td class="text-end text-nowrap">
              <button class="btn btn-sm btn-success me-1" @click="editor.openEdit(item)"><i class="bi bi-pen-fill"></i></button>
              <button class="btn btn-sm btn-danger" @click="editor.onRemove(item, `order #${item.id}`)"><i class="bi bi-x"></i></button>
            </td>
          </tr>
          <tr v-if="!items.length && !loading">
            <td colspan="8" class="text-center text-muted py-4">Nothing found</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card-footer"><PaginationBar :page="page" :count="count" :page-size="pageSize" @change="crud.changePage" /></div>
  </div>

  <AppModal v-if="showForm" :title="editingId ? 'Edit order' : 'New order'" @close="showForm = false">
    <form id="order-form" @submit.prevent="editor.submit">
      <div class="alert alert-danger py-2" v-if="formError">{{ formError }}</div>
      <div class="mb-3">
        <RelationSelect v-model="form.book" resource="books" label-key="title" caption="Book" :label="form.book_title" required />
      </div>
      <div class="mb-3">
        <label class="form-label">Customer</label>
        <input v-model="form.customer_name" class="form-control" required maxlength="200" />
      </div>
      <div class="row mb-3">
        <div class="col">
          <label class="form-label">Quantity</label>
          <input v-model="form.quantity" type="number" min="1" class="form-control" required />
        </div>
        <div class="col">
          <label class="form-label">Status</label>
          <select v-model="form.status" class="form-select">
            <option v-for="s in STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
      </div>
    </form>
    <template #footer>
      <button class="btn btn-secondary" @click="showForm = false">Close</button>
      <button class="btn btn-primary" type="submit" form="order-form" :disabled="saving">Save</button>
    </template>
  </AppModal>
</template>
