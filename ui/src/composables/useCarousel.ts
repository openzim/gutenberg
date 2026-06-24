import { ref, computed } from 'vue'

export function useCarousel<T>(items: () => T[], cardsPerView: number = 5) {
  const offset = ref(0)

  const visibleItems = computed(() => {
    const start = offset.value
    const end = start + cardsPerView
    return items().slice(start, end)
  })

  const hasPrevious = computed(() => offset.value > 0)
  const hasNext = computed(() => offset.value + cardsPerView < items().length)

  function shiftLeft() {
    if (offset.value > 0) {
      offset.value--
    }
  }

  function shiftRight() {
    if (offset.value + cardsPerView < items().length) {
      offset.value++
    }
  }

  function reset() {
    offset.value = 0
  }

  return {
    offset,
    visibleItems,
    hasPrevious,
    hasNext,
    shiftLeft,
    shiftRight,
    reset
  }
}
