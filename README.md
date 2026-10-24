



# MARIHAR - Video Downloader

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com/)

MARIHAR is a powerful video downloader application built with Python, Flask, and yt-dlp. It provides both a web interface and a desktop application for downloading videos from various platforms including YouTube, Facebook, Instagram, TikTok, and more.

## Demo Video

https://github.com/user-attachments/assets/2abde8f5-9a2e-4cd2-8a23-91c89cfdb6d4

## Platform Support

**Windows** is the officially supported platform. External executables (yt-dlp, FFmpeg, Deno) must be downloaded separately - see [Binaries/README.md](Binaries/README.md) for instructions.

**Linux and macOS** are not yet officially tested or supported. If you want to contribute support for these platforms, please open an issue first to discuss the implementation approach.

## Features

- **Multi-platform support**: Download videos from YouTube, Facebook, Instagram, TikTok, and other platforms
- **Format selection**: Choose from multiple video and audio formats
- **Subtitle support**: Download and embed subtitles in multiple languages
- **Dark/Light mode**: Modern UI with theme switching
- **Multi-language support**: Available in English, French, Italian, and Malagasy
- **Desktop application**: Native desktop app using PyWebView
- **Download management**: Pause, resume, and cancel downloads
- **Playlist support**: Download entire playlists
- **Section download**: Download specific sections of videos
- **Thumbnail embedding**: Embed video thumbnails in downloaded files

## Project Structure

```
MARIHAR/
├── Backend/              # Python Flask application
│   ├── app.py           # Main Flask application
│   ├── desktop_app.py   # PyWebView desktop app
│   ├── desktop_app_browser.py # Browser-based desktop app
│   ├── splash_screen.py # Splash screen
│   ├── ytdlp_service.py # yt-dlp service
│   └── ytdlp_wrapper.py # yt-dlp wrapper
├── Frontend/            # Web interface
│   ├── static/         # Static assets (CSS, JS, images, videos)
│   │   ├── css/        # Stylesheets
│   │   ├── js/         # JavaScript files
│   │   └── translations/ # i18n JSON files (en, fr, it, mg)
│   └── templates/      # HTML templates
├── Dependencies/       # Python requirements
│   ├── requirements.txt
│   └── requirements_desktop.txt
├── Installation/       # Build and installation scripts
├── Docs/              # Documentation
│   └── licenses/      # Dependency licenses
├── Assets/            # Desktop app assets (icons, logos)
├── Binaries/          # External executables (ffmpeg, yt-dlp, deno)
├── CONTRIBUTING.md     # Contribution guidelines
├── LICENSE.md         # GPL v3.0 license
└── .env.example       # Environment configuration template
```

## Quick Start

### Option 1: Windows Installer (Recommended for Windows Users)

For the easiest installation on Windows, download the pre-built installer:

1. Download `MARIHAR_Setup_v1.0.0.exe` from the [GitHub Releases](https://github.com/MariharRM/MARIHAR/releases) page *(link to be added after publication)*
2. Run the installer
3. Follow the installation wizard
4. Launch MARIHAR from the Start menu or desktop shortcut

The installer includes all required dependencies (yt-dlp, FFmpeg, Deno) and does not require Python installation.

### Option 2: Manual Installation (Developers)

#### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- **yt-dlp**: Download from [github.com/yt-dlp/yt-dlp/releases](https://github.com/yt-dlp/yt-dlp/releases) (Windows: place in `Binaries/yt-dlp.exe`) or install via `pip install yt-dlp`
- **FFmpeg**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) (Windows: place ffmpeg.exe, ffplay.exe, ffprobe.exe in `Binaries/`)
- **Deno**: Download from [deno.land](https://deno.land/) (Windows: place deno.exe in `Binaries/`)

See [Binaries/README.md](Binaries/README.md) for detailed download instructions.

#### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/MariharRM/MARIHAR.git
cd MARIHAR
```

2. Download required binaries (yt-dlp, FFmpeg, Deno) - see [Binaries/README.md](Binaries/README.md) for detailed instructions

3. Create a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r Dependencies/requirements.txt
```

5. Start the development server:
```bash
python Backend/app.py
```

The application will be available at `http://localhost:5000`

#### Desktop Application (Manual Installation)

For the desktop application, install additional dependencies:
```bash
pip install -r Dependencies/requirements_desktop.txt
python Backend/desktop_app.py
```

## Usage

1. Open the web interface at `http://localhost:5000`
2. Paste a video URL in the input field
3. Click "Analyze" to fetch video information
4. Select your preferred format and options
5. Click "Download" to start the download

## Configuration

### Custom yt-dlp Path

You can specify a custom path for yt-dlp:
- Go to Settings
- Enter the path to your yt-dlp executable
- The application will use this path for all downloads

### Download Location

By default, downloads are saved to your system's Downloads folder. You can change this in the settings.

## Supported Video Platforms

MARIHAR uses yt-dlp to download videos from hundreds of platforms, including:

- YouTube
- Facebook
- Instagram
- TikTok
- Twitter/X
- Vimeo

For the complete list of supported platforms, see [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

## Languages

MARIHAR supports the following languages:
- English (en)
- French (fr)
- Italian (it)
- Malagasy (mg)

The language is automatically detected from your browser settings, but you can manually change it in the interface.

## Building

### Windows Desktop Application

To build a standalone Windows executable:

1. **Download required binaries** (yt-dlp, FFmpeg, Deno) to the `Binaries/` folder - see [Binaries/README.md](Binaries/README.md)

2. **Build the executable**:
```bash
cd Installation
build_desktop.bat
```

This script will:
- Check Python installation
- Install required dependencies
- Verify all necessary files (including binaries in Binaries/)
- Build the executable using PyInstaller
- Create a `dist/MARIHAR/` folder with the application

For more details, see the build script comments or [CONTRIBUTING.md](CONTRIBUTING.md).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video downloader backend
- [FFmpeg](https://ffmpeg.org/) - Multimedia processing
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [PyWebView](https://pywebview.flowrl.com/) - Desktop GUI framework

## Disclaimer

This tool is for personal use only. Please respect the copyright laws and terms of service of the platforms you download from. The authors are not responsible for any misuse of this software.

## Documentation

For detailed user documentation (in French), see `Docs/README_UTILISATEUR.txt`.

For developer documentation, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Known Limitations

- **Platform Support**: Currently only Windows is officially supported with bundled executables
- **Download Speed**: Speed depends on your internet connection and the source platform
- **Format Availability**: Not all formats are available for all videos (depends on the source)
- **Subtitle Availability**: Subtitles may not be available for all videos or in all languages
- **Age-Gated Content**: Some platforms may require authentication for age-gated content

## Roadmap

- [ ] Add automated test suite
- [ ] Add Linux support
- [ ] Add macOS support
- [ ] Improve error handling and user feedback
- [ ] Add more language translations
- [ ] Add download queue management
- [ ] Add concurrent download support

## Support

For issues, questions, or contributions, please open an issue on [GitHub](https://github.com/MariharRM/MARIHAR/issues).

---

**Note**: This is an open-source project. If you find it useful, consider giving it a star on GitHub!


