/**
 * Composable that provides formatting utilities with i18n support
 * This wraps the pure format-utils functions and injects the current locale
 */

import { useI18n } from 'vue-i18n'
import * as formatUtils from '@/utils/format-utils'

export function useFormatters() {
  const { locale } = useI18n()

  return {
    ...formatUtils,
    formatLanguages: (languages: string[]) =>
      formatUtils.formatLanguages(languages, { uiLocale: locale.value })
  }
}
