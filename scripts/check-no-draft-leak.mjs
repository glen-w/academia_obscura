/**
 * Fail the build if any draft post slug/title leaks into dist/.
 */
import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { join, extname } from 'node:path';

const root = join(import.meta.dirname, '..');
const dist = join(root, 'dist');
const blogDir = join(root, 'src/content/blog');

function walk(dir) {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...walk(p));
    else out.push(p);
  }
  return out;
}

function parseFrontmatter(raw) {
  const m = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!m) return {};
  const fm = m[1];
  const title = fm.match(/^title:\s*["']?(.+?)["']?\s*$/m)?.[1];
  const slug = fm.match(/^originalSlug:\s*["']?(.+?)["']?\s*$/m)?.[1];
  const idFromFile = null;
  const draft = /draft:\s*true/.test(fm);
  return { title, slug, draft, idFromFile };
}

if (!existsSync(dist)) {
  console.error('dist/ missing — run npm run build first');
  process.exit(1);
}

const posts = walk(blogDir)
  .filter((f) => f.endsWith('.md'))
  .map((f) => {
    const meta = parseFrontmatter(readFileSync(f, 'utf8'));
    const base = f.split('/').pop().replace(/\.md$/, '');
    return { ...meta, id: base };
  });

const drafts = posts.filter((p) => p.draft);
const published = posts.filter((p) => !p.draft);

const distFiles = walk(dist).filter((f) =>
  ['.html', '.xml', '.txt', '.js', '.json'].includes(extname(f)),
);
const haystack = distFiles.map((f) => readFileSync(f, 'utf8')).join('\n');

const leaks = [];
for (const d of drafts) {
  if (d.id && haystack.includes(`/blog/${d.id}`)) {
    leaks.push(`draft path /blog/${d.id}`);
  }
  if (d.slug && haystack.includes(`/blog/${d.slug}`)) {
    leaks.push(`draft slug path /blog/${d.slug}`);
  }
}

const blogHtml = join(dist, 'blog/index.html');
if (existsSync(blogHtml)) {
  const html = readFileSync(blogHtml, 'utf8');
  for (const d of drafts) {
    if (d.title && html.includes(d.title) && d.title.length > 12) {
      leaks.push(`draft title on blog index: ${d.title}`);
    }
  }
}

if (published.length === 0) {
  leaks.push('expected published posts, found none');
}

if (leaks.length) {
  console.error('Draft leak check FAILED:\n' + leaks.map((l) => ` - ${l}`).join('\n'));
  process.exit(1);
}

console.log(
  `Draft leak check OK (${published.length} published, ${drafts.length} drafts, ${distFiles.length} dist files, 0 leaks)`,
);
