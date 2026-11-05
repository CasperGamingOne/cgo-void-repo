# AGENT.md - Master Operational Playbook for `cgo-void-repo`

> **Scope**: This document serves as the authoritative operational manual for AI agents and human maintainers managing the custom Void Linux package repository **`cgo-void-repo`** for **CasperGamingOne** (**Games4Everyone**). It encodes all architectural rules, suckless engineering principles, pitfalls, container quirks, kernel configurations, and automation practices to guarantee flawless, error-free operations.

---

## 1. Workspace Layout & Directory Standards

All Git development occurs in an isolated, dedicated directory structure in the user's home directory.

| Path | Purpose | Git Tracking Status |
| :--- | :--- | :--- |
| `~/git` (`/home/caspergamingone/git`) | **Dedicated Git Workspace** for all projects | Root Workspace (Not in Git) |
| `~/git/cgo-void-repo` | **Custom Repository Root** (public GitHub repository) | Tracked in Git |
| `~/git/cgo-void-repo/docs` | **GitHub Pages Website & Static Web Portal** | Tracked (`index.html`, `packages.json`, `style.css`, `.nojekyll`, keys) |
| `~/git/cgo-void-repo/docs/assets` | **Branding Media** (banner, avatar, project logo) | Tracked (Strictly NO loose images in repo root) |
| `~/git/cgo-void-repo/repo-keys` | **Public RSA Keys** (`.pem` / `.pub` / `.plist`) | Tracked (Public keys ONLY) |
| `~/git/cgo-void-repo/srcpkgs` | **Source Package Templates** (xbps-src definitions) | Tracked in Git |
| `~/git/cgo-void-repo/scripts` | **Automation Scripts** (build, matrix, web gen, sign, notify) | Tracked in Git |
| `~/git/cgo-void-repo/binpkgs` | **Local Binary Packages** (local `.xbps` cache) | **Ignored** in `.gitignore` |
| `~/.local/share/cgo-void-repo` | **Secure Local Private Key Storage** | **NEVER in Git** (`0700` dir, `0600` key) |
| `~/git/void-packages` | Upstream Void packaging engine (`xbps-src`) | Separate cloned Git repository |
| `AGENT.md` & `AGENTS.md` | Authoritative operational playbooks | Tracked (`AGENTS.md` symlinked to `AGENT.md`) |

---

## 2. Strict Security & Cryptography Policy (Zero Private Keys in Git)

Because this repository is public on GitHub and deployed to GitHub Pages:

> [!CAUTION]
> **ABSOLUTELY NO PRIVATE KEYS OR SECRETS IN THE GIT REPOSITORY**
> 1. **No Secrets Directory**: Never create a `SECRETS` or `private` folder inside the Git tree.
> 2. **Local Signing Key**: Stored exclusively outside the repository at `~/.local/share/cgo-void-repo/cgo-void-repo.rsa` with file permissions `0600`.
> 3. **CI/CD Signing Key**: Injected solely via the encrypted GitHub Actions repository secret `RSA_PRIVATE_KEY`. In workflows, the key is written to a temporary runner file, used to sign repodata and packages, and immediately wiped.
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

## 4. Suckless Engineering & Coding Principles

To maintain maximum reliability, performance, and maintainability across the repository, all code must follow the **Suckless Philosophy**:

1. **Simplicity Over Complexity**: Prefer simple, obvious, and readable code over convoluted abstractions or unnecessary frameworks.
2. **Frugality & Zero Redundant Code**: Never maintain duplicate logic, dead code branches, or redundant file copies. Every line of code must serve an active purpose.
3. **Standard Library Exclusivity**: Python automation scripts (`generate-matrix.py`, `generate-web.py`, `notify-ci.py`, `notify-requester.py`, `check-updates.py`) must rely **strictly on Python standard libraries** (`urllib.request`, `json`, `re`, `pathlib`, `hashlib`, `subprocess`). No external pip dependencies.
4. **POSIX / Standard Bourne Shell**: Shell scripts must be clean, deterministic, use `set -euo pipefail`, quote variables, and avoid non-standard shell extensions.
5. **Single Source of Truth**: Package versions, revisions, and metadata reside exclusively in `srcpkgs/<pkgname>/template`. Generators and matrices must extract from this single source of truth.
6. **Strict `xlint` Compliance**: Every template under `srcpkgs/` must pass `xlint` with **zero errors and zero warnings**.
7. **Separation of Concerns**: Website deployment is completely decoupled from heavyweight package compilation so that documentation and metadata publish in ~15 seconds without triggering redundant builds.

