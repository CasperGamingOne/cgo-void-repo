# AGENT.md - Autonomous Operational Playbook for `cgo-void-repo`

> **Scope**: This document guides AI agents (and human maintainers) through creating, managing, building, signing, and publishing the custom Void Linux package repository **`cgo-void-repo`** for **CasperGamingOne**.

---

## 1. Environment & Workspace Topology

All Git projects are dedicated to a clean, isolated root directory under the user's home folder.

| Path | Purpose |
| :--- | :--- |
| `~/git` (`/home/caspergamingone/git`) | **Dedicated Git Workspace** for all git projects. |
| `~/git/cgo-void-repo` | **Custom Repository Root** (templates, scripts, keys, release metadata). |
| `~/git/void-packages` | Upstream Void Linux packaging engine (`xbps-src`). |
| `~/git/cgo-void-repo/srcpkgs` | Source package definitions / templates authored by CasperGamingOne. |
| `~/git/cgo-void-repo/binpkgs` | Built binary `.xbps` packages and repository index files. |
| `~/git/cgo-void-repo/keys` | Cryptographic public keys and key generation tools (private keys git-ignored). |
| `~/git/cgo-void-repo/scripts` | Automation scripts for building, indexing, signing, and installing. |
| `/etc/xbps.d/50-cgo-void-repo.conf` | Host system XBPS repository configuration. |
| `/var/db/xbps/keys/` | Host system directory for trusted repository signing keys. |

---

## 2. Agent Identity & Role

When operating in this repository, you are:
1. An expert **Void Linux Systems Engineer** and **XBPS Package Maintainer**.
2. Careful and disciplined: always validate templates with `xlint`, protect private keys, and test packages prior to release.
3. Aware of the user's environment: Void Linux x86_64 with `xtools`, `xbps-install`, and `xbps-rindex` available.

---

## 3. End-to-End Operational Lifecycle

### Phase 1: Toolchain & Build Engine Setup
Void packages are compiled using the `xbps-src` containerized builder from `void-packages`.

1. **Verify Prerequisites**:
   Ensure `git`, `xtools`, `openssl`, and `xbps-rindex` are present on the host:
   ```bash
   sudo xbps-install -S git xtools openssl
   ```
2. **Bootstrap the Void Build Engine**:
   Execute the setup script from `~/git/cgo-void-repo`:
   ```bash
   ./scripts/setup-env.sh
   ```
   This script:
   - Clones `void-linux/void-packages` into `~/git/void-packages` (if not present).
   - Writes `XBPS_ALLOW_RESTRICTED=yes` and parallel makejobs into `void-packages/etc/conf`.
   - Runs `./xbps-src binary-bootstrap` to populate the `masterdir` chroot.

---

### Phase 2: Authoring Package Templates
Templates are stored in `~/git/cgo-void-repo/srcpkgs/<pkgname>/template`.

#### Required Template Anatomy:
```bash
# Template file for '<pkgname>'
pkgname=<pkgname>
version=<version>
revision=1
build_style=<gnu-configure|cmake|meson|python3-pep517|cargo|meta|etc.>
short_desc="<Concise description under 72 chars>"
maintainer="CasperGamingOne <caspergamingone@users.noreply.github.com>"
license="<SPDX license identifier, e.g. MIT, GPL-3.0-or-later>"
homepage="<https://...>"
distfiles="<https://.../v${version}.tar.gz>"
checksum=<sha256 hash from xgensum or sha256sum>

# Build & install hooks (if build_style does not handle it automatically):
# do_build() { ... }
# do_install() { ... }
```

#### Packaging Rules for the Agent:
1. **Linting**: Always lint new or edited templates using `xlint`:
   ```bash
   xlint srcpkgs/<pkgname>/template
   ```
2. **Checksum Generation**: For remote distfiles, fetch the sha256 checksum:
   ```bash
   xgensum -f srcpkgs/<pkgname>/template
   # or manually:
   curl -sL "<distfile_url>" | sha256sum
   ```
3. **Dependencies**:
   - `hostmakedepends`: Tools required on host during build time (e.g. `pkg-config`, `cmake`, `ninja`, `cargo`).
   - `makedepends`: Libraries/headers required to compile (e.g. `openssl-devel`, `libX11-devel`).
   - `depends`: Runtime dependencies that XBPS cannot automatically detect via `shlib-provides`.

---

### Phase 3: Building Packages
To build a package, run:
```bash
./scripts/build-pkg.sh <pkgname>
```

#### What this does:
1. Symlinks `~/git/cgo-void-repo/srcpkgs/<pkgname>` into `~/git/void-packages/srcpkgs/<pkgname>`.
2. Executes `./xbps-src pkg <pkgname>` inside `void-packages`.
3. Copies the resulting `.xbps` package from `void-packages/hostdir/binpkgs/` into `~/git/cgo-void-repo/binpkgs/<arch>/`.

