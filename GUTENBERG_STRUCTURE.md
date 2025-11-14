# Gutenberg UI Revamp - Complete Structure

## 📁 Directory Structure

```
gutenberg/
├── src/gutenberg2zim/              # Python scraper (existing)
│   ├── __init__.py
│   ├── __main__.py
│   ├── entrypoint.py
│   ├── book_processor.py
│   ├── csv_catalog.py
│   ├── download.py
│   ├── export.py                    # MODIFIED: Add JSON generation
│   ├── models.py                    # MODIFIED: Add Pydantic schemas
│   ├── schemas.py                   # NEW: Pydantic models for JSON
│   ├── zim.py                       # MODIFIED: Add Vue dist export
│   ├── templates/                   # Existing Jinja2 templates
│   │   ├── base.html
│   │   ├── Home.html
│   │   ├── cover_article.html
│   │   ├── author.html
│   │   └── noscript/                # NEW: No-JS fallback templates
│   │       ├── books.html
│   │       ├── book.html
│   │       └── author.html
│   └── ...
├── ui/                              # NEW: Vue.js frontend
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── stores/
│   │   │   └── main.ts
│   │   ├── views/
│   │   │   ├── HomeView.vue
│   │   │   ├── BookListView.vue
│   │   │   ├── BookDetailView.vue
│   │   │   ├── AuthorListView.vue
│   │   │   ├── AuthorDetailView.vue
│   │   │   ├── LCCShelfListView.vue
│   │   │   ├── LCCShelfDetailView.vue
│   │   │   └── AboutView.vue
│   │   ├── components/
│   │   │   ├── book/
│   │   │   │   ├── BookCard.vue
│   │   │   │   ├── BookGrid.vue
│   │   │   │   ├── BookList.vue
│   │   │   │   └── BookDetailInfo.vue
│   │   │   ├── author/
│   │   │   │   ├── AuthorCard.vue
│   │   │   │   └── AuthorDetailInfo.vue
│   │   │   ├── common/
│   │   │   │   ├── SearchBar.vue
│   │   │   │   ├── LanguageFilter.vue
│   │   │   │   ├── FormatFilter.vue
│   │   │   │   ├── SortControl.vue
│   │   │   │   └── ErrorDisplay.vue
│   │   │   └── layout/
│   │   │       ├── AppHeader.vue
│   │   │       └── AppFooter.vue
│   │   ├── types/
│   │   │   ├── Book.ts
│   │   │   ├── Author.ts
│   │   │   ├── LCCShelf.ts
│   │   │   └── Config.ts
│   │   └── utils/
│   │       ├── format-utils.ts
│   │       └── search-utils.ts
│   └── public/
│       └── favicon.ico
└── ...
```

---

## 📄 JSON File Structure

Following Youtube scraper pattern: **High-level metadata files + Detail files**

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

## 🐍 Python Side - Pydantic Schemas

### `src/gutenberg2zim/schemas.py` (NEW)

```python
from humps import camelize
from pydantic import BaseModel

class CamelModel(BaseModel):
    """Model to transform Python snake_case into JSON camelCase."""
    class Config:
        alias_generator = camelize
        populate_by_name = True


# Author Models
class Author(CamelModel):
    """Author information for JSON export"""
    id: str  # gut_id
    firstName: str | None = None
    lastName: str
    birthYear: str | None = None
    deathYear: str | None = None
    name: str  # Formatted full name


class AuthorPreview(CamelModel):
    """Author preview for list views"""
    id: str
    name: str
    bookCount: int


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
    coverPath: str | None = None
    lccShelf: str | None = None


class Book(CamelModel):
    """Full book details"""
    id: int
    title: str
    subtitle: str | None = None
    author: Author
    languages: list[str]
    license: str
    downloads: int
    popularity: int
    lccShelf: str | None = None
    coverPath: str | None = None
    formats: list[BookFormat]
    description: str | None = None  # If available from RDF


# LCC Shelf Models
class LCCShelfPreview(CamelModel):
    """LCC shelf preview for list views"""
    code: str
    name: str | None = None
    bookCount: int


class LCCShelf(CamelModel):
    """Full LCC shelf details"""
    code: str
    name: str | None = None
    books: list[BookPreview]
    bookCount: int


# Collection Models
class Books(CamelModel):
    """List of book previews"""
    books: list[BookPreview]
    totalCount: int


class Authors(CamelModel):
    """List of author previews"""
    authors: list[AuthorPreview]
    totalCount: int


class LCCShelves(CamelModel):
    """List of LCC shelf previews"""
    shelves: list[LCCShelfPreview]
    totalCount: int


class Config(CamelModel):
    """UI configuration"""
    title: str
    description: str | None = None
    mainColor: str | None = None
    secondaryColor: str | None = None
```

---

## 📊 JSON File Examples

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
  "mainColor": null,
  "secondaryColor": null
}
```

---

## 🔄 Python Export Flow

### `src/gutenberg2zim/export.py` - New Functions

```python
def generate_json_files(zim_name: str, formats: list[str]) -> None:
    """Generate all JSON files for Vue.js frontend"""
    
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

## 🎨 Vue.js Side Structure

### `ui/src/types/Book.ts`
```typescript
export interface Author {
  id: string
  firstName?: string
  lastName: string
  birthYear?: string
  deathYear?: string
  name: string
}

export interface AuthorPreview {
  id: string
  name: string
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
  author: Author
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
```typescript
import { defineStore } from 'pinia'
import axios from 'axios'
import type { Book, BookPreview, Author, AuthorPreview } from '@/types/Book'

export const useMainStore = defineStore('main', {
  state: () => ({
    books: [] as BookPreview[],
    authors: [] as AuthorPreview[],
    currentBook: null as Book | null,
    currentAuthor: null as Author | null,
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
      path: '/books',
      name: 'books',
      component: () => import('@/views/BookListView.vue')
    },
    {
      path: '/book/:id',
      name: 'book-detail',
      component: () => import('@/views/BookDetailView.vue')
    },
    {
      path: '/authors',
      name: 'authors',
      component: () => import('@/views/AuthorListView.vue')
    },
    {
      path: '/author/:id',
      name: 'author-detail',
      component: () => import('@/views/AuthorDetailView.vue')
    },
    {
      path: '/lcc-shelves',
      name: 'lcc-shelves',
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

## 🔗 Integration Points

### 1. Build Process
1. **Python side**: Generate JSON files during ZIM creation
2. **Vue side**: Build with `npm run build` → `ui/dist/`
3. **Python side**: Export `ui/dist/` to ZIM (similar to Youtube's `add_zimui()`)
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
- Generate static HTML pages using Jinja2 templates
- Include in ZIM alongside Vue app
- Users without JS see HTML pages
- Users with JS see Vue app (better UX)

---

## 📝 Key Differences from Youtube

| Aspect | Youtube | Gutenberg |
|--------|---------|-----------|
| **Entity** | Videos, Playlists, Channels | Books, Authors, LCC Shelves |
| **Navigation** | Channel-centric | Book/Author-centric |
| **Formats** | Video formats (webm, mp4) | Book formats (html, epub, pdf) |
| **Search** | Video search | Book/Author search |
| **LCC Shelves** | N/A | Unique to Gutenberg |

---

## ✅ Next Steps

1. Create `schemas.py` with Pydantic models
2. Modify `export.py` to generate JSON files
3. Set up Vue.js project in `ui/` folder
4. Create TypeScript interfaces matching Pydantic schemas
5. Implement Vue components and views
6. Test end-to-end flow

---

*This structure follows Youtube scraper patterns while adapting to Gutenberg's specific needs (books, authors, LCC shelves).*

