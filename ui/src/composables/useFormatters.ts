/**
 * Composable that provides formatting utilities with i18n support
 * This wraps the pure format-utils functions and injects i18n context
 */

import { useI18n } from 'vue-i18n'
import * as formatUtils from '@/utils/format-utils'

export function useFormatters() {
  const { t, te } = useI18n()

  return {
    ...formatUtils,
    // Override formatLanguages to inject i18n
    formatLanguages: (languages: string[]) => formatUtils.formatLanguages(languages, { t, te })
  }
}
