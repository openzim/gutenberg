/**
 * TypeScript interfaces for Book-related data structures
 * Matches Pydantic schemas from scraper/src/gutenberg2zim/schemas.py
 */

import type { AuthorPreview, Author } from './Author'

export interface BookFormat {
  format: string // "html", "epub", "pdf"
  path: string // ZIM path to file
  available: boolean
}

export interface BookPreview {
  id: number
  title: string
  author: AuthorPreview
  languages: string[]
  popularity: number // Star rating (0-5)
  coverPath: string | null
  lccShelf: string | null
}

export interface Book extends Omit<BookPreview, 'author'> {
  subtitle: string | null
  author: Author // Full author instead of preview
  license: string
  downloads: number
  formats: BookFormat[]
  description: string | null
}

export interface Books {
  books: BookPreview[]
  totalCount: number
}

