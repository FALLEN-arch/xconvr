# xconvr

A tiny universal file converter that routes to the best native engine already on your system.

- **Images** → ImageMagick (`magick`, falling back to `convert`)
- **Audio / Video** → FFmpeg (`ffmpeg`)
- **Archives** → 7-Zip (`7z`, falling back to `7zz`, then `7za`)
- **Documents** → LibreOffice (`soffice`, falling back to `libreoffice`)

## Install

```bash
git clone https://github.com/<you>/xconvr.git
cd xconvr
chmod +x install.sh
./install.sh
```

Manual install:

```bash
sudo apt update && sudo apt install -y ffmpeg imagemagick p7zip-full
# optional, for documents (~500MB):
# sudo apt install -y libreoffice
pip install --user .
# on distros that block system-wide pip (PEP 668), use pipx instead:
# pipx install .
```

Make sure `~/.local/bin` is on your `PATH`.

## Usage

```bash
# Images
xconvr photo.jpg photo.png
xconvr logo.svg logo.webp

# Audio
xconvr song.flac song.mp3
xconvr voice.wav voice.opus

# Video
xconvr clip.mov clip.mp4
xconvr clip.mp4 clip.gif

# Archives (targets: zip, 7z, tar)
xconvr backup.zip backup.7z

# Documents
xconvr report.docx report.pdf
```

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

## License

MIT. See [LICENSE](LICENSE).
