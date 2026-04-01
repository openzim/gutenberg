/**
 * Unit tests for useSearchFilter composable
 * Tests search/filter functionality for filtering items based on text query
 */

import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useSearchFilter } from './useSearchFilter'

interface TestBook {
  title: string
  author: string
  tags: string[]
}

const SAMPLE_BOOKS: TestBook[] = [
  { title: 'Pride and Prejudice', author: 'Jane Austen', tags: ['classic', 'romance'] },
  { title: 'Great Expectations', author: 'Charles Dickens', tags: ['classic', 'drama'] },
  { title: '1984', author: 'George Orwell', tags: ['dystopian', 'political'] }
]

describe('useSearchFilter', () => {
  const createFilter = (searchFields: (item: TestBook) => string[]) => {
    const items = ref([...SAMPLE_BOOKS])
    return { items, ...useSearchFilter(() => items.value, searchFields) }
  }

  it('returns all items when search query is empty', () => {
    const { filteredItems } = createFilter((item) => [item.title])

    expect(filteredItems.value).toEqual(SAMPLE_BOOKS)
  })

  it('filters items by searchable fields', () => {
    const { filteredItems, searchQuery } = createFilter((item) => [item.title, item.author])

    searchQuery.value = 'pride'
    expect(filteredItems.value).toHaveLength(1)
    expect(filteredItems.value[0]!.title).toBe('Pride and Prejudice')

    searchQuery.value = 'dickens'
    expect(filteredItems.value).toHaveLength(1)
    expect(filteredItems.value[0]!.author).toBe('Charles Dickens')
  })

  it('is case-insensitive', () => {
    const { filteredItems, searchQuery } = createFilter((item) => [item.author])

    searchQuery.value = 'ORWELL'

    expect(filteredItems.value).toHaveLength(1)
    expect(filteredItems.value[0]!.author).toBe('George Orwell')
  })

  it('trims whitespace from query', () => {
    const { filteredItems, searchQuery } = createFilter((item) => [item.title])

    searchQuery.value = '  1984  '

    expect(filteredItems.value).toHaveLength(1)
    expect(filteredItems.value[0]!.title).toBe('1984')
  })

  it('returns empty array when no matches found', () => {
    const { filteredItems, searchQuery } = createFilter((item) => [item.title])

    searchQuery.value = 'nonexistent'

    expect(filteredItems.value).toEqual([])
  })

  it('searches across multiple fields including arrays', () => {
    const { filteredItems, searchQuery } = createFilter((item) => [
      item.title,
      item.author,
      ...item.tags
    ])

    searchQuery.value = 'classic'

    expect(filteredItems.value).toHaveLength(2)
  })

  it('handles partial matches', () => {
    const { filteredItems, searchQuery } = createFilter((item) => [item.title])

    searchQuery.value = 'exp'

    expect(filteredItems.value).toHaveLength(1)
    expect(filteredItems.value[0]!.title).toBe('Great Expectations')
  })

  it('reacts to changes in the source items', () => {
    const { items, filteredItems, searchQuery } = createFilter((item) => [item.title])

    searchQuery.value = 'pride'
    expect(filteredItems.value).toHaveLength(1)

    items.value = [...items.value, { title: 'Pride of Lions', author: 'Test Author', tags: [] }]
    expect(filteredItems.value).toHaveLength(2)
  })

  it('handles empty items array', () => {
    const items = ref<TestBook[]>([])
    const { filteredItems, searchQuery } = useSearchFilter(
      () => items.value,
      (item) => [item.title]
    )

    searchQuery.value = 'test'

    expect(filteredItems.value).toEqual([])
  })
})
