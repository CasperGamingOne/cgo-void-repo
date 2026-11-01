#!/usr/bin/env bash
# ==============================================================================
# sign-repo.sh - Index and sign local xbps repository
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BINPKGS_DIR="${REPO_DIR}/binpkgs"
PRIVKEY="${REPO_DIR}/keys/cgo-void-repo.rsa"
SIGNED_BY="${SIGNED_BY:-CasperGamingOne Void Repository <caspergamingone>}"

if [ ! -d "${BINPKGS_DIR}" ]; then
    echo "ERROR: ${BINPKGS_DIR} does not exist. Build packages first."
    exit 1
fi

if [ ! -f "${PRIVKEY}" ]; then
    echo "Notice: Signing key not found at ${PRIVKEY}. Generating one now..."
    "${SCRIPT_DIR}/gen-keys.sh"
fi

echo "=== Indexing and Signing cgo-void-repo ==="

# Find all architecture directories in binpkgs (or binpkgs itself if flat)
ARCH_DIRS=$(find "${BINPKGS_DIR}" -mindepth 1 -maxdepth 1 -type d)
if [ -z "${ARCH_DIRS}" ]; then
    ARCH_DIRS="${BINPKGS_DIR}"
fi

for dir in ${ARCH_DIRS}; do
    echo "--> Processing repository directory: ${dir}"
    
    # 1. Add packages to repository index
    PKGS=$(find "${dir}" -maxdepth 1 -name "*.xbps" ! -name "*-repodata*")
    if [ -n "${PKGS}" ]; then
        echo "--> Registering packages with xbps-rindex -a..."
        # xbps-rindex expects packages as arguments
        cd "${dir}"
        xbps-rindex -a ./*.xbps
    else
        echo "No .xbps packages found in ${dir}."
        continue
    fi

    # 2. Sign repository index
    echo "--> Signing repodata with private key..."
    xbps-rindex --sign --signedby "${SIGNED_BY}" --privkey "${PRIVKEY}" "${dir}"

    # 3. Clean obsolete packages from index
    echo "--> Cleaning obsolete packages with xbps-rindex -c..."
    xbps-rindex -c "${dir}" || true
done

echo "=== Repository indexing and signing complete! ==="
