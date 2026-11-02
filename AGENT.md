# AGENT.md - Master Operational Playbook for `cgo-void-repo`

> **Scope**: This document serves as the authoritative operational manual for AI agents and human maintainers managing the custom Void Linux package repository **`cgo-void-repo`** for **CasperGamingOne** (**Games4Everyone**). It encodes all hard-earned architectural rules, pitfalls, container quirks, and automation practices to guarantee flawless, error-free operations.

---

## 1. Workspace Layout & Directory Standards

All Git development occurs in an isolated, dedicated directory structure in the user's home directory.

| Path | Purpose | Git Tracking Status |
| :--- | :--- | :--- |
| `~/git` (`/home/caspergamingone/git`) | **Dedicated Git Workspace** for all projects | Root Workspace (Not in Git) |
| `~/git/cgo-void-repo` | **Custom Repository Root** (public GitHub repository) | Tracked in Git |
| `~/git/cgo-void-repo/docs` | **GitHub Pages Website & Static XBPS Web Repo** | Tracked (`index.html`, `style.css`, `.nojekyll`, keys) |
| `~/git/cgo-void-repo/docs/assets` | **Branding Media** (banner, avatar, project logo) | Tracked (Strictly NO loose images in repo root) |
| `~/git/cgo-void-repo/repo-keys` | **Public RSA Keys** (`.pem` / `.pub` / `.plist`) | Tracked (Public keys ONLY) |
| `~/git/cgo-void-repo/srcpkgs` | **Source Package Templates** (xbps-src definitions) | Tracked in Git |
| `~/git/cgo-void-repo/scripts` | **Automation Scripts** (build, sign, web gen, setup) | Tracked in Git |
| `~/git/cgo-void-repo/binpkgs` | **Local Binary Packages** (local `.xbps` cache) | **Ignored** in `.gitignore` |
| `~/.local/share/cgo-void-repo` | **Secure Local Private Key Storage** | **NEVER in Git** (`0700` dir, `0600` key) |
| `~/git/void-packages` | Upstream Void packaging engine (`xbps-src`) | Separate cloned Git repository |
| `~/AGENT.md` | Convenience symlink to `~/git/cgo-void-repo/AGENT.md` | Host symlink |

---

## 2. Strict Security & Cryptography Policy (Zero Private Keys in Git)

Because this repository is public on GitHub and deployed to GitHub Pages:

> [!CAUTION]
> **ABSOLUTELY NO PRIVATE KEYS OR SECRETS IN THE GIT REPOSITORY**
> 1. **No Secrets Directory**: Never create a `SECRETS` or `private` folder inside the Git tree.
> 2. **Local Signing Key**: Stored exclusively outside the repository at `~/.local/share/cgo-void-repo/cgo-void-repo.rsa` with file permissions `0600`.
> 3. **CI/CD Signing Key**: Injected solely via the encrypted GitHub Actions repository secret `RSA_PRIVATE_KEY`. In workflows, the key is written to a temporary runner file, used to sign repodata, and immediately wiped.
> 4. **Public Keys**: `repo-keys/cgo-void-repo.pem`, `repo-keys/cgo-void-repo.rsa.pub`, and `docs/cgo-void-repo.pem` contain only public keys and are safe for public distribution.

---

## 3. Personal Brand Identity & Creator Ownership Policy

> [!IMPORTANT]
> **BRANDING AND LOGOS ARE STRICTLY PERSONAL TO THE CREATOR**
> 1. **Dual Licensing Structure**:
>    - **Open Source Code**: Software, packaging templates, automation scripts, and configuration files are licensed under the **MIT License**.
>    - **Personal Creative Assets**: The names **"CasperGamingOne"** and **"Games4Everyone"**, the identifier **"cgo-void-repo"**, the avatar (`personal-logo.jpeg`), the banner (`banner.jpeg`), and the logo (`games4everyone-logo.png`) belong solely and personally to **CasperGamingOne**.
> 2. **Non-Corporate Status**: These assets are personal creative property, not a registered corporate or judicial entity. They must be respected as the creator's personal work.
> 3. **Exclusion from License**: Brand assets are strictly excluded from the MIT software license and may NOT be used, copied, or modified without prior written consent.
> 4. **Clean Root Hygiene**: Never leave loose images in the repository root. All branding media must reside neatly inside `docs/assets/`.

