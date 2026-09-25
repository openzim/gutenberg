/**
 * TypeScript interfaces for Author-related data structures
 * Matches the scraper's source-neutral JSON schemas.
 */

import type { BookPreview } from './Book'

export interface AuthorPreview {
  id: string
  name: string
  firstName: string | null
  lastName: string
  bookCount: number
  totalPopularity?: number
  portraitPath?: string | null
}

export interface Author extends AuthorPreview {
  birthYear: string | null
  deathYear: string | null
  name: string
  bio?: string | null
  portraitPath?: string | null
  webpageResource?: string | null
}

export interface AuthorDetail extends Author {
  books: BookPreview[]
}

export interface Authors {
  authors: AuthorPreview[]
  totalCount: number
}
