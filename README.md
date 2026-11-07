# xconvr

A tiny universal file converter. One command, two arguments: `xconvr <input> <output>`.

`xconvr` doesn't convert anything itself. It reads the file extensions, picks the right native engine, and runs it for you.

| Kind | Engine | Binaries tried, in order |
|---|---|---|
| Images | ImageMagick | `magick`, `convert` |
| Audio / Video | FFmpeg | `ffmpeg` |
| Archives | 7-Zip | `7z`, `7zz`, `7za` |
| Documents | LibreOffice | `soffice`, `libreoffice` |

## Features

- Single command for images, audio, video, archives, and documents
- No Python dependencies, standard library only
- Engines are looked up lazily, so a missing LibreOffice never breaks image conversion
- Missing engines produce a clear error with the exact `apt install` command
- Exits non-zero on any failure, so it works in scripts

## How it works

1. Checks that the input file exists.
2. Reads both extensions (case-insensitive, last extension only, so `a.tar.gz` counts as `gz`).
3. If they match, copies the file and stops.
4. Otherwise uses the first group that contains both formats, checked in this order: images, media, archives, documents.
5. Finds that group's engine on your system and runs it.

Note: `gif` is in both the image and media groups. `gif -> png` goes to ImageMagick, `mp4 -> gif` goes to FFmpeg.

## Supported formats

| Group | Formats |
|---|---|
| Images | jpg, jpeg, png, webp, bmp, tiff, tif, gif, heic, svg, ico, avif |
| Audio / Video | mp3, wav, flac, ogg, m4a, aac, opus, mp4, mkv, avi, mov, webm, gif, m4v, wmv, flv |
| Archives (read) | zip, 7z, tar, gz, tgz, bz2, xz, rar |
| Archives (write) | zip, 7z, tar |
| Documents | docx, pdf, odt, xlsx, pptx, txt, html, md |

Conversions only work **within** a group. `mp4 -> mp3` works (audio extraction), `jpg -> pdf` does not.

## Requirements

- Python 3.8 or newer
- Debian or Ubuntu for `install.sh`. On other systems, install the engines with your package manager.
- Only the engines for the conversions you actually need

## Install

```bash
git clone https://github.com/FALLEN-arch/xconvr.git
cd xconvr
chmod +x install.sh
./install.sh
```

Run it with `./install.sh` or `bash install.sh`, not `sh install.sh`. The script uses bash features that `sh` (dash) doesn't support.

### Manual install

```bash
sudo apt update && sudo apt install -y ffmpeg imagemagick p7zip-full
# optional, for documents (~500MB):
# sudo apt install -y libreoffice
pip install --user .
```

Debian 12 and Ubuntu 23.04+ block system-wide `pip`. Use `pipx` instead:

```bash
sudo apt install -y pipx
pipx install .
pipx ensurepath
```

Inside an active virtual environment, use plain `pip install .` (the `--user` flag doesn't work in a venv).

Make sure `~/.local/bin` is on your `PATH`.

### Run without installing

```bash
python3 xconvr.py photo.jpg photo.png
```

## Usage

```bash
# Images
xconvr photo.jpg photo.png
xconvr logo.svg logo.webp
xconvr photo.heic photo.jpg

# Audio
xconvr song.flac song.mp3
xconvr voice.wav voice.opus

# Video
xconvr clip.mov clip.mp4
xconvr clip.mp4 clip.gif
xconvr clip.mp4 audio.mp3

# Archives (output must be zip, 7z, or tar)
xconvr backup.zip backup.7z
xconvr data.tar.gz data.zip

# Documents
xconvr report.docx report.pdf
xconvr slides.pptx slides.pdf
xconvr notes.html notes.docx
```

Typical output (the engine path depends on your system):

```
$ xconvr photo.jpg photo.png
Converting jpg -> png
  $ /usr/bin/convert photo.jpg photo.png
[OK] Wrote photo.png
```

### Behavior to know about

- **Overwriting:** existing output files are replaced without asking.
- **Output folder:** it must already exist.
- **Extensions decide everything:** file contents are not inspected, so a mislabeled file is routed by its label.
- **Default settings:** engines run with default options. There are no quality, bitrate, or resolution flags.
- **Exit codes:** `0` on success, `1` on any failure (error text goes to stderr).

## Archives

Archive conversion extracts to a temporary folder, then repacks. Compressed tarballs (`.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`) are unwrapped twice, so the result holds your files rather than an inner `.tar`.

7-Zip can't create `rar`, `gz`, `bz2`, or `xz` archives, so those are rejected as targets. Reading `rar` may need an extra package on some systems (for example `p7zip-rar`).

## Documents

Documents go through LibreOffice in headless mode, using a throwaway profile so it works even if LibreOffice is already open.

- **Markdown:** `md` can't be a target.
- **PDF:** a PDF source can only become `docx`, `odt`, or `txt`, and layout fidelity is limited.
- **Unsupported pairs:** LibreOffice exits successfully even when it has no filter for a pair. `xconvr` detects the missing output file and reports an error.

## Why so small?

`xconvr` is not a codec library. It looks at the input and output extensions, picks the right group of formats, and shells out to the tool that already does that job best. Engines are looked up only when a conversion actually needs them, so a machine without LibreOffice can still convert images, audio, video, and archives.

## Engines

If an engine is missing, `xconvr` tells you which one and how to install it.

| Error message mentions | Install with |
|---|---|
| `Could not find engine 'magick'` | `sudo apt install imagemagick` |
| `Could not find engine 'ffmpeg'` | `sudo apt install ffmpeg` |
| `Could not find engine '7z'` | `sudo apt install p7zip-full` |
| `Could not find engine 'soffice'` | `sudo apt install libreoffice` |

## Troubleshooting

| Problem | Fix |
|---|---|
| `xconvr: command not found` | Add `~/.local/bin` to `PATH`, or run `python3 xconvr.py ...` |
| `externally-managed-environment` | Use `pipx install .` |
| `Illegal option -o pipefail` | Run `./install.sh` or `bash install.sh`, not `sh` |
| `Unsupported conversion: a -> b` | The formats are in different groups, or one isn't listed above |
| HEIC, AVIF, or SVG fails | Your ImageMagick build lacks that delegate. Check with `magick -list format` |
| `[FAIL] Engine exited with code N` | The engine's own error is printed above it; read that first |

## Development

```bash
pip install pytest
python3 -m pytest
```

## License

MIT. See [LICENSE](LICENSE).
