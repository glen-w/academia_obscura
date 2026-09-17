import type { APIRoute } from 'astro';

const paths = ['/', '/book/', '/lectures/', '/blog/', '/contact/'];

export const GET: APIRoute = () => {
  const urls = paths
    .map(
      (p) => `  <url>
    <loc>https://academiaobscura.com${p}</loc>
  </url>`,
    )
    .join('\n');
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`;
  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
};
