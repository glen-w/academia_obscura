import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';

export const GET: APIRoute = async () => {
  const published = (await getCollection('blog')).filter((p) => p.data.draft !== true);
  const items = published
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf())
    .map(
      (p) => `    <item>
      <title><![CDATA[${p.data.title}]]></title>
      <pubDate>${p.data.date.toUTCString()}</pubDate>
      <guid>https://academiaobscura.com/blog/${p.id}/</guid>
    </item>`,
    )
    .join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Academia Obscura</title>
    <link>https://academiaobscura.com/blog/</link>
    <description>The lighter side of academia. Silly, not stupid.</description>
${items}
  </channel>
</rss>
`;
  return new Response(xml, {
    headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' },
  });
};
