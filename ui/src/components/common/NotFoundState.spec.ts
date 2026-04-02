/**
 * Component tests for NotFoundState
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import NotFoundState from './NotFoundState.vue'
import EmptyState from './EmptyState.vue'

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'common.browseAll': 'Browse All',
        'common.returnHome': 'Return to Home'
      }
      return translations[key] || key
    }
  })
}))

// Mock vue-router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

describe('NotFoundState', () => {
  describe('Rendering', () => {
    it('renders EmptyState with error type inside v-col', () => {
      const wrapper = mount(NotFoundState, {
        props: {
          message: 'Item not found'
        }
      })

      const emptyState = wrapper.findComponent(EmptyState)
      expect(emptyState.exists()).toBe(true)
      expect(emptyState.props('message')).toBe('Item not found')
      expect(emptyState.props('type')).toBe('error')

      const col = wrapper.findComponent({ name: 'VCol' })
      expect(col.exists()).toBe(true)
      expect(col.props('cols')).toBe('12')
    })

    it.each([
      'Not found',
      'The requested item could not be found in the database. It may have been removed or the ID is incorrect.',
      'Book "Pride & Prejudice" not found'
    ])('handles different message format: %s', (message) => {
      const wrapper = mount(NotFoundState, {
        props: { message }
      })

      expect(wrapper.findComponent(EmptyState).props('message')).toBe(message)
    })
  })

  describe('Buttons - Without List Route', () => {
    it('renders only home button with correct properties', () => {
      const wrapper = mount(NotFoundState, {
        props: {
          message: 'Item not found'
        }
      })

      const buttons = wrapper.findAllComponents({ name: 'VBtn' })
      expect(buttons).toHaveLength(1)

      const homeButton = buttons[0]!
      expect(homeButton.text()).toBe('Return to Home')
      expect(homeButton.props('to')).toBe('/')
      expect(homeButton.props('variant')).toBe('outlined')
      expect(homeButton.props('color')).toBe('primary')
    })
  })

  describe('Buttons - With List Route', () => {
    it('renders both buttons when listRoute provided', () => {
      const wrapper = mount(NotFoundState, {
        props: {
          message: 'Book not found',
          listRoute: '/books'
        }
      })

      const buttons = wrapper.findAllComponents({ name: 'VBtn' })
      expect(buttons).toHaveLength(2)

      const listButton = buttons[0]!
      expect(listButton.text()).toBe('Browse All')
      expect(listButton.props('to')).toBe('/books')
      expect(listButton.props('variant')).toBe('elevated')
      expect(listButton.props('color')).toBe('primary')
      expect(listButton.classes()).toContain('mr-2')

      const homeButton = buttons[1]!
      expect(homeButton.text()).toBe('Return to Home')
      expect(homeButton.props('to')).toBe('/')
    })

    it('uses custom label when provided', () => {
      const wrapper = mount(NotFoundState, {
        props: {
          message: 'Book not found',
          listRoute: '/books',
          listLabel: 'View All Books'
        }
      })

      const buttons = wrapper.findAllComponents({ name: 'VBtn' })
      expect(buttons[0]!.text()).toBe('View All Books')
    })

    it.each(['/books', '/authors', '/lcc-shelves', '/books?sort=title'])(
      'handles list route: %s',
      (route) => {
        const wrapper = mount(NotFoundState, {
          props: {
            message: 'Not found',
            listRoute: route
          }
        })

        const buttons = wrapper.findAllComponents({ name: 'VBtn' })
        expect(buttons[0]!.props('to')).toBe(route)
      }
    )
  })

  describe('Layout', () => {
    it('has centered button container with top margin', () => {
      const wrapper = mount(NotFoundState, {
        props: {
          message: 'Item not found'
        }
      })

      const buttonContainer = wrapper.find('.text-center.mt-4')
      expect(buttonContainer.exists()).toBe(true)
    })
  })
})
