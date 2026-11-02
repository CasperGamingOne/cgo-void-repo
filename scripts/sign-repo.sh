#!/usr/bin/env bash
# ==============================================================================
# sign-repo.sh - Index and sign local xbps repository
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BINPKGS_DIR="${REPO_DIR}/binpkgs"

# Secure private key location (outside git repo)
SECURE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/cgo-void-repo"
PRIVKEY="${CGO_PRIVKEY:-${SECURE_DIR}/cgo-void-repo.rsa}"
SIGNED_BY="${SIGNED_BY:-CasperGamingOne Void Repository <caspergamingone>}"

if [ ! -d "${BINPKGS_DIR}" ]; then
    echo "ERROR: ${BINPKGS_DIR} does not exist. Build packages first with ./scripts/build-pkg.sh"
    exit 1
fi

if [ ! -f "${PRIVKEY}" ]; then
    echo "Notice: Private signing key not found at ${PRIVKEY}."
    echo "Generating new keypair now via scripts/gen-keys.sh..."
    "${SCRIPT_DIR}/gen-keys.sh"
fi

echo "=== Indexing and Signing cgo-void-repo ==="
echo "Using Private Key: ${PRIVKEY}"

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
        cd "${dir}"
        xbps-rindex -a ./*.xbps
    else
        echo "No .xbps packages found in ${dir}."
        continue
    fi

    # 2. Sign individual binary package archives (.sig2)
    echo "--> Signing binary packages with private key..."
    rm -f ./*.sig2
    xbps-rindex --sign-pkg --privkey "${PRIVKEY}" ./*.xbps

    # 3. Sign repository index
    echo "--> Signing repodata with private key..."
    xbps-rindex --sign --signedby "${SIGNED_BY}" --privkey "${PRIVKEY}" "${dir}"

    # 4. Clean obsolete packages from index
    echo "--> Cleaning obsolete packages with xbps-rindex -c..."
    xbps-rindex -c "${dir}" || true
done

echo "=== Repository indexing and signing complete! ==="
