import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'

export function useDetailView<T>(
  fetchFn: (id: string | number) => Promise<T>,
  paramName: string = 'id',
  parseParam?: (value: string) => string | number
) {
  const route = useRoute()
  const data = ref<T | null>(null)
  const notFound = ref(false)
  const loading = ref(false)
  let isMounted = false

  function getTitle(item: T): string {
    if (typeof item === 'object' && item !== null) {
      const obj = item as Record<string, unknown>
      if ('title' in obj) return String(obj.title)
      if ('name' in obj) return String(obj.name)
    }
    return 'Details'
  }

  function loadData() {
    const param = route.params[paramName]
    const paramValue = Array.isArray(param) ? param[0] : param
    
    if (!paramValue) {
      notFound.value = true
      return
    }

    let id: string | number
    try {
      id = parseParam 
        ? parseParam(paramValue as string)
        : (paramValue as string)
    } catch {
      notFound.value = true
      return
    }
    
    if (!id) {
      notFound.value = true
      return
    }

    loading.value = true
    fetchFn(id)
      .then(result => {
        if (!isMounted) return
        data.value = result
        if (route.meta.title) {
          document.title = `${getTitle(result)} - Gutenberg Library`
        }
      })
      .catch((error) => {
        if (!isMounted) return
        notFound.value = true
        console.error(`Failed to load detail for ${paramName}:`, error)
      })
      .finally(() => {
        if (isMounted) {
          loading.value = false
        }
      })
  }

  watch(() => route.params[paramName], () => {
    loadData()
  })

  onMounted(() => {
    isMounted = true
    loadData()
  })

  onBeforeUnmount(() => {
    isMounted = false
  })

  return {
    data,
    notFound,
    loading
  }
}

