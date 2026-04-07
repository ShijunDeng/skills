#!/usr/bin/env python3
"""
Email sender using Python standard library only.
No third-party dependencies. Compatible with Python 3.6+.

Usage:
    python email-sender.py <config_path> --subject "..." --body "..." --to "email1,email2"

Output: JSON result with success status and message.
"""

import smtplib
import json
import sys
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate


def load_config(config_path):
    """Load and return config dict from JSON file."""
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def save_config(config_path, config):
    """Save config dict to JSON file."""
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def validate_email_format(email):
    """Validate email address format."""
    if not email or not isinstance(email, str):
        return False
    # Basic format: local@domain.tld
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None


# Default SMTP config
DEFAULT_SMTP_HOST = "smtpscn.huawei.com"
DEFAULT_SMTP_PORT = 25


def validate_required_config(config):
    """Check required SMTP config fields. Return list of missing fields."""
    required = ["sender_email", "sender_password"]
    missing = []
    for field in required:
        value = config.get(field)
        if not value:
            missing.append(field)
    return missing


def build_message(subject, body, sender_email, sender_name, to_list, cc_list, is_html=False):
    """Build MIME email message."""
    if is_html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "html", "utf-8"))
    else:
        msg = MIMEText(body, "plain", "utf-8")

    # From header
    if sender_name:
        msg["From"] = formataddr((sender_name, sender_email))
    else:
        msg["From"] = sender_email

    # To header
    msg["To"] = ", ".join(to_list)

    # Cc header
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)

    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)

    return msg


def send_email(config, subject, body, to_list, cc_list=None, bcc_list=None, is_html=False):
    """
    Send email via SMTP.

    Returns dict: {"success": bool, "message": str, "error_type": str (if failed)}
    """
    cc_list = cc_list or []
    bcc_list = bcc_list or []

    # Validate recipients
    all_recipients = to_list + cc_list + bcc_list
    invalid_emails = [e for e in all_recipients if not validate_email_format(e)]
    if invalid_emails:
        return {
            "success": False,
            "message": f"Invalid email format: {', '.join(invalid_emails)}",
            "error_type": "validation"
        }

    if not all_recipients:
        return {
            "success": False,
            "message": "No recipients specified",
            "error_type": "validation"
        }

    # Get config values (smtp_host and smtp_port have defaults)
    smtp_host = config.get("smtp_host") or DEFAULT_SMTP_HOST
    smtp_port = config.get("smtp_port", DEFAULT_SMTP_PORT)
    if not isinstance(smtp_port, int):
        smtp_port = DEFAULT_SMTP_PORT
    use_ssl = config.get("smtp_use_ssl", True)
    sender_email = config["sender_email"]
    sender_password = config["sender_password"]
    sender_name = config.get("sender_display_name", "")

    # Build message
    msg = build_message(subject, body, sender_email, sender_name, to_list, cc_list, is_html)

    # Send via SMTP
    try:
        timeout = 30

        if use_ssl:
            # SSL connection (port 465)
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout)
        else:
            # Non-SSL, with STARTTLS for port 587
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=timeout)
            if smtp_port == 587:
                server.ehlo()
                server.starttls()
                server.ehlo()

        server.login(sender_email, sender_password)
        server.sendmail(sender_email, all_recipients, msg.as_string())
        server.quit()

        return {
            "success": True,
            "message": f"Email sent to {', '.join(to_list)}"
        }

    except smtplib.SMTPAuthenticationError as e:
        return {
            "success": False,
            "message": "Authentication failed. Check password/app-password.",
            "error_type": "auth",
            "detail": str(e)
        }
    except smtplib.SMTPConnectError as e:
        return {
            "success": False,
            "message": f"Cannot connect to {smtp_host}:{smtp_port}",
            "error_type": "connection",
            "detail": str(e)
        }
    except smtplib.SMTPException as e:
        return {
            "success": False,
            "message": "SMTP error occurred",
            "error_type": "smtp",
            "detail": str(e)
        }
    except TimeoutError:
        return {
            "success": False,
            "message": "Connection timeout",
            "error_type": "timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {type(e).__name__}",
            "error_type": "unknown",
            "detail": str(e)
        }


def update_recipients(config_path, to_list, cc_list=None, bcc_list=None):
    """Update default recipients in config file."""
    config = load_config(config_path)
    if not config:
        return False

    config["default_to"] = to_list if to_list else []
    config["default_cc"] = cc_list if cc_list else []
    config["default_bcc"] = bcc_list if bcc_list else []

    save_config(config_path, config)
    return True


def get_config_status(config_path):
    """Check config file status and return info."""
    config = load_config(config_path)

    if config is None:
        return {
            "exists": False,
            "valid": False,
            "missing_fields": ["sender_email", "sender_password"]
        }

    missing = validate_required_config(config)

    return {
        "exists": True,
        "valid": len(missing) == 0,
        "missing_fields": missing,
        "has_default_recipients": len(config.get("default_to", [])) > 0
    }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        result = {
            "success": False,
            "message": "Usage: email-sender.py <config_path> [--subject S] [--body B] [--to emails] [--cc emails] [--html] [--check]"
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    config_path = sys.argv[1]

    # Parse arguments
    args = sys.argv[2:]
    subject = None
    body = None
    to_override = None
    cc_override = None
    bcc_override = None
    is_html = False
    check_only = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--subject" and i + 1 < len(args):
            subject = args[i + 1]
            i += 2
        elif arg == "--body" and i + 1 < len(args):
            body = args[i + 1]
            i += 2
        elif arg == "--to" and i + 1 < len(args):
            to_override = [e.strip() for e in args[i + 1].split(",") if e.strip()]
            i += 2
        elif arg == "--cc" and i + 1 < len(args):
            cc_override = [e.strip() for e in args[i + 1].split(",") if e.strip()]
            i += 2
        elif arg == "--bcc" and i + 1 < len(args):
            bcc_override = [e.strip() for e in args[i + 1].split(",") if e.strip()]
            i += 2
        elif arg == "--html":
            is_html = True
            i += 1
        elif arg == "--check":
            check_only = True
            i += 1
        else:
            i += 1

    # Check config status only
    if check_only:
        status = get_config_status(config_path)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return

    # Load config
    config = load_config(config_path)
    if config is None:
        result = {"success": False, "message": "Config file not found or invalid"}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    # Validate required fields
    missing = validate_required_config(config)
    if missing:
        result = {
            "success": False,
            "message": f"Missing required fields: {', '.join(missing)}",
            "missing_fields": missing
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    # Determine recipients
    to_list = to_override if to_override else config.get("default_to", [])
    cc_list = cc_override if cc_override else config.get("default_cc", [])
    bcc_list = bcc_override if bcc_override else config.get("default_bcc", [])

    # Require subject and body
    if not subject:
        result = {"success": False, "message": "Subject is required (--subject)"}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    if not body:
        result = {"success": False, "message": "Body is required (--body)"}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    # Send email
    result = send_email(config, subject, body, to_list, cc_list, bcc_list, is_html)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Update config on success
    if result["success"]:
        update_recipients(config_path, to_list, cc_list, bcc_list)

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()