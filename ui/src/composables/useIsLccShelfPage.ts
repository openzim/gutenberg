import { computed } from 'vue'
import { useRoute } from 'vue-router'

export function useIsLccShelfPage() {
  const route = useRoute()
  return computed(() => route.path === '/lcc-shelves')
}
