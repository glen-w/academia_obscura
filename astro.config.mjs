import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://academiaobscura.com',
  trailingSlash: 'always',
  redirects: {
    '/book': '/',
    '/book/': '/',
  },
  markdown: {
    syntaxHighlight: false,
  },
});
