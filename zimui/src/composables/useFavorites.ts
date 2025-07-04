import { ref } from 'vue'

const favorites = ref<Set<number>>(new Set())

export function useFavorites() {
  const isFavorite = (id: number) => favorites.value.has(id)
  const toggleFavorite = (id: number) => {
    if (favorites.value.has(id)) {
      favorites.value.delete(id)
    } else {
      favorites.value.add(id)
    }
  }

  return {
    favorites,
    isFavorite,
    toggleFavorite
  }
}
