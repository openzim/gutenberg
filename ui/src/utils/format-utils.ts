import { getLanguageName } from '@/utils/language-names'

export function formatAuthorLifespan(birthYear: string | null, deathYear: string | null): string {
  if (birthYear && deathYear) {
    return `${birthYear} - ${deathYear}`
  }
  if (birthYear) {
    return `${birthYear} -`
  }
  if (deathYear) {
    return `- ${deathYear}`
  }
  return ''
}

export function compareAuthorNames(a: string, b: string): number {
  const lastName = (name: string) => name.trim().split(/\s+/).pop() ?? name
  return lastName(a).localeCompare(lastName(b)) || a.localeCompare(b)
}

export function formatLabel(format: string): string {
  return format === 'epub' ? 'ePUB' : format.toUpperCase()
}

export function formatMetric(value: number): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`
  }
  return value.toString()
}

export function formatLanguages(languages: string[], options?: { uiLocale?: string }): string {
  const locale = options?.uiLocale || 'en'

  return languages.map((code) => getLanguageName(code, locale)).join(', ')
}

export function pluralize(count: number, singular: string, plural?: string): string {
  return count === 1 ? singular : plural || `${singular}s`
}

export function extractUniqueValues<T>(items: T[], getter: (item: T) => string[]): string[] {
  const values = new Set<string>()
  items.forEach((item) => {
    getter(item).forEach((value) => values.add(value))
  })
  return Array.from(values).sort()
}

export function normalizeImagePath(path: string): string {
  return normalizeZimPath(path)
}

/** Make an archive-relative ZIM path unambiguously relative to the app. */
export function normalizeZimPath(path: string): string {
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(path) || /^(?:blob|data|mailto|tel):/i.test(path)) {
    return path
  }
  if (path.startsWith('/')) return path
  return path.startsWith('./') ? path : `./${path}`
}
