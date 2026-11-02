#!/usr/bin/env python3
"""
notify-requester.py - Automated status notification dispatcher for cgo-void-repo.

Alerts package requesters directly via:
1. Discord DM (via Discord Bot API using user ID or guild member search)
2. Email (via standard SMTP)

Tracks 4 canonical statuses:
- accepted
- in progress
- completed
- denied
"""

import os
import sys
import json
import re
import smtplib
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

STATUS_CONFIG = {
    "accepted": {
        "label": "Accepted",
        "emoji": "✅",
        "color": 0x22C55E, # Green
        "description": "Your package request has been accepted and is approved for packaging.",
    },
    "in progress": {
        "label": "In Progress",
        "emoji": "⚙️",
        "color": 0x38BDF8, # Cyan
        "description": "A Void Linux xbps template is actively being written and tested for this package.",
    },
    "completed": {
        "label": "Completed",
        "emoji": "🎉",
        "color": 0xA855F7, # Purple
        "description": "The package has been successfully built, signed with RSA, and published to the repository!",
    },
    "denied": {
        "label": "Denied",
        "emoji": "❌",
        "color": 0xEF4444, # Red
        "description": "This request could not be fulfilled at this time. Please see the issue comments for maintainer details.",
    },
}


def parse_issue_contact(issue_body: str) -> dict:
    """Extract email and discord handles from the issue template body."""
    info = {
        "email": None,
        "discord_id": None,
        "discord_username": None,
        "package_name": None
    }

    if not issue_body:
        return info

    # 1. Package Name
    pkg_match = re.search(r"### Package Name\s*\n+([^\n\r]+)", issue_body, re.IGNORECASE)
    if not pkg_match:
        pkg_match = re.search(r"Package Name[:\*]*\s*([a-zA-Z0-9_\-\.]+)", issue_body)
    if pkg_match:
        info["package_name"] = pkg_match.group(1).strip("` ")

    # 2. Email detection
    email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", issue_body)
    if email_match:
        info["email"] = email_match.group(0).strip()

    # 3. Discord detection (Snowflake User ID or username)
    # Check for 17-20 digit user ID
    id_match = re.search(r"(?:discord|id|user)[\s:]*([0-9]{17,20})", issue_body, re.IGNORECASE)
    if not id_match:
        id_match = re.search(r"\b([0-9]{17,20})\b", issue_body)
    if id_match:
        info["discord_id"] = id_match.group(1).strip()

    # Check for Discord username (e.g. @username or username#1234 or Discord: username)
    user_match = re.search(r"(?:discord|handle)[\s:]*@?([a-zA-Z0-9_.-]{2,32}(?:#[0-9]{4})?)", issue_body, re.IGNORECASE)
    if user_match:
        cand = user_match.group(1).strip()
        if not cand.isdigit():
            info["discord_username"] = cand

    return info


