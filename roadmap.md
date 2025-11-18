# Gutenberg UI Revamp - Implementation Roadmap

> **Note:** This document is for general reference purposes during development and will be removed later.

## Overview
This roadmap outlines the complete implementation plan for migrating Gutenberg from Jinja2/jQuery to Vue.js, following the patterns established in the Youtube scraper. The plan is organized into logical phases that build upon each other.

---

## Phase 1: Project Structure Reorganization

### 1.1 Create Working Branch
- Create `ui-revamp2` branch from `main` branch
- Set this as the base branch for all future PRs
- Ensure branch is up-to-date with latest `main` changes

### 1.2 Reorganize Python Code into `scraper/` Folder
Following Youtube scraper structure:
- Create `scraper/` directory at repository root
- Move `src/gutenberg2zim/` → `scraper/src/gutenberg2zim/`
- Move `pyproject.toml` → `scraper/pyproject.toml` (or create new one)
- Update all import paths and references
- Update `entrypoint.py` to work from new location
- Update `hatch_build.py` if needed
- Test that scraper still runs correctly from new location

### 1.3 Create Vue.js Project Structure
- Create `ui/` directory at repository root (parallel to `scraper/`)
- Initialize Vue 3 project with Vite
- Set up TypeScript configuration
- Configure Vue Router (hash mode: `createWebHashHistory()`)
- Set up Pinia for state management
- Configure Vuetify 3 for UI components
- Set up ESLint and Prettier
- Configure `@vitejs/plugin-legacy` for browser compatibility
- Add polyfills (ResizeObserver, etc.) similar to Youtube scraper

### 1.4 Update Build Configuration
- Update `scraper/pyproject.toml` to reference new paths
- Ensure `ui/` build outputs to `ui/dist/`
- Configure Python scraper to export `ui/dist/` to ZIM
- Update any CI/CD configurations

---

## Phase 2: JSON Schema Design & Implementation

### 2.1 Create Pydantic Schemas
Create `scraper/src/gutenberg2zim/schemas.py`:
- Implement `CamelModel` base class (custom camelCase helper)
- Define `Author` model (full details)
- Define `AuthorPreview` model (for lists)
- Define `BookFormat` model (format availability info)
- Define `BookPreview` model (for lists)
- Define `Book` model (full details)
- Define `LCCShelfPreview` model (for lists)
- Define `LCCShelf` model (full details)
- Define collection models: `Books`, `Authors`, `LCCShelves`
- Define `Config` model (UI configuration)

### 2.2 Design JSON File Structure (Folder-Based)
Following Youtube scraper pattern:
```
ZIM_ROOT/
├── books.json                    # High-level: list of all books (preview)
├── authors.json                  # High-level: list of all authors (preview)
├── lcc_shelves.json              # High-level: list of all LCC shelves (preview)
├── config.json                   # UI configuration
├── books/
│   ├── {id}.json                 # Detail: individual book (e.g., 12345.json)
├── authors/
│   ├── {id}.json                 # Detail: individual author (e.g., 68.json)
└── lcc_shelves/
    ├── {code}.json               # Detail: individual LCC shelf (e.g., PR.json)
```

