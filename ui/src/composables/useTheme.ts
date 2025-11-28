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

  function watchSystemTheme() {
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleThemeChange)
    } else if (mediaQuery.addListener) {
      mediaQuery.addListener(handleThemeChange)
    }
  }

  function unwatchSystemTheme() {
    if (mediaQuery.removeEventListener) {
      mediaQuery.removeEventListener('change', handleThemeChange)
    } else if (mediaQuery.removeListener) {
      mediaQuery.removeListener(handleThemeChange)
    }
  }

  onMounted(() => {
    applySystemTheme()
    watchSystemTheme()
  })

  onUnmounted(() => {
    unwatchSystemTheme()
  })

  return {
    theme,
    applySystemTheme
  }
}
