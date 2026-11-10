<p align="center">
  <img src="docs/assets/banner.jpeg" alt="cgo-void-repo Banner" width="100%">
</p>

<p align="center">
  <img src="docs/assets/personal-logo.jpeg" alt="CasperGamingOne" width="80" style="border-radius: 16px;">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="docs/assets/games4everyone-logo.png" alt="Games4Everyone" width="80" style="border-radius: 16px;">
</p>

# cgo-void-repo 🐧

> [!IMPORTANT]
> I am no longer on Void Linux, but as my love for it is still there, i will keep maintaining this repo for as long as i can, plus the automated actions i put in place will help me do just that 🫀

Personal XBPS binary package repository for **Void Linux**, maintained by **CasperGamingOne** under the **Games4Everyone** project. Features continuous rolling releases with dual-channel architecture: standard baseline and native **x86_64-v3 microarchitecture performance optimizations**.

🌐 **Website & Portal:** [https://caspergamingone.github.io/cgo-void-repo](https://caspergamingone.github.io/cgo-void-repo)  
📥 **Package Request Form:** [Submit a Request](https://caspergamingone.github.io/cgo-void-repo#request)

> [!NOTE]
> For Discord notifications on your package request, you will have to join this server => [DJSnowDogs's pups](https://dcserver.link/djsnowdogs). I am sorry, it's Discord limitations, not mine. 💬

---

## ⚡ Dual-Channel Release Architecture

`cgo-void-repo` uses clean package names (`noctalia`, `umbriel`, `vmware-workstation`, etc.) distributed across two distinct GitHub Release channels:

| Channel Tag | Target Architecture | Compiler Optimization | Recommended For |
|---|---|---|---|
| **`rolling-v3`** | `x86_64-v3` | `-O3 -march=x86-64-v3 -pipe` (AVX2, FMA, BMI1/2) | Intel Haswell (2013+), AMD Zen (2017+) or newer |
| **`rolling`** | `x86_64` | `-O2 -pipe` (Universal Baseline) | All 64-bit x86 CPUs, Hypervisors, Virtual Machines |

> [!TIP]
> Both channels are completely self-contained. Packages that cannot be compiled from source (e.g. VMware, MegaSync, Google Antigravity) are automatically mirrored into both channels so you can configure whichever channel suits your machine.

---

## 🔍 Check Your CPU Microarchitecture

To verify if your processor supports the optimized `x86_64-v3` channel, run this command in your Void Linux terminal:

```bash
/lib/ld-linux-x86-64.so.2 --help | grep -E "x86-64-v[234]"
```

* If you see **`x86-64-v3 (supported, searched)`**, your CPU is ready for **`rolling-v3`**!
* If only `x86-64` or `x86-64-v2` is supported, use the baseline **`rolling`** channel.

---

## 🚀 Quick Setup for Clients

### Option A: Modern Processors (`x86_64-v3` Optimized - Recommended)

```bash
# 1. Download and trust the repository RSA signing key
sudo wget -O /var/db/xbps/keys/cgo-void-repo.pem https://caspergamingone.github.io/cgo-void-repo/cgo-void-repo.pem

# 2. Add x86_64-v3 repository channel
echo "repository=https://github.com/CasperGamingOne/cgo-void-repo/releases/download/rolling-v3" | sudo tee /etc/xbps.d/10-cgo-void-repo.conf

# 3. Synchronize repository index and install
sudo xbps-install -S
sudo xbps-install -S noctalia umbriel vmware-workstation megasync
```

### Option B: Universal Compatibility (`x86_64` Baseline)

```bash
# 1. Download and trust the repository RSA signing key
sudo wget -O /var/db/xbps/keys/cgo-void-repo.pem https://caspergamingone.github.io/cgo-void-repo/cgo-void-repo.pem

# 2. Add baseline repository channel
echo "repository=https://github.com/CasperGamingOne/cgo-void-repo/releases/download/rolling" | sudo tee /etc/xbps.d/10-cgo-void-repo.conf

# 3. Synchronize repository index and install
sudo xbps-install -S
```

---

## 📦 Available Packages

The complete, real-time package catalog—including up-to-date versions, microarchitecture channel availability (`rolling` vs `rolling-v3`), licenses, and package details—is hosted on our live repository portal:

👉 **[https://caspergamingone.github.io/cgo-void-repo](https://caspergamingone.github.io/cgo-void-repo)**

You can also programmatically inspect the repository feed at [`packages.json`](https://caspergamingone.github.io/cgo-void-repo/packages.json).

---

## ⚖️ Packaging Standards & License Compliance

All packages follow the [Void Linux Packaging Manual](https://github.com/void-linux/void-packages/blob/master/Manual.md):
- **Free Software (FOSS)**: Licensed under upstream terms (`MIT`) with complete license texts installed via `vlicense`.
- **Restricted Software**: Marked with `restricted=yes`, requiring acceptance of official vendor EULAs (VMware, Google Antigravity, MegaSync).
- **Quality Assurance**: Every template passes `xlint` with zero errors or warnings.
- **Clean System Integration**: Proprietary binaries are cleanly isolated under `/usr/lib/` or `/opt/`, system runit services are provided under `/etc/sv/`, and kernel drivers utilize official DKMS triggers.

---

## 📁 Repository Structure

```text
cgo-void-repo/
├── docs/                    # GitHub Pages interactive portal and JSON package feed
├── binpkgs/
│   ├── x86_64/              # Baseline generic packages (rolling release)
│   └── x86_64-v3/           # Microarchitecture-optimized packages (rolling-v3 release)
├── etc/xbps.d/              # Sample client configuration files
├── repo-keys/               # Public RSA verification keys
├── scripts/
│   ├── build-pkg.sh         # Modular builder with generic and --v3 support
│   ├── check-updates.py     # Upstream version and sha256 update monitor
│   ├── generate-matrix.py   # Parallel GitHub Actions matrix generator
│   ├── generate-web.py      # Website and packages.json generator
│   ├── notify-ci.py         # Discord CI/CD build tracker (start/finish/fail)
│   ├── notify-requester.py  # Discord DM bot notification pipeline
│   └── sign-repo.sh         # Cryptographic indexer and RSA signer
├── srcpkgs/                 # Void Linux package templates
└── .github/
    ├── workflows/           # CI/CD and automated issue notification workflows
    └── ISSUE_TEMPLATE/      # Structured package request forms
```

---

## 📄 License & Personal Branding

* **Packaging Code & Scripts**: Licensed under the [MIT License](LICENSE).
* **Personal Branding & Artworks**: Brand names (**CasperGamingOne**, **Games4Everyone**), logos, avatars, and banner artworks are exclusive personal creative assets and may not be reused or modified without prior written consent.
