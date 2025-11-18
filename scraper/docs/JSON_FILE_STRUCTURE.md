# JSON File Structure Specification

## Overview

This document defines the complete JSON file structure for the Gutenberg Vue.js UI, following the pattern established in the Youtube scraper. The structure uses a two-tier approach: **high-level preview files** for listing/pagination, and **detail files** for full content.

---

## File Organization

### High-Level Files (Root Level)
These files contain preview/summary data and are loaded once when the UI initializes.

```
ZIM_ROOT/
├── books.json              # All books (preview format)
├── authors.json            # All authors (preview format)
├── lcc_shelves.json        # All LCC shelves (preview format)
└── config.json             # UI configuration
```

### Detail Files (Folder-Based)
These files contain full details and are loaded on-demand when a user views a specific resource.

```
ZIM_ROOT/
├── books/
│   ├── {id}.json           # Individual book details (e.g., 12345.json)
├── authors/
│   ├── {id}.json           # Author details + their books (e.g., 68.json)
└── lcc_shelves/
    ├── {code}.json         # LCC shelf details + books (e.g., PR.json)
```

---

## File Naming Conventions

### Books
- **High-level**: `books.json`
- **Detail files**: `books/{id}.json` where `{id}` is the numeric book ID (e.g., `12345.json`)
- **Example**: `books/1.json`, `books/12345.json`

### Authors
- **High-level**: `authors.json`
- **Detail files**: `authors/{id}.json` where `{id}` is the author's `gut_id` (e.g., `68.json`)
- **Example**: `authors/68.json`, `authors/116.json` (for "Various")

### LCC Shelves
- **High-level**: `lcc_shelves.json`
- **Detail files**: `lcc_shelves/{code}.json` where `{code}` is the LCC shelf code (e.g., `PR.json`)
- **Example**: `lcc_shelves/PR.json`, `lcc_shelves/Q.json`
- **Note**: LCC codes are uppercase and may contain multiple characters (e.g., `PA`, `PR`, `PS`)

### Configuration
- **File**: `config.json` (always at root level)

---

## Data Size Considerations

### High-Level Files
- **Target size**: < 5MB per file (for large ZIMs with 70,000+ books)
- **Optimization**: Only include essential fields for listing
- **Pagination**: Frontend handles client-side pagination/filtering

### Detail Files
- **Typical size**: 1-10KB per file
- **Largest files**: Author detail files with many books (may be 50-100KB for prolific authors)
- **Loading strategy**: Load on-demand, cache in browser

### Performance Targets
- Initial load: < 2 seconds for high-level files
- Detail file load: < 100ms per file
- Total ZIM size impact: < 100MB for JSON files (even with 70,000 books)

---

## File Contents Specification

### `books.json`
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
    }
  ],
  "totalCount": 70000
}
```

**Fields included**:
- `id`: Book ID
- `title`: Book title
- `author`: Author preview (id, name, bookCount)
- `languages`: List of language codes
- `popularity`: Star rating (0-5)
- `coverPath`: Path to cover image/article
- `lccShelf`: LCC shelf code (optional)

**Fields excluded** (to keep file small):
- Full author details
- Formats list
- Downloads count
- Subtitle
- Description

### `books/{id}.json`
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
    }
  ],
  "description": null
}
```

**All fields included** for full book details.

### `authors.json`
```json
{
  "authors": [
    {
      "id": "68",
      "name": "Austen, Jane",
      "bookCount": 7
    }
  ],
  "totalCount": 15000
}
```

**Minimal fields** for author listing.

### `authors/{id}.json`
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
    }
  ],
  "bookCount": 7
}
```

**Includes**: Full author details + list of their books (as previews).

### `lcc_shelves.json`
```json
{
  "shelves": [
    {
      "code": "PR",
      "name": "English literature",
      "bookCount": 5000
    }
  ],
  "totalCount": 200
}
```

**Minimal fields** for shelf listing.

### `lcc_shelves/{code}.json`
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
    }
  ]
}
```

**Includes**: Shelf details + list of books in shelf (as previews).

### `config.json`
```json
{
  "title": "Project Gutenberg Library",
  "description": "Free eBooks from Project Gutenberg",
  "mainColor": null,
  "secondaryColor": null
}
```

**UI configuration** for theming and branding.

---

## Loading Strategy

### Initial Load (UI Startup)
1. Load `config.json` - UI configuration
2. Load `books.json` - All book previews (for main listing)
3. Load `authors.json` - All author previews (for author listing)
4. Load `lcc_shelves.json` - All shelf previews (for shelf listing)

### On-Demand Load
1. **Book detail page**: Load `books/{id}.json`
2. **Author detail page**: Load `authors/{id}.json`
3. **LCC shelf page**: Load `lcc_shelves/{code}.json`

### Caching Strategy
- Cache high-level files in Pinia store (loaded once)
- Cache detail files in Pinia store (loaded on first access)
- Use browser's HTTP cache for subsequent ZIM access

---

## Edge Cases

### Missing Data
- **Missing author**: Use "Anonymous" (ID: "216") or "Various" (ID: "116")
- **Missing LCC shelf**: `lccShelf` field is `null`
- **Missing cover**: `coverPath` is `null`
- **Missing format**: Format marked as `available: false` in formats array

### Special Characters
- **File names**: Use numeric IDs for books, alphanumeric IDs for authors, uppercase codes for LCC shelves
- **JSON encoding**: All files use UTF-8 encoding
- **Path separators**: Use forward slashes (`/`) in JSON paths (ZIM standard)

### Large Collections
- **70,000+ books**: High-level `books.json` may be large; frontend implements virtual scrolling/pagination
- **Prolific authors**: Author detail files may contain 100+ books; frontend paginates the book list
- **Popular shelves**: LCC shelf detail files may contain 1000+ books; frontend paginates

---

## Implementation Notes

### Python Side
- Use Pydantic models for type safety and validation
- Generate JSON with `model_dump_json(by_alias=True, indent=2)`
- Ensure all paths use forward slashes
- Handle missing/optional fields gracefully

### Vue.js Side
- Use Axios for JSON fetching
- Implement error handling for missing files
- Use TypeScript interfaces matching Pydantic schemas
- Cache loaded data in Pinia store

### ZIM Export
- All JSON files use `mimetype="application/json"`
- Files are not marked as `is_front=True` (except `config.json` if needed)
- Ensure proper UTF-8 encoding

---

## Migration from Old Format

The old format used JavaScript files like:
- `full_by_popularity.js` (containing `var json_data = [...]`)
- `lang_en_by_popularity.js`
- `auth_68_by_popularity.js`

**New format advantages**:
- Standard JSON (easier to parse)
- On-demand loading (better performance)
- Type-safe (Pydantic validation)
- Folder-based organization (scalable)

The old format has been removed. The scraper now only generates the new JSON files for the Vue.js UI.

