# Gutenberg Project Architecture

> **Note:** This document provides architectural context and design decisions for the Gutenberg scraper and Vue.js UI. While the implementation may have evolved, the core concepts remain relevant for understanding the system.

## Directory Structure

```
gutenberg/
├── scraper/
│   ├── docs/                        # Technical documentation
│   │   ├── JSON_FILE_STRUCTURE.md   # JSON schema specification
│   │   └── GUTENBERG_STRUCTURE.md   # Architecture overview
│   ├── src/gutenberg2zim/           # Python scraper
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── __about__.py
│   │   ├── entrypoint.py            # CLI entry point
│   │   ├── book_processor.py        # Book processing logic
│   │   ├── csv_catalog.py           # CSV catalog handling
│   │   ├── download.py              # Book downloading
│   │   ├── export.py                # JSON generation + Vue dist export
│   │   ├── i18n.py                  # Internationalization
│   │   ├── iso639.py                # Language code handling
│   │   ├── models.py                # Data models
│   │   ├── pg_archive_urls.py       # Archive URL handling
│   │   ├── rdf.py                   # RDF metadata parsing
│   │   ├── schemas.py               # Pydantic models for JSON
│   │   ├── scraper_progress.py      # Progress tracking
│   │   ├── shared.py                # Shared utilities
│   │   ├── utils.py                 # Utility functions
│   │   ├── zim.py                   # ZIM file creation
│   │   ├── templates/               # Jinja2 templates
│   │   │   ├── book_infobox.html    # Book infobox for HTML books
│   │   │   ├── css/
│   │   │   │   └── gutenberg-infobox.css
│   │   │   ├── js/
│   │   │   │   └── gutenberg-infobox.js
│   │   │   ├── icons/               # Infobox icons
│   │   │   │   ├── epub.svg
│   │   │   │   ├── info.svg
│   │   │   │   ├── pdf.svg
│   │   │   │   └── scroll-up.svg
│   │   │   ├── favicon.png
│   │   │   └── noscript/            # No-JS fallback templates
│   │   │       ├── _nav.html
│   │   │       ├── books.html
│   │   │       ├── book.html
│   │   │       ├── authors.html
│   │   │       ├── author.html
│   │   │       ├── lcc_shelves.html
│   │   │       ├── lcc_shelf.html
│   │   │       └── common.css
│   │   └── __pycache__/
│   ├── tests/                       # Python tests
│   │   └── test_rdf.py
│   ├── pyproject.toml               # Python project configuration
│   └── tasks.py                     # Invoke tasks
├── ui/                              # Vue.js frontend
│   ├── dist/                        # Build output (generated)
│   ├── node_modules/                # npm dependencies
│   ├── public/                      # Static assets
│   ├── src/
│   │   ├── main.ts                  # App entry point
│   │   ├── App.vue                  # Root component
│   │   ├── router/
│   │   │   └── index.ts             # Vue Router configuration
│   │   ├── stores/
│   │   │   └── main.ts              # Pinia store
│   │   ├── views/                   # Page components
│   │   │   ├── HomeView.vue
│   │   │   ├── BookDetailView.vue
│   │   │   ├── AuthorListView.vue
│   │   │   ├── AuthorDetailView.vue
│   │   │   ├── LCCShelfListView.vue
│   │   │   ├── LCCShelfDetailView.vue
│   │   │   ├── AboutView.vue
│   │   │   └── NotFoundView.vue
│   │   ├── components/
│   │   │   ├── book/
│   │   │   │   ├── BookCard.vue
│   │   │   │   ├── BookGrid.vue
│   │   │   │   ├── BookList.vue
│   │   │   │   └── BookDetailInfo.vue
│   │   │   ├── author/
│   │   │   │   ├── AuthorCard.vue
│   │   │   │   ├── AuthorGrid.vue
│   │   │   │   └── AuthorDetailInfo.vue
│   │   │   ├── lccshelf/
│   │   │   │   ├── LCCShelfCard.vue
│   │   │   │   ├── LCCShelfGrid.vue
│   │   │   │   └── LCCShelfDetailInfo.vue
│   │   │   ├── common/
│   │   │   │   ├── BaseFilter.vue
│   │   │   │   ├── BookCoverImage.vue
│   │   │   │   ├── BooksSection.vue
│   │   │   │   ├── Breadcrumbs.vue
│   │   │   │   ├── CollapsibleFilters.vue
│   │   │   │   ├── CoverFallback.vue
│   │   │   │   ├── DetailInfoCard.vue
│   │   │   │   ├── DetailViewWrapper.vue
│   │   │   │   ├── EmptyState.vue
│   │   │   │   ├── ErrorDisplay.vue
│   │   │   │   ├── FormatFilter.vue
│   │   │   │   ├── ImagePlaceholder.vue
│   │   │   │   ├── ItemCount.vue
│   │   │   │   ├── LanguageFilter.vue
│   │   │   │   ├── LanguageSwitcher.vue
│   │   │   │   ├── ListViewWrapper.vue
│   │   │   │   ├── LoadingSpinner.vue
│   │   │   │   ├── NotFoundState.vue
│   │   │   │   ├── PaginationControl.vue
│   │   │   │   └── SortControl.vue
│   │   │   └── layout/
│   │   │       ├── AppHeader.vue
│   │   │       └── AppFooter.vue
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript type definitions
│   │   ├── constants/
│   │   │   ├── messages.ts
│   │   │   └── theme.ts
│   │   ├── composables/             # Vue composables
│   │   │   ├── useListLoader.ts
│   │   │   ├── usePagination.ts
│   │   │   ├── useSearchFilter.ts
│   │   │   └── useSorting.ts
│   │   ├── plugins/
│   │   │   ├── i18n.ts              # i18n configuration
│   │   │   └── vuetify.ts           # Vuetify configuration
│   │   └── utils/
│   │       └── format-utils.ts
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── eslint.config.js
│   ├── .prettierrc.json
│   ├── env.d.ts
│   └── README.md
├── locales/                         # UI translations
│   ├── en.json
│   ├── fr.json
│   ├── es.json
│   ├── de.json
│   └── ... (many more languages)
├── pictures/                        # Screenshots
│   ├── screenshot_1.png
│   └── screenshot_2.png
├── .github/
│   └── workflows/                   # CI/CD workflows
│       ├── Publish.yaml
│       ├── PublishDockerDevImage.yaml
│       ├── QA.yaml
│       ├── Tests.yaml
│       └── update-zim-offliner-definition.yaml
├── Dockerfile
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── CHANGELOG.md
├── offliner-definition.json
├── pg_catalog.csv.gz
└── .pre-commit-config.yaml
```