---

## 5. Dual-Channel Repository Architecture (Generic vs x86_64-v3)

`cgo-void-repo` delivers high-performance packaging through a dual-channel microarchitecture design:

### Channels:
* **`rolling` (Generic Baseline)**:
  - Target CPUs: Universal 64-bit x86 CPUs (`x86_64`).
  - Compiler Flags: `-O2 -pipe`.
  - Release Endpoint: `https://github.com/CasperGamingOne/cgo-void-repo/releases/download/rolling`
* **`rolling-v3` (x86_64-v3 Optimized)**:
  - Target CPUs: Modern x86-64 processors supporting AVX, AVX2, FMA, BMI1, BMI2, and MOVBE (Intel Haswell+, AMD Excavator/Zen+).
  - Compiler Flags: `-march=x86-64-v3 -O3 -pipe`.
  - Release Endpoint: `https://github.com/CasperGamingOne/cgo-void-repo/releases/download/rolling-v3`

### Architecture Rules:
1. **Identical Package Names**: Never append `-v3` to `pkgname` in templates. Package names remain strictly identical (e.g. `linux-cachyos-lts`, `noctalia`, `ananicy-cpp`). The channel endpoint chosen by the user in `/etc/xbps.d/10-cgo-void-repo.conf` determines which architecture is fetched.
2. **Performance-Critical Software**: Compiled natively for both channels (`ananicy-cpp`, `linux-cachyos-lts`, `noctalia`, `umbriel`, `xdg-desktop-portal-umbriel`, `vmware-workstation`).
3. **Universal Binary Mirroring**: Proprietary binaries, Electron bundles, and architecture-agnostic packages (`antigravity`, `antigravity-ide`, `artcraft-launcher`, `cgo-hello`, `change-kernel`, `dolphin-megasync`, `linux-cachyos-lts-meta`, `megasync`, `noctalia-meta`) are mirrored to both channels so users on `rolling-v3` have access to the complete catalog without dual-repo setups.
4. **CPU Detection**: Users can verify compatibility via:
   ```bash
   /lib/ld-linux-x86-64.so.2 --help | grep -A 4 "v3"
   ```

---

## 6. Dynamic Parallel Matrix Build Engine

Sequential package builds in CI are slow and error-prone. The repository uses an asynchronous dynamic matrix engine:

1. **Matrix Planner (`scripts/generate-matrix.py`)**:
   - Queries the GitHub Releases API for existing `.xbps` assets in `rolling` and `rolling-v3`.
   - Reads `version` and `revision` from every template in `srcpkgs/` (excluding subpackage symlinks).
   - Generates a targeted matrix JSON: `{ "include": [ { "pkg": "...", "channel": "generic"|"x86_64-v3" } ] }`.
   - Sets `needs_build=false` if all assets already exist, skipping runner containers entirely.
2. **Parallel Runners (`build-package`)**:
   - Runs on `strategy: matrix` with `fail-fast: false`.
   - Each package and channel compiles concurrently on separate GitHub Actions runners.
   - Outputs an isolated artifact `binpkgs-<pkg>-<channel>`.
3. **Consolidation & Signing (`assemble-and-publish`)**:
   - Merges newly built artifacts with existing release assets.
   - Signs packages with RSA (`xbps-rindex --sign-pkg`) producing individual `.sig2` signatures.
   - Signs the repodata index (`xbps-rindex --sign`) and cleans obsolete revisions.
   - Releases assets directly to GitHub Releases.

---

## 7. Linux CachyOS LTS Kernel Architecture & Performance Suite

`linux-cachyos-lts` bundles the complete CachyOS performance ecosystem tailored for Void Linux:

