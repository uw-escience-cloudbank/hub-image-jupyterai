#!/usr/bin/env python3
"""Configure Claude Code to use the CloudBank LiteLLM proxy.

Writes ~/.claude/settings.json pointing Claude Code at the CloudBank proxy,
backing up any existing settings.json to settings.json.bak first.

Usage:
    setup-claude-cloudbank              # prompt for key and write settings.json
    setup-claude-cloudbank --verify-key # query the proxy for key/user info
    setup-claude-cloudbank --restore    # put the pre-workshop settings.json back
"""

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://cloudbank-litellm.westus2.cloudapp.azure.com"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def settings_template(api_key):
    return {
        "env": {
            "ANTHROPIC_BASE_URL": BASE_URL,
            "ANTHROPIC_API_KEY": api_key,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4-5",
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-5",
            "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5",
            "ANTHROPIC_MODEL": "haiku",
        },
        "availableModels": ["haiku", "sonnet", "opus"],
        "enforceAvailableModels": True,
        "theme": "auto",
    }


def prompt_for_key():
    """Read ANTHROPIC_API_KEY from the environment or prompt for it."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        print(f"Using ANTHROPIC_API_KEY from environment ({mask(key)})")
        return key

    if not sys.stdin.isatty():
        sys.exit(
            "error: no tty to prompt on; set ANTHROPIC_API_KEY in the environment instead"
        )

    while True:
        key = getpass.getpass("ANTHROPIC_API_KEY (input hidden): ").strip()
        if key:
            return key
        print("A key is required.")


def mask(key):
    return f"{key[:7]}...{key[-4:]}" if len(key) > 15 else "***"


def unique_path(path):
    """Return path if free, otherwise the first variant that does not exist."""
    if not path.exists():
        return path
    candidate = path.with_name(f"{path.name}-backup")
    n = 2
    while candidate.exists():
        candidate = path.with_name(f"{path.name}-backup-{n}")
        n += 1
    return candidate


def backup_existing(path):
    if not path.exists():
        return
    backup = unique_path(path.with_suffix(".json.bak"))
    path.replace(backup)
    print(f"Backed up existing settings to {backup}")


def restore_settings():
    """Undo a previous run: stash the workshop config, put settings.json.bak back."""
    backup = SETTINGS_PATH.with_suffix(".json.bak")
    if not backup.exists():
        sys.exit(f"error: nothing to restore, {backup} does not exist")

    if SETTINGS_PATH.exists():
        stashed = unique_path(SETTINGS_PATH.with_suffix(".json.workshop"))
        SETTINGS_PATH.replace(stashed)
        print(f"Moved workshop settings to {stashed}")

    backup.replace(SETTINGS_PATH)
    print(f"Restored {SETTINGS_PATH} from {backup.name}")


def write_settings(api_key):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    backup_existing(SETTINGS_PATH)
    SETTINGS_PATH.write_text(json.dumps(settings_template(api_key), indent=2) + "\n")
    SETTINGS_PATH.chmod(0o600)
    print(f"Wrote {SETTINGS_PATH}")
    print("Start Claude Code with: claude")


def key_from_settings():
    """Recover the key from an already-written settings.json."""
    if not SETTINGS_PATH.exists():
        return None
    try:
        return json.loads(SETTINGS_PATH.read_text()).get("env", {}).get(
            "ANTHROPIC_API_KEY"
        )
    except (json.JSONDecodeError, OSError):
        return None


def api_get(path, api_key):
    """GET a LiteLLM proxy endpoint, returning parsed JSON or None on 404."""
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            sys.exit(f"error: proxy rejected the key ({e.code} {e.reason})")
        if e.code == 404:
            return None
        body = e.read().decode(errors="replace")[:500]
        sys.exit(f"error: {path} returned {e.code} {e.reason}\n{body}")
    except urllib.error.URLError as e:
        sys.exit(f"error: could not reach {BASE_URL}: {e.reason}")


def fmt_usd(value):
    return f"${float(value):,.4f}" if value is not None else "unlimited"


def show(label, value):
    if value not in (None, "", [], {}):
        print(f"  {label:<22} {value}")


def report(info):
    """Print the interesting fields of a LiteLLM key/user info payload."""
    show("key alias", info.get("key_alias"))
    show("user id", info.get("user_id"))
    show("user email", info.get("user_email"))
    show("team id", info.get("team_id"))
    show("created", info.get("created_at"))
    show("expires", info.get("expires") or "never")

    spend = info.get("spend")
    max_budget = info.get("max_budget")
    if spend is not None:
        show("spend", fmt_usd(spend))
    if max_budget is not None:
        show("budget", fmt_usd(max_budget))
        show("remaining", fmt_usd(float(max_budget) - float(spend or 0)))
    else:
        show("budget", "unlimited")

    show("soft budget", fmt_usd(info["soft_budget"]) if info.get("soft_budget") else None)
    show("budget duration", info.get("budget_duration"))
    show("budget resets", info.get("budget_reset_at"))
    show("tpm limit", info.get("tpm_limit") or "unlimited")
    show("rpm limit", info.get("rpm_limit") or "unlimited")
    show("max parallel reqs", info.get("max_parallel_requests"))
    show("blocked", info.get("blocked"))

    models = info.get("models")
    print(f"  {'models':<22} {', '.join(models) if models else 'all proxy models'}")


def verify_key(api_key):
    print(f"Querying {BASE_URL} with key {mask(api_key)}\n")

    payload = api_get("/key/info", api_key)
    info = (payload or {}).get("info", payload) or {}
    print("Key info:")
    if info:
        report(info)
    else:
        print("  (proxy returned no key details)")

    user_id = info.get("user_id")
    if user_id:
        payload = api_get(
            f"/user/info?user_id={urllib.parse.quote(str(user_id))}", api_key
        )
        user_info = (payload or {}).get("user_info") or {}
        if user_info:
            print("\nUser info:")
            report(user_info)

    models = api_get("/models", api_key) or {}
    ids = sorted(m.get("id", "") for m in models.get("data", []))
    if ids:
        print(f"\nAvailable models ({len(ids)}):")
        for model_id in ids:
            print(f"  {model_id}")

    print("\n✓ Key is valid")


def main():
    parser = argparse.ArgumentParser(
        description=f"Configure Claude Code to use the CloudBank LiteLLM proxy at {BASE_URL}"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verify-key",
        action="store_true",
        help="query the proxy for key info (budget, balance, quotas) instead of writing settings",
    )
    mode.add_argument(
        "--restore",
        action="store_true",
        help="put settings.json.bak back, stashing the workshop config as settings.json.workshop",
    )
    args = parser.parse_args()

    if args.restore:
        restore_settings()
        return

    if args.verify_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip() or key_from_settings()
        if not api_key:
            api_key = prompt_for_key()
        verify_key(api_key)
        return

    write_settings(prompt_for_key())


if __name__ == "__main__":
    main()
