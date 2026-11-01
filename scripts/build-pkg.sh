#!/usr/bin/env bash
# ==============================================================================
# build-pkg.sh - Build an xbps package using void-packages engine
# ==============================================================================
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <pkgname> [xbps-src flags...]"
    exit 1
fi

PKGNAME="$1"
shift || true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
GIT_BASE_DIR="$(cd "${REPO_DIR}/.." && pwd)"
VOID_PACKAGES_DIR="${GIT_BASE_DIR}/void-packages"
TEMPLATE_SRC="${REPO_DIR}/srcpkgs/${PKGNAME}"
TEMPLATE_DST="${VOID_PACKAGES_DIR}/srcpkgs/${PKGNAME}"

if [ ! -d "${TEMPLATE_SRC}" ] || [ ! -f "${TEMPLATE_SRC}/template" ]; then
    echo "ERROR: Template not found at ${TEMPLATE_SRC}/template"
    exit 1
fi

if [ ! -d "${VOID_PACKAGES_DIR}" ]; then
    echo "ERROR: void-packages not found at ${VOID_PACKAGES_DIR}. Run ./scripts/setup-env.sh first."
    exit 1
fi

# Lint template if xlint is installed
if command -v xlint >/dev/null 2>&1; then
    echo "--> Linting template with xlint..."
    xlint "${TEMPLATE_SRC}/template" || true
fi

# Copy template into void-packages (xbps-src treats symlinks as subpackages)
echo "--> Copying ${PKGNAME} into void-packages/srcpkgs..."
rm -rf "${TEMPLATE_DST}"
cp -a "${TEMPLATE_SRC}" "${TEMPLATE_DST}"

# Build package
echo "--> Building ${PKGNAME} with xbps-src..."
cd "${VOID_PACKAGES_DIR}"
./xbps-src pkg "$PKGNAME" "$@"

# Determine architecture
ARCH=$(xbps-uhelper arch 2>/dev/null || uname -m)

# Sync generated packages into local binpkgs directory
BINPKGS_DEST="${REPO_DIR}/binpkgs/${ARCH}"
mkdir -p "${BINPKGS_DEST}"

echo "--> Copying built package(s) to ${BINPKGS_DEST}..."
find "${VOID_PACKAGES_DIR}/hostdir/binpkgs" -type f -name "${PKGNAME}*.xbps" -exec cp -uv {} "${BINPKGS_DEST}/" \;

echo "=== Build finished for ${PKGNAME} ==="
echo "Package located in: ${BINPKGS_DEST}"
echo "To index and sign your repository, run: ./scripts/sign-repo.sh"
