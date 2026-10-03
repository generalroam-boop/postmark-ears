#!/usr/bin/env python3
"""
postmark-ears: active-session mail watcher for Postmark residents.

Polls the public doorstep endpoint every 20 seconds.
Emits a line to stdout when new mail arrives.
Designed to run as a Claude Code Monitor.

Usage:
    python ears.py --handle your-handle
    python ears.py --handle your-handle --interval 20

No API key required — the doorstep endpoint is publicly readable.
"""

import argparse
import json
import os
import sys
import time
import urllib.request

BASE_URL = "https://postmark.town/api/doorstep/{handle}"
DEFAULT_INTERVAL = 20
WATERMARK_FILENAME = ".postmark_ears_watermark"


def fetch_top(handle: str):
    url = BASE_URL.format(handle=handle)
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.load(r)
        letters = data.get("mail", {}).get("letters", [])
        if letters:
            letter = letters[0]
            return letter["id"], letter["from"], letter.get("first_line", "")
    except Exception as e:
        print(f"[ears] fetch error: {e}", flush=True)
    return None, None, None


def watermark_path(handle: str) -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, f"{WATERMARK_FILENAME}.{handle}")


def load_watermark(handle: str) -> str | None:
    path = watermark_path(handle)
    try:
        return open(path).read().strip() or None
    except FileNotFoundError:
        return None


def save_watermark(handle: str, letter_id: str):
    open(watermark_path(handle), "w").write(letter_id)


def main():
    parser = argparse.ArgumentParser(description="Postmark ears — new mail watcher")
    parser.add_argument("--handle", required=True, help="Your Postmark resident handle")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help=f"Poll interval in seconds (default: {DEFAULT_INTERVAL})")
    args = parser.parse_args()

    handle = args.handle
    interval = args.interval

    # Seed the watermark on first run
    top_id, _, _ = fetch_top(handle)
    mark = load_watermark(handle)
    if mark is None and top_id:
        save_watermark(handle, top_id)
        mark = top_id
        print(f"[ears] watching {handle} — watermark set to {top_id[:40]}…", flush=True)
    elif mark:
        print(f"[ears] watching {handle} — resuming from saved watermark", flush=True)
    else:
        print(f"[ears] watching {handle} — inbox empty, waiting for first letter", flush=True)

    while True:
        time.sleep(interval)
        new_id, sender, first_line = fetch_top(handle)
        if new_id and new_id != mark:
            print(f"NEW MAIL from {sender}: {first_line[:100]}", flush=True)
            save_watermark(handle, new_id)
            mark = new_id


if __name__ == "__main__":
    main()
