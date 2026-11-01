#!/usr/bin/env bash
# ==============================================================================
# setup-env.sh - Setup development environment for cgo-void-repo
# ==============================================================================
set -euo pipefail

GIT_BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPO_DIR="${GIT_BASE_DIR}/cgo-void-repo"
VOID_PACKAGES_DIR="${GIT_BASE_DIR}/void-packages"

echo "=== [cgo-void-repo] Initializing Void Packaging Environment ==="
echo "Git Work Directory: ${GIT_BASE_DIR}"
echo "Custom Repo Dir:    ${REPO_DIR}"
echo "Void Packages Dir:  ${VOID_PACKAGES_DIR}"

# 1. Check for required host tools
echo "--> Checking host tools..."
MISSING_TOOLS=()
for tool in git openssl xbps-rindex xbps-install; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        MISSING_TOOLS+=("$tool")
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo "ERROR: Missing required tools: ${MISSING_TOOLS[*]}"
    echo "Run: sudo xbps-install -S ${MISSING_TOOLS[*]} xtools"
    exit 1
fi

# 2. Clone void-packages if not already present
if [ ! -d "${VOID_PACKAGES_DIR}/.git" ]; then
    echo "--> Cloning void-packages into ${VOID_PACKAGES_DIR}..."
    git clone --depth=1 https://github.com/void-linux/void-packages.git "${VOID_PACKAGES_DIR}"
else
    echo "--> void-packages already exists. Pulling latest changes..."
    git -C "${VOID_PACKAGES_DIR}" pull --rebase || true
fi

# 3. Configure void-packages/etc/conf if missing
if [ ! -f "${VOID_PACKAGES_DIR}/etc/conf" ]; then
    echo "--> Creating default ${VOID_PACKAGES_DIR}/etc/conf..."
    cat << 'EOF' > "${VOID_PACKAGES_DIR}/etc/conf"
# Configuration for xbps-src
XBPS_CHROOT_CMD=uchroot
XBPS_ALLOW_RESTRICTED=yes
XBPS_MAKEJOBS=$(nproc)
EOF
fi

# 4. Binary bootstrap masterdir
echo "--> Bootstrapping xbps-src masterdir..."
cd "${VOID_PACKAGES_DIR}"
./xbps-src binary-bootstrap

echo "=== Environment Setup Complete! ==="
echo "You can now build packages using: ./scripts/build-pkg.sh <pkgname>"