---

## JSON File Structure

Following YouTube scraper pattern: **High-level metadata files + Detail files**
### High-Level Files (List/Preview Data)
```
ZIM_ROOT/
├── books.json              # List of all books (preview format)
├── authors.json            # List of all authors (preview format)
├── lcc_shelves.json        # List of all LCC shelves (preview format)
└── config.json             # UI configuration (theme, etc.)
```

### Detail Files (Full Content - Folder-Based Structure)
```
ZIM_ROOT/
├── books/
│   ├── {id}.json           # Individual book details (e.g., 12345.json)
├── authors/
│   ├── {id}.json           # Author details + their books (e.g., 68.json)
└── lcc_shelves/
    ├── {code}.json         # LCC shelf details + books in shelf (e.g., PR.json)
```

---

## Python Side - Pydantic Schemas

### `scraper/src/gutenberg2zim/schemas.py`

> **Note:** Code examples below are simplified for illustration. See actual implementation for complete details.

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    """Base model that converts snake_case to camelCase for JSON"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

# Author Models
class AuthorPreview(CamelModel):
    """Author preview for list views"""
    id: str
    name: str
    book_count: int

class AuthorDetail(CamelModel):
    """Full author details"""
    id: str
    first_name: str | None = None
    last_name: str
    birth_year: str | None = None
    death_year: str | None = None
    name: str
    books: list["BookPreview"]
    book_count: int

# Book Models
class BookFormat(CamelModel):
    """Available format information"""
    format: str  # "html", "epub", "pdf"
    path: str    # ZIM path to file
    available: bool = True

class BookPreview(CamelModel):
    """Book preview for list views"""
    id: int
    title: str
    author: AuthorPreview
    languages: list[str]
    popularity: int  # Star rating (0-5)
    cover_path: str | None = None
    lcc_shelf: str | None = None

class Book(CamelModel):
    """Full book details"""
    id: int
    title: str
    subtitle: str | None = None
    author: AuthorDetail
    languages: list[str]
    license: str
    downloads: int
    popularity: int
    lcc_shelf: str | None = None
    cover_path: str | None = None
    formats: list[BookFormat]
    description: str | None = None

# LCC Shelf Models
class LCCShelfPreview(CamelModel):
    """LCC shelf preview for list views"""
    code: str
    name: str | None = None
    book_count: int

class LCCShelf(CamelModel):
    """Full LCC shelf details"""
    code: str
    name: str | None = None
    books: list[BookPreview]
    book_count: int

# Collection Models
class Books(CamelModel):
    """List of book previews"""
    books: list[BookPreview]
    total_count: int

class Authors(CamelModel):
    """List of author previews"""
    authors: list[AuthorPreview]
    total_count: int

class LCCShelves(CamelModel):
    """List of LCC shelf previews"""
    shelves: list[LCCShelfPreview]
    total_count: int

class Config(CamelModel):
    """UI configuration"""
    title: str
    description: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
```

---

## JSON File Examples

### `books.json` (High-Level)
```json
{
  "books": [
    {
      "id": 12345,
      "title": "Pride and Prejudice",
      "author": {
        "id": "68",
        "name": "Austen, Jane",
        "bookCount": 7
      },
      "languages": ["en"],
      "popularity": 5,
      "coverPath": "A/cover_article_12345.html",
      "lccShelf": "PR"
    },
    ...
  ],
  "totalCount": 70000
}
```

### `books/12345.json` (Detail)
```json
{
  "id": 12345,
  "title": "Pride and Prejudice",
  "subtitle": null,
  "author": {
    "id": "68",
    "firstName": "Jane",
    "lastName": "Austen",
    "birthYear": "1775",
    "deathYear": "1817",
    "name": "Austen, Jane"
  },
  "languages": ["en"],
  "license": "Public domain in the USA.",
  "downloads": 50000,
  "popularity": 5,
  "lccShelf": "PR",
  "coverPath": "A/cover_article_12345.html",
  "formats": [
    {
      "format": "html",
      "path": "A/12345.html",
      "available": true
    },
    {
      "format": "epub",
      "path": "I/12345.epub",
      "available": true
    },
    {
      "format": "pdf",
      "path": "I/12345.pdf",
      "available": true
    }
  ]
}
```

### `authors.json` (High-Level)
```json
{
  "authors": [
    {
      "id": "68",
      "name": "Austen, Jane",
      "bookCount": 7
    },
    ...
  ],
  "totalCount": 15000
}
```

### `authors/68.json` (Detail)
```json
{
  "id": "68",
  "firstName": "Jane",
  "lastName": "Austen",
  "birthYear": "1775",
  "deathYear": "1817",
  "name": "Austen, Jane",
  "books": [
    {
      "id": 12345,
      "title": "Pride and Prejudice",
      "author": {
        "id": "68",
        "name": "Austen, Jane",
        "bookCount": 7
      },
      "languages": ["en"],
      "popularity": 5,
      "coverPath": "A/cover_article_12345.html",
      "lccShelf": "PR"
    },
    ...
  ],
  "bookCount": 7
}
```

### `lcc_shelves.json` (High-Level)
```json
{
  "shelves": [
    {
      "code": "PR",
      "name": "English literature",
      "bookCount": 5000
    },
    ...
  ],
  "totalCount": 200
}
```

### `lcc_shelves/PR.json` (Detail)
```json
{
  "code": "PR",
  "name": "English literature",
  "bookCount": 5000,
  "books": [
    {
      "id": 12345,
      "title": "Pride and Prejudice",
      "author": {
        "id": "68",
        "name": "Austen, Jane",
        "bookCount": 7
      },
      "languages": ["en"],
      "popularity": 5,
      "coverPath": "A/cover_article_12345.html",
      "lccShelf": "PR"
    },
    ...
  ]
}
```

### `config.json`
```json
{
  "title": "Project Gutenberg Library",
  "description": "Free eBooks from Project Gutenberg",
  "primaryColor": null,
  "secondaryColor": null
}
```

---

## Python Export Flow

### `src/gutenberg2zim/export.py` - New Functions

```python
def generate_json_files(zim_name: str, formats: list[str]) -> None:
    """Generate all JSON files for Vue.js frontend"""
    
    # Note: Helper functions like book_to_preview(), book_to_detail(), etc.
    # convert internal data models to Pydantic schema instances
    
    # 1. Generate high-level files
    books_preview = [book_to_preview(book) for book in repository.get_all_books()]
    authors_preview = [author_to_preview(author) for author in repository.get_all_authors()]
    shelves_preview = [shelf_to_preview(shelf) for shelf in repository.get_lcc_shelves()]
    
    # Write high-level files
    Global.add_item_for(
        path="books.json",
        content=Books(books=books_preview, totalCount=len(books_preview))
            .model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False
    )
    
    # Similar for authors.json, lcc_shelves.json
    
    # 2. Generate detail files (folder-based structure)
    for book in repository.get_all_books():
        book_detail = book_to_detail(book, formats)
        Global.add_item_for(
            path=f"books/{book.book_id}.json",
            content=book_detail.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False
        )
    
    for author in repository.get_all_authors():
        author_detail = author_to_detail(author)
        Global.add_item_for(
            path=f"authors/{author.gut_id}.json",
            content=author_detail.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False
        )
    
    for shelf_code in repository.get_lcc_shelves():
        shelf_detail = shelf_to_detail(shelf_code)
        Global.add_item_for(
            path=f"lcc_shelves/{shelf_code}.json",
            content=shelf_detail.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False
        )
    
    # 3. Generate config.json
    Global.add_item_for(
        path="config.json",
        content=Config(title=zim_name).model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False
    )


def export_vue_dist(dist_dir: Path) -> None:
    """Export Vue.js dist folder to ZIM (similar to Youtube's add_zimui)"""
    for file in dist_dir.rglob("*"):
        if file.is_dir():
            continue
        path = str(file.relative_to(dist_dir))
        if path == "index.html":
            # Modify title
            html_content = file.read_text(encoding="utf-8")
            new_html = re.sub(
                r"(<title>)(.*?)(</title>)",
                rf"\1{Global.zim_name}\3",
                html_content,
                flags=re.IGNORECASE
            )
            Global.add_item_for(
                path=path,
                content=new_html,
                mimetype="text/html",
                is_front=True
            )
        else:
            Global.add_item_for(path=path, fpath=file, is_front=False)
```

---

## Vue.js Side Structure

### `ui/src/types/index.ts`

> **Note:** TypeScript interfaces match the Pydantic schemas (camelCase).

```typescript
export interface AuthorPreview {
  id: string
  name: string
  bookCount: number
}

export interface AuthorDetail {
  id: string
  firstName?: string
  lastName: string
  birthYear?: string
  deathYear?: string
  name: string
  books: BookPreview[]
  bookCount: number
}

export interface BookFormat {
  format: string
  path: string
  available: boolean
}

export interface BookPreview {
  id: number
  title: string
  author: AuthorPreview
  languages: string[]
  popularity: number
  coverPath?: string
  lccShelf?: string
}

export interface Book {
  id: number
  title: string
  subtitle?: string
  author: AuthorDetail
  languages: string[]
  license: string
  downloads: number
  popularity: number
  lccShelf?: string
  coverPath?: string
  formats: BookFormat[]
  description?: string
}
```

### `ui/src/stores/main.ts` (Pinia Store)

> **Note:** Simplified example. See actual implementation for complete store logic.

```typescript
import { defineStore } from 'pinia'
import axios from 'axios'
import type { Book, BookPreview, AuthorDetail, AuthorPreview } from '@/types'

export const useMainStore = defineStore('main', {
  state: () => ({
    books: [] as BookPreview[],
    authors: [] as AuthorPreview[],
    currentBook: null as Book | null,
    currentAuthor: null as AuthorDetail | null,
    isLoading: false,
    errorMessage: ''
  }),
  
  actions: {
    async fetchBooks() {
      const response = await axios.get('./books.json')
      this.books = response.data.books
    },
    
    async fetchBook(id: number) {
      const response = await axios.get(`./books/${id}.json`)
      this.currentBook = response.data
    },
    
    async fetchAuthors() {
      const response = await axios.get('./authors.json')
      this.authors = response.data.authors
    },
    
    async fetchAuthor(id: string) {
      const response = await axios.get(`./authors/${id}.json`)
      this.currentAuthor = response.data
    }
  }
})
```

### `ui/src/router/index.ts`

> **Note:** Simplified example showing route structure.

```typescript
import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue')
    },
    {
      path: '/book/:id',
      name: 'book-detail',
      component: () => import('@/views/BookDetailView.vue')
    },
    {
      path: '/authors',
      name: 'author-list',
      component: () => import('@/views/AuthorListView.vue')
    },
    {
      path: '/author/:id',
      name: 'author-detail',
      component: () => import('@/views/AuthorDetailView.vue')
    },
    {
      path: '/lcc-shelves',
      name: 'lcc-shelf-list',
      component: () => import('@/views/LCCShelfListView.vue')
    },
    {
      path: '/lcc-shelf/:code',
      name: 'lcc-shelf-detail',
      component: () => import('@/views/LCCShelfDetailView.vue')
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('@/views/AboutView.vue')
    }
  ]
})

