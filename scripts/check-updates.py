#!/usr/bin/env python3
"""
check-updates.py - Modular upstream release checker and template updater for cgo-void-repo.

Usage:
    python3 scripts/check-updates.py [pkgname] [--check-only]

Examples:
    python3 scripts/check-updates.py antigravity
    python3 scripts/check-updates.py antigravity-ide
    python3 scripts/check-updates.py --all
"""

import sys
import os
import re
import json
import urllib.request
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRCPKGS_DIR = REPO_ROOT / "srcpkgs"

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}


def fetch_github_release(repo: str):
    """Fetches the latest release or tag from a GitHub repository."""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tag = data.get("tag_name", "")
            if tag:
                ver = tag.lstrip("v")
                tarball_url = f"https://github.com/{repo}/archive/refs/tags/{tag}.tar.gz"
                return {"version": ver, "tag": tag, "url": tarball_url}
    except Exception:
        pass

    # Fallback to tags
    try:
        tags_url = f"https://api.github.com/repos/{repo}/tags"
        req = urllib.request.Request(tags_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data:
                tag = data[0].get("name", "")
                ver = tag.lstrip("v")
                tarball_url = f"https://github.com/{repo}/archive/refs/tags/{tag}.tar.gz"
                return {"version": ver, "tag": tag, "url": tarball_url}
    except Exception:
        pass
    return None


def fetch_official_download_page():
    url = "https://antigravity.google/download?os=linux"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def fetch_megasync_metadata():
    """Scrapes latest Debian 12 package from Mega's official Linux repository."""
    url = "https://mega.nz/linux/repo/Debian_12/amd64/"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    matches = re.findall(r"megasync_([0-9\.]+)-([0-9\.]+)_amd64\.deb", html)
    if matches:
        def ver_key(item):
            return [int(x) if x.isdigit() else 0 for x in item[0].split(".")]
        latest = sorted(matches, key=ver_key, reverse=True)[0]
        ver, debrev = latest
        return {
            "version": ver,
            "debrev": debrev,
            "url": f"https://mega.nz/linux/repo/Debian_12/amd64/megasync_{ver}-{debrev}_amd64.deb"
        }
    return None


def get_latest_upstream_metadata():
    """Scrapes latest release URLs from the official portal."""
    html = fetch_official_download_page()

    metadata = {}

    # Match antigravity hub:
    # https://storage.googleapis.com/antigravity-public/antigravity-hub/2.28.2-5937220255875072/linux-x64/Antigravity.tar.gz
    hub_match = re.search(
        r"storage\.googleapis\.com/antigravity-public/antigravity-hub/([0-9\.]+)-([0-9]+)/linux-x64/Antigravity\.tar\.gz",
        html,
    )
    if hub_match:
        ver, build = hub_match.groups()
        metadata["antigravity"] = {
            "version": ver,
            "buildver": build,
            "url": f"https://storage.googleapis.com/antigravity-public/antigravity-hub/{ver}-{build}/linux-x64/Antigravity.tar.gz",
        }

    # Match antigravity-ide:
    # https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/2.6.0-5526304964083712/linux-x64/Antigravity%20IDE.tar.gz
    ide_match = re.search(
        r"edgedl\.me\.gvt1\.com/edgedl/release2/j0qc3/antigravity/stable/([0-9\.]+)-([0-9]+)/linux-x64/Antigravity(?:%20|\s)IDE\.tar\.gz",
        html,
    )
    if ide_match:
        ver, build = ide_match.groups()
        metadata["antigravity-ide"] = {
            "version": ver,
            "buildver": build,
            "url": f"https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{ver}-{build}/linux-x64/Antigravity%20IDE.tar.gz",
        }

    return metadata


def read_template_vars(template_path: Path):
    content = template_path.read_text(encoding="utf-8")
    vars_dict = {}
    for line in content.splitlines():
        m = re.match(r"^([a-zA-Z0-9_]+)=[\"']?([^\"']*)[\"']?$", line.strip())
        if m:
            vars_dict[m.group(1)] = m.group(2)
    return vars_dict, content


def compute_sha256(url: str):
    print(f"--> Calculating SHA-256 for: {url}")
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        h = hashlib.sha256()
        while chunk := resp.read(2 * 1024 * 1024):
            h.update(chunk)
        return h.hexdigest()


def update_package(pkgname: str, check_only: bool = False):
    template_path = SRCPKGS_DIR / pkgname / "template"
    if not template_path.exists():
        print(f"ERROR: Template not found at {template_path}", file=sys.stderr)
        return False, None

    current_vars, original_content = read_template_vars(template_path)
    current_ver = current_vars.get("version")
    current_build = current_vars.get("_buildver")
    current_debrev = current_vars.get("_debrev")

    if pkgname in ["noctalia", "noctalia-greeter"]:
        repo = f"noctalia-dev/{pkgname}"
        print(f"[{pkgname}] Current local version: {current_ver}")
        target = fetch_github_release(repo)
        if not target:
            print(f"[{pkgname}] Unable to extract release info from GitHub API for {repo}.", file=sys.stderr)
            return False, None
        up_ver = target["version"]
        up_url = target["url"]
        print(f"[{pkgname}] Latest upstream release: {up_ver}")

        if current_ver == up_ver:
            print(f"[{pkgname}] Package is already up to date ({current_ver}).")
            return False, current_ver

        print(f"[{pkgname}] NEW VERSION DETECTED: {current_ver} -> {up_ver}")
        if check_only:
            return True, up_ver

        new_hash = compute_sha256(up_url)
        print(f"[{pkgname}] Computed SHA-256: {new_hash}")

        content = original_content
        content = re.sub(r"^version=.*$", f"version={up_ver}", content, flags=re.MULTILINE)
        content = re.sub(r"^revision=.*$", "revision=1", content, flags=re.MULTILINE)
        content = re.sub(r"^checksum=.*$", f"checksum={new_hash}", content, flags=re.MULTILINE)

        template_path.write_text(content, encoding="utf-8")
        print(f"[{pkgname}] Successfully updated {template_path} to {up_ver}!")
        return True, up_ver

    if pkgname == "megasync":
        print(f"[{pkgname}] Current local version: {current_ver}-{current_debrev}")
        target = fetch_megasync_metadata()
        if not target:
            print(f"[{pkgname}] Unable to extract upstream metadata from Mega Linux repository.", file=sys.stderr)
            return False, None
        up_ver = target["version"]
        up_debrev = target["debrev"]
        up_url = target["url"]
        print(f"[{pkgname}] Latest upstream version: {up_ver}-{up_debrev}")

        if current_ver == up_ver and current_debrev == up_debrev:
            print(f"[{pkgname}] Package is already up to date ({current_ver}-{current_debrev}).")
            return False, current_ver

        print(f"[{pkgname}] NEW VERSION DETECTED: {current_ver}-{current_debrev} -> {up_ver}-{up_debrev}")
        if check_only:
            return True, up_ver

        new_hash = compute_sha256(up_url)
        print(f"[{pkgname}] Computed SHA-256: {new_hash}")

        content = original_content
        content = re.sub(r"^version=.*$", f"version={up_ver}", content, flags=re.MULTILINE)
        content = re.sub(r"^_debrev=.*$", f"_debrev={up_debrev}", content, flags=re.MULTILINE)
        content = re.sub(r"^revision=.*$", "revision=1", content, flags=re.MULTILINE)
        content = re.sub(r"^checksum=.*$", f"checksum={new_hash}", content, flags=re.MULTILINE)

        template_path.write_text(content, encoding="utf-8")
        print(f"[{pkgname}] Successfully updated {template_path} to {up_ver}-{up_debrev}!")
        return True, up_ver

    print(f"[{pkgname}] Current local version: {current_ver} (build: {current_build})")

    upstream_meta = get_latest_upstream_metadata()
    if pkgname not in upstream_meta:
        print(f"[{pkgname}] Unable to extract upstream metadata from release page.", file=sys.stderr)
        return False, None

    target = upstream_meta[pkgname]
    up_ver = target["version"]
    up_build = target["buildver"]
    up_url = target["url"]

    print(f"[{pkgname}] Latest upstream version: {up_ver} (build: {up_build})")

    if current_ver == up_ver and current_build == up_build:
        print(f"[{pkgname}] Package is already up to date ({current_ver}).")
        return False, current_ver

    print(f"[{pkgname}] NEW VERSION DETECTED: {current_ver} -> {up_ver} (build: {up_build})")

    if check_only:
        return True, up_ver

    new_hash = compute_sha256(up_url)
    print(f"[{pkgname}] Computed SHA-256: {new_hash}")

    # Rewrite template content with updated version, buildver, revision, and checksum
    content = original_content
    content = re.sub(r"^version=.*$", f"version={up_ver}", content, flags=re.MULTILINE)
    content = re.sub(r"^_buildver=.*$", f"_buildver={up_build}", content, flags=re.MULTILINE)
    content = re.sub(r"^revision=.*$", "revision=1", content, flags=re.MULTILINE)
    content = re.sub(r"^checksum=.*$", f"checksum={new_hash}", content, flags=re.MULTILINE)

    template_path.write_text(content, encoding="utf-8")
    print(f"[{pkgname}] Successfully updated {template_path} to {up_ver}!")
    return True, up_ver


def main():
    check_only = "--check-only" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    packages = ["antigravity", "antigravity-ide", "megasync", "noctalia", "noctalia-greeter"] if not args or args[0] == "--all" else args

    updated_packages = []
    for pkg in packages:
        print(f"\n=== Checking updates for {pkg} ===")
        is_updated, ver = update_package(pkg, check_only=check_only)
        if is_updated:
            updated_packages.append((pkg, ver))

    print("\n=== Summary ===")
    if updated_packages:
        print(f"Updates found for {len(updated_packages)} package(s):")
        for pkg, ver in updated_packages:
            print(f"  - {pkg}: {ver}")
        sys.exit(0 if not check_only else 10)
    else:
        print("All packages are completely up to date.")
        sys.exit(0)


if __name__ == "__main__":
    main()
