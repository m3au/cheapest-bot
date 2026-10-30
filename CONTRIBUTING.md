# Contributing

The useful contribution here is keeping prices right.

## Updating a price

1. Open the source page (normally https://cursor.com/docs/models) and read the current price.
2. Edit the model's row in `data/models.json`:
   - `input_per_m`, `cached_input_per_m`, `output_per_m` in USD per 1M tokens (`null` if not published),
   - `billing`: `allowance` (Cursor's own models) or `credit` (everyone else),
   - `fast_variant_note` if the model has a pricier fast variant,
   - `source`: the exact public URL you read,
   - `checked`: today's date as `YYYY-MM-DD`.
3. Bump the top-level `checked` date if you re-checked the whole table.
4. Run `python3 -m unittest discover -s tests`.
5. Open a PR with the source link in the description. One PR per price change is fine.

If a price change flips a pick, update `cheapest.py`, the rules table in `README.md`, and the tests in the same PR.

## Rules

- Public sources only. No screenshots of personal dashboards, no account ids, no invoices.
- No dependencies. Python stdlib only.
- No tracking, analytics or logging of visitors.
- No referral or affiliate links. This project doesn't make money and won't.
