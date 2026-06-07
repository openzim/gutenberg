/**
 * Unit tests for PaginationControl component
 * Tests pagination navigation control
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PaginationControl from './PaginationControl.vue'

const createWrapper = (props: { currentPage: number; totalPages: number }) =>
  mount(PaginationControl, {
    props,
    global: {
      mocks: {
        $t: (key: string) => key.split('.').pop()
      },
      stubs: {
        BasePaginationButton: {
          props: ['active', 'disabled'],
          template:
            '<button :disabled="disabled" :class="{ active }" @click="$emit(\'click\')"><slot /></button>'
        }
      }
    }
  })

describe('PaginationControl', () => {
  it.each([
    { currentPage: 1, totalPages: 0, shouldRender: false },
    { currentPage: 1, totalPages: 1, shouldRender: false },
    { currentPage: 1, totalPages: 2, shouldRender: true },
    { currentPage: 5, totalPages: 10, shouldRender: true }
  ])(
    'renders pagination when totalPages is $totalPages',
    ({ currentPage, totalPages, shouldRender }) => {
      const wrapper = createWrapper({ currentPage, totalPages })

      expect(wrapper.find('.pagination-control').exists()).toBe(shouldRender)
    }
  )

  it('highlights the active page button', () => {
    const wrapper = createWrapper({
      currentPage: 3,
      totalPages: 10
    })

    const buttons = wrapper.findAll('button')
    const activeButton = buttons.find((btn) => btn.classes('active'))

    expect(activeButton).toBeDefined()
    expect(activeButton!.text()).toBe('3')
  })

  it('emits go-to-page when a page button is clicked', async () => {
    const wrapper = createWrapper({
      currentPage: 1,
      totalPages: 5
    })

    const buttons = wrapper.findAll('button')
    const page3Button = buttons.find((btn) => btn.text() === '3')

    expect(page3Button).toBeDefined()
    await page3Button!.trigger('click')

    expect(wrapper.emitted('go-to-page')).toBeDefined()
    expect(wrapper.emitted('go-to-page')![0]).toEqual([3])
  })

  it('emits go-to-page with previous page when Previous is clicked', async () => {
    const wrapper = createWrapper({
      currentPage: 3,
      totalPages: 5
    })

    const buttons = wrapper.findAll('button')
    const prevButton = buttons[0]!

    expect(prevButton.text()).toContain('previous')
    await prevButton.trigger('click')

    expect(wrapper.emitted('go-to-page')).toBeDefined()
    expect(wrapper.emitted('go-to-page')![0]).toEqual([2])
  })

  it('emits go-to-page with next page when Next is clicked', async () => {
    const wrapper = createWrapper({
      currentPage: 3,
      totalPages: 5
    })

    const buttons = wrapper.findAll('button')
    const nextButton = buttons[buttons.length - 1]!

    expect(nextButton.text()).toContain('next')
    await nextButton.trigger('click')

    expect(wrapper.emitted('go-to-page')).toBeDefined()
    expect(wrapper.emitted('go-to-page')![0]).toEqual([4])
  })

  it('disables Previous button on first page', () => {
    const wrapper = createWrapper({
      currentPage: 1,
      totalPages: 5
    })

    const buttons = wrapper.findAll('button')
    expect(buttons[0]!.attributes('disabled')).toBeDefined()
  })

  it('disables Next button on last page', () => {
    const wrapper = createWrapper({
      currentPage: 5,
      totalPages: 5
    })

    const buttons = wrapper.findAll('button')
    expect(buttons[buttons.length - 1]!.attributes('disabled')).toBeDefined()
  })
})
