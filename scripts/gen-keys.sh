#!/usr/bin/env bash
# ==============================================================================
# gen-keys.sh - Generate RSA key pair for signing cgo-void-repo packages
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
KEYS_DIR="${REPO_DIR}/keys"
PRIVKEY="${KEYS_DIR}/cgo-void-repo.rsa"
PUBKEY="${KEYS_DIR}/cgo-void-repo.rsa.pub"

mkdir -p "${KEYS_DIR}"

if [ -f "${PRIVKEY}" ]; then
    echo "Notice: Key pair already exists at ${PRIVKEY}"
    echo "Public key: ${PUBKEY}"
    exit 0
fi

echo "=== Generating 2048-bit RSA key pair for cgo-void-repo ==="
openssl genrsa -out "${PRIVKEY}" 2048
chmod 600 "${PRIVKEY}"

openssl rsa -in "${PRIVKEY}" -pubout -out "${PUBKEY}"
chmod 644 "${PUBKEY}"

echo "--> Generated:"
echo "    Private Key: ${PRIVKEY} (mode 0600 - DO NOT COMMIT)"
echo "    Public Key:  ${PUBKEY} (safe to share/commit)"
echo "Done!"