### Kernel Core Optimizations:
* **CPU Scheduler**: **BORE** (Burst-Oriented Response Enhancer) by firelzrd via `patches/0001-bore-cachy.patch` (`CONFIG_SCHED_BORE=y`).
* **Storage I/O Scheduler**: **ADIOS** (Adaptive Deadline I/O Scheduler) v3.3.0 by firelzrd via `patches/0002-adios.patch` (`CONFIG_MQ_IOSCHED_ADIOS=y`, `CONFIG_MQ_IOSCHED_DEFAULT_ADIOS=y`).
* **Responsiveness**: 1000 Hz timer tick (`CONFIG_HZ=1000`) and Full Dynamic Preemption (`CONFIG_PREEMPT=y`, `CONFIG_PREEMPT_DYNAMIC=y`).
* **Memory Management**:
  - Multi-Gen LRU (`CONFIG_LRU_GEN=y`, `CONFIG_LRU_GEN_ENABLED=y`, `CONFIG_LRU_GEN_WALKS_MMU=y`).
  - Zswap enabled by default with ZSTD compression and `zsmalloc` allocator (`CONFIG_ZSWAP=y`, `CONFIG_ZSWAP_DEFAULT_ON=y`, `CONFIG_ZSWAP_COMPRESSOR_DEFAULT="zstd"`).
  - ZRAM with ZSTD compressor (`CONFIG_ZRAM_DEF_COMP="zstd"`).
  - Data Access Monitor (`CONFIG_DAMON_LRU_SORT=y`, `CONFIG_DAMON_STAT=y`).
* **Networking**:
  - BBR congestion control as default algorithm (`CONFIG_TCP_CONG_BBR=y`, `CONFIG_DEFAULT_TCP_CONG="bbr"`).
  - CAKE queuing discipline as default (`CONFIG_NET_SCH_CAKE=y`, `CONFIG_DEFAULT_NET_SCH="cake"`, `CONFIG_NET_SCH_DEFAULT=y`).
* **Gaming & Hardware Sync**:
  - NTSync (`CONFIG_NTSYNC=y`): In-kernel fast NT synchronization emulation for Proton/Wine.
  - Frequency scaling: AMD P-State EPP active mode 3 (`CONFIG_X86_AMD_PSTATE=y`) and Intel P-State.
* **System Hardware & Sysctl Profiles (Installed Automatically)**:
  - `/usr/lib/udev/rules.d/60-ioschedulers.rules`: Assigns `adios` to NVMe, `mq-deadline` to SATA SSDs, `bfq` to HDDs.
  - `/usr/lib/sysctl.d/70-cachyos-settings.conf`: Applies CachyOS kernel sysctl tuning (`vm.vfs_cache_pressure = 50`, `vm.dirty_bytes`, `vm.page-cluster = 0`, `net.core.netdev_max_backlog = 4096`, etc.).

---

## 8. Discord Webhook & Bot Automation

The repository provides automated two-way Discord integrations:

### A. CI/CD Build Tracker (`scripts/notify-ci.py`)
* Triggered in `.github/workflows/build-and-release.yml` using `DISCORD_CI_WEBHOOK` (fallback: `DISCORD_WEBHOOK`).
* **Build Start**: Posts a rich embed showing commit hash, message, author, branch, and workflow run link.
* **Build Result**: Posts status (Success / Failure / Cancelled) with a breakdown of each pipeline job.

### B. Package Request Intake & Status DMs (`scripts/notify-requester.py`)
* **Intake (`package-request-notify.yml`)**:
  - User submits request on website -> opens GitHub Issue with template.
  - Action auto-applies `package-request` and `status: pending-triage` labels.
  - Posts acknowledgment comment on issue and notifies Discord maintainer channel.
* **Status Updates (`package-request-status.yml`)**:
  - When maintainers apply labels (`status: accepted`, `status: in-progress`, `status: completed`, `status: denied`) or comment (`/accept`, `/progress`, `/complete`, `/deny`), the script resolves the user's Discord handle/ID and dispatches a private Discord DM.
  - Requires `DISCORD_BOT_TOKEN` and `DISCORD_GUILD_ID` secrets (with *Server Members Intent* enabled).

---

## 9. Critical Technical Lessons & Void Packaging Pitfalls

These hard-won lessons prevent errors that break builds and CI workflows:

