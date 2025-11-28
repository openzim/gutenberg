/**
 * TypeScript interfaces for Author-related data structures
 * Matches Pydantic schemas from scraper/src/gutenberg2zim/schemas.py
 */

import type { BookPreview } from './Book'

export interface AuthorPreview {
  id: string
  name: string
  bookCount: number
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

