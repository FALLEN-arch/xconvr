#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing xconvr and its conversion engines"

sudo apt update && sudo apt install -y ffmpeg imagemagick p7zip-full

# LibreOffice is needed for document conversion (docx, pdf, odt, ...).
# It is large (~500MB), so it is opt-in. Uncomment to install:
# sudo apt install -y libreoffice

# Debian 12 / Ubuntu 23.04+ block system-wide pip (PEP 668); fall back to pipx.
if ! pip install --user . ; then
    echo "==> pip refused the install (externally-managed environment); using pipx"
    sudo apt install -y pipx
    pipx install --force .
    pipx ensurepath
fi

echo
echo "==> Done. Try it:  xconvr photo.jpg photo.png"
echo "    If 'xconvr' is not found, add ~/.local/bin to your PATH."
