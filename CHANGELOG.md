# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-07-24

### Added
- Collection support for converting entire UCalgary Cards collections with multiple decks
- Hierarchical organization with smart deck structure creation (Collection → Deck → Patient)
- Curriculum detection with special handling for RIME-style collections
- Enhanced content extraction for better table, image, and formatted content preservation
- GUI file dialogs with modern save dialogs and command-line fallback
- Real-time progress bars for collection processing
- Comprehensive cross-platform setup script (`setup.sh`)
- Dual-version system: modular (`main.py`) + debug (`export_ucalgary_anki_debug.py`)
- Windows-specific activation scripts (`.bat` and `.ps1`)
- Auto-detection setup script that automatically detects OS and installs appropriate dependencies
- Automatic installation of missing components (Homebrew, Git, Chrome)
- GUI support with automatic tkinter installation and fallback handling
- System verification with `test_setup.py` for comprehensive system validation
- Comprehensive troubleshooting section with Windows-specific solutions
- Beginner-friendly quick start guides
- Terminal requirements and common mistake warnings

### Changed
- Split monolithic script into modular components for maintainability
- Rewrote README with clear OS-specific instructions
- Major refactoring for enhanced Windows support
- Updated documentation to require Git Bash for Windows users

### Fixed
- Virtual environment activation on Windows
- ChromeDriver compatibility issues
- Image processing and sizing problems
- Path handling across different operating systems
- Setup script (`setup.sh`) failures in Windows Command Prompt and PowerShell

### Security
- Enhanced dependency management with automatic verification

## [0.9.0] - 2025-07-20

### Added
- Comprehensive testing on Windows 11, macOS, and Ubuntu Linux
- Fresh installation testing from GitHub clone
- End-to-end workflow validation with real UCalgary Cards data
- Cross-platform compatibility verification

### Changed
- Improved error handling and recovery mechanisms

## [0.8.0] - 2025-07-15

### Added
- Enhanced documentation with detailed troubleshooting guides
- Cross-platform compatibility improvements

### Fixed
- Various Windows-specific installation issues
- Browser driver management improvements

## [0.7.0] - 2025-07-10

### Added
- Progress tracking and user feedback improvements
- Better error messaging and logging

### Changed
- Improved code organization and structure

## [0.6.0] - 2025-07-05

### Added
- Image processing capabilities for portrait detection
- Enhanced content extraction features

### Fixed
- Content formatting issues in generated Anki cards

## [0.5.0] - 2025-06-30

### Added
- GUI components for better user interaction
- File dialog support

### Changed
- Improved user interface design

## [0.4.0] - 2025-06-25

### Added
- Web scraping enhancements
- Better authentication handling

### Fixed
- Session management issues

## [0.3.0] - 2025-06-20

### Added
- Selenium-based browser automation
- ChromeDriver integration

### Changed
- Moved from basic HTTP requests to full browser automation

## [0.2.0] - 2025-06-15

### Added
- Anki deck generation using genanki library
- Basic card formatting and styling

### Changed
- Improved card content extraction

## [0.1.0] - 2025-06-10

### Added
- Basic deck scraping from UCalgary Cards
- Single-file Python script implementation
- Manual dependency installation process
- Command-line interface
- Core HTTP and web scraping functionality

### Security
- Basic authentication for UCalgary Cards access

[1.0.0]: https://github.com/ammargrowme/anki_converter/releases/tag/v1.0.0
[0.9.0]: https://github.com/ammargrowme/anki_converter/releases/tag/v0.9.0
[0.8.0]: https://github.com/ammargrowme/anki_converter/releases/tag/v0.8.0
[0.7.0]: https://github.com/ammargrowme/anki_converter/releases/tag/v0.7.0
[0.6.0]: https://github.com/ammargrowme/anki_converter/releases/tag/v0.6.0
[0.5.0]: https://github.com/ammargrowme/anki_converter/releases/tag/v0.5.0
[0.4.0]: https://github.com/ammargrowme/anki_converter/releases/tag/v0.4.0
[0.3.0]: https://github.com/ammargrowme/anki_converter/releases/tag/v0.3.0
[0.2.0]: https://github.com/ammargrowme/anki_converter/releases/tag/v0.2.0
[0.1.0]: https://github.com/ammargrowme/anki_converter/releases/tag/v0.1.0