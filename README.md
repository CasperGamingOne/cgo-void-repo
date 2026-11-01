# cgo-void-repo 🐧

Personal XBPS binary package repository for **Void Linux**, maintained by **CasperGamingOne**.

## 📁 Repository Layout

```text
cgo-void-repo/
├── AGENT.md                 # Master instructions & operational guide for AI agents
├── README.md                # Project overview and user instructions
├── etc/
│   └── xbps.d/
│       └── 50-cgo-void-repo.conf   # Client repository configuration template
├── keys/                    # Public signing keys (.rsa.pub / .pem)
├── scripts/                 # Maintenance, build, and signing scripts
│   ├── build-pkg.sh         # Lints and builds a package using xbps-src
│   ├── gen-keys.sh          # Generates RSA signing keys
│   ├── install-local.sh     # Registers local repo and key on this system
│   ├── setup-env.sh         # Clones and bootstraps void-packages
│   └── sign-repo.sh         # Indexes and cryptographically signs packages
├── srcpkgs/                 # Source package templates (xbps-src format)
│   └── cgo-hello/           # Starter demonstration package
└── .github/
    └── workflows/
        └── build-and-release.yml   # Automated CI/CD build & release pipeline
```

## 🚀 Quick Setup for Local Packaging

1. **Bootstrap Build Environment:**
   ```bash
   ./scripts/setup-env.sh
   ```
2. **Generate Signing Keys:**
   ```bash
   ./scripts/gen-keys.sh
   ```
3. **Build a Package:**
   ```bash
   ./scripts/build-pkg.sh cgo-hello
   ```
4. **Sign and Index the Repository:**
   ```bash
   ./scripts/sign-repo.sh
   ```
5. **Enable Local Repository on Host:**
   ```bash
   ./scripts/install-local.sh
   ```

## 📦 How to Install on Other Void Linux Systems

Once published to GitHub Releases:

1. Download and install the public signing key:
   ```bash
   sudo cp keys/cgo-void-repo.rsa.pub /var/db/xbps/keys/cgo-void-repo.pem
   ```
2. Add repository configuration to `/etc/xbps.d/50-cgo-void-repo.conf`:
   ```text
   repository=https://github.com/caspergamingone/cgo-void-repo/releases/latest/download
   ```
3. Update XBPS repository cache:
   ```bash
   sudo xbps-install -S
   ```
