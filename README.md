# audioroom-assets

Static host for email logo images, served from Vercel over HTTPS so email
signatures and templates can reference them with `<img src="https://...">`
instead of attachments.

- `source/` — original logo files (kept in git, excluded from the deploy)
- `email/` — processed, deployable assets (`<name>-v1.png`)
- `scripts/process.py` — Pillow pipeline: white-key → recolour `#3A3A3A` → trim → scale
- `preview.html` — optical-weight check for the partner logo row

## Rules

- Never overwrite a published filename. A changed logo gets a `-v2` suffix;
  Gmail's image proxy caches hard and recipients would keep the old image.
- No base64 data URIs in emails — Gmail strips them.
- Assets stay mono (`#3A3A3A` for partner logos, pure black for the
  Audioroom wordmark). No red.

## Deploy

Plain static directory, no build step. `vercel --prod` from the repo root.
Production alias: `https://audioroom-assets.vercel.app`

Deployment Protection must be **disabled** in the Vercel dashboard
(Settings → Deployment Protection → Vercel Authentication → Disabled),
otherwise Gmail's image proxy gets a 401 and logos break for recipients.