def resolve_discord_user_id(username: str, token: str, guild_id: str) -> str:
    """Find Discord User ID in a guild by username if only username was provided."""
    if not token or not guild_id or not username:
        return None

    clean_user = username.split("#")[0].lstrip("@")
    url = f"https://discord.com/api/v10/guilds/{guild_id}/members/search?query={urllib.request.quote(clean_user)}&limit=1"
    headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": "cgo-void-repo-bot (https://github.com/CasperGamingOne/cgo-void-repo)"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0 and "user" in data[0]:
                return data[0]["user"]["id"]
    except Exception as e:
        print(f"--> Notice: Could not resolve Discord username '{clean_user}': {e}")
    return None


def send_discord_dm(user_id: str, status_key: str, pkgname: str, issue_num: int, issue_url: str, token: str) -> bool:
    """Send Direct Message (DM) to Discord user."""
    if not user_id or not token:
        print("--> Notice: Discord user ID or bot token missing; skipping Discord DM.")
        return False

    status_data = STATUS_CONFIG.get(status_key, STATUS_CONFIG["in progress"])
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "cgo-void-repo-bot (https://github.com/CasperGamingOne/cgo-void-repo)"
    }

    # 1. Create or open DM channel with recipient
    dm_url = "https://discord.com/api/v10/users/@me/channels"
    dm_payload = json.dumps({"recipient_id": user_id}).encode("utf-8")
    req = urllib.request.Request(dm_url, data=dm_payload, headers=headers)

    channel_id = None
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            channel_id = data.get("id")
    except urllib.error.HTTPError as e:
        print(f"--> Error opening Discord DM channel with {user_id}: HTTP {e.code} - {e.read().decode()}")
        return False
    except Exception as e:
        print(f"--> Error opening Discord DM channel with {user_id}: {e}")
        return False

    if not channel_id:
        return False

    # 2. Post DM message embed
    msg_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    display_title = f"{status_data['emoji']} Package Request #{issue_num}: {status_data['label']}"
    msg_payload = json.dumps({
        "embeds": [{
            "title": display_title,
            "url": issue_url,
            "description": status_data["description"],
            "color": status_data["color"],
            "fields": [
                {"name": "Package", "value": f"`{pkgname}`", "inline": True},
                {"name": "Status", "value": f"**{status_data['label']}**", "inline": True},
                {"name": "Issue Tracking ID", "value": f"#{issue_num}", "inline": True},
                {"name": "Issue Link", "value": f"[View on GitHub]({issue_url})", "inline": False}
            ],
            "footer": {
                "text": "cgo-void-repo • Games4Everyone",
                "icon_url": "https://caspergamingone.github.io/cgo-void-repo/assets/games4everyone-logo.png"
            }
        }]
    }).encode("utf-8")

    req_msg = urllib.request.Request(msg_url, data=msg_payload, headers=headers)
    try:
        with urllib.request.urlopen(req_msg) as resp:
            print(f"--> Discord DM sent successfully to user {user_id} (Status: {status_data['label']})")
            return True
    except urllib.error.HTTPError as e:
        print(f"--> Error sending Discord DM: HTTP {e.code} - {e.read().decode()}")
        return False
    except Exception as e:
        print(f"--> Error sending Discord DM: {e}")
        return False


def send_email(to_email: str, status_key: str, pkgname: str, issue_num: int, issue_url: str) -> bool:
    """Send notification email via SMTP."""
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user or "noreply@cgo-void-repo.org")

    if not smtp_host or not smtp_user or not smtp_pass:
        print("--> Notice: SMTP credentials not configured (SMTP_HOST, SMTP_USER, SMTP_PASS); skipping email.")
        return False

    status_data = STATUS_CONFIG.get(status_key, STATUS_CONFIG["in progress"])
    subject = f"[cgo-void-repo] Package Request #{issue_num} ({pkgname}): {status_data['label']}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_email

    text_content = f"""Hello!

Your package request #{issue_num} for '{pkgname}' on cgo-void-repo has an update.

Current Status: {status_data['label']} {status_data['emoji']}
Details: {status_data['description']}

Track this issue on GitHub:
{issue_url}

--
CasperGamingOne • Games4Everyone Void Linux Repository
https://caspergamingone.github.io/cgo-void-repo
"""

    html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0c0e1a; color: #f8fafc; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: #131628; border: 1px solid #222744; border-radius: 10px; padding: 25px;">
    <h2 style="color: #c084fc; margin-top: 0;">cgo-void-repo Package Update</h2>
    <p>Your package request <strong>#{issue_num}</strong> (<code>{pkgname}</code>) has been updated:</p>
    
    <div style="background: #090a14; border-left: 4px solid #{status_data['color']:06x}; padding: 15px; margin: 20px 0; border-radius: 4px;">
      <h3 style="margin: 0; color: #f8fafc;">{status_data['emoji']} Status: {status_data['label']}</h3>
      <p style="margin: 8px 0 0 0; color: #94a3b8;">{status_data['description']}</p>
    </div>

    <p style="margin: 25px 0;">
      <a href="{issue_url}" style="background: #7c3aed; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">View Issue on GitHub</a>
    </p>

    <hr style="border: none; border-top: 1px solid #222744; margin: 20px 0;">
    <p style="font-size: 12px; color: #64748b; margin: 0;">
      Games4Everyone • CasperGamingOne Void Linux Repository<br>
      <a href="https://caspergamingone.github.io/cgo-void-repo" style="color: #94a3b8;">caspergamingone.github.io/cgo-void-repo</a>
    </p>
  </div>
