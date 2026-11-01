# cgo-void-repo 🐧

Personal XBPS binary package repository for **Void Linux**, maintained by **CasperGamingOne**.

🌐 **Website & Documentation:** [https://caspergamingone.github.io/cgo-void-repo](https://caspergamingone.github.io/cgo-void-repo)

---

## 📁 Repository Structure

```text
cgo-void-repo/
├── AGENT.md                 # Master operational playbook for AI agents & maintainers
├── README.md                # Project overview and instructions
├── docs/                    # GitHub Pages website & public web distribution
│   ├── .nojekyll            # Prevents Jekyll processing for repodata & assets
│   ├── index.html           # Modern repository landing page & package browser
│   ├── style.css            # Void-themed responsive styling
│   ├── app.js               # Copy handlers & package search filter
│   └── cgo-void-repo.pem    # Public verification key served to clients
├── etc/
│   └── xbps.d/
│       └── 50-cgo-void-repo.conf   # Client XBPS configuration template
├── repo-keys/               # Public signing keys (.pem / .pub) for XBPS clients
│   ├── cgo-void-repo.pem
│   └── cgo-void-repo.rsa.pub
├── scripts/                 # Build, index, and maintenance automation
│   ├── build-pkg.sh         # Lints and builds packages using xbps-src
│   ├── gen-keys.sh          # Generates RSA keys (private key kept OUTSIDE git)
│   ├── install-local.sh     # Registers local repo and key on host system
│   ├── setup-env.sh         # Clones and bootstraps void-packages build engine
│   └── sign-repo.sh         # Indexes and cryptographically signs packages
├── srcpkgs/                 # Package definitions / templates
│   └── cgo-hello/           # Verification package
└── .github/
    └── workflows/
        └── build-and-release.yml   # CI/CD: Builds, signs, and deploys to GitHub Pages & Releases
```

---

## 🔐 Cryptography & Secrets Architecture

To ensure the repository is completely safe to host as a public GitHub repository and deploy to **GitHub Pages**:

* **NO private keys or secrets are stored in this Git repository.**
* **Local Private Key**: Stored outside the repository tree in `~/.local/share/cgo-void-repo/cgo-void-repo.rsa` (permissions `0600`).
* **CI/CD Signing**: Uses encrypted GitHub Actions Secret `RSA_PRIVATE_KEY`.
* **Public Keys**: `repo-keys/cgo-void-repo.pem` and `docs/cgo-void-repo.pem` are public and freely distributable.

---

## 🧩 Compatibility with System & Community Repositories

This repository is designed to coexist cleanly with:
* **Official Void Linux Repositories** (`current`, `multilib`, `nonfree`)
* **XLibre (`xlibre-void`)**: Fully tested on Void systems running the XLibre display stack
* **Third-Party Repositories**: Compatible alongside `gsr4xbps` and `sonicde-void`

---

## 🚀 Quick Setup for Clients

```bash
# 1. Download and trust the public key
sudo wget -O /var/db/xbps/keys/cgo-void-repo.pem https://caspergamingone.github.io/cgo-void-repo/cgo-void-repo.pem

# 2. Add repository source
echo "repository=https://caspergamingone.github.io/cgo-void-repo/x86_64" | sudo tee /etc/xbps.d/50-cgo-void-repo.conf

# 3. Synchronize repository index
sudo xbps-install -S
```
