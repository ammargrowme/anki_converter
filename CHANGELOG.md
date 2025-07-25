# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-01

### Major Refactoring & Enhanced Windows Support

#### 🔄 Architecture Changes
- Split monolithic script into modular components for maintainability
- Created dual-version system: modular (`main.py`) + debug (`export_ucalgary_anki_debug.py`)
- Implemented comprehensive cross-platform setup script (`setup.sh`)

#### 🪟 Windows Compatibility Fixes
- **Fixed:** Setup script (`setup.sh`) failed in Windows Command Prompt and PowerShell
- **Improved:** Updated documentation to require Git Bash for Windows users
- **Added:** Windows-specific activation scripts (`.bat` and `.ps1`)
- **Tested:** Verified fresh installation from scratch on Windows systems

#### 📚 Documentation Overhaul
- Rewrote README with clear OS-specific instructions
- Added comprehensive troubleshooting section with Windows-specific solutions
- Created beginner-friendly quick start guides
- Added terminal requirements and common mistake warnings

#### 🔧 Setup & Installation Improvements
- **Auto-Detection:** Setup script automatically detects OS and installs appropriate dependencies
- **Dependency Management:** Automatic installation of missing components (Homebrew, Git, Chrome)
- **GUI Support:** Automatic tkinter installation and fallback handling
- **Verification:** Added `test_setup.py` for comprehensive system verification

#### ✨ Added
- **Collection Support:** Convert entire UCalgary Cards collections with multiple decks
- **Hierarchical Organization:** Smart deck structure creation (Collection → Deck → Patient)
- **Curriculum Detection:** Special handling for RIME-style collections
- **Enhanced Content Extraction:** Better table, image, and formatted content preservation
- **GUI File Dialogs:** Modern save dialogs with command-line fallback
- **Progress Tracking:** Real-time progress bars for collection processing

#### 🐛 Fixed
- Fixed virtual environment activation on Windows
- Resolved ChromeDriver compatibility issues
- Fixed image processing and sizing problems
- Corrected path handling across different operating systems

#### 📊 Testing & Validation
- Comprehensive testing on Windows 11, macOS, and Ubuntu Linux
- Fresh installation testing from GitHub clone
- End-to-end workflow validation with real UCalgary Cards data
- Cross-platform compatibility verification

## [1.0.0] - Initial Release

### Added
- Basic deck scraping from UCalgary Cards
- Single-file Python script
- Manual dependency installation
- Command-line only interface

### Limitations (Resolved in v2.0)
- Windows setup complexity
- Manual ChromeDriver management
- Limited error handling
- No collection support
- Basic content extraction
- Limited cross-platform support