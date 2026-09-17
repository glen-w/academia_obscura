# Academia Obscura

The lighter side of academia. Silly, not stupid.

Public site: **landing + empty blog**. Old posts live in `src/content/blog/` as `draft: true` **on this machine only** (gitignored; not on GitHub).

## Local

```sh
npm install
python3 scripts/migrate-drafts.py   # only if re-importing
npm run build
npm run check:no-draft-leak
npm run dev
```

## Analytics

Separate Umami site ID for `academiaobscura.com`. Copy `.env.example` → `.env` and paste the reserved ID from Vaultwarden. Leave empty to ship with tracking off. Never reuse the glenwright.earth ID.

## Deploy

GitHub Pages from the `gh-pages` branch (Actions deploy is ready in `.github/workflows/deploy.yml` but needs a `workflow` token scope to push). After `npm run build`, publish `dist/` to `gh-pages`.

Point OVH `academiaobscura.com` + `www` at Pages after the first green deploy — see [DNS.md](DNS.md).
