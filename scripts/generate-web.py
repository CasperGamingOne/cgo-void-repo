#!/usr/bin/env python3
"""
generate-web.py - Generate GitHub Pages website & package index for cgo-void-repo.

This script parses srcpkgs/*/template to extract package metadata, builds an
interactive HTML portal and JSON index, bundles the public verification keys,
copies branding assets, and organizes architecture-specific package directories.
"""

import os
import sys
import re
import json
import shutil
from pathlib import Path


def parse_template(template_path: Path) -> dict:
    data = {
        "pkgname": "",
        "version": "",
        "revision": "1",
        "short_desc": "No description provided",
        "homepage": "",
        "license": "Unspecified",
        "maintainer": "",
    }
    content = template_path.read_text(encoding="utf-8", errors="replace")
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for key in data.keys():
            pattern = rf"^{key}=[\"']?(.*?)[\"']?$"
            match = re.match(pattern, line)
            if match:
                data[key] = match.group(1).strip()
    return data


def scan_packages(srcpkgs_dir: Path) -> list:
    packages = []
    if not srcpkgs_dir.exists():
        return packages
    for item in sorted(srcpkgs_dir.iterdir()):
        template = item / "template"
        if item.is_dir() and template.is_file():
            meta = parse_template(template)
            if meta["pkgname"]:
                packages.append(meta)
    return packages


