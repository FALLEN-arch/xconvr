"""xconvr: a thin router that shells out to native conversion engines.

Images         -> ImageMagick (magick, falling back to convert)
Audio / Video  -> FFmpeg (ffmpeg)
Archives       -> 7-Zip (7z, falling back to 7zz, then 7za)
Documents      -> LibreOffice (soffice, falling back to libreoffice)
Each engine is resolved lazily, only when its handler is invoked.
"""
import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

IMAGE_FORMATS = {
    "jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif",
    "gif", "heic", "svg", "ico", "avif",
}
MEDIA_FORMATS = {
    "mp3", "wav", "flac", "ogg", "m4a", "aac", "opus",
    "mp4", "mkv", "avi", "mov", "webm", "gif", "m4v", "wmv", "flv",
}
ARCHIVE_FORMATS = {"zip", "7z", "tar", "gz", "tgz", "bz2", "xz", "rar"}
DOC_FORMATS = {"docx", "pdf", "odt", "xlsx", "pptx", "txt", "html", "md"}
# 7-Zip cannot create rar/gz/bz2/xz archives
ARCHIVE_TARGETS = {"zip", "7z", "tar"}

# Single-stream compressed formats that usually wrap an inner .tar
_COMPRESSED_STREAMS = {"gz", "tgz", "bz2", "xz"}
# LibreOffice cannot export Markdown; PDF import only yields text-like docs
_DOC_UNEXPORTABLE = {"md"}
_PDF_TARGETS = {"docx", "odt", "txt"}
_DOC_EXPORT_FILTER = {"txt": "txt:Text"}

_APT_PACKAGES = {
    "magick": "imagemagick",
    "ffmpeg": "ffmpeg",
    "7z": "p7zip-full",
    "soffice": "libreoffice",
}


def resolve_engine(name, *fallbacks):
    """Locate an engine executable, trying bundled dir, script dir, then PATH."""
    candidates = (name,) + tuple(fallbacks)
    search_dirs = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        search_dirs.append(Path(meipass))
    search_dirs.append(Path(__file__).resolve().parent)

    for directory in search_dirs:
        for cand in candidates:
            local = directory / cand
            if local.is_file() and os.access(str(local), os.X_OK):
                return str(local)
    for cand in candidates:
        found = shutil.which(cand)
        if found:
            return found

    package = _APT_PACKAGES.get(name, name)
    raise FileNotFoundError(
        "Could not find engine '{}' (tried: {}). Install it with: "
        "sudo apt install {}".format(name, ", ".join(candidates), package)
    )


def _ext(path):
    return Path(path).suffix.lower().lstrip(".")


