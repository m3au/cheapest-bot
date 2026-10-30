# Cheapest Bot

A tiny, read-only service that tells you which model gives the most for the money in Cursor right now, and hands back the exact launch params so you don't get billed for a variant you didn't ask for. Humans can read the page; bots and scripts can call the API before they launch a cloud agent.

**Open source (MIT), non-profit, and nobody earns anything from it.** No ads, no affiliate links, no trackers, no cookies, no IP logging, no accounts.

Live at: <PORTAL_URL>

## The trap

If you launch a Cursor cloud agent with only `composer-2.5` as the model id, Cursor resolves it to the default variant, which is **composer-2.5-fast**:

| Variant | Input / 1M tokens | Output / 1M tokens |
|---|---|---|
| composer-2.5 (standard) | $0.50 | $2.50 |
| composer-2.5-fast (what you get by default) | $3.00 | $15.00 |

That's 6x on output. Cursor staff confirmed the behaviour here:
https://forum.cursor.com/t/sdk-reports-composer-2-5-but-usage-dashboard-bills-composer-2-5-fast/163046/7

**Fix:** pass `fast=false`, and check your usage dashboard once: it should show `composer-2.5`, not `composer-2.5-fast`.

```json
{ "model": "composer-2.5", "model_params": { "fast": false } }
```

With the Cursor Agent SDK the same thing looks like:

```json
{ "id": "composer-2.5", "params": [{ "id": "fast", "value": "false" }] }
```

Second trap: **always name the model.** A launch with no model falls back to the default model, which can be a much pricier one.

Also good to know: Cursor's own models (Composer, Grok) come out of your plan's included allowance. Every other model (Claude, GPT, Gemini, GLM, DeepSeek, Kimi, ...) bills credit at API list price from the first request.

## Use it

```
GET /api/cheapest?task=short|long|code&max_input_k=N[&billing=any|allowance]
GET /api/models       # the full price table (data/models.json)
GET /api/benchmark    # CursorBench numbers used for the quality floor
GET /healthz
GET /                 # human page
```

- `task`: `short` (quick jobs, default), `code` (coding jobs), `long` (big inputs).
- `max_input_k`: the largest input per request you expect, in thousands of tokens. Defaults: short 20, code 50, long 200.
- `billing`: `any` (default, credit models allowed) or `allowance` (only Cursor's own models, no credit spend).

Example:

```sh
curl '<PORTAL_URL>/api/cheapest?task=code&max_input_k=40'
```

```json
{
  "model": "Claude Haiku 5.5",
  "billing": "credit",
  "price_per_m": { "input": 0.1, "output": 0.5 },
  "launch": { "model": "Claude Haiku 5.5", "model_params": {} },
  "reason": "Cheapest credit model with decent quality: ...",
  "notes": ["Use High effort. ...", "Exact model id not recorded yet; ..."],
  "checked": "2026-10-30"
}
```

### Current rules

| Ask | Pick | Why |
|---|---|---|
| `billing=allowance` | Composer 2.5 with `fast=false` | Cheapest priced allowance model; never the Fast variant. |
| any task, input up to 100k | Claude Haiku 5.5 | $0.10 / $0.50, 42.3% on CursorBench 4.0 at about $0.32/task. |
| `code`, input over 100k | DeepSeek V4.1 Flash | Haiku bills 5x over 100k input. 46.3% at about $0.80/task, but slow. |
| `short` / `long`, input over 100k | GLM 5.3 Flash | Cheapest credit model listed ($0.15 / $0.50). |

Bigger models (Sonnet, Opus, Grok High) are never the default answer. Reach for them only when the cheap pick has already failed the same task.

The rules live in `cheapest.py` and are covered by `tests/`.

## Run it yourself

Python 3.9+ and nothing else.

```sh
python3 server.py                     # listens on 127.0.0.1:8787
HOST=127.0.0.1 PORT=9000 python3 server.py
python3 -m unittest discover -s tests # run the tests
```

Put it behind any reverse proxy that does TLS. The page uses relative URLs, so it also works under a sub-path if the proxy strips the prefix. The server only answers GET, HEAD and OPTIONS, sends `Access-Control-Allow-Origin: *`, and writes no access log.

## Where the prices come from

- Prices are read **by hand** from Cursor's public model docs (https://cursor.com/docs/models). Quality numbers come from CursorBench (https://cursor.com/cursorbench), which is Cursor's own benchmark, not an independent one; small score gaps may be noise.
- Every row in `data/models.json` has its own `source` and `checked` date. There's no scraper and no cron job.
- Prices go stale. If you spot a change, open a PR (see [CONTRIBUTING.md](CONTRIBUTING.md)).
- All prices are USD per 1M tokens.

## Disclaimer

Not affiliated with, endorsed by, or sponsored by Cursor (Anysphere), xAI, or any model provider. Prices and billing behaviour can change at any time; always check your own usage dashboard. No warranty, see [LICENSE](LICENSE).
