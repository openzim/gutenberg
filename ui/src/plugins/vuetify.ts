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
    primaryColor = response.data.primaryColor || primaryColor
    secondaryColor = response.data.secondaryColor || secondaryColor
  } catch (error) {
    console.warn('Failed to load config.json for theme colors, using defaults.', error)
  }

  const sharedColors = {
    primary: primaryColor,
    secondary: secondaryColor,
    accent: THEME_COLORS.ACCENT,
    error: THEME_COLORS.ERROR,
    info: THEME_COLORS.INFO,
    success: THEME_COLORS.SUCCESS,
    warning: THEME_COLORS.WARNING,
    format: THEME_COLORS.FORMAT,
    star: THEME_COLORS.STAR,
    title: THEME_COLORS.TITLE,
    author: THEME_COLORS.AUTHOR,
    authorFocus: THEME_COLORS.AUTHOR_FOCUS,
    description: THEME_COLORS.DESCRIPTION,
    focusBook: THEME_COLORS.FOCUS_BOOK,
    menuActive: THEME_COLORS.MENU_ACTIVE,
    bgd1: THEME_COLORS.BGD_1,
    bgd2: THEME_COLORS.BGD_2,
    bgd3Fill: THEME_COLORS.BGD_3_FILL,
    bgd3Outline: THEME_COLORS.BGD_3_OUTLINE,
    text: THEME_COLORS.TEXT,
    grid: THEME_COLORS.GRID
  }

  const lightColors = {
    ...sharedColors,
    grid: THEME_COLORS.GRID,
    text: THEME_COLORS.TEXT,
    bgd3Fill: THEME_COLORS.BGD_3_FILL,
    bgd3Outline: THEME_COLORS.BGD_3_OUTLINE
  }

  const darkColors = {
    ...sharedColors,
    grid: THEME_COLORS.GRID_DARK,
    text: THEME_COLORS.TEXT_DARK,
    bgd3Fill: THEME_COLORS.BGD_3_FILL_DARK,
    bgd3Outline: THEME_COLORS.BGD_3_OUTLINE_DARK
  }

  const lightTheme: ThemeDefinition = {
    dark: false,
    colors: {
      background: THEME_COLORS.BACKGROUND_LIGHT,
      surface: THEME_COLORS.SURFACE_LIGHT,
      ...lightColors
    }
  }

  const darkTheme: ThemeDefinition = {
    dark: true,
    colors: {
      background: THEME_COLORS.BACKGROUND_DARK,
      surface: THEME_COLORS.SURFACE_DARK,
      ...darkColors
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