---

## 4. System Ecosystem Awareness: XLibre Integration

The maintainer's host system runs **XLibre** (`xlibre-void`), an independent fork/implementation of the X display stack for Void Linux:

* **XLibre Repository**: `https://github.com/xlibre-void/xlibre/releases/latest/download`
* **XLibre Key**: `/var/db/xbps/keys/00:ca:42:57:c9:c0:9a:ec:94:b4:7d:97:e5:a9:aa:1e.plist`
* **Host Packages**: `xlibre`, `xlibre-xserver`, XLibre input & video drivers.
* **Coexisting Repos**: `cherrybtw/gsr4xbps`, `sonicde-void`, and Void Linux official repos.

### Agent Rules for Packaging Software with XLibre:
1. **Never Depend on `xorg-server` Directly**: If packaging graphical software, depend on modular client libraries (`libX11-devel`, `libXext-devel`, `libXrandr-devel`), never on specific display server implementations.
2. **Prevent File Clashes**: Avoid packaging conflicting configurations under `/etc/X11/xorg.conf.d/` that disrupt the XLibre server stack.

---

## 5. Critical Technical Lessons & Void Packaging Pitfalls

These hard-won lessons prevent errors that cause builds and CI workflows to break:

### Rule 1: NEVER Symlink Templates into `void-packages/srcpkgs/`
- **The Mistake**: Running `ln -sf "$pkg" void-packages/srcpkgs/$pkgname`.
- **Why It Fails**: In Void Linux, symlinks inside `void-packages/srcpkgs/` are reserved for subpackages (`[ -h "$XBPS_SRCPKGDIR/$pkg" ]`). `xbps-src` interprets a symlink as a subpackage and crashes with:
  ```text
  => ERROR: <pkg>: missing <pkg>_package() function!
  ```
- **The Fix**: **Always copy** the template directory recursively:
  ```bash
  rm -rf "void-packages/srcpkgs/$pkgname"
  cp -a "$pkg" "void-packages/srcpkgs/$pkgname"
  ```

### Rule 2: Container Image for Void CI
- **The Mistake**: Pulling `ghcr.io/void-linux/xbps-src-masterdir:latest`.
- **Why It Fails**: The image does not exist / has been deprecated, resulting in `failed to resolve reference ... not found` (exit code 1).
- **The Fix**: Always use the official `ghcr.io/void-linux/void-glibc-full:latest`.

### Rule 3: `xbps-src` Strictly Refuses to Run as Root
- **The Mistake**: Executing `./xbps-src` as root inside a Docker container.
- **Why It Fails**: `xbps-src` explicitly exits with `ERROR: xbps-src cannot be used as root.`
- **The Fix**: Provision an unprivileged `builder` user inside the container and run via `runuser`:
  ```bash
  useradd -m -G xbuilder -s /bin/bash builder || usermod -aG xbuilder builder
  runuser -u builder -g xbuilder -- ./xbps-src pkg <pkgname>
  ```

### Rule 4: User Namespaces Blocked in Docker (`uchroot` Required)
- **The Mistake**: Relying on default unprivileged user namespaces (`xbps-uunshare`) inside Docker on Ubuntu 24.04 runners.
- **Why It Fails**: The runner kernel blocks nested unprivileged user namespaces, failing with:
  ```text
  ERROR failed to write to /proc/self/uid_map (Operation not permitted)
  ```
- **The Fix**:
  1. Set container `options: --privileged` in the GitHub Actions job.
  2. Add `builder` user to the `xbuilder` group.
  3. Configure `echo "XBPS_CHROOT_CMD=uchroot" >> void-packages/etc/conf`.
  `xbps-uchroot` is SUID root and performs mounts/chroots without user namespaces.