def generate_html(packages: list, base_url: str) -> str:
    rows = []
    for pkg in packages:
        pkgname = pkg["pkgname"]
        version = f"{pkg['version']}_{pkg['revision']}"
        desc = pkg["short_desc"]
        hp = pkg.get("homepage", "")
        hp_link = f' <a href="{hp}" target="_blank" rel="noopener">🌐</a>' if hp else ""
        rows.append(f"""
        <tr class="pkg-row">
          <td class="pkg-name"><code>{pkgname}</code>{hp_link}</td>
          <td><code>{version}</code></td>
          <td>x86_64</td>
          <td class="pkg-desc">{desc}</td>
        </tr>""")

    package_rows_html = "\n".join(rows) if rows else """
        <tr>
          <td colspan="4" style="text-align: center; color: var(--text-secondary); padding: 2rem;">
            No packages built yet. Templates are available in <code>srcpkgs/</code>.
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>cgo-void-repo | CasperGamingOne's Void Linux Repository</title>
  <link rel="stylesheet" href="style.css">
  <link rel="icon" type="image/jpeg" href="assets/personal-logo.jpeg">
</head>
<body>

<!-- Navigation Bar -->
<nav class="navbar">
  <div class="container nav-content">
    <a href="#" class="nav-brand">
      <img src="assets/personal-logo.jpeg" alt="CasperGamingOne" class="nav-logo">
      <div>
        <span class="nav-title">cgo-void-repo</span>
        <span class="nav-company">Games4Everyone</span>
      </div>
    </a>
    <div class="nav-links">
      <a href="#quick-install" class="nav-link">Install</a>
      <a href="#packages" class="nav-link">Packages</a>
      <a href="#request" class="nav-link">Request</a>
      <a href="#ecosystem" class="nav-link">Ecosystem</a>
      <a href="https://github.com/CasperGamingOne/cgo-void-repo" target="_blank" rel="noopener" class="nav-link">GitHub ↗</a>
    </div>
  </div>
</nav>

<!-- Hero Banner Header -->
<div class="banner-wrapper">
  <img src="assets/banner.jpeg" alt="CasperGamingOne Banner" class="banner-img">
  <div class="banner-overlay"></div>
</div>

<header class="container">
  <div class="hero-card">
    <div class="avatar-wrapper">
      <img src="assets/personal-logo.jpeg" alt="CasperGamingOne Logo" class="hero-avatar">
      <div class="company-badge-float" title="Games4Everyone">
        <img src="assets/games4everyone-logo.png" alt="Games4Everyone Logo">
      </div>
    </div>
    <div class="hero-details">
      <div class="branding-tagline">
        <span>🎮 Games4Everyone</span>
        <span>•</span>
        <span>Void Linux Repository</span>
      </div>
      <h1>cgo-void-repo</h1>
      <p>Personal XBPS binary package repository for Void Linux by <strong>CasperGamingOne</strong></p>
      <div class="badges">
        <span class="badge badge-g4e">
          <img src="assets/games4everyone-logo.png" style="width: 14px; height: 14px; border-radius: 3px;" alt="G4E">
          Games4Everyone
        </span>
        <span class="badge badge-void">🐧 Void Linux</span>
        <span class="badge">📦 XBPS Native</span>
        <span class="badge">⚙️ x86_64</span>
        <span class="badge">🧩 XLibre Ready</span>
        <span class="badge">🔐 RSA Signed</span>
      </div>
    </div>
  </div>
</header>

<main class="container">

  <!-- Quick Installation Section -->
  <section class="section" id="quick-install">
    <h2 class="section-title">⚡ Quick Installation</h2>
    <div class="card">

      <div class="step-item">
        <div class="step-header">
          <span class="step-num">1</span>
          Import Public Verification Key
        </div>
        <div class="step-desc">Download and trust the official RSA signing key in your system's XBPS database:</div>
        <div class="code-box">
          <button class="copy-btn" data-target="cmd-step1">Copy</button>
          <pre id="cmd-step1">sudo wget -O /var/db/xbps/keys/cgo-void-repo.pem {base_url}/cgo-void-repo.pem</pre>
        </div>
      </div>

      <div class="step-item" style="margin-top: 1.5rem;">
        <div class="step-header">
          <span class="step-num">2</span>
          Add Repository Source
        </div>
        <div class="step-desc">Configure XBPS to fetch binary packages directly from the official GitHub Releases distribution:</div>
        <div class="code-box">
          <button class="copy-btn" data-target="cmd-step2">Copy</button>
          <pre id="cmd-step2">echo "repository=https://github.com/CasperGamingOne/cgo-void-repo/releases/latest/download" | sudo tee /etc/xbps.d/50-cgo-void-repo.conf</pre>
        </div>
      </div>

      <div class="step-item" style="margin-top: 1.5rem;">
        <div class="step-header">
          <span class="step-num">3</span>
          Synchronize & Install
        </div>
        <div class="step-desc">Update your XBPS index and install packages:</div>
        <div class="code-box">
          <button class="copy-btn" data-target="cmd-step3">Copy</button>
          <pre id="cmd-step3">sudo xbps-install -S
sudo xbps-install &lt;package-name&gt;</pre>
        </div>
      </div>

    </div>
  </section>

  <!-- Package Catalog -->
  <section class="section" id="packages">
    <h2 class="section-title">📦 Package Catalog ({len(packages)} Available)</h2>
    <div class="card">
      <input type="text" id="pkg-search" class="pkg-search" placeholder="Search packages (e.g. cgo-hello, games, tools)...">
      <div style="overflow-x: auto;">
        <table class="pkg-table">
          <thead>
            <tr>
              <th>Package</th>
              <th>Version</th>
              <th>Architecture</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody id="pkg-table-body">
{package_rows_html}
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- Package Request Section -->
  <section class="section" id="request">
    <h2 class="section-title">📥 Request a Package</h2>
    <div class="card">
      <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
        Need software packaged natively for Void Linux? Submit a package request below. Our automated GitHub pipeline registers an Issue Tracking ID, evaluates compatibility, and triggers Discord / email notifications upon status updates.
      </p>

      <form id="package-request-form">
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="req-pkgname">Package Name <span class="required">*</span></label>
            <input type="text" id="req-pkgname" class="form-control" placeholder="e.g. moonlight-qt" required>
          </div>
          <div class="form-group">
            <label class="form-label" for="req-homepage">Official Website / Homepage <span class="required">*</span></label>
            <input type="url" id="req-homepage" class="form-control" placeholder="https://moonlight-stream.org" required>
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="req-upstream">Source Code Repository <span class="required">*</span></label>
            <input type="url" id="req-upstream" class="form-control" placeholder="https://github.com/moonlight-stream/moonlight-qt" required>
          </div>
          <div class="form-group">
            <label class="form-label" for="req-version">Latest Stable Version & Download URL <span class="required">*</span></label>
            <input type="text" id="req-version" class="form-control" placeholder="e.g. 6.1.0 (https://...)" required>
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="req-buildsystem">Build System / Language</label>
            <select id="req-buildsystem" class="form-control">
              <option value="CMake (C / C++)">CMake (C / C++)</option>
              <option value="Meson / Ninja (C / C++)">Meson / Ninja (C / C++)</option>
              <option value="Cargo (Rust)">Cargo (Rust)</option>
              <option value="Go (golang)">Go (golang)</option>
              <option value="Python (PEP 517 / wheel)">Python (PEP 517 / wheel)</option>
              <option value="Autotools / Make">Autotools / Make</option>
              <option value="Pre-built Binary Repackage">Pre-built Binary Repackage</option>
              <option value="Other / Unknown">Other / Unknown</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label" for="req-license">License <span class="required">*</span></label>
            <input type="text" id="req-license" class="form-control" placeholder="e.g. GPL-3.0, MIT, Proprietary" required>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="req-description">Description & Purpose <span class="required">*</span></label>
          <textarea id="req-description" class="form-control" rows="3" placeholder="Briefly describe what this software does and why Void Linux users would benefit from it..." required></textarea>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="req-dependencies">Known Dependencies</label>
            <input type="text" id="req-dependencies" class="form-control" placeholder="e.g. qt6-base, ffmpeg, libva, alsa-lib">
          </div>
          <div class="form-group">
            <label class="form-label" for="req-contact">Discord for Status DM Alerts <span class="required">*</span></label>
            <input type="text" id="req-contact" class="form-control" placeholder="18-digit Discord User ID or @username" required>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Void Linux Considerations</label>
          <div class="form-checkbox-grid">
            <label class="form-checkbox-label">
              <input type="checkbox" class="req-void-spec" value="Requires runit background service (/etc/sv/)">
              Runit Service (/etc/sv/)
            </label>
            <label class="form-checkbox-label">
              <input type="checkbox" class="req-void-spec" value="Requires DKMS kernel module (/usr/src/)">
              DKMS Kernel Module
            </label>
            <label class="form-checkbox-label">
              <input type="checkbox" class="req-void-spec" value="Requires desktop integration (.desktop & icons)">
              Desktop & Icons (.desktop)
            </label>
            <label class="form-checkbox-label">
              <input type="checkbox" class="req-void-spec" value="Glibc only (incompatible with musl)">
              Glibc only (not musl)
            </label>
            <label class="form-checkbox-label">
              <input type="checkbox" class="req-void-spec" value="Requires proprietary drivers / firmware">
              Proprietary Drivers / Firmware
            </label>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="req-notes">Additional Context / References</label>
          <textarea id="req-notes" class="form-control" rows="2" placeholder="Links to AUR PKGBUILD, Nix derivation, build flags, or special setup instructions..."></textarea>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary">
            🚀 Submit Package Request
          </button>
        </div>

        <div class="form-notice-box">
          <div>💡</div>
          <div>
            <strong>How Direct Discord DMs Work:</strong>
            Submitting registers a GitHub Issue with an assigned <strong>Issue Tracking ID</strong> (e.g. <code>#12</code>). Whenever the status updates (<strong>Accepted</strong>, <strong>In Progress</strong>, <strong>Completed</strong>, or <strong>Denied</strong>), our automation bot directly DMs you on Discord with live progress!
          </div>
        </div>
      </form>
    </div>
  </section>

  <!-- Ecosystem & Compatibility -->
  <section class="section" id="ecosystem">
    <h2 class="section-title">🧩 Ecosystem & Compatibility</h2>
    <div class="card">
      <p style="color: var(--text-secondary);">This repository is maintained by <strong>CasperGamingOne</strong> under the <strong>Games4Everyone</strong> project, engineered to coexist cleanly with your Void Linux setup:</p>
      
      <div class="ecosystem-grid">
        <div class="ecosystem-item">
          <h3>🐧 Official Void Linux</h3>
          <p>Fully compliant with upstream Void packages (glibc and musl) and standard xbps packaging conventions.</p>
        </div>
        <div class="ecosystem-item">
          <h3>🖥️ XLibre Display Stack</h3>
          <p>Engineered and tested alongside <code>xlibre-void</code> display servers and hardware drivers without package conflicts.</p>
        </div>
        <div class="ecosystem-item">
          <h3>🎮 Games4Everyone Ecosystem</h3>
          <p>Tailored gaming tools, desktop enhancements, and utilities for the modern Linux workstation.</p>
        </div>
      </div>

      <div class="info-callout" style="margin-top: 1.25rem;">
        <strong>Security & Cryptography:</strong> All packages are signed with RSA-2048 keys. Build pipelines run in clean, isolated Void containers via GitHub Actions.
      </div>
    </div>
  </section>

</main>

<footer>
  <div class="container">
    <div class="footer-brand">
      <img src="assets/games4everyone-logo.png" alt="Games4Everyone" class="footer-logo">
      <span><strong>Games4Everyone</strong> • CasperGamingOne</span>
    </div>
    <p>Powered by <a href="https://voidlinux.org" target="_blank" rel="noopener">Void Linux</a> & <a href="https://pages.github.com" target="_blank" rel="noopener">GitHub Pages</a> • <a href="https://github.com/CasperGamingOne/cgo-void-repo">Source Repository</a> • <a href="https://github.com/CasperGamingOne/cgo-void-repo/blob/main/LICENSE">License</a></p>
    <p style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-muted);">
      Software and packaging templates licensed under MIT. Personal branding, logos, and banner artworks belong solely to CasperGamingOne (Games4Everyone) and require prior consent for use.
    </p>
  </div>
</footer>

<script src="app.js"></script>
</body>
</html>
"""


