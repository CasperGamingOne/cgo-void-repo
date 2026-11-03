#!/usr/bin/env bash
# ==============================================================================
# build-pkg.sh - Modular package builder for cgo-void-repo
# Supports building standard generic x86_64 and optimized x86_64-v3 packages.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
GIT_BASE_DIR="$(cd "${REPO_DIR}/.." && pwd)"
VOID_PACKAGES_DIR="${GIT_BASE_DIR}/void-packages"

if [ ! -d "${VOID_PACKAGES_DIR}" ]; then
    echo "ERROR: void-packages not found at ${VOID_PACKAGES_DIR}. Run ./scripts/setup-env.sh first."
    exit 1
fi

# Ensure conf.x86_64-v3 exists in void-packages/etc/
mkdir -p "${VOID_PACKAGES_DIR}/etc"
if [ ! -f "${VOID_PACKAGES_DIR}/etc/conf.x86_64-v3" ]; then
    cat > "${VOID_PACKAGES_DIR}/etc/conf.x86_64-v3" << 'EOF'
XBPS_CHROOT_CMD=uchroot
XBPS_ALLOW_RESTRICTED=yes
XBPS_CFLAGS="-O3 -march=x86-64-v3 -pipe"
XBPS_CXXFLAGS="-O3 -march=x86-64-v3 -pipe"
XBPS_TARGET_CFLAGS="-march=x86-64-v3 -mtune=generic"
XBPS_TARGET_CXXFLAGS="${XBPS_TARGET_CFLAGS}"
EOF
fi

# Packages that are binary-only / noarch / proprietary (mirrored to both repos)
BINARY_ONLY_PACKAGES=(
    "antigravity"
    "antigravity-ide"
    "cgo-hello"
    "megasync"
)

is_binary_only() {
    local target="$1"
    for b in "${BINARY_ONLY_PACKAGES[@]}"; do
        if [ "$b" = "$target" ]; then
            return 0
        fi
    done
    return 1
}

sync_binary_packages() {
    echo "--> Synchronizing universal/binary packages into binpkgs/x86_64-v3..."
    mkdir -p "${REPO_DIR}/binpkgs/x86_64" "${REPO_DIR}/binpkgs/x86_64-v3"
    for b in "${BINARY_ONLY_PACKAGES[@]}"; do
        find "${REPO_DIR}/binpkgs/x86_64" -maxdepth 1 -type f -name "${b}-*.xbps" -exec cp -uv {} "${REPO_DIR}/binpkgs/x86_64-v3/" \; 2>/dev/null || true
    done
}

show_usage() {
    cat << EOF
Usage: $0 <pkgname> [OPTIONS] [xbps-src flags...]

Targets:
  <pkgname>            Build a specific package (e.g. noctalia, umbriel)
  --all                Build all packages in srcpkgs/ for generic x86_64
  --all-v3             Build all packages with x86-64-v3 optimizations
  --sync-binary        Mirror universal/binary packages into binpkgs/x86_64-v3

Options:
  --v3                 Build optimized x86_64-v3 variant into binpkgs/x86_64-v3/
  --both               Build both generic baseline and x86_64-v3 variants
  -h, --help           Show this help message

Examples:
  $0 noctalia          # Builds standard generic noctalia into binpkgs/x86_64/
  $0 noctalia --v3     # Builds optimized noctalia into binpkgs/x86_64-v3/
  $0 noctalia --both   # Builds both generic and v3 variants
  $0 --all-v3          # Builds all source packages for v3 and syncs binaries
EOF
    exit 1
}

if [ $# -lt 1 ]; then
    show_usage
fi

BUILD_V3=false
BUILD_BOTH=false
BUILD_ALL=false
BUILD_ALL_V3=false
SYNC_ONLY=false
TARGET_PKGS=()
EXTRA_ARGS=()

while [ $# -gt 0 ]; do
    case "$1" in
        --v3)
            BUILD_V3=true
            shift
            ;;
        --both)
            BUILD_BOTH=true
            shift
            ;;
        --all)
            BUILD_ALL=true
            shift
            ;;
        --all-v3)
            BUILD_ALL_V3=true
            shift
            ;;
        --sync-binary)
            SYNC_ONLY=true
            shift
            ;;
        -h|--help)
            show_usage
            ;;
        -*)
            EXTRA_ARGS+=("$1")
            shift
            ;;
        *)
            TARGET_PKGS+=("$1")
            shift
            ;;
    esac
done

