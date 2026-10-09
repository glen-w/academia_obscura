import path from 'node:path';
import sharp from 'sharp';

const IMAGE_EXT = /\.(avif|gif|jpe?g|png|svg|webp)(\?.*)?$/i;

const dimensionCache = new Map<string, { width: number; height: number } | null>();

function isImageCandidate(url: string): boolean {
  if (!url || url.startsWith('data:')) return false;
  return IMAGE_EXT.test(url) || url.startsWith('/posts/');
}

/** All suitable image URLs from markdown, in document order. */
export function imageUrlsFromMarkdown(body: string | undefined): string[] {
  if (!body) return [];

  const urls: string[] = [];
  const pattern = /!\[[^\]]*]\(([^)]+)\)/g;
  for (const match of body.matchAll(pattern)) {
    const raw = match[1].trim();
    const url = raw.split(/\s+/)[0];
    if (isImageCandidate(url)) urls.push(url);
  }
  return urls;
}

function squareness(width: number, height: number): number {
  if (width <= 0 || height <= 0) return 0;
  return Math.min(width, height) / Math.max(width, height);
}

async function getDimensions(url: string): Promise<{ width: number; height: number } | null> {
  const cached = dimensionCache.get(url);
  if (cached !== undefined) return cached;

  let result: { width: number; height: number } | null = null;
  if (url.startsWith('/')) {
    const filePath = path.join(process.cwd(), 'public', url);
    try {
      const meta = await sharp(filePath).metadata();
      if (meta.width && meta.height) {
        result = { width: meta.width, height: meta.height };
      }
    } catch {
      result = null;
    }
  }

  dimensionCache.set(url, result);
  return result;
}

/**
 * Picks the in-post image closest to square (by pixel aspect ratio).
 * Falls back to the first image when none can be measured.
 */
export async function bestThumbnailFromMarkdown(body: string | undefined): Promise<string | undefined> {
  const urls = imageUrlsFromMarkdown(body);
  if (urls.length === 0) return undefined;
  if (urls.length === 1) return urls[0];

  let bestUrl = urls[0];
  let bestScore = -1;

  for (const url of urls) {
    const dims = await getDimensions(url);
    const score = dims ? squareness(dims.width, dims.height) : 0;
    if (score > bestScore) {
      bestScore = score;
      bestUrl = url;
    }
  }

  return bestUrl;
}
