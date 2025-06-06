# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
as of 2.0.0.

## [2.2.0] - 2025-06-06

### Added

- Add support for `--debug` flag to output debug logs
- Add support for `-L` long_description flags
- Add request timeout for util.py (#197)
- Add Booklanguage DB to support multi-languages books (#218)
- Add RTL support to UI (#248)
- Add language filter to combobox for requested languages (#249)

### Changed

- Simplify Gutenberg scraping (no more rsync, no more fallback URLs / filenames) (#97)
- Prefer EPUB 3 to EPUB (#235)
- Do not force the presence of PDF format for all books (#160)
- Replace usage of os.path and path.py with pathlib.Path (#195)
- Finalize ZIM metadata title translations and multilingual detection (#229)
- Replaced magic number with named constant and clarified comment regarding book ID URL rules (#196)
- Replace print and pp calls with logger (#192)
- Update to Python3.13
- Update python-scraperlib to 5.1.1 and dependencies (#188)
- Rename Book DB table fields (#199)
- Update multi-resolution favicons (#165)

### Fixed

- Fix regression on missing HTML content (#219)
- Simplify the logger name (used `gutenberg2zim` instead of `gutenberg2zim.constants`) (#206)
- Add retry logic on book downloads (#254)
- Fix UI and navigation glitches on bookshelves (#262)
- Remove dependencies on binaries + buggy pngquant (#257)

## [2.1.1] - 2024-01-17

### Added

- `Publisher` ZIM metadata can now be customized at CLI (#210)

### Changed

- `Publisher` ZIM metadata default value is changed to `openZIM` intead of `Kiwix` (#210)

### Fixed

- Do not fail if temporary directory already exists (#207)
- Typo in `Scraper` ZIM metadata (#212)
- Adapt to hatchling v1.19.0 which mandates packages setting (#211)

## [2.1.0] - 2023-08-18

### Changed

- Fixed regression with broken filters on on multiple-languages ZIM (#175)
- Fixed `Name` metadata that was incorrectly including period (#177)
- Fixed `Language` metadata (and filename) for multilang ZIMs (#174)
- Using zimscraperlib 2.1.0
- Using localized Title and Description metadata (#148)
- Fixed regression with epub files stored as `application/zip` (#181)
- Adopt Python bootstrap conventions, especially migration to hatch instead of setuptools and Github CI Workflows adaptations (#190)
- Removed inline Javascript in HTML files (#145)

### Fixed

- Support single quotes in author names (#162)
- Migrated to another Gutenberg server (#187)
- Removed useless file languages_06_2018 (#180)

### Removed

- Removed Datatables JS code from repository, fetch online now (#116)
- Dropped Python 2 support (#191)

## [2.0.0] - 2023-02-20

### Added

- Porgress report using `--stats-filename`

### Changed

- Updated dependencies, including zimscraperlib (2.0)
- Now creating no-namespace ZIM with Illustration
- Fixed/reduced sqlite timeouts
- Better handling of rsync'd list of URLs
- RDF files are not extracted to disk anymore (faster on selections)
- Remove all Urls from DB before processing rsync'd ones
- Fixed --concurrency short flag (now `-c`)
- Docker image now uses python3.11
- DB don't use a separate Format table anymore

### Removed

- Dependency to zimwriterfs binary.
- `-r`/`--rdf-folder` flag: rdf not extracted to disk anymore
- `--export`: HTML files not written to disk first anymore
- `--dev`: idem
- Binaries from docker images: jpegoptim, pngquant, gifsicle, zip, curl, p7zip

## [1.1.9]

- Added portuguese translation
- Changed mirror used as aleph doesn't contain all files anymore

## [1.1.8]

- Changed links to accomodate zimwriterfs 2.1.0-2 (#144)

## [1.1.7]

- Using --zstd option with zimwriterfs

## [1.1.6]

- removed duplicate dependencies
- Added tag \_category:gutenberg which was missing
- docker-only release with updated zimwriterfs (2.1.0-1)

## [1.1.5]

- simplified home page results on smaller screen sizes
- added bookshelves mode option
- added title search option (doesn't scale!)
- fixed setup_urls on macos
- add s3 based optimization cache
- do not allow checking other URLs if downloaded from s3
- remove book from DB if not downloaded in any format
- better handling of downloaded/optimized files
- More informative and better displayed logs
- switched to python3.6+
- docker image now based on bionic
- docker image only writes onto /output
- using zimwriterfs 1.3.10-4
- using zimscraperlib
- fixed some articles missing titles
- zimwriterfs error on all-langs now stops whole process
- safer extraction of rdf-files.tar

## [1.1.4]

- Fixed broken setup.py (moved LICENSE file)
- Added changelog
- fixed running on macOS
- fixed running with PY3
- defaulting to PY3 on Docker

## [1.1.3]

- Added ability to set an output folder for --one-language-one-zim
- removed unused -m parameter
- Added --tags
- Added --scraper
- Harmonized ZIM name and filename with other projects
- Removed format list in filename, title and description if all formats selected
- Changed dockerfile to use source instead of pypi
- Fixed --one-language-one-zim not completing
- Fixed IntegrityError on thread colision
- fixed python3 compatibility
- cleaned-up code (tab/space mix)

## [1.1.2]

- initial version
