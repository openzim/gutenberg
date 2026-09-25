import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createMemoryHistory, createRouter } from 'vue-router'

import SelectedAuthorsCarousel from './SelectedAuthorsCarousel.vue'
import { normalizeImagePath } from '@/utils/format-utils'
import type { AuthorPreview } from '@/types'

const author = (overrides: Partial<AuthorPreview>): AuthorPreview => ({
  id: 'austen-jane',
  name: 'Jane Austen',
  firstName: 'Jane',
  lastName: 'Austen',
  bookCount: 42,
  ...overrides
})

const mountCarousel = (authors: AuthorPreview[]) => {
  const i18n = createI18n({
    legacy: false,
    locale: 'en',
    messages: {
      en: {
        home: { selectedAuthors: 'Selected authors', allAuthors: 'All authors' },
        author: { bookCount: (count: number) => (count === 1 ? '1 book' : `${count} books`) }
      },
      qq: {}
    }
  })
  const router = createRouter({
    history: createMemoryHistory(),
    routes: []
  })

  return mount(SelectedAuthorsCarousel, {
    props: { authors },
    global: { plugins: [i18n, router] }
  })
}

describe('SelectedAuthorsCarousel', () => {
  it('renders a portrait in a circular avatar when portraitPath is available', () => {
    const wrapper = mountCarousel([author({ id: 'a', portraitPath: './authors/austen-jane.webp' })])

    const avatar = wrapper.findComponent({ name: 'VAvatar' })
    expect(avatar.exists()).toBe(true)
    expect(avatar.classes()).toContain('selected-author-card__avatar')

    const portrait = avatar.findComponent({ name: 'VImg' })
    expect(portrait.exists()).toBe(true)
    expect(portrait.props('src')).toBe(normalizeImagePath('./authors/austen-jane.webp'))
    expect(portrait.props('cover')).toBe(true)
  })

  it('renders an account icon avatar when no portrait is available', () => {
    const wrapper = mountCarousel([author({ id: 'b' })])

    const avatar = wrapper.findComponent({ name: 'VAvatar' })
    expect(avatar.exists()).toBe(true)
    const portrait = avatar.findComponent({ name: 'VImg' })
    expect(portrait.exists()).toBe(false)
    expect(avatar.findComponent({ name: 'VIcon' }).props('icon')).toBe('mdi-account')
  })

  it('falls back to an account icon placeholder when a portrait fails to load', async () => {
    const wrapper = mountCarousel([
      author({ id: 'a', portraitPath: './authors/austen-jane.webp' }),
      author({ id: 'b', portraitPath: './authors/dickens.webp' })
    ])

    const avatars = wrapper.findAllComponents({ name: 'VAvatar' })
    expect(avatars).toHaveLength(2)
    expect(avatars[0].findComponent({ name: 'VImg' }).exists()).toBe(true)

    await avatars[0].find('img').trigger('error')
    await nextTick()

    expect(avatars[0].findComponent({ name: 'VImg' }).exists()).toBe(false)
    expect(avatars[0].findComponent({ name: 'VIcon' }).props('icon')).toBe('mdi-account')
    expect(avatars[1].findComponent({ name: 'VImg' }).exists()).toBe(true)
  })
})
