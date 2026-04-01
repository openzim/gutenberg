/**
 * Unit tests for useMultiSelectFilter composable
 * Tests multi-select filter functionality for toggling, clearing, and selecting all items
 */

import { describe, it, expect, vi } from 'vitest'
import { useMultiSelectFilter } from './useMultiSelectFilter'

describe('useMultiSelectFilter', () => {
  const createFilter = <T>(modelValue: T[]) => {
    const emit = vi.fn()
    const props = { modelValue }
    return { ...useMultiSelectFilter(props, emit), emit }
  }

  describe('toggle', () => {
    it('adds item when not selected', () => {
      const { toggle, emit } = createFilter(['a', 'b'])

      toggle('c')

      expect(emit).toHaveBeenCalledWith('update:modelValue', ['a', 'b', 'c'])
    })

    it('removes item when already selected', () => {
      const { toggle, emit } = createFilter(['a', 'b', 'c'])

      toggle('b')

      expect(emit).toHaveBeenCalledWith('update:modelValue', ['a', 'c'])
    })

    it('handles empty initial selection', () => {
      const { toggle, emit } = createFilter<string>([])

      toggle('first')

      expect(emit).toHaveBeenCalledWith('update:modelValue', ['first'])
    })

    it('does not mutate original array', () => {
      const original = ['a', 'b']
      const emit = vi.fn()
      const { toggle } = useMultiSelectFilter({ modelValue: original }, emit)

      toggle('c')

      expect(original).toEqual(['a', 'b'])
    })
  })

  it('clears all selections', () => {
    const { clearAll, emit } = createFilter(['a', 'b', 'c'])

    clearAll()

    expect(emit).toHaveBeenCalledWith('update:modelValue', [])
  })

  it('selects all items', () => {
    const { selectAll, emit } = createFilter(['a'])

    selectAll(['a', 'b', 'c', 'd'])

    expect(emit).toHaveBeenCalledWith('update:modelValue', ['a', 'b', 'c', 'd'])
  })

  it('works with different data types', () => {
    const { toggle, emit } = createFilter([1, 2, 3])

    toggle(2)

    expect(emit).toHaveBeenCalledWith('update:modelValue', [1, 3])
  })
})
