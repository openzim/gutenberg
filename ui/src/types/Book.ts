/**
 * TypeScript interfaces for Book-related data structures
 * Matches the scraper's source-neutral JSON schemas.
 */

import type { AuthorPreview, Author } from './Author'

export interface BookFormat {
  format: string // "html", "epub", "pdf"
  path: string // ZIM path to file
  available: boolean
}

export interface BookPreview {
  id: string
  title: string
  author: AuthorPreview
  languages: string[]
  popularity: number // Flame rating (0-3)
  coverPath: string | null
  primaryCollection: string | null
  availableFormats?: string[]
  description?: string | null
}

export interface Book extends Omit<BookPreview, 'author'> {
  subtitle: string | null
  author: Author // Full author instead of preview
  license: string
  primaryMetric: number
  formats: BookFormat[]
  description: string | null
}

export interface Books {
  books: BookPreview[]
  totalCount: number
}
