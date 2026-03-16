# Gutenberg Offline

This scraper downloads the whole [Project Gutenberg](https://www.gutenberg.org) library and packages it into a [ZIM](https://openzim.org) file, a clean and user-friendly format for storing content for offline usage.

The ZIM file includes a modern, responsive Vue.js interface with features like:
- Browse books by title, author, or Library of Congress Classification (LCC) shelves
- Advanced filtering by language, format, and more
- Full-text search across all content
- Multilingual support with automatic language detection
- Responsive design that works on desktop and mobile devices
- No-JavaScript fallback for maximum compatibility

[![CodeFactor](https://www.codefactor.io/repository/github/openzim/gutenberg/badge)](https://www.codefactor.io/repository/github/openzim/gutenberg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![codecov](https://codecov.io/gh/openzim/gutenberg/branch/main/graph/badge.svg)](https://codecov.io/gh/openzim/gutenberg)
[![PyPI version shields.io](https://img.shields.io/pypi/v/gutenberg2zim.svg)](https://pypi.org/project/gutenberg2zim/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gutenberg2zim.svg)](https://pypi.org/project/gutenberg2zim/)
[![Docker](https://ghcr-badge.egpl.dev/openzim/gutenberg/latest_tag?label=docker)](https://ghcr.io/openzim/gutenberg)

## Getting Started

The recommended way to use the Gutenberg scraper is with Docker, which includes all dependencies pre-installed.

### Using Docker (Recommended)

**Run the scraper**:

```bash
docker run -v $(pwd)/output:/output ghcr.io/openzim/gutenberg gutenberg2zim
```

The `-v $(pwd)/output:/output` option mounts your local `output` folder to save the ZIM file.

**Note**: On Windows PowerShell, replace `$(pwd)` with `${PWD}`. Alternatively, use the full path: `-v C:\Users\YourName\output:/output`

**View available options**:

```bash
docker run ghcr.io/openzim/gutenberg gutenberg2zim --help
```

**Example with custom options**:

```bash
docker run -v $(pwd)/output:/output ghcr.io/openzim/gutenberg \
  gutenberg2zim -l en,fr -f pdf --books 100-200 --lcc-shelves all
```

This downloads English and French books with IDs 100-200 in PDF format, including LCC shelf pages.

### Using PyPI

Alternatively, install from PyPI:

```bash
pip install gutenberg2zim
gutenberg2zim --help
```

Note: You'll need to install system dependencies (zim-tools) separately. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Command-Line Options

```
-h --help                       Display this help message
--overwrite                     Overwrite existing ZIM file

-l --languages=<list>                Comma-separated language codes (ISO 639-1 or ISO 639-3)
-f --formats=<list>                  Comma-separated formats (epub, html, pdf, all)

-z --zim-file=<file>                 ZIM file output path
--zim-name=<name>                    ZIM name (metadata)
-t --zim-title=<title>               ZIM title
-n --zim-desc=<description>          ZIM description
-L --zim-long-desc=<description>     ZIM long description
--zim-languages=<languages>          ZIM language metadata

-b --books=<ids>                     Specific book IDs (comma-separated or ranges with dashes)
-c --concurrency=<nb>                Number of concurrent workers (default: 16)

--no-index                           Skip full-text index creation
--lcc-shelves=<shelves>              LCC shelf codes (comma-separated or 'all')
--primary-color=<color>              Primary UI color (hex format, e.g., #1976D2)
--secondary-color=<color>            Secondary UI color (hex format, e.g., #424242)

--publisher=<publisher>              Custom publisher name (default: openZIM)
--mirror-url=<url>                   Custom Gutenberg mirror URL
--output=<folder>                    Output folder (default: ./output)
--debug                              Enable verbose output
```

## Features

### User Interface
- **Modern Web Interface**: Fast, responsive single-page application with smooth navigation
- **Multiple View Modes**: Switch between grid and list views for books
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Dark/Light Theme**: Automatic theme switching based on system preferences
- **Customizable Colors**: Configure primary and secondary brand colors

### Content Organization
- **Browse by Books**: View all books with cover images, titles, and authors
- **Browse by Authors**: Explore authors with their complete bibliographies
- **LCC Shelves**: Browse books by Library of Congress Classification categories
- **Smart Pagination**: Efficient navigation through large collections

### Search & Discovery
- **Full-Text Search**: Search across all books, authors, and shelves
- **Quick Filters**: Find authors by name or shelves by code
- **Rich Search Results**: Search results include descriptions and metadata

### Filtering & Sorting
- **Language Filter**: Filter books by language (supports all Gutenberg languages)
- **Format Filter**: Filter by available formats (EPUB, HTML, PDF, TXT, MOBI)
- **Sort Options**: Sort by popularity (download count) or title
- **Sort Order**: Toggle between ascending and descending order

### Book Details
- **Comprehensive Metadata**: Title, subtitle, author, description, languages, license
- **Author Information**: Author name with birth/death years and lifespan
- **Popularity Rating**: Star rating based on download statistics
- **Download Counts**: Formatted download statistics
- **LCC Classification**: Link to Library of Congress Classification shelf
- **Multiple Formats**: Download books in available formats (EPUB, HTML, PDF, etc.)
- **Cover Images**: High-quality book cover images where available

### Internationalization
- **Multiple Languages**: Full UI translations for many languages
- **Automatic Detection**: Detects browser language and sets UI accordingly
- **Language Switcher**: Easy language selection from header menu
- **RTL Support**: Right-to-left layout support for Arabic, Hebrew, etc.

### Accessibility
- **No-JavaScript Fallback**: Complete HTML-only version for browsers without JavaScript
- **Semantic HTML**: Proper heading hierarchy and ARIA labels
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: ARIA labels and descriptions throughout
- **High Contrast**: Readable text with proper color contrast ratios

### Technical Features
- **ZIM Format**: Compressed, indexed format for offline usage
- **Full-Text Indexing**: Optional full-text search index within ZIM
- **Concurrent Processing**: Multi-threaded book processing for faster scraping
- **Custom Mirrors**: Support for custom Gutenberg mirror URLs
- **Docker Support**: Pre-built Docker images with all dependencies

## Contributing

We welcome contributions! Whether you want to:

- Add or improve UI translations
- Fix bugs or add features  
- Improve documentation
- Develop the Vue.js interface

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on setting up the development environment, code style, testing, and the pull request process.

Main coding guidelines follow the [openZIM Wiki](https://github.com/openzim/overview/wiki).

## Screenshots

![](https://raw.githubusercontent.com/openzim/gutenberg/main/pictures/screenshot_1.png)
![](https://raw.githubusercontent.com/openzim/gutenberg/main/pictures/screenshot_2.png)
![](https://raw.githubusercontent.com/openzim/gutenberg/main/pictures/screenshot_3.png)

## License

[GPLv3](https://www.gnu.org/licenses/gpl-3.0) or later, see
[LICENSE](LICENSE) for more details.
