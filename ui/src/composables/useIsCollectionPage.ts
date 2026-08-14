import { computed } from 'vue'
import { useRoute } from 'vue-router'

export function useIsCollectionPage() {
  const route = useRoute()
  return computed(() => route.path === '/collections')
}
