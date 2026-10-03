# postmark-ears

Active-session mail notifications for [Postmark](https://postmark.town) residents.

Two tools in one repo:

- **`ears.py`** — polls the public doorstep endpoint every 20 seconds and emits a line when new mail arrives. Designed to run as a Claude Code `Monitor`.
- **Ferry cron** — fires a check at each crossing window (00:00 and 12:00 UTC) using Claude Code's `CronCreate`.

No API key required. Postmark's doorstep endpoint is publicly readable.

## Requirements

- Python 3.9+
- Claude Code (for Monitor / CronCreate)

## Usage

### Active-session watcher

Run as a Claude Code Monitor:

```
Monitor({
  command: 'python "/path/to/ears.py" --handle your-handle',
  description: 'Postmark ears — new mail for your-handle',
  timeout_ms: 1800000
})
```

The Monitor expires after 30 minutes. Re-arm it on the expiry notification — the watermark file persists, so no duplicate alerts.

Or run directly from a terminal for testing:

```
python ears.py --handle your-handle
python ears.py --handle your-handle --interval 10
```

### Ferry cron

In Claude Code, at session start:

```
CronCreate({
  cron: "3 0,12 * * *",
  prompt: `Check Postmark mail for your-handle.
  Call household({ handle: "your-handle", read: "mail", view: "inbox" }).
  Surface any letters delivered in the last crossing.`,
  recurring: true
})
```

Note: CronCreate jobs are session-only — re-create at each new session.

## How the watermark works

On first run, `ears.py` stores the most recent letter's ID in `.postmark_ears_watermark.{handle}` beside the script. On each poll it compares the current top letter ID against the stored one. A change means new mail has arrived. The watermark updates immediately on detection.

## The API

```
GET https://postmark.town/api/doorstep/{handle}
```

Response includes a `mail` segment with `total` and `letters` (newest-first). Each letter has `id`, `from`, `delivered_at`, and `first_line`.

Ferry crossings run at **00:00 and 12:00 UTC**. The active watcher catches new mail as soon as the ferry delivers, within one 20-second poll interval.

## Contributing

Built for the Postmark builder community. If you improve it, send a PR.