</body>
</html>
"""

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_from, [to_email], msg.as_string())
        server.quit()
        print(f"--> Email notification sent successfully to {to_email} (Status: {status_data['label']})")
        return True
    except Exception as e:
        print(f"--> Error sending email to {to_email}: {e}")
        return False


def detect_status_transition(event: dict) -> str:
    """
    Detect whether this GitHub event is a status transition to:
    accepted, in progress, completed, or denied.
    """
    action = event.get("action")

    # 1. Check for labeled event
    if action == "labeled":
        label_name = event.get("label", {}).get("name", "").lower()
        if "accepted" in label_name:
            return "accepted"
        elif "progress" in label_name:
            return "in progress"
        elif "completed" in label_name:
            return "completed"
        elif "denied" in label_name or "rejected" in label_name:
            return "denied"

    # 2. Check for closed event
    if action == "closed":
        state_reason = event.get("issue", {}).get("state_reason")
        if state_reason == "completed":
            return "completed"
        elif state_reason == "not_planned":
            return "denied"

    # 3. Check for issue comment commands (e.g. /accept, /deny, /progress, /complete)
    if action == "created" and "comment" in event:
        body = event.get("comment", {}).get("body", "").strip().lower()
        if body.startswith("/accept") or "/status accepted" in body:
            return "accepted"
        elif body.startswith("/progress") or "/status in-progress" in body:
            return "in progress"
        elif body.startswith("/complete") or "/status completed" in body:
            return "completed"
        elif body.startswith("/deny") or body.startswith("/reject") or "/status denied" in body:
            return "denied"

    return None


def main():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not os.path.exists(event_path):
        print("ERROR: GITHUB_EVENT_PATH not set or file does not exist.")
        sys.exit(1)

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    issue = event.get("issue")
    if not issue:
        print("Notice: Event does not pertain to an issue.")
        sys.exit(0)

    # Only process issues labeled 'package-request' or with '[Package Request]' in title
    title = issue.get("title", "")
    labels = [l.get("name", "").lower() for l in issue.get("labels", [])]
    is_pkg_req = "[package request]" in title.lower() or "package-request" in labels
    if not is_pkg_req:
        print("Notice: Issue is not a package request; skipping notification.")
        sys.exit(0)

    # Detect the status transition
    status_key = detect_status_transition(event)
    if not status_key:
        print("Notice: Event does not trigger a package request status transition (accepted/in progress/completed/denied).")
        sys.exit(0)

    issue_num = issue.get("number")
    issue_url = issue.get("html_url")
    issue_body = issue.get("body", "")

    contact_info = parse_issue_contact(issue_body)
    pkgname = contact_info["package_name"] or title.replace("[Package Request]:", "").strip() or f"package-#{issue_num}"

    print(f"=== Processing Status Update for Request #{issue_num}: {pkgname} ===")
    print(f"--> Target Status: '{status_key}' ({STATUS_CONFIG[status_key]['label']})")
    print(f"--> Extracted Contact: Email={contact_info['email']}, DiscordID={contact_info['discord_id']}, DiscordUser={contact_info['discord_username']}")

    discord_token = os.environ.get("DISCORD_BOT_TOKEN")
    discord_guild = os.environ.get("DISCORD_GUILD_ID")

    # Resolve Discord ID if only username was provided
    discord_id = contact_info["discord_id"]
    if not discord_id and contact_info["discord_username"] and discord_token:
        print(f"--> Resolving username '{contact_info['discord_username']}' via Discord API...")
        discord_id = resolve_discord_user_id(contact_info["discord_username"], discord_token, discord_guild)
        if discord_id:
            print(f"--> Resolved to Discord User ID: {discord_id}")

    # 1. Dispatch Discord DM
    discord_sent = False
    if discord_id and discord_token:
        discord_sent = send_discord_dm(discord_id, status_key, pkgname, issue_num, issue_url, discord_token)

    # 2. Dispatch Email
    email_sent = False
    if contact_info["email"]:
        email_sent = send_email(contact_info["email"], status_key, pkgname, issue_num, issue_url)

    # Output summary for GitHub Actions step
    print(f"=== Notification Dispatch Complete ===")
    print(f"--> Discord DM: {'Sent' if discord_sent else 'Skipped/Failed'}")
    print(f"--> Email: {'Sent' if email_sent else 'Skipped/Failed'}")


if __name__ == "__main__":
    main()
