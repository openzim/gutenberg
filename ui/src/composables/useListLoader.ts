import { ref } from 'vue'

export function useListLoader<T, TData>(fetchFn: () => Promise<TData>, itemsKey: keyof TData) {
  const items = ref<T[]>([])
  const loading = ref(false)

  async function loadItems() {
    loading.value = true
    try {
      const data = await fetchFn()
      const value = data[itemsKey]
      if (!Array.isArray(value)) {
        items.value = []
        return
      }
      items.value = value as T[]
    } catch (error) {
      items.value = []
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    items,
    loading,
    loadItems
  }
}