if [ "${SYNC_ONLY}" = true ]; then
    sync_binary_packages
    echo "=== Universal package synchronization complete! ==="
    exit 0
fi

# Function to build a package variant
build_package_variant() {
    local pkg="$1"
    local variant="$2" # "generic" or "v3"
    local template_src="${REPO_DIR}/srcpkgs/${pkg}"
    local template_dst="${VOID_PACKAGES_DIR}/srcpkgs/${pkg}"

    if [ ! -d "${template_src}" ] || [ ! -f "${template_src}/template" ]; then
        echo "ERROR: Template not found at ${template_src}/template"
        return 1
    fi

    echo "===================================================================="
    echo "==> Building ${pkg} [Variant: ${variant}]"
    echo "===================================================================="

    if command -v xlint >/dev/null 2>&1; then
        echo "--> Linting template with xlint..."
        xlint "${template_src}/template" || true
    fi

    echo "--> Syncing ${pkg} into void-packages/srcpkgs..."
    rm -rf "${template_dst}"
    cp -a "${template_src}" "${template_dst}"

    cd "${VOID_PACKAGES_DIR}"
    local dest_dir
    if [ "${variant}" = "v3" ]; then
        dest_dir="${REPO_DIR}/binpkgs/x86_64-v3"
        if is_binary_only "${pkg}"; then
            echo "--> Package ${pkg} is universal binary/script. Building standard..."
            ./xbps-src pkg "${pkg}" "${EXTRA_ARGS[@]}"
        else
            echo "--> Compiling with x86_64-v3 optimization flags (-c x86_64-v3)..."
            ./xbps-src -c x86_64-v3 -f pkg "${pkg}" "${EXTRA_ARGS[@]}"
        fi
    else
        dest_dir="${REPO_DIR}/binpkgs/x86_64"
        echo "--> Compiling with generic baseline flags..."
        ./xbps-src pkg "${pkg}" "${EXTRA_ARGS[@]}"
    fi

    mkdir -p "${dest_dir}"
    echo "--> Collecting generated package into ${dest_dir}..."
    find "${VOID_PACKAGES_DIR}/hostdir/binpkgs" -maxdepth 1 -type f -name "${pkg}-*.xbps" -exec cp -uv {} "${dest_dir}/" \;

    # If it is binary-only, mirror to both directories
    if is_binary_only "${pkg}"; then
        mkdir -p "${REPO_DIR}/binpkgs/x86_64" "${REPO_DIR}/binpkgs/x86_64-v3"
        find "${dest_dir}" -maxdepth 1 -type f -name "${pkg}-*.xbps" -exec cp -uv {} "${REPO_DIR}/binpkgs/x86_64/" \;
        find "${dest_dir}" -maxdepth 1 -type f -name "${pkg}-*.xbps" -exec cp -uv {} "${REPO_DIR}/binpkgs/x86_64-v3/" \;
    fi

    echo "=== Build finished for ${pkg} [${variant}] ==="
}

# Resolve packages to build
PACKAGES_TO_BUILD=()

if [ "${BUILD_ALL}" = true ] || [ "${BUILD_ALL_V3}" = true ]; then
    for dir in "${REPO_DIR}/srcpkgs"/*; do
        # Subpackage templates are symlinks to their parent template.
        [ -L "$dir" ] && continue
        if [ -d "$dir" ] && [ -f "$dir/template" ]; then
            PACKAGES_TO_BUILD+=("$(basename "$dir")")
        fi
    done
else
    PACKAGES_TO_BUILD=("${TARGET_PKGS[@]}")
fi

if [ ${#PACKAGES_TO_BUILD[@]} -eq 0 ]; then
    echo "No packages specified to build."
    show_usage
fi

echo "Packages queued for build (${#PACKAGES_TO_BUILD[@]}): ${PACKAGES_TO_BUILD[*]}"

for p in "${PACKAGES_TO_BUILD[@]}"; do
    if [ "${BUILD_ALL_V3}" = true ]; then
        build_package_variant "$p" "v3"
    elif [ "${BUILD_BOTH}" = true ]; then
        build_package_variant "$p" "generic"
        build_package_variant "$p" "v3"
    elif [ "${BUILD_V3}" = true ]; then
        build_package_variant "$p" "v3"
    else
        build_package_variant "$p" "generic"
    fi
done

# Always ensure universal binary packages are synced into v3 repo
sync_binary_packages

echo ""
echo "=== All requested package builds completed! ==="
echo "To index and sign repositories, run: ./scripts/sign-repo.sh"
