import type { BookPreview } from './Book'

export interface CollectionPreview {
  id: string
  name: string
  bookCount: number
  totalPopularity?: number
}

export interface Collection extends CollectionPreview {
  books: BookPreview[]
}

export interface Collections {
  collections: CollectionPreview[]
  totalCount: number
}