export default router
```

---

## Integration Points

### 1. Build Process
1. **Python side**: Generate JSON files during ZIM creation
2. **Vue side**: Build with `npm run build` → `ui/dist/`
3. **Python side**: Export `ui/dist/` to ZIM
4. **Result**: ZIM contains both JSON files and Vue.js app

### 2. Data Flow
```
Python (models.py) 
  → Pydantic schemas (schemas.py)
  → JSON files (export.py)
  → ZIM file
  → Vue.js app loads JSON via Axios
  → Pinia store
  → Components display data
```

### 3. No-JS Fallback
- Generate static HTML pages using Jinja2 templates in `noscript/`
- Include in ZIM alongside Vue app
- Users without JS see HTML pages
- Users with JS see Vue app (better UX)

---

## Key Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Data Format** | JSON (two-tier: preview + detail) | Efficient loading, follows Youtube pattern |
| **Frontend** | Vue.js 3 + Vite | Modern, fast, component-based |
| **State Management** | Pinia | Official Vue store, simpler than Vuex |
| **Routing** | Vue Router (hash mode) | Works in ZIM without server |
| **Styling** | Vuetify 3 | Material Design, comprehensive components |
| **No-JS Fallback** | Jinja2 templates | Accessibility, works without JavaScript |
| **Type Safety** | Pydantic + TypeScript | Ensures data consistency |

---

*This architecture provides a modern, maintainable foundation while preserving backwards compatibility through no-JS fallback pages.*