def main():
    repo_root = Path(__file__).resolve().parent.parent
    srcpkgs_dir = repo_root / "srcpkgs"
    docs_dir = repo_root / "docs"
    keys_dir = repo_root / "repo-keys"

    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else repo_root / "site"
    out_dir.mkdir(parents=True, exist_ok=True)

    base_url = os.environ.get("PAGES_URL", "https://caspergamingone.github.io/cgo-void-repo")
    print(f"==> Generating website into: {out_dir}")
    print(f"==> Base URL: {base_url}")

    # 1. Parse packages
    packages = scan_packages(srcpkgs_dir)
    print(f"==> Discovered {len(packages)} package(s): {[p['pkgname'] for p in packages]}")

    # 2. Write packages.json
    (out_dir / "packages.json").write_text(json.dumps(packages, indent=2), encoding="utf-8")

    # 3. Write index.html
    html_content = generate_html(packages, base_url)
    (out_dir / "index.html").write_text(html_content, encoding="utf-8")

    # 4. Copy static assets from docs (style.css, app.js, .nojekyll)
    for asset in ["style.css", "app.js", ".nojekyll"]:
        src = docs_dir / asset
        dst = out_dir / asset
        if src.exists():
            if src.resolve() != dst.resolve():
                shutil.copy2(src, dst)
        elif asset == ".nojekyll":
            dst.touch()

    # 5. Copy branding assets directory (assets/)
    assets_src = docs_dir / "assets"
    assets_dst = out_dir / "assets"
    if assets_src.exists() and assets_src.resolve() != assets_dst.resolve():
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)
        print(f"==> Copied branding assets to {assets_dst}")

    # 6. Copy public verification keys
    for key_file in keys_dir.glob("*.pem"):
        shutil.copy2(key_file, out_dir / key_file.name)
    for key_file in keys_dir.glob("*.pub"):
        shutil.copy2(key_file, out_dir / key_file.name)

    print("==> Website generation complete!")


if __name__ == "__main__":
    main()
