# AGENT.md - Autonomous Operational Playbook for `cgo-void-repo`

> **Scope**: This document guides AI agents (and human maintainers) through creating, managing, building, signing, and deploying the custom Void Linux package repository **`cgo-void-repo`** for **CasperGamingOne**, hosted publicly on **GitHub** with a **GitHub Pages** website.

---

## 1. Environment, Workspace & Architecture

All Git projects are dedicated to a clean, isolated root directory under the user's home folder.

| Path | Purpose | Public / Git Tracked |
| :--- | :--- | :--- |
| `~/git` (`/home/caspergamingone/git`) | **Dedicated Git Workspace** for all git projects | N/A (Workspace root) |
| `~/git/cgo-void-repo` | **Custom Repository Root** (public GitHub repo) | Yes (Git tracked) |
| `~/git/cgo-void-repo/docs` | **GitHub Pages Website & Web Distribution** | Yes (`index.html`, `.nojekyll`, styles, public key) |
| `~/git/cgo-void-repo/repo-keys` | **Public RSA Keys** (`.pem` / `.pub` / `.plist`) | Yes (Public keys only) |
| `~/git/cgo-void-repo/srcpkgs` | **Source Package Templates** (xbps-src definitions) | Yes (Git tracked) |
| `~/git/cgo-void-repo/scripts` | **Automation Scripts** (build, sign, setup, deploy) | Yes (Git tracked) |
| `~/git/cgo-void-repo/binpkgs` | **Local Binary Packages** (local `.xbps` cache) | No (Git ignored) |
| `~/.local/share/cgo-void-repo` | **Secure Local Private Key Storage** | **NEVER in Git** (`0700` dir, `0600` key) |
| `~/git/void-packages` | Upstream Void Linux packaging engine (`xbps-src`) | Separate Git repo |

---

## 2. Cryptography & Secrets Directives (STRICT POLICY)

Because this repository is public on GitHub and hosted via GitHub Pages:

> [!CAUTION]
> **NO SECRETS OR PRIVATE KEYS IN THE REPOSITORY TREE**
> 1. **Do NOT create a "SECRETS" directory inside the git tree.**
> 2. **Local Private Key**: Kept exclusively in `~/.local/share/cgo-void-repo/cgo-void-repo.rsa` with mode `0600`.
> 3. **CI/CD Private Key**: Provided exclusively as an encrypted GitHub Actions secret (`RSA_PRIVATE_KEY`). The workflow writes it to a temporary runner file, signs repodata, and immediately unlinks it.
> 4. **Public Keys**: `repo-keys/cgo-void-repo.pem` and `docs/cgo-void-repo.pem` contain only public keys. These are 100% safe to commit and distribute.

---

## 2.1 Personal Brand Identity & Ownership Directives

> [!IMPORTANT]
> **BRANDING AND LOGOS ARE STRICTLY PERSONAL**
> - The software, templates, and scripts in this repo are open-source under the MIT License.
> - **Branding is exempt**: The creator names **CasperGamingOne**, **Games4Everyone**, the logos, avatar, banner, and assets under `docs/assets/` belong solely to CasperGamingOne.
> - When generating templates, documentation, or new web assets, preserve and respect the creator's personal identity. Brand assets and creator names must never be licensed under open-source terms.

---

## 3. System Ecosystem Awareness: XLibre Integration

The maintainer's host system runs **XLibre** alongside Void Linux:

* **XLibre Repository**: `https://github.com/xlibre-void/xlibre/releases/latest/download`
* **XLibre Key**: `/var/db/xbps/keys/00:ca:42:57:c9:c0:9a:ec:94:b4:7d:97:e5:a9:aa:1e.plist`
* **Installed Packages**: `xlibre`, `xlibre-xserver`, XLibre input & video drivers (`xf86-video-*`, `xf86-input-*`).
* **Coexisting Repos**: `cherrybtw/gsr4xbps`, `sonicde-void`, and Void Linux official repositories.

### Agent Packaging Rules for XLibre Compatibility:
1. When packaging X11 applications, depend on generic development libraries (e.g. `makedepends="libX11-devel libXext-devel libXrandr-devel"`), not specific xorg server implementations.
2. If creating display-related tools or window manager components, ensure compatibility with XLibre server interfaces.
3. Follow the clean public repository pattern modeled by `xlibre-void` (public key in `repo-keys/`, release binaries published online).

---

## 4. GitHub Pages Dual Role (Website + Static XBPS Repository)

