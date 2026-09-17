import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://academiaobscura.com',
  trailingSlash: 'always',
  markdown: {
    syntaxHighlight: false,
  },
});
