import { onMounted, onUnmounted } from 'vue'
import { useTheme as useVuetifyTheme } from 'vuetify'

export function useTheme() {
  const theme = useVuetifyTheme()
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

  function applySystemTheme() {
    theme.global.name.value = mediaQuery.matches ? 'dark' : 'light'
  }

  function handleThemeChange(e: MediaQueryListEvent) {
    theme.global.name.value = e.matches ? 'dark' : 'light'
  }

  onMounted(() => {
    applySystemTheme()
    mediaQuery.addEventListener('change', handleThemeChange)
  })

  onUnmounted(() => {
    mediaQuery.removeEventListener('change', handleThemeChange)
  })

  return {
    theme,
    applySystemTheme
  }
}
