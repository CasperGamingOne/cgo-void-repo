#!/usr/bin/env python3
"""
generate-web.py - Generate GitHub Pages website & package index for cgo-void-repo.

This script parses srcpkgs/*/template to extract package metadata, builds an
interactive HTML portal and JSON index with architecture switcher, bundles the
public verification keys, copies branding assets, and organizes repo data.
"""

import os
import sys
import re
import json
import shutil
from pathlib import Path

SOURCE_BUILT_PACKAGES = {
    "ananicy-cpp",
    "linux-cachyos-lts",
    "linux-cachyos-lts-headers",
    "noctalia",
    "noctalia-greeter",
    "umbriel",
    "vmware-workstation",
    "xdg-desktop-portal-umbriel",
}

BINARY_PACKAGES = {
    "antigravity",
    "antigravity-ide",
    "artcraft-launcher",
    "cgo-hello",
    "megasync",
}


def parse_template(template_path: Path, pkg_override: str = None) -> dict:
    data = {
        "pkgname": "",
        "version": "",
        "revision": "1",
        "short_desc": "No description provided",
        "homepage": "",
        "license": "Unspecified",
        "maintainer": "",
        "restricted": "no",
    }
    content = template_path.read_text(encoding="utf-8", errors="replace")
    in_function = False
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Stop reading global top-level variables when functions begin
        if line.endswith("()") or line.endswith("() {") or line.endswith("{"):
            in_function = True
        if not in_function:
            for key in data.keys():
                pattern = rf"^{key}=[\"']?(.*?)[\"']?$"
                match = re.match(pattern, line)
                if match:
                    data[key] = match.group(1).strip()

    # Expand any bash parameter expansions in short_desc if present
    if data["version"]:
        v = data["version"]
        major_minor = ".".join(v.split(".")[:2]) if "." in v else v
        data["short_desc"] = data["short_desc"].replace("${version%.*}", major_minor)
        data["short_desc"] = data["short_desc"].replace("${version%%.*}", v.split(".")[0])
        data["short_desc"] = data["short_desc"].replace("${version}", v)

    # Subpackage handling (symlinked packages)
    if pkg_override and pkg_override != data["pkgname"]:
        data["pkgname"] = pkg_override
        func_name = pkg_override.replace("-", "_")
        subpkg_match = re.search(rf"{re.escape(pkg_override)}_package\(\)\s*\{{([^}}]+)\}}", content)
        if not subpkg_match:
            subpkg_match = re.search(rf"{re.escape(func_name)}_package\(\)\s*\{{([^}}]+)\}}", content)

        if subpkg_match:
            body = subpkg_match.group(1)
            desc_set = re.search(r'short_desc=["\']?(.*?)["\']?$', body, re.MULTILINE)
            desc_plus = re.search(r'short_desc\+=["\']?(.*?)["\']?$', body, re.MULTILINE)
            if desc_set:
                data["short_desc"] = desc_set.group(1).strip()
            elif desc_plus:
                data["short_desc"] = f"{data['short_desc']} {desc_plus.group(1).strip()}".strip()
        else:
            if "headers" in pkg_override:
                data["short_desc"] = f"Kernel headers and development files for DKMS modules ({data.get('version', '')})"

    return data


def scan_packages(srcpkgs_dir: Path) -> list:
    packages = []
    seen_pkgnames = set()
    if not srcpkgs_dir.exists():
        return packages
    for item in sorted(srcpkgs_dir.iterdir()):
        template = item / "template"
        if (item.is_dir() or item.is_symlink()) and template.is_file():
            pkg_override = item.name if item.is_symlink() else None
            meta = parse_template(template, pkg_override=pkg_override)
            pkgname = meta.get("pkgname")
            if pkgname and pkgname not in seen_pkgnames:
                seen_pkgnames.add(pkgname)
                packages.append(meta)
    return packages


