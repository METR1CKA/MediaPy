# AGENTS.md

Instructions for coding agents working in this repository.

## What this project is

A desktop app that downloads YouTube videos as MP4 or extracts the audio as
MP3, with a tkinter window for the URL, filename, destination folder and mode
(Video / Video+MP3 / Solo audio). Downloads run through yt-dlp; merging and
audio extraction run through ffmpeg.

## Stack and layout

- Python 3.12+, tkinter from the standard library, yt-dlp for downloads,
  ffmpeg (external binary) for merging and MP3 conversion.
- `main.py` — launcher only. `--selftest` runs the headless selftest before
  any tkinter import.
- `mediapy/gui.py` — tkinter window, Spanish widgets, worker thread + queue
  polling, download button disabled when ffmpeg is missing.
- `mediapy/app.py` — `Job`/`Progress`/`Mode` types and `run()`, the bridge
  between GUI and library, translating yt-dlp hooks into progress states.
- `mediapy/download.py` — yt-dlp orchestration and ffmpeg resolution
  (`resolve_ffmpeg`/`resolve_ffprobe` prefer the copy bundled in a frozen
  binary via `sys._MEIPASS`, then fall back to PATH).
- `mediapy/convert.py` — `to_mp3` via `ffmpeg -vn -acodec libmp3lame -q:a 2`.
- `mediapy/paths.py`, `mediapy/errors.py` — name sanitizing and the
  `MediaPyError` hierarchy.
- `mediapy/selftest.py` — headless check used by CI and frozen binaries.
- `tests/` — pytest suite.

## Dependencies

`yt-dlp` is the only runtime dependency and it should stay that way.
ffmpeg is required at runtime but never a Python dependency: source installs
take it from PATH, frozen binaries bundle a static copy. Do not add Pillow,
requests or anything else; yt-dlp already handles HTTP.

## Running and testing

```console
python -m pip install -e ".[dev]"
python -m pytest
```

- `python main.py` opens a blocking GUI window. **Never leave it running in a
  test or CI step.**
- `python main.py --selftest` runs headlessly: synthesizes a 0.5 s video with
  ffmpeg lavfi (native `mpeg4`/`aac` encoders, not libx264 — the bundled
  builds are LGPL), converts it to MP3, checks name validation, writes
  `selftest.log` in the working directory (windowed binaries have no console
  output) and exits 0/1. Needs ffmpeg on PATH in dev.
- GUI tests skip themselves without a display; CI runs them under
  `xvfb-run -a` with `python3-tk` installed.

## Behavior to preserve

- Temp downloads are written as `<stem>.tmp.<ext>` next to the destination
  and cleaned up in a `finally` block; stale `.tmp*` files must never be
  promoted over a fresh download.
- The final file replaces the destination atomically (`Path.replace`), so a
  failed download never destroys an existing file.
- One download at a time; the button stays disabled until it finishes.
- `ffmpeg_location` is passed to yt-dlp as the *directory* holding ffmpeg so
  ffprobe is found next to it.

## Packaging and releases

- Binaries are built with PyInstaller from `mediapy.spec` by
  `.github/workflows/release.yml`: a `tests` job (ubuntu-22.04, xvfb, ffmpeg)
  gates a `build` matrix that produces four assets —
  `mediapy-windows-amd64.exe`, `mediapy-macos-arm64.zip`,
  `mediapy-macos-intel.zip`, `mediapy-linux-amd64` — each verified with
  `--selftest` (which uses the bundled ffmpeg, so runners need none) before
  publishing on `v*` tags via softprops/action-gh-release. `workflow_dispatch`
  builds the same binaries as artifacts without releasing.
- The spec embeds static ffmpeg/ffprobe from `ffmpeg-bin/` (gitignored,
  filled per-OS by the workflow): gyan.dev essentials (Windows), BtbN
  linux64-lgpl (Linux), evermeet.cx (macOS Intel), descriptinc
  ffmpeg-ffprobe-static (macOS arm64). All are LGPL builds without libx264,
  which is fine: MediaPy only merges (`-c copy`) and encodes MP3
  (libmp3lame). Keep the selftest on native encoders for the same reason.
- PyInstaller is a build-time tool. Never add it to `pyproject.toml`.
- macOS Intel uses the `macos-15-intel` runner label (`macos-13` was retired
  in 2025 and its jobs queue forever). GitHub drops x86_64 images in August
  2027; after that, remove the Intel job.
- Keep Linux on `ubuntu-22.04` so the binary's glibc baseline stays at 2.35,
  and macOS pinned to `macos-15`/`macos-15-intel` instead of `macos-latest`
  (which migrated to macOS 26) for reproducible builds.

## Conventions

- **GUI strings are in Spanish; error messages raised from the library are
  in English.** Code identifiers and these agent docs are in English.
- No superfluous comments. A comment should state a constraint the code
  cannot show, such as why the selftest uses lavfi encoders instead of
  libx264.
- **Do not touch `.commandcode/`.** It is tooling configuration, not part of
  the app.
- Do not commit unless explicitly asked.
