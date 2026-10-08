# Academia Obscura

The lighter side of academia. Silly, not stupid.

Public site: landing, book, lectures, contact, and the blog archive.

## Local

```sh
npm install
npm run build
npm run dev
```

Empty-bodied stubs stay `draft: true` and are omitted from the index, RSS, and sitemap.

## Analytics

Separate Umami site ID for `academiaobscura.com`. Copy `.env.example` → `.env` and paste the reserved ID from Vaultwarden. Leave empty to ship with tracking off. Never reuse the glenwright.earth ID.

## Deploy

GitHub Pages via Actions on `main` (see `.github/workflows/deploy.yml`).
