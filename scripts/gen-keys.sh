#!/usr/bin/env bash
# ==============================================================================
# gen-keys.sh - Generate RSA key pair for cgo-void-repo
#
# IMPORTANT: Private keys are NEVER stored in the Git repository tree!
# They are stored in ~/.local/share/cgo-void-repo/cgo-void-repo.rsa (mode 0600)
# Only PUBLIC keys are placed in repo-keys/ and docs/ (safe to commit & publish).
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_KEYS_DIR="${REPO_DIR}/repo-keys"
DOCS_DIR="${REPO_DIR}/docs"

# External private storage (outside git repository)
SECURE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/cgo-void-repo"
PRIVKEY="${SECURE_DIR}/cgo-void-repo.rsa"

PUBKEY_PEM="${REPO_KEYS_DIR}/cgo-void-repo.pem"
PUBKEY_PUB="${REPO_KEYS_DIR}/cgo-void-repo.rsa.pub"
DOCS_PUBKEY="${DOCS_DIR}/cgo-void-repo.pem"

mkdir -p "${SECURE_DIR}" "${REPO_KEYS_DIR}" "${DOCS_DIR}"
chmod 700 "${SECURE_DIR}"

if [ -f "${PRIVKEY}" ]; then
    echo "Notice: Private key already exists at: ${PRIVKEY}"
else
    echo "=== Generating 2048-bit RSA Private Key in secure local storage ==="
    echo "Private key location: ${PRIVKEY} (OUTSIDE git repository)"
    openssl genrsa -out "${PRIVKEY}" 2048
    chmod 600 "${PRIVKEY}"
fi

echo "--> Generating public key in PEM and PUB formats for repository and website..."
openssl rsa -in "${PRIVKEY}" -pubout -out "${PUBKEY_PEM}"
chmod 644 "${PUBKEY_PEM}"

cp "${PUBKEY_PEM}" "${PUBKEY_PUB}"
cp "${PUBKEY_PEM}" "${DOCS_PUBKEY}"

echo "--> Cryptography setup complete!"
echo "    [PRIVATE KEY] ${PRIVKEY} (Kept safely outside repository, mode 0600)"
echo "    [PUBLIC KEY]  ${PUBKEY_PEM} (Stored in repo-keys/ and docs/ for GitHub Pages)"
