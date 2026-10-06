#!/bin/bash
# SessionStart hook: make the full KDP build work in Claude Code cloud sessions.
#
# The cheap checks (build_kdp.py --master, audit_book.py) need only Python. The full
# interior PDF and the covers also need XeLaTeX, makeindex, the TeX Gyre and DejaVu
# fonts, and PyMuPDF, none of which a fresh cloud container has. This script installs
# whatever is missing and does nothing when everything is already present.
#
# pandoc and pdffonts (poppler-utils) are already in the cloud image.
#
# Runs in cloud sessions only. Synchronous on purpose: the build must not start
# before the toolchain exists. The container is ephemeral, so the first start of each
# new session pays the install cost; putting the same commands in the environment's
# Setup script (cached) is the faster alternative.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Debian/Ubuntu packages the build needs (see book/build/header.tex for the LaTeX
# packages and fonts it loads).
APT_PACKAGES=(
  texlive-xetex          # xelatex, fontspec, polyglossia
  texlive-latex-recommended
  texlive-latex-extra    # imakeidx, titlesec, emptypage, newunicodechar, ...
  texlive-lang-english   # hyphenation patterns for the American-English setting
  fonts-texgyre          # TeX Gyre Pagella (main font)
  fonts-dejavu-core      # DejaVu Serif (fallback for glyphs Pagella lacks)
)

privileged() {
  # Run a command as root, using sudo only when we are not already root.
  if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo "$@"; fi
}

install_missing_apt_packages() {
  local missing_packages=()
  local package
  for package in "${APT_PACKAGES[@]}"; do
    dpkg -s "$package" >/dev/null 2>&1 || missing_packages+=("$package")
  done
  if [ "${#missing_packages[@]}" -eq 0 ]; then
    return 0
  fi
  echo "Installing build packages: ${missing_packages[*]}" >&2
  export DEBIAN_FRONTEND=noninteractive
  privileged apt-get update -qq
  privileged apt-get install -y -qq --no-install-recommends "${missing_packages[@]}"
}

install_pymupdf_if_missing() {
  if python3 -c "import pymupdf" >/dev/null 2>&1; then
    return 0
  fi
  echo "Installing PyMuPDF" >&2
  # Ubuntu 24.04 marks the system Python as externally managed; retry with the
  # override if the plain install is refused.
  pip install --quiet pymupdf 2>/dev/null || pip install --quiet --break-system-packages pymupdf
}

verify_toolchain() {
  local tool
  for tool in pandoc xelatex makeindex pdffonts; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      echo "Build toolchain incomplete: $tool not found after install." >&2
      return 1
    fi
  done
  python3 -c "import pymupdf" >/dev/null 2>&1 || { echo "PyMuPDF import failed after install." >&2; return 1; }
}

install_missing_apt_packages
install_pymupdf_if_missing
verify_toolchain