### Rule 1: NEVER Symlink Templates into `void-packages/srcpkgs/`
- **Mistake**: `ln -sf "$pkg" void-packages/srcpkgs/$pkgname`.
- **Reason**: `xbps-src` reserves symlinks for subpackages (`[ -h "$XBPS_SRCPKGDIR/$pkg" ]`). It crashes with `missing <pkg>_package() function!`.
- **Fix**: **Always copy** the directory recursively: `cp -a "$source_pkg_dir" "void-packages/srcpkgs/$pkg"`.

### Rule 2: Container Image for Void CI
- **Mistake**: Pulling deprecated `ghcr.io/void-linux/xbps-src-masterdir:latest`.
- **Reason**: Image does not exist, crashing with exit code 1.
- **Fix**: Use the official `ghcr.io/void-linux/void-glibc-full:latest`.

### Rule 3: `xbps-src` Refuses to Run as Root
- **Mistake**: Running `./xbps-src` as root inside containers.
- **Reason**: `xbps-src` exits with `ERROR: xbps-src cannot be used as root.`
- **Fix**: Create unprivileged `builder` user and execute with `runuser -u builder -g xbuilder -- ./xbps-src ...`.

### Rule 4: User Namespaces Blocked in Docker (`uchroot` Required in ALL Profiles)
- **Mistake**: Relying on default unprivileged namespaces (`xbps-uunshare`) inside Docker runners.
- **Reason**: Runner kernels block nested user namespaces (`ERROR failed to write to /proc/self/uid_map`).
- **Fix**:
  1. Add `options: --privileged` to the container job.
  2. Add `builder` to `xbuilder` group and set `chmod 4750 /usr/bin/xbps-uchroot`.
  3. **Critical Gotcha**: When passing `./xbps-src -c x86_64-v3`, `xbps-src` loads `etc/conf.x86_64-v3` *instead* of `etc/conf`. Therefore, `XBPS_CHROOT_CMD=uchroot` must be set in **both** `etc/conf` and `etc/conf.x86_64-v3`.

### Rule 5: Git Discovery Across Filesystem Boundaries
- **Mistake**: Running git commands inside containers on mounted volumes.
- **Reason**: Git detects safe directory mismatches (`fatal: not a git repository ... stopping at filesystem boundary`).
- **Fix**:
  ```bash
  export GIT_DISCOVERY_ACROSS_FILESYSTEM=1
  git config --global --add safe.directory "*"
  ```

### Rule 6: GitHub Pages `.nojekyll` Requirement
- **Mistake**: Deploying binary files without a `.nojekyll` file.
- **Reason**: Jekyll silently drops directories with leading dots or non-standard file extensions (`.xbps`, repodata), returning 404.
- **Fix**: Ensure `.nojekyll` is generated in `docs/` and deployed to the GitHub Pages site root.

### Rule 7: Distfiles with URL Encoding (`%20`) Require Filename Aliases
- **Mistake**: Specifying URLs with `%20` directly in `distfiles` without renaming.
- **Reason**: `xbps-src` internals pass filenames through `printf`, throwing `printf: 'I': invalid format character`.
- **Fix**: Use distfile rename alias syntax: `URL>target_filename.tar.gz`.

### Rule 8: Directory Names with Spaces in `do_install()`
- **Mistake**: `cp -a ${_srcdir}/*` when upstream extracts into a directory with spaces (`./Antigravity IDE/`).
- **Reason**: Shell splits unquoted paths into separate arguments, failing with `No such file or directory`.
- **Fix**: Always double-quote variables in shell operations: `cp -a "${_srcdir}"/* ...`.

### Rule 9: 100 MB Git File Limit (GitHub Releases vs GitHub Pages)
- **Mistake**: Pushing `.xbps` binary files directly to a Git branch.
- **Reason**: GitHub enforces a 100 MB per-file limit on Git commits. Electron packages over 100 MB cause `GH001: Large files detected`.
- **Fix**: Distribute all `.xbps` binaries and repodata via **GitHub Releases** (`/releases/latest/download`), which supports files up to 2 GB. GitHub Pages serves only the web portal and public verification keys.

### Rule 10: Remote Signed Repositories Require Package Signatures (`.sig2`)
- **Mistake**: Signing only the repodata index (`xbps-rindex --sign`) and omitting package signatures, or using `xbps-rindex -f --sign-pkg`.
- **Reason**: Remote XBPS downloads require `<pkg>.<arch>.xbps.sig2`. If missing, `xbps-install` aborts. Furthermore, `xbps-rindex -f --sign-pkg` has a bug opening files without `O_CREAT`.
- **Fix**: Remove old signatures first (`rm -f ./*.sig2`), then run `xbps-rindex --sign-pkg --privkey <key> ./*.xbps` followed by `xbps-rindex --sign`.

