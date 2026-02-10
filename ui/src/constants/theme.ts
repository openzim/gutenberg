export const THEME_COLORS = {
  PRIMARY: '#1976D2',
  SECONDARY: '#424242',
  SURFACE_LIGHT: '#FAFAFA',
  SURFACE_DARK: '#1E1E1E',
  BACKGROUND_LIGHT: '#FFFFFF',
  BACKGROUND_DARK: '#121212',
  ACCENT: '#82B1FF',
  ERROR: '#D32F2F',
  INFO: '#1976D2',
  SUCCESS: '#388E3C',
  WARNING: '#F57C00',
  ON_PRIMARY: '#FFFFFF'
} as const

export const LAYOUT = {
  MAX_CONTENT_WIDTH: '1200px',
  HEADER_HEIGHT: '64px',
  FOOTER_HEIGHT: '136px',
  VIEW_PADDING: '2rem 0',
  VIEW_PADDING_MOBILE: '1.5rem 0',
  SIDEBAR_MARGIN_MOBILE: '1rem',
  CARD_SPACING: 'mb-6',
  CARD_PADDING: 'pa-4',
  SECTION_SPACING: 'mb-8',
  GRID_GAP: 'gap-4'
} as const

export const AVATAR_SIZES = {
  CARD: 80,
  DETAIL: 120,
  DETAIL_MOBILE: 80,
  LIST: 56
} as const

export const ICON_SIZES = {
  CARD: 48,
  DETAIL: 48,
  DETAIL_MOBILE: 40,
  LIST: 32,
  STAT: 48,
  SMALL: 20
} as const

export const MESSAGES = {
  NO_BOOKS: 'No books found.',
  NO_AUTHORS: 'No authors found.',
  NO_SHELVES: 'No LCC shelves found.',
  NO_BOOKS_FOR_AUTHOR: 'No books available for this author.',
  NO_BOOKS_IN_SHELF: 'No books available in this shelf.',
  NO_LANGUAGES: 'No languages available.',
  NO_FORMATS: 'No formats available.',
  NOT_FOUND_BOOK: "Book not found. The book you're looking for doesn't exist or has been removed.",
  NOT_FOUND_AUTHOR:
    "Author not found. The author you're looking for doesn't exist or has been removed.",
  NOT_FOUND_SHELF:
    "LCC shelf not found. The shelf you're looking for doesn't exist or has been removed."
} as const
