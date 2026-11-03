#!/usr/bin/env python3
"""
notify-ci.py - Discord Webhook Notification Tracker for GitHub Actions CI/CD.

Sends rich Discord embed cards when GitHub Actions workflows:
- Start (🚀 Started)
- Succeed (✅ Succeeded)
- Fail (❌ Failed)
- Are Cancelled (⚠️ Cancelled)

Requires:
  DISCORD_WEBHOOK (GitHub Actions Secret / Environment variable)
"""

import os
import sys
import json
import urllib.request
import urllib.error
import subprocess

AVATAR_URL = "https://caspergamingone.github.io/cgo-void-repo/assets/games4everyone-logo.png"
FOOTER_ICON = "https://caspergamingone.github.io/cgo-void-repo/assets/personal-logo.jpeg"
REPO_WEB_URL = "https://caspergamingone.github.io/cgo-void-repo"

STATUS_MAP = {
    "started": {
        "title": "🚀 CI Build Started",
        "color": 0x38BDF8, # Cyan
        "desc_prefix": "A new build workflow has been initiated.",
    },
    "success": {
        "title": "✅ CI Build Succeeded",
        "color": 0x22C55E, # Emerald Green
        "desc_prefix": "All packages compiled, signed, and published successfully!",
    },
    "failure": {
        "title": "❌ CI Build Failed",
        "color": 0xEF4444, # Crimson Red
        "desc_prefix": "Build or deployment pipeline encountered an error.",
    },
    "cancelled": {
        "title": "⚠️ CI Build Cancelled",
        "color": 0x6B7280, # Gray
        "desc_prefix": "The workflow run was manually cancelled or aborted.",
    },
}


def get_git_commit_info():
    """Extract commit sha, message, and author from git or environment."""
    sha = os.environ.get("GITHUB_SHA", "")
    short_sha = sha[:7] if sha else "unknown"
    commit_msg = ""
    author = os.environ.get("GITHUB_ACTOR", "CI")

    try:
        commit_msg = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        commit_msg = os.environ.get("GITHUB_EVENT_NAME", "Triggered event")

    return short_sha, commit_msg, author


def determine_finish_status():
    """Inspect job results passed via environment variables to determine overall status."""
    results = [
        os.environ.get("BUILD_RESULT", ""),
        os.environ.get("PAGES_RESULT", ""),
        os.environ.get("GENERIC_RESULT", ""),
        os.environ.get("V3_RESULT", ""),
    ]
    # Filter out empty strings
    results = [r.lower() for r in results if r]

    if any(r == "failure" for r in results):
        return "failure"
    elif any(r == "cancelled" for r in results):
        return "cancelled"
    elif all(r in ("success", "skipped") for r in results) and "success" in results:
        return "success"
    else:
        # Default fallback
        return "success" if results and all(r == "success" for r in results) else "failure"


def build_embed(status_key: str, custom_message: str = "") -> dict:
    config = STATUS_MAP.get(status_key, STATUS_MAP["started"])
    repo = os.environ.get("GITHUB_REPOSITORY", "CasperGamingOne/cgo-void-repo")
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_num = os.environ.get("GITHUB_RUN_NUMBER", "1")
    workflow = os.environ.get("GITHUB_WORKFLOW", "Build, Sign and Deploy cgo-void-repo")
    ref_name = os.environ.get("GITHUB_REF_NAME", "main")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "push")

    short_sha, commit_msg, author = get_git_commit_info()
    run_url = f"{server_url}/{repo}/actions/runs/{run_id}" if run_id else f"{server_url}/{repo}/actions"
    commit_url = f"{server_url}/{repo}/commit/{os.environ.get('GITHUB_SHA', '')}"

    fields = [
        {
            "name": "Commit",
            "value": f"[`{short_sha}`]({commit_url}) {commit_msg}" if commit_msg else f"`{short_sha}`",
            "inline": False,
        },
        {
            "name": "Branch / Tag",
            "value": f"`{ref_name}`",
            "inline": True,
        },
        {
            "name": "Triggered By",
            "value": f"@{author} (`{event_name}`)",
            "inline": True,
        },
        {
            "name": "Workflow Run",
            "value": f"[Run #{run_num}]({run_url})",
            "inline": True,
        },
    ]

    # Additional breakdown for completion
    if status_key in ("success", "failure", "cancelled"):
        job_breakdown = []
        jobs = [
            ("Build Packages", os.environ.get("BUILD_RESULT")),
            ("Deploy Website", os.environ.get("PAGES_RESULT")),
            ("Generic Release", os.environ.get("GENERIC_RESULT")),
            ("v3 Release", os.environ.get("V3_RESULT")),
        ]
        status_icons = {
            "success": "✅",
            "failure": "❌",
            "cancelled": "⚠️",
            "skipped": "⏭️",
        }
        for name, res in jobs:
            if res:
                icon = status_icons.get(res.lower(), "❓")
                job_breakdown.append(f"{icon} **{name}**: `{res}`")

        if job_breakdown:
            fields.append({
                "name": "Pipeline Breakdown",
                "value": "\n".join(job_breakdown),
                "inline": False,
            })

    if custom_message:
        fields.append({
            "name": "Details",
            "value": custom_message,
            "inline": False,
        })

    # Resource links
    fields.append({
        "name": "Links",
        "value": f"[🌐 Repository Website]({REPO_WEB_URL}) • [📦 Releases]({server_url}/{repo}/releases) • [📋 CI Logs]({run_url})",
        "inline": False,
    })

    return {
        "title": f"{config['title']} • {workflow}",
        "url": run_url,
        "description": config["desc_prefix"],
        "color": config["color"],
        "fields": fields,
        "footer": {
            "text": "cgo-void-repo • Games4Everyone Void Linux Engine",
            "icon_url": FOOTER_ICON,
        },
    }


def send_webhook(webhook_url: str, embed: dict) -> bool:
    payload = json.dumps({
        "username": "cgo-void-repo CI",
        "avatar_url": AVATAR_URL,
        "embeds": [embed],
    }).encode("utf-8")

    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "cgo-void-ci-notifier/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"--> Discord CI notification posted successfully (HTTP {resp.status}).")
            return True
    except urllib.error.HTTPError as e:
        print(f"--> Error posting Discord CI webhook: HTTP {e.code} - {e.read().decode('utf-8', errors='ignore')}")
        return False
    except Exception as e:
        print(f"--> Error posting Discord CI webhook: {e}")
        return False


def main():
    webhook_url = (os.environ.get("DISCORD_CI_WEBHOOK") or os.environ.get("DISCORD_WEBHOOK") or "").strip()
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "started"
    custom_msg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if action == "finish":
        action = determine_finish_status()

    if not webhook_url:
        print("--> Notice: DISCORD_WEBHOOK environment variable is not configured. Skipping Discord CI alert.")
        sys.exit(0)

    print(f"--> Dispatching Discord CI notification: action='{action}'...")
    embed = build_embed(action, custom_msg)
    send_webhook(webhook_url, embed)


if __name__ == "__main__":
    main()
