import { ref, onMounted, onUnmounted } from 'vue'

export function useIntersectionObserver(
  onIntersect: () => void,
  options?: IntersectionObserverInit
) {
  const sentinelRef = ref<HTMLElement | null>(null)
  let observer: IntersectionObserver | null = null

  function setupObserver() {
    observer?.disconnect()

    observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          onIntersect()
        }
      },
      { rootMargin: '100px', ...options }
    )

    if (sentinelRef.value) {
      observer.observe(sentinelRef.value)
    }
  }

  onMounted(setupObserver)

  onUnmounted(() => {
    observer?.disconnect()
  })

  return {
    sentinelRef,
    setupObserver
  }
}
