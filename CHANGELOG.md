# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-07-25

### Added
- Comprehensive production-ready UCalgary Cards to Anki converter
- Complete documentation with version control
- Stable API and feature set for public release

### Changed
- Finalized user interface and experience
- Stabilized all major features for production use

## [0.9.0] - 2025-07-25

### Added
- Enhanced duplicate analysis in APKG Analyzer
- Exact duplicate detection for question-answer pairs
- Improved reporting and output formatting

### Fixed
- APKG analysis accuracy and reliability
- Duplicate detection algorithms

## [0.8.0] - 2025-07-24

### Added
- APKG analysis script (`analyze_apkg.py`) to inspect Anki deck contents
- Comprehensive deck structure and card content analysis
- Media file reporting (images, SVGs)
- Duplicate note detection and statistics
- Usage instructions for APKG analysis tools

### Changed
- Enhanced error handling in analysis functions
- Improved output formatting for analysis results

## [0.7.0] - 2025-07-24

### Added
- Modular architecture with separate Python modules
- Enhanced user experience with improved logging
- Streamlined code structure for better maintainability

### Changed
- Refactored monolithic script into modular components:
  - `main.py`: Main entry point
  - `auth.py`: Authentication handling
  - `deck_scraping.py`: Web scraping functionality
  - `content_extraction.py`: Content processing
  - `image_processing.py`: Image handling
  - `sequential_extraction.py`: Card processing logic
  - `anki_export.py`: Anki deck generation
  - `utils.py`: Shared utilities
- Cleaned up redundant print statements
- Improved Chrome options for better performance

### Removed
- Unnecessary debug output
- Redundant code sections

## [0.6.0] - 2025-07-24

### Added
- Comprehensive background extraction for tables, images, lists, charts, and rich text
- Enhanced content extraction capabilities
- Image filtering to remove portrait images while preserving medical content
- Sequential extraction methods for structured card processing
- Support for complex interactive elements from Cards

### Changed
- Improved HTML content parsing and formatting
- Enhanced image processing workflow
- Better preservation of table formatting and structure

## [0.5.0] - 2025-07-23

### Added
- Collection support for converting entire UCalgary Cards collections
- Hierarchical deck organization (Collection → Deck → Patient)
- Smart tagging system for cards by source deck
- Curriculum pattern detection for RIME-style collections
- Proper deck name extraction
- Multi-patient deck support

### Changed
- Enhanced deck structure creation
- Improved card organization and hierarchy
- Better handling of multiple cards per patient

## [0.4.0] - 2025-07-23

### Added
- GUI support for file dialogs across all platforms
- Modern "Save As" dialog functionality
- Success notifications and popups
- Enhanced user experience with GUI integration
- Cross-platform GUI compatibility (Windows, macOS, Linux)

### Changed
- Improved user interface from command-line only to GUI-enhanced
- Better file saving workflow
- Enhanced user feedback and notifications

### Fixed
- GUI support installation for different operating systems
- File dialog compatibility issues

## [0.3.0] - 2025-07-23

### Added
- Comprehensive README documentation
- Full setup guides for macOS, Ubuntu/Debian, and Windows
- Terminal editing instructions (Nano, Vi/Vim, Notepad)
- Detailed troubleshooting section
- Installation verification commands
- Environment variable configuration guides

### Changed
- Restructured documentation for better clarity
- Enhanced installation instructions
- Improved cross-platform compatibility guides

## [0.2.0] - 2025-07-22

### Added
- Automated setup script (`setup.sh`) for cross-platform installation
- Enhanced login functionality with improved error handling
- Credential management and secure storage
- Comprehensive system verification
- Multiple output formats (JSON, CSV, APKG)

### Changed
- Improved scraping logic for better content extraction
- Enhanced card template with better styling
- Better Chrome browser automation

### Fixed
- Login validation and error handling
- Network request reliability

## [0.1.0] - 2025-07-22

### Added
- Initial UCalgary Cards to Anki converter functionality
- Selenium-based web scraping for card extraction
- Basic Anki deck generation using genanki
- Login authentication for UCalgary Cards
- Support for multiple choice and free-text questions
- Interactive card elements preservation
- Basic image and content extraction

### Changed
- Implemented core conversion workflow
- Added progress tracking for card processing

## [0.0.1] - 2025-07-22

### Added
- Initial project structure and repository setup
- Basic project files and configuration
- Git repository initialization
- Initial README with project description

[1.0.0]: https://github.com/ammargrowme/anki_converter/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/ammargrowme/anki_converter/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/ammargrowme/anki_converter/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/ammargrowme/anki_converter/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/ammargrowme/anki_converter/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/ammargrowme/anki_converter/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/ammargrowme/anki_converter/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/ammargrowme/anki_converter/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ammargrowme/anki_converter/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ammargrowme/anki_converter/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/ammargrowme/anki_converter/releases/tag/v0.0.1