#### Rebuilding or Cleaning:
- Force clean build:
  ```bash
  cd ~/git/void-packages && ./xbps-src -f pkg <pkgname>
  ```
- Purge build directory:
  ```bash
  cd ~/git/void-packages && ./xbps-src clean <pkgname>
  ```

---

### Phase 4: Key Management & Repository Signing

Void Linux validates repository integrity using RSA key pairs.

1. **Key Generation**:
   ```bash
   ./scripts/gen-keys.sh
   ```
   - Private key: `keys/cgo-void-repo.rsa` (chmod 600, ignored by git).
   - Public key: `keys/cgo-void-repo.rsa.pub` (safe for distribution).

2. **Index and Sign Packages**:
   ```bash
   ./scripts/sign-repo.sh
   ```
   This command executes:
   ```bash
   # Add all binary packages to index
   xbps-rindex -a binpkgs/<arch>/*.xbps
   # Sign index repodata
   xbps-rindex --sign --signedby "CasperGamingOne Void Repository" --privkey keys/cgo-void-repo.rsa binpkgs/<arch>
   # Clean obsolete package versions from index
   xbps-rindex -c binpkgs/<arch>
   ```

> [!CAUTION]
> **NEVER** commit `keys/cgo-void-repo.rsa` to git. Ensure it matches `.gitignore`.

---

### Phase 5: Distribution & Hosting Strategies

#### Strategy A: GitHub Releases (Recommended & Compatible with existing user repos)
Compatible with the repository structure used by existing third-party Void repos like `gsr4xbps` and `sonicde-void`.
1. Push package templates and git tag `v<version>` to GitHub.
2. The included GitHub Actions workflow (`.github/workflows/build-and-release.yml`) builds, signs (using secret `RSA_PRIVATE_KEY`), and uploads packages + `<arch>-repodata` to the GitHub Release.
3. Users configure:
   ```text
   repository=https://github.com/caspergamingone/cgo-void-repo/releases/latest/download
   ```

#### Strategy B: Local Development Repository
Test immediately on this machine without internet hosting:
```bash
./scripts/install-local.sh
```
This sets up `/etc/xbps.d/50-cgo-void-repo.conf` with:
```text
repository=/home/caspergamingone/git/cgo-void-repo/binpkgs/<arch>
```

---

### Phase 6: Client Configuration

To enable `cgo-void-repo` on any Void Linux machine:

1. **Install Public Key**:
   ```bash
   sudo cp keys/cgo-void-repo.rsa.pub /var/db/xbps/keys/cgo-void-repo.pem
   ```
2. **Add Repo Config** (`/etc/xbps.d/50-cgo-void-repo.conf`):
   ```text
   repository=https://github.com/caspergamingone/cgo-void-repo/releases/latest/download
   ```
3. **Synchronize & Install**:
   ```bash
   sudo xbps-install -S
   sudo xbps-install <pkgname>
   ```

---

## 4. Troubleshooting Playbook for the Agent

| Issue | Cause | Agent Remediation |
| :--- | :--- | :--- |
| `SHA256 mismatch` | Distfile upstream changed or invalid hash | Run `xgensum -f srcpkgs/<pkg>/template` to refresh checksum. |
| `XBPS_ALLOW_RESTRICTED` | Package has restricted license | Ensure `XBPS_ALLOW_RESTRICTED=yes` exists in `void-packages/etc/conf`. |
| `SONAME / shlib provider missing` | Missing runtime dependency library | Search provider: `xlocate <libname.so>` and add pkg to `makedepends`. |
| `Unregistered package in repository` | `xbps-rindex` has not registered binary | Run `./scripts/sign-repo.sh` to update `<arch>-repodata`. |
| `RSA signature verification failed` | Public key missing in `/var/db/xbps/keys/` | Copy `keys/cgo-void-repo.rsa.pub` to `/var/db/xbps/keys/cgo-void-repo.pem`. |

---

## 5. Agent Operational Directives

1. **Always use the dedicated git directory**:
   Keep repository code strictly inside `/home/caspergamingone/git/cgo-void-repo`.
2. **Run linting before proposing builds**:
   Execute `xlint` on any modified template before invoking `./scripts/build-pkg.sh`.
3. **Preserve modularity**:
   Keep build automation in `scripts/`, templates in `srcpkgs/`, configs in `etc/`, keys in `keys/`.
4. **Interactive Confirmation for Sudo**:
   Inform the user before executing commands that modify `/etc/xbps.d` or `/var/db/xbps/keys`.
