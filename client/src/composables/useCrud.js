import { onBeforeUnmount, reactive, ref, watch } from 'vue'
import api, { formatError } from '@/api'

/**
 * Everything a CRUD table needs: list + pagination + column filters + sorting,
 * statistics, create / update / delete and the Excel export.
 *
 *   resource   – API path, e.g. 'books' -> /api/books/
 *   fields     – writable fields that are sent to the server
 *   fileFields – subset of `fields` that hold pictures (sent only when a new File was chosen)
 */
export function useCrud(resource, { fields, fileFields = [], pageSize = 20, ordering: initialOrdering = '' }) {
  const items = ref([])
  const count = ref(0)
  const page = ref(1)
  const stats = ref(null)
  const loading = ref(false)
  const error = ref('')
  const filters = reactive({})
  const ordering = ref(initialOrdering)

  let requestId = 0 // ignore answers of outdated requests

  function queryParams() {
    const params = {}
    for (const [key, value] of Object.entries(filters)) {
      if (value !== '' && value !== null && value !== undefined) params[key] = value
    }
    if (ordering.value) params.ordering = ordering.value
    return params
  }

  async function fetchList() {
    const id = ++requestId
    loading.value = true
    try {
      const { data } = await api.get(`/${resource}/`, {
        params: { ...queryParams(), page: page.value, page_size: pageSize },
      })
      if (id !== requestId) return
      items.value = data.results
      count.value = data.count
      error.value = ''
    } catch (e) {
      if (e.response?.status === 404 && page.value > 1) {
        // the last page disappeared (e.g. after deleting its last row)
        page.value -= 1
        return fetchList()
      }
      error.value = formatError(e)
    } finally {
      if (id === requestId) loading.value = false
    }
  }

  async function fetchStats() {
    try {
      const { data } = await api.get(`/${resource}/stats/`, { params: queryParams() })
      stats.value = data
    } catch (e) {
      error.value = formatError(e)
    }
  }

  const reload = () => Promise.all([fetchList(), fetchStats()])

  // changing a filter goes back to page 1 and reloads the table and the statistics
  let timer
  watch(filters, () => {
    clearTimeout(timer)
    timer = setTimeout(() => {
      page.value = 1
      reload()
    }, 300)
  })
  onBeforeUnmount(() => clearTimeout(timer))

  function changePage(n) {
    page.value = n
    fetchList()
  }

  function sort(field) {
    ordering.value = ordering.value === field ? `-${field}` : field
    page.value = 1
    fetchList()
  }

  function clearFilters() {
    for (const key of Object.keys(filters)) filters[key] = ''
  }

  function buildBody(form) {
    const body = new FormData()
    for (const key of fields) {
      const value = form[key]
      if (fileFields.includes(key)) {
        if (value instanceof File) body.append(key, value)
      } else {
        body.append(key, value === null || value === undefined ? '' : value)
      }
    }
    return body
  }

  // creates (no id) or updates (id) a row; throws a readable Error on validation problems
  async function save(form, id = null) {
    const body = buildBody(form)
    try {
      if (id) await api.put(`/${resource}/${id}/`, body)
      else await api.post(`/${resource}/`, body)
    } catch (e) {
      throw new Error(formatError(e))
    }
    await reload()
  }

  async function remove(id) {
    try {
      await api.delete(`/${resource}/${id}/`)
    } catch (e) {
      error.value = formatError(e)
      return
    }
    await reload()
  }

  // the document is built by the backend (/export/ action); we only download it
  async function exportExcel() {
    try {
      const { data } = await api.get(`/${resource}/export/`, {
        params: queryParams(),
        responseType: 'blob',
      })
      const url = URL.createObjectURL(data)
      const link = document.createElement('a')
      link.href = url
      link.download = `${resource}.xlsx`
      link.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      error.value = formatError(e)
    }
  }

  return {
    items, count, page, pageSize, stats, loading, error, filters, ordering,
    fetchList, fetchStats, reload, changePage, sort, clearFilters, save, remove, exportExcel,
  }
}

/**
 * State of the "add / edit" modal window that belongs to a table.
 *   crud      – result of useCrud()
 *   emptyForm – function returning a blank form object
 */
export function useEditor(crud, emptyForm) {
  const showForm = ref(false)
  const editingId = ref(null)
  const form = ref(emptyForm())
  const formError = ref('')
  const saving = ref(false)

  function openAdd() {
    editingId.value = null
    form.value = emptyForm()
    formError.value = ''
    showForm.value = true
  }

  // copy the clicked row into the form (the row itself must not change until we save)
  function openEdit(item) {
    editingId.value = item.id
    form.value = { ...emptyForm(), ...item }
    formError.value = ''
    showForm.value = true
  }

  async function submit() {
    saving.value = true
    try {
      await crud.save(form.value, editingId.value)
      showForm.value = false
    } catch (e) {
      formError.value = e.message
    } finally {
      saving.value = false
    }
  }

  async function onRemove(item, what) {
    if (confirm(`Delete ${what}?`)) await crud.remove(item.id)
  }

  return { showForm, editingId, form, formError, saving, openAdd, openEdit, submit, onRemove }
}
