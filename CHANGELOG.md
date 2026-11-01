# Changelog

All notable changes to MARIHAR will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub issue forms (Bug Report, Feature Request, Question) and blank-issue template.
- Pull request template with manual-testing checklist.
- Project wiki (Home, Installation, Getting Started, User Guide, Update Manager,
  Configuration, Supported Platforms, Developer Guide, Troubleshooting & FAQ,
  Contributing & License).
- Application screenshot gallery and demo video section in the README.
- Expanded, code-verified project Roadmap in the README.

### Changed
- Project structure trees harmonized between README and CONTRIBUTING.

## [1.0.0] - 2026-10-25

First public release. Windows installer: `MARIHAR_Setup_v1.0.0.exe`.

### Added
- **Desktop application** (PyWebView window with animated splash screen) and a
  browser-based launch alternative, served by a local Flask server
  (`127.0.0.1:5000`) — fully local, no account required.
- **Downloads by URL or by title search** — non-URL input runs a yt-dlp search
  (top 20 results) with a selectable search platform.
- **Playlist support** — list entries and pick which videos to download.
- **Format selection** — video quality tables and audio-only extraction
  (MP3/M4A) powered by FFmpeg.
- **Subtitles** — selection/embedding options with in-app subtitle preview.
- **Advanced download options** — time-section downloads (`--download-sections`)
  and thumbnail embedding (`--embed-thumbnail`).
- **Download management** — live progress cards with speed and ETA, pause,
  resume, cancel and cancel-all, built-in yt-dlp console output.
- **Local download history** — last 100 operations, individually or fully
  clearable (`%LOCALAPPDATA%\MARIHAR\history.json`).
- **Custom output folder** — native folder picker, sensible default to the
  system Downloads folder.
- **Update Manager** — auto-update the bundled yt-dlp binary from the
  interface (`yt-dlp -U`), set a custom yt-dlp path, or reset to default.
- **Interface personalization** — Dark/Light themes and 4 UI languages
  (French, English, Italian, Malagasy), plus a built-in 5-step user guide
  with FAQ.
- **Bundled toolchain** — installer ships Python, FFmpeg, Deno and yt-dlp so
  no extra tools are needed on Windows 10/11 (64-bit).
- **Documentation & licensing** — README, CONTRIBUTING guide, French
  end-user guide, supported-platforms list, GPL-3.0 license and the complete
  set of third-party license texts (Flask, flask-cors, pywebview, PyInstaller,
  yt-dlp, FFmpeg, Deno, Python).

[Unreleased]: https://github.com/MariharRM/MARIHAR/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/MariharRM/MARIHAR/releases/tag/v1.0.0