The `docs/` directory acts as both:
1. **Interactive Web Front**: A modern landing page (`docs/index.html`, `style.css`, `app.js`) explaining setup steps with 1-click command copying, package search, and compatibility badges.
2. **Static XBPS Repository**: The `.nojekyll` file ensures GitHub Pages serves raw files (`<arch>-repodata`, `*.xbps`, `cgo-void-repo.pem`) directly over HTTPS.

Clients can configure:
```text
repository=https://caspergamingone.github.io/cgo-void-repo/x86_64
```
And import the key directly from the site:
```bash
sudo wget -O /var/db/xbps/keys/cgo-void-repo.pem https://caspergamingone.github.io/cgo-void-repo/cgo-void-repo.pem
```

---

## 5. End-to-End Operational Lifecycle

### Phase 1: Environment Setup
Verify host dependencies and initialize the `void-packages` builder:
```bash
# Verify host tools
sudo xbps-install -S git xtools openssl xbps-rindex

# Bootstrap build engine in ~/git/void-packages
./scripts/setup-env.sh
```

### Phase 2: Generating Cryptographic Keys
Run key generator:
```bash
./scripts/gen-keys.sh
```
- Creates `~/.local/share/cgo-void-repo/cgo-void-repo.rsa` (secure local private key).
- Exports `repo-keys/cgo-void-repo.pem` and `docs/cgo-void-repo.pem` (public keys for repo and website).

### Phase 3: Authoring & Linting Templates
Place package definitions in `srcpkgs/<pkgname>/template`:
```bash
# Required template variables
pkgname=<pkgname>
version=<version>
revision=1
build_style=<meson|cmake|gnu-configure|python3-pep517|cargo|meta>
short_desc="<Summary under 72 chars>"
maintainer="CasperGamingOne <caspergamingone@users.noreply.github.com>"
license="<SPDX License>"
homepage="<https://...>"
distfiles="<https://...>"
checksum=<sha256>
```
Always lint before building:
```bash
xlint srcpkgs/<pkgname>/template
```

### Phase 4: Compiling Packages
Build package using the helper script:
```bash
./scripts/build-pkg.sh <pkgname>
```
Output packages land in `binpkgs/<arch>/`.

### Phase 5: Indexing & Signing Locally
```bash
./scripts/sign-repo.sh
```
- Uses private key from `~/.local/share/cgo-void-repo/cgo-void-repo.rsa`.
- Adds packages via `xbps-rindex -a`.
- Signs `<arch>-repodata` with `xbps-rindex --sign`.
- Cleans stale package versions via `xbps-rindex -c`.

### Phase 6: Local System Testing
To install and test on the local machine immediately:
```bash
./scripts/install-local.sh
sudo xbps-install <pkgname>
```

### Phase 7: GitHub Pages & Releases Deployment
1. Commit template changes, website updates, and public keys:
   ```bash
   git add srcpkgs/ docs/ repo-keys/
   git commit -m "feat(pkg): add <pkgname>"
   git push origin main
   ```
2. For releases, push a version tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. The GitHub Actions workflow (`.github/workflows/build-and-release.yml`):
   - Compiles packages inside `ghcr.io/void-linux/void-glibc-full:latest`.
   - Signs repodata using repository secret `RSA_PRIVATE_KEY`.
   - Generates the website and package catalog dynamically via `scripts/generate-web.py`.
   - Automatically commits & pushes the entire website and binary repository to the `gh-pages` branch.
   - Deploys directly to GitHub Pages via the GitHub Pages deployment API.
   - Attaches binary packages to GitHub Releases on version tags.

---

## 6. Troubleshooting Playbook for the Agent

| Issue | Cause | Agent Action |
| :--- | :--- | :--- |
| `Signing key not found` | Private key not yet generated | Run `./scripts/gen-keys.sh` to initialize `~/.local/share/cgo-void-repo/`. |
| `Private key in git status` | Accidentally copied key into repo | Stop immediately, delete key from repo, ensure it is only in `~/.local/share/`. |
| `XLibre dependency conflict` | Package declares conflicting xorg-server | Change dependency to modular X11 libs (e.g. `libX11-devel`). |
| `GitHub Pages 404 on .xbps` | Jekyll filtering unlisted extensions | Verify `docs/.nojekyll` exists and is tracked in git. |
| `Checksum mismatch` | Source tarball changed upstream | Run `xgensum -f srcpkgs/<pkg>/template`. |
| `failed to write to /proc/self/uid_map` | Docker/CI blocking user namespaces | Set `XBPS_CHROOT_CMD=uchroot` and add user to `xbuilder` group. |