### 2.3 Create Design Mockup
Create visual design mockup (similar to siemsie's approach in libkiwix PR #1240):
- Homepage layout (cards, grid, modern spacing)
- Book detail page
- Author detail page
- LCC shelf pages
- Navigation structure
- Responsive breakpoints
- Color scheme and typography
- Share mockup for team review before implementation

### 2.4 Implement JSON Generation Functions
Modify `scraper/src/gutenberg2zim/export.py`:
- Create `generate_json_files()` function to replace `export_to_json_helpers()`
- Generate `books.json` (all book previews)
- Generate `authors.json` (all author previews)
- Generate `lcc_shelves.json` (all LCC shelf previews)
- Generate `config.json` (UI configuration)
- Generate `books/{id}.json` (individual book details)
- Generate `authors/{id}.json` (individual author details with their books)
- Generate `lcc_shelves/{code}.json` (individual LCC shelf details with books)
- Use Pydantic models for serialization (`model_dump_json(by_alias=True, indent=2)`)
- Ensure proper error handling and logging

### 2.5 Update Data Models
Modify `scraper/src/gutenberg2zim/models.py`:
- Keep existing `Book` and `Author` dataclasses (used internally)
- Add helper methods to convert to Pydantic schemas
- Ensure compatibility between dataclasses and Pydantic models

---

## Phase 3: Vue.js UI Foundation

### 3.1 Set Up Vue.js Project Structure
Create `ui/src/` directory structure:
```
ui/src/
├── main.ts                       # Entry point
├── App.vue                       # Root component
├── router/
│   └── index.ts                  # Vue Router configuration
├── stores/
│   └── main.ts                   # Pinia store (data fetching)
├── views/
│   ├── HomeView.vue
│   ├── BookListView.vue
│   ├── BookDetailView.vue
│   ├── AuthorListView.vue
│   ├── AuthorDetailView.vue
│   ├── LCCShelfListView.vue
│   ├── LCCShelfDetailView.vue
│   └── AboutView.vue
├── components/
│   ├── book/
│   │   ├── BookCard.vue
│   │   ├── BookGrid.vue
│   │   ├── BookList.vue
│   │   └── BookDetailInfo.vue
│   ├── author/
│   │   ├── AuthorCard.vue
│   │   └── AuthorDetailInfo.vue
│   ├── common/
│   │   ├── LanguageFilter.vue
│   │   ├── FormatFilter.vue
│   │   ├── SortControl.vue
│   │   └── ErrorDisplay.vue
│   └── layout/
│       ├── AppHeader.vue
│       └── AppFooter.vue
├── types/
│   ├── Book.ts
│   ├── Author.ts
│   ├── LCCShelf.ts
│   └── Config.ts
└── utils/
    └── format-utils.ts
```

### 3.2 Implement TypeScript Types
Create type definitions in `ui/src/types/`:
- `Book.ts` - Book interfaces matching Pydantic schemas
- `Author.ts` - Author interfaces
- `LCCShelf.ts` - LCC shelf interfaces
- `Config.ts` - Config interface

### 3.3 Set Up Pinia Store
Create `ui/src/stores/main.ts`:
- Implement actions to fetch JSON files:
  - `fetchBooks()` - Load `books.json`
  - `fetchBook(id)` - Load `books/{id}.json`
  - `fetchAuthors()` - Load `authors.json`
  - `fetchAuthor(id)` - Load `authors/{id}.json`
  - `fetchLCCShelves()` - Load `lcc_shelves.json`
  - `fetchLCCShelf(code)` - Load `lcc_shelves/{code}.json`
  - `fetchConfig()` - Load `config.json`
- Use Axios for HTTP requests
- Implement simple request deduplication (prevent duplicate concurrent requests to same resource)
- Do NOT cache detail files in memory (books, authors, shelves) to keep memory usage low on small devices
- Handle loading states and errors

### 3.4 Configure Vue Router
Set up routes in `ui/src/router/index.ts`:
- `/` - HomeView (book listing)
- `/book/:id` - BookDetailView
- `/authors` - AuthorListView (list all authors)
- `/author/:id` - AuthorDetailView
- `/lcc-shelves` - LCCShelfListView (list all shelves)
- `/lcc-shelf/:code` - LCCShelfDetailView
- `/about` - AboutView
- Use hash mode (`createWebHashHistory()`)
- Implement route guards if needed

### 3.5 Configure Vuetify Theme
- Set up Vuetify plugin in `ui/src/main.ts`
- Load theme colors from `config.json`
- Configure default (light) theme
- Add dark mode support with alternate color palette (using `@media (prefers-color-scheme: dark)`)
- Set up responsive breakpoints

---

## Phase 4: Core UI Components

### 4.1 Layout Components
- **AppHeader.vue**: Navigation, logo, language selector
- **AppFooter.vue**: Footer with links, about info
- **App.vue**: Root layout with router-view

### 4.2 Book Components
- **BookCard.vue**: Card display for book (cover, title, author, rating)
- **BookGrid.vue**: Grid layout for book cards (responsive)
- **BookList.vue**: List layout for books (alternative view)
- **BookDetailInfo.vue**: Full book details page component

### 4.3 Author Components
- **AuthorCard.vue**: Card display for author (name, book count)
- **AuthorGrid.vue**: Grid layout for author cards (responsive)
- **AuthorDetailInfo.vue**: Full author details with their books

### 4.4 LCC Shelf Components
- **LCCShelfCard.vue**: Card display for LCC shelf (code, name, book count)
- **LCCShelfGrid.vue**: Grid layout for shelf cards (responsive)
- **LCCShelfDetailInfo.vue**: Full shelf details with books

### 4.5 Common Components
- **LanguageFilter.vue**: Filter books by language
- **FormatFilter.vue**: Filter books by available formats
- **SortControl.vue**: Sort books (popularity, title, etc.)
- **ErrorDisplay.vue**: Error message display
- **Note**: NO SearchBar component (rely on native ZIM search only)

### 4.6 Design Implementation
- Implement card-based design with modern spacing
- Use grid layout for book listings (responsive)
- Ensure proper contrast ratios (fix known contrast issues)
- Make all components responsive (mobile, tablet, desktop)
- Apply modern design principles (clean, minimal, accessible)

---

## Phase 5: View Implementation

### 5.1 HomeView
- Display book grid/list
- Implement pagination or infinite scroll
- Add language filter
- Add format filter
- Add sort controls (popularity, title)
- Show featured/random books (better than current "not-that-random" content)
- Move long text content to AboutView
- Handle loading states and errors

### 5.2 BookDetailView
- Display full book information
- Show author link
- Show format download links (HTML, EPUB, PDF)
- Show language information
- Show LCC shelf link
- Show cover image
- Display license information
- Show popularity/rating
- Handle loading states and errors

### 5.3 AuthorListView
- Display all authors in grid/list format
- Implement pagination or infinite scroll
- Show author name and book count
- Link to individual author detail pages
- Make authors easily discoverable
- Handle loading states and errors

### 5.4 AuthorDetailView
- Display author information
- Show all books by this author
- Make it clear user is viewing author's books (fix visibility issue)
- Link to individual books
- Handle loading states and errors

### 5.5 LCCShelfListView
- Display all LCC shelves in grid/list format
- Show shelf code, name, and book count
- Link to individual shelf detail pages
- Make LCC shelves more discoverable (fix "hidden" issue)
- Handle loading states and errors

### 5.6 LCCShelfDetailView
- Display LCC shelf information
- Show all books in shelf
- Make it clear user is viewing shelf's books
- Link to individual books
- Handle loading states and errors

### 5.7 AboutView
- Move homepage text content here
- Display project information
- Show statistics
- Provide context about Gutenberg project

---

## Phase 6: Python Integration

### 6.1 Clean Up Export Functions
Modify `scraper/src/gutenberg2zim/export.py`:
- Remove old `export_to_json_helpers()` function (no longer called)
- Remove old `.js` file generation code
- Update `export_skeleton()` to handle Vue.js dist export if needed
- Note: `generate_json_files()` already implemented in Phase 2

### 6.2 Add Vue.js Dist Export
Modify `scraper/src/gutenberg2zim/zim.py`:
- Add `export_vue_dist()` function
- Export `ui/dist/` folder to ZIM root
- Update `index.html` title if needed (similar to Youtube scraper)
- Ensure all Vue.js assets are included

### 6.3 Update ZIM Index
- Create HTML redirect pages for ZIM index (similar to Youtube)
- Ensure proper entry points for Vue.js app
- Handle hash routing correctly

### 6.4 Remove Old Template System
- Remove old Jinja2 book/author templates (no longer needed)
- Keep only templates needed for No-JS fallback (Phase 7)
- Clean up template generation code that's no longer used

---

## Phase 7: No-JavaScript Fallback

### 7.1 Create No-JS Templates
Create `scraper/src/gutenberg2zim/templates/noscript/`:
- `books.html` - Simple HTML listing of all books
- `book.html` - Simple HTML book detail page
- `author.html` - Simple HTML author page
- Use minimal styling (inline CSS acceptable for no-JS)
- Ensure all book formats are accessible
- Ensure native ZIM search works

### 7.2 Implement Fallback Detection
- Add `<noscript>` tag in `ui/index.html`
- Redirect to no-JS version if JavaScript disabled
- Ensure graceful degradation

### 7.3 Test No-JS Functionality
- Verify books listing works without JS
- Verify book detail pages work without JS
- Verify format downloads work without JS
- Verify native ZIM search works (title search, full-text search)
- Test with JavaScript disabled in browser

---

## Phase 8: Browser Compatibility & Testing

### 8.1 Configure Polyfills
- Add ResizeObserver polyfill (like Youtube scraper)
- Add any other required polyfills for target browsers
- Test with minimum browser versions:
  - Firefox >= 70
  - Chrome >= 80
  - Edge >= 80
  - ChromeAndroid >= 80
  - Safari >= 14
  - iOS >= 14

### 8.2 Test with Kiwix Readers
- Test with kiwix-serve (old browsers)
- Test with kiwix-js
- Test with kiwix-apple
- Test with kiwix-android
- Verify hash routing works correctly
- Verify JSON loading works correctly
- Verify native search works

### 8.3 Handle Inline JavaScript
- Monitor inline JS situation (wait-and-see approach per Benoit)
- Test ZIMs with old browsers and readers
- Document any issues found
- Address if problems arise (but don't preemptively fix)

---

## Phase 9: UI Improvements & Polish

### 9.1 Fix Known UI Issues
- **Contrast**: Improve color contrast ratios throughout UI
- **Responsiveness**: Ensure all views work on mobile/tablet/desktop
- **Design**: Modernize look and feel (cards, grid, spacing)
- **Homepage**: Move text to AboutView, show better content
- **Big Colored Areas**: Remove empty colored sections
- **Context Visibility**: Make it clear what user is viewing (author page, etc.)
- **LCC Shelves**: Make LCC shelves more discoverable

### 9.2 Implement Features
- Book favorites (if needed, per milestone)
- Language switching
- Format filtering
- Sorting options
- Pagination or infinite scroll
- Loading states
- Error handling

### 9.3 Performance Optimization
- Optimize JSON file sizes
- Implement lazy loading for images
- Optimize Vue.js bundle size
- Ensure fast initial load
- Optimize for low-memory devices

---

## Phase 10: Documentation

### 10.1 Contributing Documentation
Create `CONTRIBUTING.md`:
- Project structure overview
- Setup instructions for development
- Vue.js UI development guide
- Python scraper development guide
- JSON schema documentation
- Testing instructions
- Code style guidelines
- PR submission process

### 10.2 Vue.js UI Documentation
Add detailed Vue.js documentation:
- Component architecture
- State management (Pinia)
- Routing structure
- Data fetching patterns
- Styling guidelines
- Component usage examples

### 10.3 Python Scraper Documentation
Update Python documentation:
- JSON generation process
- Schema definitions
- Export functions
- Integration with Vue.js UI

### 10.4 README Updates
Update main `README.md`:
- Reflect new project structure (`scraper/` and `ui/`)
- Update build instructions
- Update development setup
- Add Vue.js UI information

---

## Phase 11: Issue Resolution & Milestone Completion

### 11.1 Close Issue #282
- Document JSON-based approach in issue #282
- Reference implementation details
- Get maintainer approval
- Close issue

### 11.2 Close Issue #286
- Create design mockup (similar to siemsie's approach)
- Share for review
- Get approval
- Close issue

### 11.3 Address Milestone 12 Issues
- Review all issues in milestone 12 (4.0.0)
- Implement missing features
- Fix bugs
- Ensure feature parity with current ZIM
- Open new issues for anything not implemented in first version

### 11.4 Test Full Workflow
- Build ZIM file with new UI
- Test all functionality
- Verify JSON files are correct
- Verify Vue.js UI works correctly
- Verify no-JS fallback works
- Verify native search works
- Test with all Kiwix readers

---

## Phase 12: Final Polish & Release Preparation

### 12.1 Code Review & Refactoring
- Review all code for quality
- Refactor as needed
- Ensure consistent code style
- Add missing comments/documentation
- Optimize performance

### 12.2 Final Testing
- Comprehensive testing of all features
- Cross-browser testing
- Cross-platform testing (Kiwix readers)
- Performance testing
- Accessibility testing

### 12.3 Update Changelog
- Document all changes
- List new features
- List bug fixes
- List breaking changes (if any)

### 12.4 Prepare for Release
- Ensure all tests pass
- Ensure documentation is complete
- Get final maintainer approval
- Merge to main branch
- Tag release (v4.0.0)

---

## Key Implementation Principles

1. **Start Fresh from Main**: Use `main` branch as base, reference `ui-revamp` only for ideas
2. **Follow Youtube Patterns**: Use Youtube scraper as reference for structure and patterns
3. **JSON-First Approach**: Generate JSON files, Vue.js consumes them
4. **Progressive Enhancement**: No-JS fallback for basic functionality
5. **Browser Compatibility**: Support minimum browser versions per libkiwix #1029
6. **Modern Design**: Cards, grid layout, modern spacing, good contrast
7. **No SearchBar**: Rely only on native ZIM search capabilities
8. **Documentation**: Comprehensive docs for contributors, especially Vue.js UI

---

## Dependencies & Tools

### Python Side
- `pydantic` - JSON schema validation and serialization
- camelCase helper function for JSON aliases
- `json` - JSON serialization
- Existing dependencies (beautifulsoup4, Jinja2, etc.)

### Vue.js Side
- `vue` (v3) - Frontend framework
- `vue-router` - Client-side routing (hash mode)
- `pinia` - State management
- `vuetify` (v3) - UI component framework
- `axios` - HTTP client for JSON fetching
- `typescript` - Type safety
- `vite` - Build tool
- `@vitejs/plugin-vue` - Vue plugin for Vite
- `@vitejs/plugin-legacy` - Browser compatibility

---

## Notes

- This roadmap is a living document and may be updated as implementation progresses
- Some phases may overlap or be done in parallel
- Issues may arise that require adjustments to the plan
- Regular communication with maintainers is essential
- Test frequently throughout implementation
- Keep `ui-revamp2` branch updated with `main` branch changes

