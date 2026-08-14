/**
 * TypeScript interfaces for Author-related data structures
 * Matches the scraper's source-neutral JSON schemas.
 */

import type { BookPreview } from './Book'

export interface AuthorPreview {
  id: string
  name: string
  bookCount: number
  totalPopularity?: number
}

export interface Author {
  id: string
  firstName: string | null
  lastName: string
  birthYear: string | null
  deathYear: string | null
  name: string
}

export interface AuthorDetail extends Author {
  bookCount: number
  books: BookPreview[]
}

export interface Authors {
  authors: AuthorPreview[]
  totalCount: number
}