def _run(cmd, cwd=None):
    print("  $ " + " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True, cwd=cwd)


def _convert_image(in_path, out_path):
    engine = resolve_engine("magick", "convert")
    _run([engine, in_path, out_path])


def _convert_media(in_path, out_path):
    engine = resolve_engine("ffmpeg")
    _run([engine, "-y", "-i", in_path, out_path])


def _convert_archive(src, dst, in_path, out_path):
    if dst not in ARCHIVE_TARGETS:
        raise ValueError(
            "Cannot create .{} archives (supported targets: {})".format(
                dst, ", ".join(sorted(ARCHIVE_TARGETS))
            )
        )
    engine = resolve_engine("7z", "7zz", "7za")
    in_abs = Path(in_path).resolve()
    out_abs = Path(out_path).resolve()

    with tempfile.TemporaryDirectory() as tmp, \
            tempfile.TemporaryDirectory() as tmp_inner:
        _run([engine, "x", "-y", "-o" + tmp, in_abs])
        content_dir = tmp
        entries = list(Path(tmp).iterdir())
        if not entries:
            raise ValueError("Archive is empty: {}".format(in_path))

        # .tar.gz / .tgz / .tar.bz2 / .tar.xz extract to a single inner .tar;
        # unwrap it so the repacked archive holds the real files.
        if (src in _COMPRESSED_STREAMS and len(entries) == 1
                and entries[0].is_file()
                and entries[0].suffix.lower() == ".tar"):
            _run([engine, "x", "-y", "-o" + tmp_inner, entries[0]])
            if not any(Path(tmp_inner).iterdir()):
                raise ValueError("Archive is empty: {}".format(in_path))
            content_dir = tmp_inner

        # `7z a` appends to an existing archive; start from a clean slate.
        if out_abs.exists():
            out_abs.unlink()
        _run([engine, "a", "-y", out_abs, "*"], cwd=content_dir)


def _convert_document(src, dst, in_path, out_path):
    if dst in _DOC_UNEXPORTABLE:
        raise ValueError("LibreOffice cannot export .{} files".format(dst))
    if src == "pdf" and dst not in _PDF_TARGETS:
        raise ValueError(
            "PDF can only be converted to: {}".format(
                ", ".join(sorted(_PDF_TARGETS))
            )
        )

    engine = resolve_engine("soffice", "libreoffice")
    out_abs = Path(out_path).resolve()
    outdir = out_abs.parent
    target = _DOC_EXPORT_FILTER.get(dst, dst)

    # Throwaway profile so this works even if LibreOffice is already open.
    with tempfile.TemporaryDirectory() as profile:
        cmd = [engine, "-env:UserInstallation=" + Path(profile).as_uri(),
               "--headless"]
        if src == "pdf":
            cmd.append("--infilter=writer_pdf_import")
        cmd += ["--convert-to", target, "--outdir", outdir,
                Path(in_path).resolve()]
        _run(cmd)

    produced = outdir / (Path(in_path).stem + "." + dst)
    # LibreOffice exits 0 even when it has no filter for the pair.
    if not produced.exists():
        raise RuntimeError(
            "LibreOffice did not produce {} (unsupported conversion "
            "{} -> {}?)".format(produced.name, src, dst)
        )
    if produced != out_abs:
        produced.replace(out_abs)


def convert(in_path, out_path):
    if not Path(in_path).exists():
        raise FileNotFoundError("Input not found: {}".format(in_path))
    src, dst = _ext(in_path), _ext(out_path)
    if not src or not dst:
        raise ValueError("Both input and output need a file extension")

    if src == dst:
        shutil.copy2(in_path, out_path)
        print("[OK] Same format \u2014 copied to {}".format(out_path))
        return

    print("Converting {} -> {}".format(src, dst))

    if src in IMAGE_FORMATS and dst in IMAGE_FORMATS:
        _convert_image(in_path, out_path)
    elif src in MEDIA_FORMATS and dst in MEDIA_FORMATS:
        _convert_media(in_path, out_path)
    elif src in ARCHIVE_FORMATS and dst in ARCHIVE_FORMATS:
        _convert_archive(src, dst, in_path, out_path)
    elif src in DOC_FORMATS and dst in DOC_FORMATS:
        _convert_document(src, dst, in_path, out_path)
    else:
        raise ValueError("Unsupported conversion: {} -> {}".format(src, dst))

    print("[OK] Wrote {}".format(out_path))


USAGE = """Usage: xconvr <input> <output>

Examples:
  Image:    xconvr photo.jpg photo.png
            xconvr logo.svg logo.webp
  Audio:    xconvr song.flac song.mp3
            xconvr voice.wav voice.opus
  Video:    xconvr clip.mov clip.mp4
            xconvr clip.mp4 clip.gif
  Archive:  xconvr backup.zip backup.7z
            xconvr data.tar data.zip
  Document: xconvr report.docx report.pdf
            xconvr slides.pptx slides.pdf
"""


def main():
    if len(sys.argv) != 3:
        print(USAGE)
        sys.exit(1)
    try:
        convert(sys.argv[1], sys.argv[2])
    except subprocess.CalledProcessError as e:
        print("[FAIL] Engine exited with code {}".format(e.returncode),
              file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("[FAIL] {}".format(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