### Rule 11: Packaging Applications with Vendored Libraries (MEGAsync)
- **Context**: Applications bundling private libraries (e.g. ffmpeg in `/opt/megasync/lib/`).
- **Fix**: Set `noshlibprovides=yes` to keep internal vendored libraries private. Set `noverifyrdeps=yes` and declare system dependencies explicitly. Install udev rules to `/usr/lib/udev/rules.d/` and sysctl limits to `/usr/lib/sysctl.d/`.

### Rule 12: Packaging Native C++23 / Meson Wayland Stacks (Noctalia, Umbriel, Greeter, Portal)
- **Fix**:
  1. Strip host-specific CPU flags in `post_patch()` (`vsed -i "s/'-march=native', '-mtune=native',//g" meson.build`).
  2. Pass `-Dlocaled=disabled` to Meson so the compositor falls back to `xkbcommon` without `libsystemd`.
  3. Map header-only `nlohmann/json` to `json-c++`, and markdown parsing to `libmd4c-devel`.

### Rule 13: Packaging Hypervisors with DKMS Kernel Modules (VMware Workstation Pro)
- **Fix**:
  1. Extract `.bundle` with `skip_extraction` and `bash "${bundle}" --extract extracted`.
  2. Place module sources under `/usr/src/<pkgname>-<version>/` inside a decoupled `vmware-workstation-dkms` subpackage with `triggers="dkms"` and `dkms_modules="vmware-workstation ${version}"`.
  3. Specify `python_version=ignore` to prevent shebang rewriting on bundled internal runtimes.
  4. Provide runit services `/etc/sv/vmware-networks` and `/etc/sv/vmware-usbarbitrator`.
  5. Bypass `vmware-modconfig` GUI check in `/usr/bin/vmware`.
  6. **Preserve Internal Module Include Paths in DKMS**: When passing compiler optimization flags via `EXTRA_CFLAGS` in `dkms.conf`, GNU Make treats command-line variables as immutable, causing VMware's internal `Makefile.kernel` to drop its own `$(INCLUDE)` paths (triggering `fatal error: driver-config.h: No such file or directory` on `vmmon`). Patch `Makefile.kernel` in both `vmmon-only` and `vmnet-only` with `override EXTRA_CFLAGS := $(CC_OPTS) $(INCLUDE) $(VMW_CFLAGS) $(EXTRA_CFLAGS)`.

### Rule 14: GitHub Release 2 GiB Asset Limit (No Monolithic Debug Packages)
- **Mistake**: Creating subpackages bundling uncompressed kernel debug symbols (`vmlinux` + `.ko.debug`).
- **Reason**: The asset exceeds 3.1 GB, and the GitHub Releases API rejects uploads exceeding 2,147,483,648 bytes with `Validation Failed: size must be less than 2147483648`.
- **Fix**: Never package monolithic `*-dbg` kernel archives. In `files/mv-debug`, strip and zstd-compress kernel modules directly without producing debug symbol archives.

### Rule 15: Kernel Source Directory Hierarchy (`arch/x86/` NOT `arch/x86_64/`)
- **Mistake**: Writing `local arch=x86_64` and copying `arch/${arch}/include` in `do_install()`.
- **Reason**: The Linux kernel source tree only has `arch/x86/`, never `arch/x86_64/`. It crashes with `cp: cannot stat 'arch/x86_64/include': No such file or directory`.
- **Fix**: In the template, use: `local arch=x86 subarch=x86_64`. Use `$arch` for file paths and `$subarch` for `make ARCH=...`.

### Rule 16: Bash Parameter Expansion in Metadata Generators
- **Mistake**: Naive regex parsing extracting raw template strings like `${version%.*}` into website descriptions.
- **Reason**: Bash parameter expansions are evaluated by bash at build time, not by naive text scrapers.
- **Fix**: In `generate-web.py`, explicitly expand `${version%.*}` to the major.minor version string and substitute variables before rendering HTML/JSON catalogs.

