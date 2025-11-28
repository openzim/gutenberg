import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import axios from 'axios'
import { createVuetify, type ThemeDefinition } from 'vuetify'
import type { Config } from '@/types/Config'
import { THEME_COLORS } from '@/constants/theme'

async function loadVuetify() {
  let primaryColor: string = THEME_COLORS.PRIMARY
  let secondaryColor: string = THEME_COLORS.SECONDARY

  try {
    const response = await axios.get<Config>('./config.json')
    primaryColor = response.data.mainColor || primaryColor
    secondaryColor = response.data.secondaryColor || secondaryColor
  } catch {}

  const sharedColors = {
    primary: primaryColor,
    secondary: secondaryColor,
    accent: THEME_COLORS.ACCENT,
    error: THEME_COLORS.ERROR,
    info: THEME_COLORS.INFO,
    success: THEME_COLORS.SUCCESS,
    warning: THEME_COLORS.WARNING
  }

  const lightTheme: ThemeDefinition = {
    dark: false,
    colors: {
      background: THEME_COLORS.BACKGROUND_LIGHT,
      surface: THEME_COLORS.SURFACE_LIGHT,
      ...sharedColors
    }
  }

  const darkTheme: ThemeDefinition = {
    dark: true,
    colors: {
      background: THEME_COLORS.BACKGROUND_DARK,
      surface: THEME_COLORS.SURFACE_DARK,
      ...sharedColors
    }
  }

  return createVuetify({
    theme: {
      defaultTheme: 'light',
      variations: {
        colors: ['primary', 'secondary'],
        lighten: 3,
        darken: 3
      },
      themes: {
        light: lightTheme,
        dark: darkTheme
      }
    },
    display: {
      mobileBreakpoint: 'sm',
      thresholds: {
        xs: 0,
        sm: 600,
        md: 960,
        lg: 1280,
        xl: 1920
      }
    },
    defaults: {
      VBtn: {
        elevation: 2,
        variant: 'elevated'
      },
      VCard: {
        elevation: 2,
        variant: 'elevated'
      }
    }
  })
}

export default loadVuetify