def generate_html(packages: list, base_url: str) -> str:
    rows = []
    for pkg in packages:
        pkgname = pkg["pkgname"]
        version = f"{pkg['version']}_{pkg['revision']}"
        desc = pkg["short_desc"]
        hp = pkg.get("homepage", "")
        lic = pkg.get("license", "Unspecified")
        restricted = pkg.get("restricted", "no") == "yes"
        hp_link = f' <a href="{hp}" target="_blank" rel="noopener" title="Homepage">🌐</a>' if hp else ""

        is_optimized = pkgname in SOURCE_BUILT_PACKAGES
        if is_optimized:
            channel_badges = (
                '<span class="badge badge-v3" title="Compiled with AVX2/FMA/BMI2 in rolling-v3">⚡ rolling-v3</span> '
                '<span class="badge badge-generic" title="Compiled for generic baseline in rolling">📦 rolling</span>'
            )
        else:
            channel_badges = '<span class="badge badge-universal" title="Available in both rolling and rolling-v3">🌐 All Channels</span>'

        if restricted or "proprietary" in lic.lower() or "google" in lic.lower() or "mega" in lic.lower():
            lic_badge = f'<span class="badge badge-restricted" title="Restricted / EULA license">{lic}</span>'
        else:
            lic_badge = f'<span class="badge badge-foss" title="Free and Open Source Software">{lic}</span>'

        rows.append(f"""
        <tr class="pkg-row">
          <td class="pkg-name"><code>{pkgname}</code>{hp_link}</td>
          <td><code>{version}</code></td>
          <td class="pkg-channels">{channel_badges}</td>
          <td>{lic_badge}</td>
          <td class="pkg-desc">{desc}</td>
        </tr>""")

    package_rows_html = "\n".join(rows) if rows else """
        <tr>
          <td colspan="5" style="text-align: center; color: var(--text-secondary); padding: 2rem;">
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
      <a href="#cpu-check" class="nav-link">CPU Check</a>
      <a href="#compliance" class="nav-link">Licensing</a>
      <a href="#request" class="nav-link">Request</a>
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
      <p>Continuous XBPS binary repository with dual-channel baseline and <strong>x86_64-v3 microarchitecture optimization</strong> by <strong>CasperGamingOne</strong></p>
      <div class="badges">
        <span class="badge badge-g4e">
          <img src="assets/games4everyone-logo.png" style="width: 14px; height: 14px; border-radius: 3px;" alt="G4E">
          Games4Everyone
        </span>
        <span class="badge badge-void">🐧 Void Linux</span>
        <span class="badge">📦 XBPS Native</span>
        <span class="badge badge-v3">⚡ x86_64-v3 Optimized</span>
        <span class="badge">⚙️ x86_64 Baseline</span>
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
        <div class="step-desc">Download and trust the repository RSA signing key in your system's XBPS keyrings:</div>
        <div class="code-box">
          <button class="copy-btn" data-target="cmd-step1">Copy</button>
          <pre id="cmd-step1">sudo wget -O /var/db/xbps/keys/cgo-void-repo.pem {base_url}/cgo-void-repo.pem</pre>
        </div>
      </div>

      <div class="step-item" style="margin-top: 1.5rem;">
        <div class="step-header">
          <span class="step-num">2</span>
          Choose Your Repository Channel
        </div>
        <div class="step-desc">Select the architecture variant suitable for your processor:</div>

        <!-- Architecture Switcher Tabs -->
        <div class="arch-switch-container">
          <button type="button" class="arch-tab-btn active" data-channel="v3">
            <span>⚡ x86_64-v3 (Modern CPUs)</span>
            <span class="tab-chip">Recommended</span>
          </button>
          <button type="button" class="arch-tab-btn" data-channel="generic">
            <span>📦 x86_64 (Generic / Compatibility)</span>
          </button>
        </div>

        <!-- Channel 1: x86_64-v3 -->
        <div class="channel-view" id="view-channel-v3">
          <div class="channel-hint">
            <strong>🚀 Best Performance:</strong> Compiled with <code>-march=x86-64-v3 -O3 -pipe</code> (AVX2, FMA, BMI1/2). Ideal for Intel Haswell (2013+) and AMD Zen (2017+) or newer. Self-contained channel with all packages.
          </div>
          <div class="code-box">
            <button class="copy-btn" data-target="cmd-step2-v3">Copy</button>
            <pre id="cmd-step2-v3">echo "repository=https://github.com/CasperGamingOne/cgo-void-repo/releases/download/rolling-v3" | sudo tee /etc/xbps.d/10-cgo-void-repo.conf</pre>
          </div>
        </div>

        <!-- Channel 2: generic -->
        <div class="channel-view" id="view-channel-generic" style="display: none;">
          <div class="channel-hint">
            <strong>📦 Maximum Compatibility:</strong> Standard baseline 64-bit compilation. Runs safely on any 64-bit x86 hardware, hypervisors, and legacy PCs. Self-contained channel with all packages.
          </div>
          <div class="code-box">
            <button class="copy-btn" data-target="cmd-step2-generic">Copy</button>
            <pre id="cmd-step2-generic">echo "repository=https://github.com/CasperGamingOne/cgo-void-repo/releases/download/rolling" | sudo tee /etc/xbps.d/10-cgo-void-repo.conf</pre>
          </div>
        </div>

      </div>

      <div class="step-item" style="margin-top: 1.5rem;">
        <div class="step-header">
          <span class="step-num">3</span>
          Synchronize & Install
        </div>
        <div class="step-desc">Synchronize package indexes and install packages with native clean names:</div>
        <div class="code-box">
          <button class="copy-btn" data-target="cmd-step3">Copy</button>
          <pre id="cmd-step3">sudo xbps-install -S
sudo xbps-install -S noctalia umbriel vmware-workstation megasync</pre>
        </div>
      </div>

    </div>
  </section>

  <!-- CPU Architecture Checker Card -->
  <section class="section" id="cpu-check">
    <h2 class="section-title">🔍 Check Your CPU Microarchitecture</h2>
    <div class="card">
      <p style="color: var(--text-secondary); margin-bottom: 1rem;">
        Wondering if your CPU supports the <code>x86_64-v3</code> channel? Run this single command in your Void Linux terminal to verify your dynamic linker capabilities:
      </p>
      <div class="code-box">
        <button class="copy-btn" data-target="cmd-cpu-check">Copy</button>
        <pre id="cmd-cpu-check">/lib/ld-linux-x86-64.so.2 --help | grep -E "x86-64-v[234]"</pre>
      </div>
      <div class="cpu-result-guide">
        <div class="cpu-result-item">
          <span class="badge badge-v3">x86-64-v3 (supported, searched)</span>
          <span>Your CPU supports AVX2, FMA, BMI1/2. Use the <strong>rolling-v3</strong> channel!</span>
        </div>
        <div class="cpu-result-item">
          <span class="badge badge-generic">Only x86-64 or x86-64-v2</span>
          <span>Your CPU is baseline/legacy or running in a VM without AVX2. Use the <strong>rolling</strong> channel!</span>
        </div>
      </div>
    </div>
  </section>

  <!-- Package Catalog -->
  <section class="section" id="packages">
    <h2 class="section-title">📦 Package Catalog ({len(packages)} Available)</h2>
    <div class="card">
      <input type="text" id="pkg-search" class="pkg-search" placeholder="Search packages (e.g. noctalia, umbriel, vmware, antigravity)...">
      <div style="overflow-x: auto;">
        <table class="pkg-table">
          <thead>
            <tr>
              <th>Package</th>
              <th>Version</th>
              <th>Channel Availability</th>
              <th>License</th>
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

  <!-- Compliance & Packaging Integrity Card -->
  <section class="section" id="compliance">
    <h2 class="section-title">⚖️ Packaging Guidelines & Licensing Compliance</h2>
    <div class="card">
      <div class="compliance-grid">
        <div class="compliance-item">
          <h3>📜 License Integrity</h3>
          <p>Every package explicitly follows upstream license agreements. Free software (MIT) installs complete license files to <code>/usr/share/licenses/</code> via <code>vlicense</code>. Proprietary software (VMware, Google Antigravity, MegaSync) includes official EULAs and is marked with Void's <code>restricted=yes</code> flag.</p>
        </div>
        <div class="compliance-item">
          <h3>🐧 Void Linux Packaging Standards</h3>
          <p>All templates are linted with <code>xlint</code> (0 warnings). Packages strictly isolate <code>hostmakedepends</code>, <code>makedepends</code>, and runtime <code>depends</code>. Native Runit service scripts are placed in <code>/etc/sv/</code>, and kernel modules are managed cleanly via official DKMS triggers without modifying root partitions.</p>
        </div>
        <div class="compliance-item">
          <h3>🔐 Cryptographic Verification</h3>
          <p>Every <code>.xbps</code> package and repository index (<code>x86_64-repodata</code>) is cryptographically signed using our 4096-bit RSA signing key. Your system verifies signatures locally before installing any package.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Package Request Section -->
  <section class="section" id="request">
    <h2 class="section-title">📥 Request a Package</h2>
    <div class="card">
      <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
        Need software packaged natively for Void Linux? Submit a package request below. Our automated GitHub pipeline registers an Issue Tracking ID, evaluates compatibility, and triggers Discord Direct Message notifications on status updates.
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
            <label class="form-label" for="req-buildsystem">Build System</label>
            <select id="req-buildsystem" class="form-control">
              <option value="meson">Meson / Ninja</option>
              <option value="cmake">CMake</option>
              <option value="cargo">Cargo / Rust</option>
              <option value="gnu-configure">GNU Autotools (configure)</option>
              <option value="python3-pep517">Python (PEP517 / pyproject)</option>
              <option value="go">Go Modules</option>
              <option value="binary">Pre-compiled Binary / Wrapper</option>
              <option value="other">Other / Custom</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label" for="req-license">License <span class="required">*</span></label>
            <input type="text" id="req-license" class="form-control" placeholder="e.g. GPL-3.0-or-later, MIT, Proprietary" required>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="req-description">Description & Purpose <span class="required">*</span></label>
          <textarea id="req-description" class="form-control" rows="3" placeholder="Briefly describe what the program does and why it is useful for Void Linux users..." required></textarea>
        </div>

        <div class="form-group">
          <label class="form-label" for="req-dependencies">Known Dependencies</label>
          <input type="text" id="req-dependencies" class="form-control" placeholder="e.g. ffmpeg, sdl2, opus, qt6-base">
        </div>

        <div class="form-group">
          <label class="form-label" for="req-contact">Discord Handle or ID (for Progress Notifications) <span class="required">*</span></label>
          <input type="text" id="req-contact" class="form-control" placeholder="e.g. caspergamingone or 28392109482019" required>
          <small style="color: var(--text-muted); display: block; margin-top: 0.35rem;">
            Used by our GitHub workflow bot to DM you real-time status updates (Accepted, In Progress, Completed, Denied).
          </small>
        </div>

        <div class="form-group">
          <label class="form-label" for="req-notes">Additional Notes / Special Instructions</label>
          <textarea id="req-notes" class="form-control" rows="2" placeholder="e.g. Needs specific runit service, DKMS module, or desktop integration..."></textarea>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary">
            🚀 Submit Package Request via GitHub Issue
          </button>
        </div>
      </form>
    </div>
  </section>

</main>

<footer class="footer">
  <div class="container footer-content">
    <div class="footer-brand">
      <img src="assets/personal-logo.jpeg" alt="CasperGamingOne" class="footer-logo">
      <div>
        <div style="font-weight: 700; color: #fff;">CasperGamingOne</div>
        <div style="color: var(--text-muted); font-size: 0.85rem;">Games4Everyone • Void Linux Repository</div>
      </div>
    </div>
    <div class="footer-copy">
      Maintained by <a href="https://github.com/CasperGamingOne" target="_blank" rel="noopener">CasperGamingOne</a>.
    </div>
  </div>
</footer>

<script src="app.js"></script>
</body>
</html>"""


