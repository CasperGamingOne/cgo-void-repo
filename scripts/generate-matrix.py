#!/usr/bin/env python3
"""
generate-matrix.py - Dynamically generates the parallel build matrix for GitHub Actions.

Scans srcpkgs/ for packages needing compilation in generic and/or x86_64-v3 channels.
Outputs GitHub Actions step outputs:
  - matrix: JSON object with 'include' list of { "pkg": name, "channel": "generic"|"x86_64-v3" }
  - needs_build: "true" if any packages need building, "false" otherwise
  - pkgs: space-separated list of unique package names planned
"""

import os
import sys
import json
import urllib.request

V3_PACKAGES = {
    "ananicy-cpp",
    "linux-cachyos-lts",
    "noctalia",
    "umbriel",
    "xdg-desktop-portal-umbriel",
    "vmware-workstation",
}

def get_release_assets(repo: str, token: str):
    """Fetch existing asset names from GitHub Releases for rolling and rolling-v3."""
    headers = {"User-Agent": "CI"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    assets = {"generic": set(), "x86_64-v3": set()}
    tags = [("rolling", "generic"), ("rolling-v3", "x86_64-v3")]

    for tag, key in tags:
        url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.load(resp)
                for asset in data.get("assets", []):
                    name = asset.get("name", "")
                    if name.endswith(".xbps"):
                        assets[key].add(name)
        except Exception as e:
            print(f"Notice: Could not fetch [{tag}] release assets ({e}).")

    return assets


def get_template_metadata(template_path: str):
    """Extract version and revision from an xbps-src template file."""
    ver, rev = None, None
    with open(template_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("version="):
                ver = line.split("=", 1)[1].strip("\"'")
            elif line.startswith("revision="):
                rev = line.split("=", 1)[1].strip("\"'")
            if ver and rev:
                break
    return ver, rev


def main():
    workspace = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
    repo_dir = os.environ.get("REPO_DIR", workspace)
    if not os.path.isdir(os.path.join(repo_dir, "srcpkgs")) and os.path.isdir(os.path.join(workspace, "cgo-void-repo", "srcpkgs")):
        repo_dir = os.path.join(workspace, "cgo-void-repo")

    srcpkgs_dir = os.path.join(repo_dir, "srcpkgs")
    gh_repo = os.environ.get("GITHUB_REPOSITORY", "CasperGamingOne/cgo-void-repo")
    gh_token = os.environ.get("GITHUB_TOKEN", "")
    force = os.environ.get("FORCE_REBUILD", "").lower() == "true"

    existing_assets = get_release_assets(gh_repo, gh_token)

    planned_jobs = []
    unique_pkgs = set()

    for item in sorted(os.listdir(srcpkgs_dir)):
        pkg_path = os.path.join(srcpkgs_dir, item)
        # Skip symlinks (subpackages like headers)
        if os.path.islink(pkg_path) or not os.path.isdir(pkg_path):
            continue

        template = os.path.join(pkg_path, "template")
        if not os.path.isfile(template):
            continue

        ver, rev = get_template_metadata(template)
        if not ver or not rev:
            continue

        expected_bin = f"{item}-{ver}_{rev}.x86_64.xbps"

        # 1. Check Generic
        needs_generic = force or (expected_bin not in existing_assets["generic"])
        if needs_generic:
            planned_jobs.append({"pkg": item, "channel": "generic"})
            unique_pkgs.add(item)
            print(f"==> Plan [generic]: {item} ({expected_bin} missing from rolling)")

        # 2. Check v3 if applicable
        if item in V3_PACKAGES:
            needs_v3 = force or (expected_bin not in existing_assets["x86_64-v3"])
            if needs_v3:
                planned_jobs.append({"pkg": item, "channel": "x86_64-v3"})
                unique_pkgs.add(item)
                print(f"==> Plan [x86_64-v3]: {item} ({expected_bin} missing from rolling-v3)")

    needs_build = len(planned_jobs) > 0
    matrix_json = json.dumps({"include": planned_jobs})

    print(f"\nTotal planned jobs: {len(planned_jobs)}")
    print(f"Unique packages: {len(unique_pkgs)}")

    # Set GitHub Actions outputs
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"matrix={matrix_json}\n")
            f.write(f"needs_build={'true' if needs_build else 'false'}\n")
            f.write(f"pkgs={' '.join(sorted(unique_pkgs))}\n")
    else:
        print(f"OUTPUT: matrix={matrix_json}")
        print(f"OUTPUT: needs_build={'true' if needs_build else 'false'}")
        print(f"OUTPUT: pkgs={' '.join(sorted(unique_pkgs))}")


if __name__ == "__main__":
    main()
