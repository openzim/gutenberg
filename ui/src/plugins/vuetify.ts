import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import axios from 'axios'
import { createVuetify, type ThemeDefinition } from 'vuetify'
import type { Config } from '@/types/Config'
import { THEME_COLORS } from '@/constants/theme'

async function loadVuetify() {
  const PRIMARY = '#1976D2'
  const SECONDARY = '#424242'
  const ACCENT = '#82B1FF'
  const ERROR = '#D32F2F'
  const INFO = '#1976D2'
  const SUCCESS = '#388E3C'
  const WARNING = '#F57C00'
  const BACKGROUND_LIGHT = '#FFFFFF'
  const BACKGROUND_DARK = '#121212'
  const SURFACE_LIGHT = '#FAFAFA'
  const SURFACE_DARK = '#1E1E1E'

  let primaryColor: string = PRIMARY
  let secondaryColor: string = SECONDARY

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
    accent: ACCENT,
    error: ERROR,
    info: INFO,
    success: SUCCESS,
    warning: WARNING,
    format: THEME_COLORS.FORMAT,
    star: THEME_COLORS.STAR,
    title: THEME_COLORS.TITLE,
    author: THEME_COLORS.AUTHOR,
    authorFocus: THEME_COLORS.AUTHOR_FOCUS,
    description: THEME_COLORS.DESCRIPTION,
    focusBook: THEME_COLORS.FOCUS_BOOK,
    menuActive: THEME_COLORS.MENU_ACTIVE,
    shelfIcon: THEME_COLORS.SHELF_ICON,
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
    bgd1: THEME_COLORS.BGD_1_DARK,
    bgd2: THEME_COLORS.BGD_2_DARK,
    bgd3Fill: THEME_COLORS.BGD_3_FILL_DARK,
    bgd3Outline: THEME_COLORS.BGD_3_OUTLINE_DARK,
    focusBook: THEME_COLORS.FOCUS_BOOK_DARK,
    shelfIcon: THEME_COLORS.SHELF_ICON_DARK
  }

  const lightTheme: ThemeDefinition = {
    dark: false,
    colors: {
      background: BACKGROUND_LIGHT,
      surface: SURFACE_LIGHT,
      ...lightColors
    }
  }

  const darkTheme: ThemeDefinition = {
    dark: true,
    colors: {
      background: BACKGROUND_DARK,
      surface: SURFACE_DARK,
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
