/**
 * TypeScript interfaces for LCC Shelf-related data structures
 * Matches Pydantic schemas from scraper/src/gutenberg2zim/schemas.py
 */

import type { BookPreview } from './Book'

export interface LCCShelfPreview {
  code: string
  name: string | null
  bookCount: number
}

export interface LCCShelf extends LCCShelfPreview {
  books: BookPreview[]
}

export interface LCCShelves {
  shelves: LCCShelfPreview[]
  totalCount: number
}
