import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useMainStore = defineStore('main', () => {
  const errorMessage = ref<string | null>(null)

  function setError(message: string | null) {
    errorMessage.value = message
  }

  return {
    errorMessage,
    setError
  }
})