### Rule 5: Git Discovery Across Filesystem Boundaries
- **The Mistake**: Running git commands inside the container on mounted workspaces.
- **Why It Fails**: Git detects filesystem boundary crossings and safe directory mismatches:
  ```text
  fatal: not a git repository (or any parent up to mount point /)
  Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
  ```
- **The Fix**:
  ```bash
  export GIT_DISCOVERY_ACROSS_FILESYSTEM=1
  git config --global --add safe.directory "*"
  echo "XBPS_USE_BUILD_MTIME=yes" >> void-packages/etc/conf
  ```

### Rule 6: GitHub Pages `.nojekyll` Requirement
- **The Mistake**: Deploying binary packages without a `.nojekyll` file.
- **Why It Fails**: GitHub Pages defaults to Jekyll processing, which silently drops files with leading dots or non-standard binary extensions (`.xbps`, repodata), resulting in client 404 errors.
- **The Fix**: Ensure `docs/.nojekyll` is committed and always deployed into the site root.

### Rule 7: Distfiles with URL Encoding (`%20`) Require Filename Aliases
- **The Mistake**: Specifying URLs with `%20` directly in `distfiles` without renaming.
- **Why It Fails**: `xbps-src` internals pass filenames through `printf`, which treats `%20` or `%I` as an invalid format character, throwing `printf: 'I': invalid format character`.
- **The Fix**: Use the `xbps-src` distfile rename alias syntax: `URL>target_filename.tar.gz`.

### Rule 8: Directory Names with Spaces in `do_install()`
- **The Mistake**: Writing `cp -a ${_srcdir}/*` when upstream extracts into a directory containing spaces (e.g. `./Antigravity IDE/`).
- **Why It Fails**: The shell splits the unquoted path into multiple arguments (`./Antigravity` and `IDE/*`), failing with `cannot stat: No such file or directory`.
- **The Fix**: Always double-quote variables in file operations: `cp -a "${_srcdir}"/* ...`.

### Rule 9: 100 MB Git File Limit (GitHub Releases vs GitHub Pages)
- **The Mistake**: Pushing `.xbps` binary files directly to the `gh-pages` Git branch.
- **Why It Fails**: GitHub enforces a strict 100.00 MB file limit on Git commits. Electron packages over 100 MB (e.g. `antigravity` at 157 MB and `antigravity-ide` at 153 MB) cause GitHub's pre-receive hook to decline the push with `GH001: Large files detected`.
- **The Fix**: Distribute all `.xbps` binary packages and signed repodata via **GitHub Releases** (`/releases/latest/download`), which supports files up to 2 GB each. Dedicate **GitHub Pages** exclusively to the lightweight web interface and public `.pem` key (`< 2 MB` total).

