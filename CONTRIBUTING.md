
# Contributing to MARIHAR

Thank you for your interest in contributing to MARIHAR! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Development Guidelines](#development-guidelines)
- [Troubleshooting](#troubleshooting)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## License

MARIHAR is licensed under the GNU General Public License v3.0. The official license file is `LICENSE.md` at the root of the repository.

Note: `Docs/LICENSE.txt` contains user terms of service in French for end-users and is not the project's open source license.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- **yt-dlp**: Download from [github.com/yt-dlp/yt-dlp/releases](https://github.com/yt-dlp/yt-dlp/releases) (Windows: place in `Binaries/yt-dlp.exe`) or install via `pip install yt-dlp`
- **FFmpeg**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) (Windows: place ffmpeg.exe, ffplay.exe, ffprobe.exe in `Binaries/`)
- **Deno**: Download from [deno.land](https://deno.land/) (Windows: place deno.exe in `Binaries/`)

### Supported Platforms

**Windows** is the officially supported platform with bundled executables for yt-dlp, FFmpeg, and Deno.

**Linux and macOS** are not yet officially tested or supported. If you want to contribute support for these platforms, please open an issue first to discuss the implementation approach.

### External Dependencies Usage

MARIHAR uses the following external tools:

- **yt-dlp**: Downloads videos from various platforms. Download the Windows executable from [github.com/yt-dlp/yt-dlp/releases](https://github.com/yt-dlp/yt-dlp/releases) and place it in `Binaries/yt-dlp.exe`. On other platforms, ensure yt-dlp is installed and accessible in PATH.
- **FFmpeg**: Handles video/audio processing (format conversion, thumbnail embedding, subtitle processing). Download Windows executables from [ffmpeg.org](https://ffmpeg.org/download.html) and place them in `Binaries/` (ffmpeg.exe, ffplay.exe, ffprobe.exe). On other platforms, install FFmpeg and ensure it's in PATH.
- **Deno**: Used for JavaScript processing. Download the Windows executable from [deno.land](https://deno.land/) and place it in `Binaries/deno.exe`. On other platforms, install Deno from [deno.land](https://deno.land/).

See `Binaries/README.md` for detailed download instructions.

### Development Setup

1. Fork the repository
2. Clone your fork (replace `<your-username>` with your GitHub username):
   ```bash
   git clone https://github.com/<your-username>/MARIHAR.git
   cd MARIHAR
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix/macOS:
   source venv/bin/activate
   ```

4. Install Python dependencies:
   ```bash
   pip install -r Dependencies/requirements.txt
   ```

5. For desktop app development, install additional dependencies:
   ```bash
   pip install -r Dependencies/requirements_desktop.txt
   ```

6. Verify external dependencies:
   - On Windows: Verify executables exist in `Binaries/` folder (yt-dlp.exe, ffmpeg.exe, deno.exe)
   - On Unix/macOS: Ensure yt-dlp, ffmpeg, and deno are installed and accessible in PATH

7. Start the development server:
   ```bash
   python Backend/app.py
   ```

The application will be available at `http://localhost:5000`

> **Note**: The web application runs on Python 3.8+. However, building the desktop executable with `Installation/build_desktop.bat` requires **Python 3.12** installed at a known location (see the script).

## Project Structure

```
MARIHAR/
├── Backend/              # Python Flask application
│   ├── app.py          # Main Flask application
│   ├── desktop_app.py  # PyWebView desktop app
│   ├── desktop_app_browser.py # Browser-based desktop app
│   ├── splash_screen.py # Splash screen for desktop app
│   ├── ytdlp_service.py # yt-dlp service wrapper
│   └── ytdlp_wrapper.py # yt-dlp interface
├── Frontend/            # Web interface
│   ├── static/         # CSS, JS, images, videos
│   │   ├── css/        # Stylesheets
│   │   ├── js/         # JavaScript files
│   │   ├── translations/ # i18n JSON files (en, fr, it, mg)
│   │   └── *.mp4, *.jpg # Background and video assets
│   └── templates/      # HTML templates
│       └── index.html # Main application interface
├── Dependencies/       # Python requirements
│   ├── requirements.txt # Core dependencies (flask, flask-cors, yt-dlp)
│   └── requirements_desktop.txt # Desktop app dependencies (pywebview, pyinstaller)
├── Installation/       # Build and installation scripts
│   ├── build_desktop.bat # PyInstaller build script (Windows)
│   ├── marihar_installer.iss # Inno Setup installer script
│   └── start_server.bat # Quick server start script
├── Docs/              # Documentation
│   ├── README_UTILISATEUR.txt # User documentation (French)
│   ├── LICENSE.txt # License terms
│   └── licenses/ # Third-party license files
├── Assets/            # Desktop app assets
│   ├── Logo_marino.ico # Desktop app icon
│   └── Logo_marino.png # Desktop app logo
├── Binaries/          # External executables (Windows) - not in Git, see Binaries/README.md
│   ├── yt-dlp.exe # Video downloader (download from releases)
│   ├── ffmpeg.exe, ffplay.exe, ffprobe.exe # Multimedia tools (download from ffmpeg.org)
│   └── deno.exe # JavaScript runtime (download from deno.land)
│   └── README.md # Download instructions
├── CONTRIBUTING.md    # This file - contribution guidelines
├── LICENSE.md         # GPL v3.0 license
├── README.md          # Project README
└── .env.example       # Environment configuration template
```

## Contributing Guidelines

### Core Principles

**Preserve Existing Functionality**
- All changes must be targeted, justified, and tested
- Do not remove or modify existing behavior without a documented reason
- For significant changes, open a GitHub issue for discussion before implementation
- Maintain backward compatibility whenever possible
- If a breaking change is necessary, clearly document it in the PR description

**Documentation First**
- For major features, discuss the approach in an issue first
- Update documentation alongside code changes
- Include clear comments for complex logic
- Ensure all file paths and commands are verified against the actual project structure

### Adding New Features

1. Check existing issues and pull requests to avoid duplication
2. For significant features, open an issue to discuss the approach first
3. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. Make your changes following the existing code style
5. Test your changes thoroughly (see Testing section below)
6. Update documentation if needed
7. Ensure no existing functionality is broken

### Adding Translations

MARIHAR supports multiple languages through JSON translation files in `Frontend/static/translations/`.

To add a new language:

1. Create a new JSON file in `Frontend/static/translations/` (e.g., `es.json` for Spanish)
2. Copy the structure from existing translation files
3. Translate all keys
4. Update `Frontend/static/js/localization.js` to include the new language code
5. Test the translation in the application

### Bug Fixes

1. Search for existing issues describing the bug
2. If none exists, create a new issue with details
3. Create a branch for the fix:
   ```bash
   git checkout -b fix/bug-description
   ```

4. Implement the fix
5. Add tests if applicable
6. Verify the fix resolves the issue

## Pull Request Process

1. Ensure your code follows the project's style guidelines
2. Update documentation as needed
3. Add appropriate tests
4. Ensure all tests pass
5. Update the README if you've changed the user-facing functionality
6. Create a pull request with a clear description of your changes

### Pull Request Checklist

- [ ] Code follows project style
- [ ] Self-review of the code
- [ ] Commented complex code sections
- [ ] Updated documentation
- [ ] Added/updated tests
- [ ] All tests pass
- [ ] No new warnings generated
- [ ] Commit messages are clear and descriptive

## Reporting Issues

When reporting issues, please include:

- **Description**: A clear description of the problem
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Screenshots**: If applicable, add screenshots
- **Environment**:
  - OS: [e.g., Windows 10, macOS 13, Ubuntu 22.04]
  - Python version: [e.g., 3.11.0]
  - Browser: [e.g., Chrome 120, Firefox 121]

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and concise

### Commit Messages

Use clear and descriptive commit messages:

```
feat: add video format selection feature
fix: resolve download timeout issue
docs: update installation instructions
style: format JavaScript code
refactor: simplify ytdlp service
test: add unit tests for download manager
```

### Testing

MARIHAR does not currently have an automated test suite. All testing must be done manually using the following verification procedure:

#### Manual Testing Checklist

Before submitting a PR, verify these core functionalities:

1. **URL Analysis**
   - Test with a video URL from YouTube
   - Verify that video information is correctly displayed
   - Check that format options are available

2. **Format Selection**
   - Test selecting different video formats
   - Test selecting audio-only formats
   - Verify that the selected format is correctly applied

3. **Download Functionality**
   - Download a video with default settings
   - Download with custom format selection
   - Verify the downloaded file is playable

4. **Subtitle Support**
   - Download a video with subtitles
   - Test embedding subtitles
   - Verify subtitle language selection works

5. **Download Management**
   - Test pausing a download
   - Test resuming a paused download
   - Test canceling a download

6. **Translations**
   - Test language switching (en, fr, it, mg)
   - Verify all UI elements are translated
   - Check that translations persist across page reloads

7. **Desktop App** (if applicable)
   - Test the desktop application launches correctly
   - Verify window icon and title are displayed
   - Test that the web interface loads properly in the desktop window

8. **Regression Testing**
   - Ensure existing features still work as expected
   - Test with different video platforms (YouTube, etc.)
   - Verify no new warnings or errors in the console

#### Testing Commands

Start the development server:
```bash
python Backend/app.py
```

Test the desktop app:
```bash
python Backend/desktop_app.py
```

Test external tools:
```bash
# Test yt-dlp
Binaries/yt-dlp.exe --version

# Test FFmpeg
Binaries/ffmpeg.exe -version

# Test Deno
Binaries/deno.exe --version
```

## Troubleshooting

### Common Issues

**Python not found error:**
- Ensure Python 3.8+ is installed and added to PATH
- Use `python --version` to verify installation

**Dependencies installation fails:**
- Upgrade pip: `pip install --upgrade pip`
- Try installing with `--no-cache-dir` flag
- Check Python version compatibility with dependencies

**yt-dlp not working:**
- On Windows: Verify `Binaries/yt-dlp.exe` exists
- On Unix/macOS: Install via `pip install yt-dlp` or from source
- Update yt-dlp: `yt-dlp --update`

**FFmpeg not found:**
- On Windows: Verify executables exist in `Binaries/`
- On Unix/macOS: Install from package manager or [ffmpeg.org](https://ffmpeg.org/download.html)
- Verify installation: `ffmpeg -version`

**Desktop app won't start:**
- Ensure all dependencies are installed: `pip install -r Dependencies/requirements_desktop.txt`
- Check that PyWebView is properly installed
- Verify that all assets are in the correct locations

**Port 5000 already in use:**
- Change the port in the Flask configuration
- Or stop the process using port 5000

### Getting Help

- Check existing issues on GitHub
- Review the documentation in `Docs/`
- Ask questions in discussions or create a new issue
- Include detailed error messages and environment information

## Development Workflow

### Recommended Workflow

1. **Start**: Create an issue for the feature or bug you want to work on
2. **Discuss**: Get feedback from maintainers before starting large changes
3. **Branch**: Create a feature branch from the repository's default branch
4. **Develop**: Make your changes with small, focused commits
5. **Test**: Test thoroughly on your local environment
6. **Document**: Update relevant documentation
7. **PR**: Create a pull request with a clear description
8. **Review**: Address feedback from maintainers
9. **Merge**: Once approved, your PR will be merged

### Branch Naming Convention

- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/documentation-update` - Documentation changes
- `refactor/code-refactoring` - Code refactoring
- `test/test-addition` - Adding tests

## Questions?

Feel free to open an issue for questions or discussions about the project.

---

Thank you for contributing to MARIHAR!