def generate_json_index(packages: list, base_url: str) -> dict:
    return {
        "repository": "cgo-void-repo",
        "owner": "CasperGamingOne",
        "brand": "Games4Everyone",
        "channels": {
            "rolling-v3": {
                "name": "Rolling Release (x86_64-v3 Optimized)",
                "url": "https://github.com/CasperGamingOne/cgo-void-repo/releases/download/rolling-v3",
                "cflags": "-O3 -march=x86-64-v3 -pipe",
                "target_cpus": "Intel Haswell+, AMD Zen+ (AVX2, FMA, BMI1/2)",
            },
            "rolling": {
                "name": "Rolling Release (x86_64 Generic)",
                "url": "https://github.com/CasperGamingOne/cgo-void-repo/releases/download/rolling",
                "cflags": "-O2 -pipe",
                "target_cpus": "Universal 64-bit x86",
            },
        },
        "signing_key": f"{base_url}/cgo-void-repo.pem",
        "packages": packages,
    }


def main():
    repo_root = Path(__file__).resolve().parent.parent
    srcpkgs_dir = repo_root / "srcpkgs"
    repo_keys_dir = repo_root / "repo-keys"
    docs_dir = repo_root / "docs"
    assets_dir = repo_root / "assets"
    if not assets_dir.is_dir():
        assets_dir = docs_dir / "assets"
    site_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else docs_dir
    site_dir.mkdir(parents=True, exist_ok=True)

    base_url = "https://caspergamingone.github.io/cgo-void-repo"

    print(f"==> Scanning packages in {srcpkgs_dir}...")
    packages = scan_packages(srcpkgs_dir)
    print(f"Found {len(packages)} packages.")

    print(f"==> Generating website in {site_dir}...")
    html_content = generate_html(packages, base_url)
    (site_dir / "index.html").write_text(html_content, encoding="utf-8")

    json_index = generate_json_index(packages, base_url)
    (site_dir / "packages.json").write_text(json.dumps(json_index, indent=2), encoding="utf-8")

    # Ensure GitHub Pages does not run Jekyll
    (site_dir / ".nojekyll").touch()

    # Copy verification keys
    for key_name in ["cgo-void-repo.pem", "cgo-void-repo.rsa.pub"]:
        for src_dir in [repo_keys_dir, docs_dir]:
            key_file = src_dir / key_name
            if key_file.is_file():
                shutil.copy2(key_file, site_dir / key_name)
                break

    # Copy branding assets
    if assets_dir.is_dir():
        dest_assets = site_dir / "assets"
        dest_assets.mkdir(parents=True, exist_ok=True)
        for img in assets_dir.glob("*"):
            if img.is_file():
                shutil.copy2(img, dest_assets / img.name)

    # Copy website static assets (CSS, JS)
    if site_dir.resolve() != docs_dir.resolve():
        for static_name in ["style.css", "app.js"]:
            src = docs_dir / static_name
            if src.is_file():
                shutil.copy2(src, site_dir / static_name)

    print("==> Website generated successfully!")


if __name__ == "__main__":
    main()