### Rule 10: Remote Signed Repositories Require Individual Package Signatures (`.sig2`)
- **The Mistake**: Signing only the repodata index (`xbps-rindex --sign`) and omitting package signatures, or using `xbps-rindex -f --sign-pkg`.
- **Why It Fails**: When an XBPS client queries a remote signed repository, XBPS requires both the signed repodata and a companion signature file (`<pkg>.<arch>.xbps.sig2`) for every package downloaded. If `.sig2` is missing, `xbps-install` aborts with:
  ```text
  ERROR: [trans] failed to download `<pkg>' signature from `<repo-url>': Not Found
  ERROR: Transaction failed! see above for errors.
  ```
  Furthermore, `xbps-rindex -f --sign-pkg` contains a bug where it opens files with `O_WRONLY|O_TRUNC` omitting `O_CREAT`; if a `.sig2` file does not already exist, it crashes with `failed to create ...: No such file or directory`.
- **The Fix**: Always remove existing signatures first (`rm -f ./*.sig2`), then sign binary packages with `xbps-rindex --sign-pkg --privkey <key> ./*.xbps` to produce fresh `.sig2` files, sign the repository index with `xbps-rindex --sign`, and upload matching `.xbps` binaries, `.sig2` signatures, and repodata to the distribution release. Ensure the GitHub Actions secret `RSA_PRIVATE_KEY` is configured in repository secrets.

### Rule 11: Packaging Applications with Vendored Libraries (e.g., MEGAsync)
- **The Context**: Complex desktop applications like MEGAsync bundle private multimedia or helper libraries (e.g. ffmpeg in `/opt/megasync/lib/`) while depending dynamically on system Qt5, X11, and OpenSSL.
- **Why It Fails**:
  1. *shlib-provides leak*: `xbps-src` will expose private `/opt/<pkg>/lib/` libraries as global system providers unless `noshlibprovides=yes` is specified.
  2. *shlib-requires resolution*: In the pre-pkg phase, `04-generate-runtime-deps.sh` scans ELF binaries against Void's `common/shlibs`. If the binary links to vendored libraries (even with embedded `RUNPATH`), the hook can fail or attach invalid system package dependencies.
  3. *Filesystem placement*: Upstream packages often install configuration into `/etc/udev/rules.d/` and `/etc/sysctl.d/`. Void Linux packaging guidelines require packages to place system rules in `/usr/lib/udev/rules.d/` and `/usr/lib/sysctl.d/`, preserving `/etc/` for local user overrides.
- **The Fix**:
  - Set `noshlibprovides=yes` to keep internal vendored libraries private.
  - Set `noverifyrdeps=yes` and explicitly declare all modular system dependencies in `depends="..."`.
  - Install udev rules to `/usr/lib/udev/rules.d/` and sysctl limits to `/usr/lib/sysctl.d/`.

---

## 6. Smart Workflow & Change Detection Architecture

To ensure GitHub Actions runs fast and avoids unnecessary rebuilds:

### A. Workflow-Level Trigger Filtering
The workflow trigger specifies:
```yaml
paths:
  - 'srcpkgs/**'
  - 'docs/**'
  - 'scripts/**'
  - 'repo-keys/**'
  - '.github/workflows/**'
```
Commits touching **only** documentation or metadata (`README.md`, `AGENT.md`, `LICENSE`, `.gitignore`) **never trigger** the CI pipeline.

### B. Step-Level Change Detection (`changes` step)
When CI triggers:
1. `git diff` inspects commits between the previous SHA and `HEAD`.
2. **If `srcpkgs/` was not modified** (e.g. only CSS or web pages changed):
   - Skips cloning `void-packages` (~200MB saved).
   - Skips `binary-bootstrap` (3-5 minutes saved).
   - Recovers existing built `.xbps` packages from the `gh-pages` branch.
   - Regenerates website HTML and package catalog in ~20 seconds.
3. **If `srcpkgs/` was modified**:
   - Loops through package directories.
   - **Only compiles packages whose templates were actually modified** (or all if tag/manual dispatch).
   - Recovers unchanged packages from `gh-pages` branch, so existing packages are never lost.

---

## 7. Automated Upstream Updates & Package Isolation

To keep packaged software (like **Google Antigravity** and **Antigravity IDE**) continuously up to date without manual intervention:

### A. Modular Update Engine (`scripts/check-updates.py`)
- Can check a single package or all packages:
  ```bash
  python3 scripts/check-updates.py antigravity
  python3 scripts/check-updates.py antigravity-ide
  python3 scripts/check-updates.py --all
  ```
- Scrapes the official upstream release portal (`https://antigravity.google/download?os=linux`).
- Compares local `version` and `_buildver` against upstream releases.
- Automatically downloads and streams the SHA-256 checksum when an update is found.
- Safely rewrites `version`, `_buildver`, `checksum`, and resets `revision=1` in `srcpkgs/<pkgname>/template`.

### B. Scheduled Automation Workflow (`check-upstream-updates.yml`)
- Runs on a daily cron schedule (`0 4 * * *`) and on manual `workflow_dispatch`.
- Evaluates each target application in isolation.
- If an update is detected, it commits and pushes **only that package's template** in an independent git commit:
  `feat(pkg): update <pkgname> to <version>`.
- The push triggers `build-and-release.yml`, which compiles **only that updated package** in isolation, signs the repo, updates the dynamic web catalog, and deploys. Unchanged packages are preserved from `gh-pages`.

### C. Electron & Proprietary Binary Packaging Directives
- **`restricted=yes`**: Mandatory for proprietary binaries with custom EULAs.
- **`nostrip=yes`**: Mandatory for Electron and Node native binaries; stripping corrupts runtime code.
- **Modular X11 Libraries**: Use `libX11`, `libXext`, `libXrandr`, `libxkbcommon` instead of `xorg-server` to maintain total compatibility with the **XLibre** environment.

---

## 8. End-to-End Operational Lifecycle

### Step 1: Local Environment Bootstrap
```bash
# Verify host tools
sudo xbps-install -S git xtools openssl xbps-rindex

# Bootstrap void-packages build engine alongside repo
./scripts/setup-env.sh
```

### Step 2: Key Management
```bash
# Generate local private key and export public verification keys
./scripts/gen-keys.sh
```
- Local private key: `~/.local/share/cgo-void-repo/cgo-void-repo.rsa` (`0600`).
- Public keys: `repo-keys/cgo-void-repo.pem` and `docs/cgo-void-repo.pem`.

### Step 3: Authoring a Package
Create `srcpkgs/<pkgname>/template`:
```bash
pkgname=<pkgname>
version=<version>
revision=1
short_desc="<Concise description under 72 chars>"
maintainer="CasperGamingOne <caspergamingone@proton.me>"
license="<SPDX License>"
homepage="<https://...>"
```
Lint before building:
```bash
xlint srcpkgs/<pkgname>/template
```

### Step 4: Compiling Locally
```bash
./scripts/build-pkg.sh <pkgname>
```
Output packages land in `binpkgs/<arch>/`.

### Step 5: Signing and Indexing
```bash
./scripts/sign-repo.sh
```

### Step 6: Deploying to GitHub
```bash
git add srcpkgs/ docs/ scripts/ repo-keys/
git commit -m "feat(pkg): add <pkgname>"
git push origin main
```
For official releases with binaries attached:
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 9. Troubleshooting Matrix

| Symptom / Error | Root Cause | Verified Agent Solution |
| :--- | :--- | :--- |
| `failed to resolve reference ...: not found` | Using non-existent `xbps-src-masterdir` image | Switch workflow container to `ghcr.io/void-linux/void-glibc-full:latest`. |
| `missing <pkg>_package() function!` | Template was symlinked (`ln -sf`) into `void-packages` | Use `cp -a` instead of `ln -s`. Symlinks are reserved for subpackages. |
| `ERROR: xbps-src cannot be used as root.` | Container running as UID 0 | Create user `builder` and execute with `runuser -u builder -g xbuilder`. |
| `failed to write to /proc/self/uid_map` | User namespaces blocked on Ubuntu 24.04 runners | Add `builder` to `xbuilder` group, set `XBPS_CHROOT_CMD=uchroot`, add `options: --privileged`. |
| `Stopping at filesystem boundary` | Git detecting mounted container filesystems | Export `GIT_DISCOVERY_ACROSS_FILESYSTEM=1` and `git config --global --add safe.directory "*"`. |
| `404 Not Found` for `.xbps` on GitHub Pages | Jekyll engine ignoring binary or unlisted files | Ensure `docs/.nojekyll` exists and is published in the root of the site. |
| `Checksum mismatch` during build | Upstream release archive was modified or corrupted | Run `xgensum -f srcpkgs/<pkgname>/template` to recompute sha256. |
| `Signing key not found` locally | Key generator script not yet executed | Run `./scripts/gen-keys.sh` to initialize `~/.local/share/cgo-void-repo/`. |
