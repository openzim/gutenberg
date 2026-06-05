import type { PiniaPluginContext } from 'pinia'
import { createI18n, type ComposerTranslation } from 'vue-i18n'
import languageData from '@wikimedia/language-data'

const simplifiedBrowserLanguage =
  typeof navigator !== 'undefined' ? navigator.language?.split('-')[0] : undefined

export type Language = {
  code: string
  display: string
  rtl: boolean
}

const localesFiles = import.meta.glob('../../../locales/*.json')

// Overrides for codes not in @wikimedia/language-data or where the autonym
// differs significantly from what we want to display
const AUTONYM_OVERRIDES: Record<string, string> = {
  arp: 'Arapaho',
  enm: 'Middle English'
}

function getLocaleCodesFromFiles(): string[] {
  return Object.keys(localesFiles)
    .map((path) => {
      const match = path.match(/\/([^/]+)\.json$/)
      return match ? match[1] : null
    })
    .filter((code): code is string => code !== null && code !== 'qqq')
}

function buildSupportedLanguages(): Language[] {
  return getLocaleCodesFromFiles().map((code) => {
    const override = AUTONYM_OVERRIDES[code]
    const autonym = override || languageData.getAutonym(code)
    return {
      code,
      display: autonym && autonym !== code ? autonym : code,
      rtl: languageData.isRtl(code)
    }
  })
}

export const supportedLanguages: Language[] = buildSupportedLanguages()

const defaultLanguage: Language =
  supportedLanguages.find((lang) => lang.code === simplifiedBrowserLanguage) ||
  supportedLanguages.find((lang) => lang.code === 'en')!

const i18n = createI18n({
  legacy: false,
  locale: defaultLanguage.code,
  fallbackLocale: 'en',
  missingWarn: false,
  fallbackWarn: false,
  warnHtmlMessage: true
})

const loadedLocales: string[] = []

export async function setCurrentLocale(locale: Language): Promise<boolean> {
  if (!loadedLocales.includes(locale.code)) {
    const localeKey = `../../../locales/${locale.code}.json`
    const localeLoader = localesFiles[localeKey]
    if (!localeLoader) {
      console.error(`Locale file not found for ${locale.code}`)
      return false
    }
    const localeModule = (await localeLoader()) as
      | { default?: Record<string, unknown> }
      | Record<string, unknown>
    const localeMessages = (
      'default' in localeModule ? localeModule.default : localeModule
    ) as Record<string, unknown>
    i18n.global.setLocaleMessage(locale.code, localeMessages)
    loadedLocales.push(locale.code)
  }
  i18n.global.locale.value = locale.code
  document.documentElement.setAttribute('dir', locale.rtl ? 'rtl' : 'ltr')
  document.documentElement.setAttribute('lang', locale.code)
  localStorage.setItem('ui-locale', locale.code)
  return true
}

export function getCurrentLocale() {
  return i18n.global.locale.value
}

function getInitialLanguage(): Language {
  const storedLocale =
    typeof localStorage !== 'undefined' ? localStorage.getItem('ui-locale') : null
  if (storedLocale) {
    const storedLanguage = supportedLanguages.find((lang) => lang.code === storedLocale)
    if (storedLanguage) return storedLanguage
  }
  return defaultLanguage
}

async function loadI18n() {
  const enLocaleKey = '../../../locales/en.json'
  const enLocaleLoader = localesFiles[enLocaleKey]
  if (enLocaleLoader) {
    const enLocaleModule = (await enLocaleLoader()) as
      | { default?: Record<string, unknown> }
      | Record<string, unknown>
    const enLocaleMessages = (
      'default' in enLocaleModule ? enLocaleModule.default : enLocaleModule
    ) as Record<string, unknown>
    i18n.global.setLocaleMessage('en', enLocaleMessages)
    loadedLocales.push('en')
  }

  const initialLanguage = getInitialLanguage()
  if (initialLanguage.code !== 'en') {
    await setCurrentLocale(initialLanguage)
  } else {
    i18n.global.locale.value = 'en'
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('lang', 'en')
      document.documentElement.setAttribute('dir', 'ltr')
    }
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('ui-locale', 'en')
    }
  }

  return i18n
}

declare module 'pinia' {
  export interface PiniaCustomProperties {
    t: ComposerTranslation
  }
}

export function i18nPlugin({ store }: PiniaPluginContext) {
  store.t = i18n.global.t
}

export default loadI18n
