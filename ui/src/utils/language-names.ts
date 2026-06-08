import languageData from '@wikimedia/language-data'
import cldrNames from '@/generated/language-names.json'

// Codes not covered by either CLDR or @wikimedia/language-data
const FALLBACK_NAMES: Record<string, string> = {
  bgs: 'Tagbanwa',
  kld: 'Gamilaraay',
  myn: 'Mayan',
  nai: 'North American Indian',
  rmq: 'Caló'
}

const typedCldrNames = cldrNames as Record<string, Record<string, string>>

/**
 * Get the translated name of a language in the given UI locale.
 * Falls back to autonym, then to the raw code.
 */
export function getLanguageName(code: string, uiLocale: string): string {
  // Try CLDR translated name in the current UI locale
  const localeNames = typedCldrNames[uiLocale]
  if (localeNames?.[code]) {
    return localeNames[code]
  }

  // Try English CLDR as fallback
  const enNames = typedCldrNames['en']
  if (enNames?.[code]) {
    return enNames[code]
  }

  // Try hardcoded fallbacks
  const fallback = FALLBACK_NAMES[code.toLowerCase()]
  if (fallback) {
    return fallback
  }

  // Try @wikimedia/language-data autonym
  const autonym = languageData.getAutonym(code)
  if (autonym && autonym !== code) {
    return autonym
  }

  return code
}

/**
 * Get the autonym (native name) of a language.
 */
export function getAutonym(code: string): string {
  const autonym = languageData.getAutonym(code)
  if (autonym && autonym !== code) {
    return autonym
  }
  return FALLBACK_NAMES[code.toLowerCase()] || code
}

/**
 * Check if a language is RTL.
 */
export function isRtl(code: string): boolean {
  return languageData.isRtl(code)
}

/**
 * Check if a language code is known.
 */
export function isKnown(code: string): boolean {
  return (
    languageData.isKnown(code) ||
    code.toLowerCase() in FALLBACK_NAMES ||
    !!typedCldrNames['en']?.[code]
  )
}
