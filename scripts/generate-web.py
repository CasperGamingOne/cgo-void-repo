#!/usr/bin/env python3
"""
generate-web.py - Generate GitHub Pages website & package index for cgo-void-repo.

This script parses srcpkgs/*/template to extract package metadata, builds an
interactive HTML portal and JSON index, bundles the public verification keys,
and organizes architecture-specific package directories for GitHub Pages.
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
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220%22><text y=%2226%22 font-size=%2224%22>🐧</text></svg>">
</head>
<body>

<header>
  <div class="container hero">
    <div class="logo-circle">🐧</div>
    <div class="hero-text">
      <h1>cgo-void-repo</h1>
      <p>Personal XBPS binary package repository for Void Linux by <strong>CasperGamingOne</strong></p>
      <div class="badges">
        <span class="badge">Void Linux</span>
        <span class="badge">XBPS Native</span>
        <span class="badge">x86_64 / musl</span>
        <span class="badge badge-xlibre">XLibre Compatible</span>
        <span class="badge">Automated CI/CD</span>
      </div>
    </div>
  </div>
</header>

<main class="container">

  <!-- Quick Installation Section -->
  <section class="section">
    <h2 class="section-title">⚡ Quick Installation</h2>
    <div class="card">

      <div class="step-item">
        <div class="step-header">Step 1: Import Repository Public Key</div>
        <div class="step-desc">Download and register the public RSA verification key into XBPS trusted keys:</div>
        <div class="code-box">
          <button class="copy-btn" data-target="cmd-step1">Copy</button>
          <pre id="cmd-step1">sudo wget -O /var/db/xbps/keys/cgo-void-repo.pem {base_url}/cgo-void-repo.pem</pre>
        </div>
      </div>

      <div class="step-item" style="margin-top: 1.5rem;">
        <div class="step-header">Step 2: Add Repository Source</div>
        <div class="step-desc">Configure XBPS to fetch binary packages directly from this GitHub Pages site:</div>
        <div class="code-box">
          <button class="copy-btn" data-target="cmd-step2">Copy</button>
          <pre id="cmd-step2">echo "repository={base_url}/x86_64" | sudo tee /etc/xbps.d/50-cgo-void-repo.conf</pre>
        </div>
        <div class="info-callout" style="margin-top: 0.75rem;">
          <em>Alternative:</em> GitHub Releases source:
          <code>repository=https://github.com/CasperGamingOne/cgo-void-repo/releases/latest/download</code>
        </div>
      </div>

      <div class="step-item" style="margin-top: 1.5rem;">
        <div class="step-header">Step 3: Synchronize and Install</div>
        <div class="step-desc">Update your XBPS index and install packages:</div>
        <div class="code-box">
          <button class="copy-btn" data-target="cmd-step3">Copy</button>
          <pre id="cmd-step3">sudo xbps-install -S
sudo xbps-install &lt;package-name&gt;</pre>
        </div>
      </div>

    </div>
  </section>

  <!-- Ecosystem & Compatibility -->
  <section class="section">
    <h2 class="section-title">🧩 Ecosystem & Compatibility</h2>
    <div class="card">
      <p>This repository is built continuously via GitHub Actions and verified against:</p>
      <ul style="margin: 0.75rem 0 0.75rem 1.5rem; color: var(--text-secondary);">
        <li><strong style="color: var(--text-primary)">Official Void Repositories:</strong> Fully compatible with official Void glibc and musl packages.</li>
        <li><strong style="color: var(--text-primary)">XLibre (xlibre-void):</strong> Optimized and compatible with systems running XLibre modular display servers and drivers.</li>
        <li><strong style="color: var(--text-primary)">Community Repositories:</strong> Coexists safely with <code>gsr4xbps</code> and <code>sonicde-void</code>.</li>
      </ul>
      <div class="info-callout">
        <strong>Automated & Secure:</strong> Built inside isolated Void Linux containers. Repodata is signed using RSA cryptography. All private keys remain safely stored in encrypted GitHub Secrets.
      </div>
    </div>
  </section>

  <!-- Available Packages -->
  <section class="section">
    <h2 class="section-title">📦 Package Catalog ({len(packages)} Packages)</h2>
    <div class="card">
      <input type="text" id="pkg-search" class="pkg-search" placeholder="Filter packages by name, description, or keyword...">
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

</main>

<footer>
  <div class="container">
    <p>Maintained by <a href="https://github.com/CasperGamingOne">CasperGamingOne</a> • Automatically built & deployed via <a href="https://github.com/CasperGamingOne/cgo-void-repo/actions">GitHub Actions</a></p>
  </div>
</footer>

<script src="app.js"></script>
</body>
</html>
"""


def main():
    repo_root = Path(__file__).resolve().parent.parent
    srcpkgs_dir = repo_root / "srcpkgs"
    docs_template_dir = repo_root / "docs"
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
        src = docs_template_dir / asset
        if src.exists():
            shutil.copy2(src, out_dir / asset)
        elif asset == ".nojekyll":
            (out_dir / ".nojekyll").touch()

    # 5. Copy public verification keys
    for key_file in keys_dir.glob("*.pem"):
        shutil.copy2(key_file, out_dir / key_file.name)
    for key_file in keys_dir.glob("*.pub"):
        shutil.copy2(key_file, out_dir / key_file.name)

    print("==> Website generation complete!")


if __name__ == "__main__":
    main()
