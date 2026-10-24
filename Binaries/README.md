# Binaries - External Dependencies

This folder contains external executables required by MARIHAR. These are not included in the Git repository due to their size.

## Required Binaries

### yt-dlp
- **Purpose**: Video downloader from various platforms
- **Download**: [https://github.com/yt-dlp/yt-dlp/releases](https://github.com/yt-dlp/yt-dlp/releases)
- **Windows**: Download `yt-dlp.exe` and place it in this folder
- **Linux/macOS**: Install via `pip install yt-dlp` or download from releases
- **License**: Unlicense (see `../Docs/licenses/yt-dlp-LICENSE.txt`)

### FFmpeg
- **Purpose**: Video/audio processing (format conversion, thumbnail embedding, subtitle processing)
- **Download**: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
- **Windows**: Download and extract `ffmpeg.exe`, `ffplay.exe`, and `ffprobe.exe` to this folder
- **Linux/macOS**: Install via package manager (e.g., `apt install ffmpeg`, `brew install ffmpeg`)
- **License**: LGPL v2.1+ (see `../Docs/licenses/FFmpeg-LGPL-2.1.txt`)

### Deno
- **Purpose**: JavaScript runtime for processing
- **Download**: [https://deno.land/](https://deno.land/)
- **Windows**: Download `deno.exe` and place it in this folder
- **Linux/macOS**: Install via curl/sh script from deno.land
- **License**: MIT (see `../Docs/licenses/Deno-MIT.txt`)

## Alternative Installation

If you prefer not to download these manually, you can:

1. **yt-dlp**: Run `pip install yt-dlp` (will be installed in Python environment)
2. **FFmpeg**: Install via your system package manager
3. **Deno**: Install via the installer script from deno.land

The application will attempt to find these tools in the system PATH if they are not found in the `Binaries/` folder.

## Security Note

Always download these tools from their official sources:
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- FFmpeg: https://ffmpeg.org
- Deno: https://deno.land

Verify the checksums if available to ensure file integrity.
