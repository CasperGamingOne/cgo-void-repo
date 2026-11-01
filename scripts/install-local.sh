#!/usr/bin/env bash
# ==============================================================================
# install-local.sh - Configure this host to use local cgo-void-repo
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BINPKGS_DIR="${REPO_DIR}/binpkgs"
PUBKEY="${REPO_DIR}/keys/cgo-void-repo.rsa.pub"
XBPS_D_CONF="/etc/xbps.d/50-cgo-void-repo.conf"
XBPS_KEYS_DIR="/var/db/xbps/keys"

echo "=== Installing cgo-void-repo for local system use ==="

if [ ! -f "${PUBKEY}" ]; then
    echo "ERROR: Public key not found at ${PUBKEY}. Run ./scripts/gen-keys.sh first."
    exit 1
fi

# Detect architecture
ARCH=$(xbps-uhelper arch 2>/dev/null || uname -m)
LOCAL_REPO_PATH="${BINPKGS_DIR}"
if [ -d "${BINPKGS_DIR}/${ARCH}" ]; then
    LOCAL_REPO_PATH="${BINPKGS_DIR}/${ARCH}"
fi

echo "--> Generating ${XBPS_D_CONF} (requires sudo)..."
sudo tee "${XBPS_D_CONF}" > /dev/null << EOF
# Local cgo-void-repo configuration
repository=${LOCAL_REPO_PATH}
EOF

echo "--> Installing public key to ${XBPS_KEYS_DIR} (requires sudo)..."
sudo install -m 644 "${PUBKEY}" "${XBPS_KEYS_DIR}/cgo-void-repo.pem"

echo "--> Synchronizing repository index..."
sudo xbps-install -S

echo "=== Local repository installation complete! ==="
echo "You can now install custom packages via: sudo xbps-install <pkgname>"
