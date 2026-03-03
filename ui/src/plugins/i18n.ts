import type { PiniaPluginContext } from 'pinia'
import { createI18n, type ComposerTranslation } from 'vue-i18n'

const simplifiedBrowserLanguage =
  typeof navigator !== 'undefined' ? navigator.language?.split('-')[0] : undefined

export type Language = {
  code: string
  display: string
  rtl: boolean
}

const localesFiles = import.meta.glob('../../../locales/*.json')

export const supportedLanguages: Language[] = [
  { code: 'af', display: 'Afrikaans', rtl: false },
  { code: 'ar', display: 'العربية', rtl: true },
  { code: 'arp', display: 'Arapaho', rtl: false },
  { code: 'bg', display: 'Български', rtl: false },
  { code: 'bo', display: 'བོད་ཡིག', rtl: false },
  { code: 'br', display: 'Brezhoneg', rtl: false },
  { code: 'ca', display: 'Català', rtl: false },
  { code: 'ceb', display: 'Cebuano', rtl: false },
  { code: 'cs', display: 'Čeština', rtl: false },
  { code: 'cy', display: 'Cymraeg', rtl: false },
  { code: 'da', display: 'Dansk', rtl: false },
  { code: 'de', display: 'Deutsch', rtl: false },
  { code: 'el', display: 'Ελληνικά', rtl: false },
  { code: 'en', display: 'English', rtl: false },
  { code: 'enm', display: 'Middle English', rtl: false },
  { code: 'eo', display: 'Esperanto', rtl: false },
  { code: 'es', display: 'Español', rtl: false },
  { code: 'et', display: 'Eesti', rtl: false },
  { code: 'fa', display: 'فارسی', rtl: true },
  { code: 'fi', display: 'Suomi', rtl: false },
  { code: 'fr', display: 'Français', rtl: false },
  { code: 'fur', display: 'Furlan', rtl: false },
  { code: 'fy', display: 'Frysk', rtl: false },
  { code: 'ga', display: 'Gaeilge', rtl: false },
  { code: 'gd', display: 'Gàidhlig', rtl: false },
  { code: 'gl', display: 'Galego', rtl: false },
  { code: 'he', display: 'עברית', rtl: true },
  { code: 'hu', display: 'Magyar', rtl: false },
  { code: 'ia', display: 'Interlingua', rtl: false },
  { code: 'ilo', display: 'Ilokano', rtl: false },
  { code: 'it', display: 'Italiano', rtl: false },
  { code: 'iu', display: 'ᐃᓄᒃᑎᑐᑦ', rtl: false },
  { code: 'ja', display: '日本語', rtl: false },
  { code: 'ko', display: '한국어', rtl: false },
  { code: 'la', display: 'Latina', rtl: false },
  { code: 'lb', display: 'Lëtzebuergesch', rtl: false },
  { code: 'mi', display: 'Māori', rtl: false },
  { code: 'mk', display: 'македонски', rtl: false },
  { code: 'myn', display: 'Mayan', rtl: false },
  { code: 'nah', display: 'Nahuatl', rtl: false },
  { code: 'nap', display: 'Napulitano', rtl: false },
  { code: 'nl', display: 'Nederlands', rtl: false },
  { code: 'no', display: 'Norsk', rtl: false },
  { code: 'oc', display: 'Occitan', rtl: false },
  { code: 'oj', display: 'Ojibwe', rtl: false },
  { code: 'pl', display: 'Polski', rtl: false },
  { code: 'ps', display: 'پښتو', rtl: true },
  { code: 'pt', display: 'Português', rtl: false },
  { code: 'pt-br', display: 'Português do Brasil', rtl: false },
  { code: 'ro', display: 'Română', rtl: false },
  { code: 'ru', display: 'Русский', rtl: false },
  { code: 'sa', display: 'संस्कृतम्', rtl: false },
  { code: 'sl', display: 'Slovenščina', rtl: false },
  { code: 'sr', display: 'Српски', rtl: false },
  { code: 'sv', display: 'Svenska', rtl: false },
  { code: 'te', display: 'తెలుగు', rtl: false },
  { code: 'tl', display: 'Tagalog', rtl: false },
  { code: 'zh', display: '中文', rtl: false },
  { code: 'zh-hans', display: '简体中文', rtl: false },
  { code: 'zh-hant', display: '繁體中文', rtl: false }
]

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