### Rule 17: Subpackage Metadata Inheritance & Deduplication
- **Mistake**: Treating subpackage symlinks in `srcpkgs/` as parent packages, causing duplicate catalog rows with incorrect package names.
- **Reason**: In Void Linux, subpackages (like `linux-cachyos-lts-headers`) are symlinks pointing to the parent directory (`linux-cachyos-lts`).
- **Fix**: `scan_packages()` in `generate-web.py` inspects `item.is_symlink()`, passes `pkg_override`, parses the `<pkg>_package()` function body for custom `short_desc`, isolates shell variable assignments, and deduplicates entries by package name.

### Rule 18: Mandatory DKMS Decoupling Standard (`<pkg>-dkms` Subpackages)
- **Architectural Policy**: Kernel module sources must **NEVER** be packaged directly into the main application/software package. All out-of-tree kernel modules managed by DKMS must be completely decoupled into a standalone `<pkg>-dkms` subpackage.
- **Packaging Requirements**:
  1. **Userspace Main Package (`<pkg>`)**:
     - Bundles applications, GUI binaries, libraries, runit services, desktop files, and configs.
     - Declares `depends="<pkg>-dkms-${version}_${revision} ..."` to pull in required modules.
     - Strictly **omits** `triggers="dkms"`, `dkms_modules`, and `depends="dkms"`.
  2. **DKMS Subpackage (`<pkg>-dkms`)**:
     - Declares `subpackages="<pkg>-dkms"` after `checksum=` in the parent template.
     - Contains only DKMS module sources under `/usr/src/<pkg>-<version>/` via `pkg_install() { vmove usr/src; }`.
     - Declares `depends="dkms"`, `triggers="dkms"`, and `dkms_modules="<pkg> ${version}"`.
     - Short description must explicitly identify the DKMS nature (e.g. `short_desc="<App> - DKMS host kernel modules"`).
  3. **Symlink Convention in `srcpkgs/`**:
     - A companion symlink `srcpkgs/<pkg>-dkms -> <pkg>` must always exist in the `srcpkgs/` directory.
     - `xbps-src` recognizes this symlink as a subpackage definition, routing build execution to `<pkg>-dkms_package()`.
     - Local builders (`scripts/build-pkg.sh`) and CI workflows must synchronize these symlinks into `void-packages/srcpkgs/`.

### Rule 19: Automatic Chaining of Upstream Updates & Matrix Builds
- **Context**: When `.github/workflows/check-upstream-updates.yml` discovers new releases, updates templates, and pushes commits to `main` using `GITHUB_TOKEN`, GitHub's built-in anti-recursion security prevents standard `push` events from triggering `.github/workflows/build-and-release.yml`.
- **Architectural Policy**: Upstream package updates must immediately trigger compilation so newly updated software is built, signed, and released as quickly as possible.
- **Packaging & CI Implementation**:
  1. Grant `actions: write` and `contents: write` permissions to `check-upstream-updates.yml`.
  2. Track committed updates in a counter (`UPDATES_COMMITTED`).
  3. When `UPDATES_COMMITTED > 0`, explicitly dispatch the build pipeline via `gh workflow run build-and-release.yml --ref main` with `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}`.
  4. The dynamic matrix planner in `build-and-release.yml` automatically detects the unbuilt versions against GitHub Releases and kicks off parallel compilation runners.

---

## 10. System Ecosystem: XLibre Integration

The maintainer's host system runs **XLibre** (`xlibre-void`), an independent fork of the X display stack for Void Linux:

* **XLibre Repository**: `https://github.com/xlibre-void/xlibre/releases/latest/download`
* **XLibre Key**: `/var/db/xbps/keys/00:ca:42:57:c9:c0:9a:ec:94:b4:7d:97:e5:a9:aa:1e.plist`
* **Agent Rules**:
  1. **Never Depend on `xorg-server` Directly**: Depend on modular client libraries (`libX11-devel`, `libXext-devel`, `libXrandr-devel`).
  2. **Prevent File Clashes**: Avoid packaging conflicting configurations under `/etc/X11/xorg.conf.d/`.

---

## 11. End-to-End Operational Lifecycle

### Step 1: Local Environment Bootstrap
```bash
sudo xbps-install -S git xtools openssl xbps-rindex
./scripts/setup-env.sh
```

### Step 2: Key Management
```bash
./scripts/gen-keys.sh
```
- Local private key: `~/.local/share/cgo-void-repo/cgo-void-repo.rsa` (`0600`).
- Public keys: `repo-keys/cgo-void-repo.pem` and `docs/cgo-void-repo.pem`.

### Step 3: Authoring & Linting a Package
Create `srcpkgs/<pkgname>/template` and lint:
```bash
xlint srcpkgs/<pkgname>/template
```

### Step 4: Compiling Locally
```bash
./scripts/build-pkg.sh <pkgname>           # Generic baseline
./scripts/build-pkg.sh <pkgname> --v3      # x86_64-v3 optimized
./scripts/build-pkg.sh <pkgname> --both    # Both variants
```

### Step 5: Signing and Indexing
```bash
./scripts/sign-repo.sh
```

### Step 6: Deploying to GitHub
```bash
git add srcpkgs/ docs/ scripts/ repo-keys/ .github/
git commit -m "feat(pkg): add <pkgname>"
git push origin main
```

---

## 12. Troubleshooting Matrix

| Symptom / Error | Root Cause | Verified Agent Solution |
| :--- | :--- | :--- |
| `Validation Failed: size must be less than 2147483648` | Debug package (`*-dbg`) exceeds GitHub's 2 GiB release asset limit | Remove `*-dbg` subpackage; strip and zstd-compress kernel modules in `mv-debug`. |
| `cp: cannot stat 'arch/x86_64/include'` | Linux kernel tree uses `arch/x86`, not `arch/x86_64` | Set `local arch=x86 subarch=x86_64` in `do_install()`. |
| `failed to write to /proc/self/uid_map` in v3 profile | `etc/conf.x86_64-v3` was missing `XBPS_CHROOT_CMD=uchroot` | Add `XBPS_CHROOT_CMD=uchroot` to `etc/conf.x86_64-v3` and `chmod 4750 /usr/bin/xbps-uchroot`. |
| Website shows `${version%.*}` in description | Raw template string was unexpanded by naive regex | Expand bash parameter expressions in `scripts/generate-web.py`. |
| Duplicate package rows in web catalog | Subpackage symlinks evaluated without overriding package name | Use `pkg_override` in `generate-web.py` and isolate `<pkg>_package()` scope. |
| `missing <pkg>_package() function!` | Template was symlinked (`ln -sf`) into `void-packages` | Use `cp -a` instead of `ln -s`. Symlinks are reserved for subpackages. |
| `ERROR: xbps-src cannot be used as root.` | Container running as UID 0 | Create user `builder` and execute with `runuser -u builder -g xbuilder`. |
| `Stopping at filesystem boundary` | Git detecting mounted container filesystems | Export `GIT_DISCOVERY_ACROSS_FILESYSTEM=1` and `git config --global --add safe.directory "*"`. |
| `404 Not Found` for `.xbps` on GitHub Pages | Jekyll engine ignoring binary or unlisted files | Ensure `.nojekyll` exists and is published in the root of the site. |
| `Checksum mismatch` during build | Upstream release archive was modified or corrupted | Run `xgensum -f srcpkgs/<pkgname>/template` to recompute sha256. |
| `failed to download signature: Not Found` | Companion `.sig2` signature files missing from release | Run `xbps-rindex --sign-pkg` on all `.xbps` packages before pushing releases. |
| `Signing key not found` locally | Key generator script not yet executed | Run `./scripts/gen-keys.sh` to initialize `~/.local/share/cgo-void-repo/`. |
| `fatal error: driver-config.h: No such file or directory` in VMware DKMS | `EXTRA_CFLAGS` in `dkms.conf` overrides internal module include flags in `Makefile.kernel` | Add `override EXTRA_CFLAGS := $(CC_OPTS) $(INCLUDE) $(VMW_CFLAGS) $(EXTRA_CFLAGS)` in `vmmon` & `vmnet` patches. |
| Upstream update pushed to main but build workflow never starts | Pushes from `GITHUB_TOKEN` suppress `push` events to prevent recursion | Grant `actions: write` and dispatch via `gh workflow run build-and-release.yml --ref main`. |
