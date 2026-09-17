#!/usr/bin/env python3
"""Copy Academia Obscura posts into this repo as unpublished drafts."""

from __future__ import annotations

import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PERSONAL = Path("/Users/89298/Documents/website/glen-w.github.io")
POSTS_SRC = PERSONAL / "_posts"
IMG_SRC = PERSONAL / "assets/img/posts"
AO_LIB = Path("/Users/89298/Documents/Academia Obscura")
WXR = (
    AO_LIB
    / "content/Academia Obscura website backups 2014-2018/2018-12/academiaobscura.wordpress.2018-12-08.xml"
)
SQL = (
    AO_LIB
    / "content/Academia Obscura website backups 2014-2018/2020-07/cl23-a-wordp-xfp.sql"
)
UPLOADS = (
    AO_LIB
    / "content/Academia Obscura website backups 2014-2018/2020-07/public_html/wp-content/uploads"
)

BLOG = ROOT / "src/content/blog"
PUBLIC_POSTS = ROOT / "public/posts"
REPORT = ROOT / "MIGRATION.md"
DELETE_LIST = ROOT / "scripts/personal-posts-to-delete.txt"

BLOG.mkdir(parents=True, exist_ok=True)
PUBLIC_POSTS.mkdir(parents=True, exist_ok=True)


def slugify(text: str) -> str:
    text = html.unescape(text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "post"


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def parse_fm(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    fm_raw, body = parts[1], parts[2]
    data: dict = {}
    for key in ("title", "date", "description", "layout"):
        m = re.search(rf"^{key}:\s*(.*)$", fm_raw, re.M)
        if not m:
            continue
        val = m.group(1).strip()
        if val.startswith('"') and val.endswith('"'):
            try:
                val = json.loads(val)
            except json.JSONDecodeError:
                val = val[1:-1]
        elif val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        data[key] = val
    for key in ("tags", "categories"):
        m = re.search(rf"^{key}:\s*(\[[\s\S]*?\])", fm_raw, re.M)
        if m:
            blob = re.sub(r"\s+", " ", m.group(1))
            try:
                data[key] = json.loads(blob.replace("'", '"'))
            except json.JSONDecodeError:
                inner = blob.strip("[]")
                data[key] = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
        else:
            data[key] = []
    return data, body.lstrip("\n")


def has_ao_tag(tags) -> bool:
    return any(str(t).replace(" ", "") == "AcademiaObscura" for t in tags)


def has_ao_category(cats) -> bool:
    return any("academia obscura" in str(c).lower() for c in cats)


def norm_title(text: str) -> str:
    text = html.unescape(text or "")
    text = text.replace('\\"', '"').replace("\\'", "'")
    text = text.lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def jekyll_slug(path: Path) -> str:
    name = path.stem
    m = re.match(r"^\d{4}-\d{2}-\d{2}-(.+)$", name)
    raw = m.group(1) if m else name
    return slugify(html.unescape(raw.replace("&amp;", "&").replace("&#039;", "'")))


def rewrite_images(body: str, copied: set[str], missing: list[str]) -> str:
    def repl(match: re.Match) -> str:
        rel = match.group(1)
        name = Path(rel).name
        src = IMG_SRC / name
        dest = PUBLIC_POSTS / name
        if src.exists():
            if name not in copied:
                shutil.copy2(src, dest)
                copied.add(name)
            return f"/posts/{name}"
        missing.append(name)
        return f"/posts/{name}"

    return re.sub(r"(?:\.\./)+assets/img/posts/([^)\s]+)", repl, body)


def write_post(
    *,
    date: str,
    title: str,
    body: str,
    tags: list[str],
    categories: list[str],
    source: str,
    original_slug: str,
    description: str = "",
) -> Path:
    date_prefix = date[:10]
    fname = f"{date_prefix}-{original_slug}.md"
    path = BLOG / fname
    n = 2
    while path.exists():
        path = BLOG / f"{date_prefix}-{original_slug}-{n}.md"
        n += 1
    tags = [t for t in tags if t]
    categories = [c for c in categories if c]
    fm = "\n".join(
        [
            "---",
            f"title: {yaml_quote(title)}",
            f"date: {date_prefix}",
            f"description: {yaml_quote(description or '')}",
            f"tags: {json.dumps(tags, ensure_ascii=False)}",
            f"categories: {json.dumps(categories, ensure_ascii=False)}",
            "draft: true",
            f"source: {source}",
            f"originalSlug: {yaml_quote(original_slug)}",
            "---",
            "",
        ]
    )
    path.write_text(fm + body.rstrip() + "\n", encoding="utf-8")
    return path


def cdata(block: str, tag: str) -> str:
    m = re.search(rf"<{tag}><!\[CDATA\[(.*?)\]\]></{tag}>", block, re.S)
    if m:
        return m.group(1)
    m = re.search(rf"<{tag}>(.*?)</{tag}>", block, re.S)
    return m.group(1).strip() if m else ""


def parse_wxr(path: Path) -> list[dict]:
    xml = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for block in re.findall(r"<item>(.*?)</item>", xml, re.S):
        if cdata(block, "wp:post_type") != "post":
            continue
        if cdata(block, "wp:status") != "publish":
            continue
        title = html.unescape(cdata(block, "title"))
        slug = cdata(block, "wp:post_name") or slugify(title)
        date = cdata(block, "wp:post_date")[:10]
        content = cdata(block, "content:encoded")
        tags = re.findall(
            r'<category domain="post_tag"[^>]*><!\[CDATA\[(.*?)\]\]></category>', block
        )
        cats = re.findall(
            r'<category domain="category"[^>]*><!\[CDATA\[(.*?)\]\]></category>', block
        )
        out.append(
            {
                "title": title,
                "slug": slug,
                "date": date,
                "content": content,
                "tags": tags,
                "categories": cats,
            }
        )
    return out


def split_mysql_rows(blob: str) -> list[list[str | None]]:
    rows: list[list[str | None]] = []
    i, n = 0, len(blob)
    while i < n:
        if blob[i] != "(":
            i += 1
            continue
        i += 1
        fields: list[str | None] = []
        while i < n:
            if blob[i] in " \t\n\r":
                i += 1
                continue
            if blob[i] == ")":
                rows.append(fields)
                i += 1
                break
            if blob[i] == ",":
                i += 1
                continue
            if blob.startswith("NULL", i):
                fields.append(None)
                i += 4
                continue
            if blob[i] == "'":
                i += 1
                buf: list[str] = []
                while i < n:
                    ch = blob[i]
                    if ch == "\\" and i + 1 < n:
                        nxt = blob[i + 1]
                        buf.append(
                            {"n": "\n", "r": "\r", "t": "\t", "0": "\0"}.get(nxt, nxt)
                        )
                        i += 2
                        continue
                    if ch == "'":
                        i += 1
                        break
                    buf.append(ch)
                    i += 1
                fields.append("".join(buf))
                continue
            j = i
            while i < n and blob[i] not in ",)":
                i += 1
            fields.append(blob[j:i])
    return rows


def parse_sql_posts(path: Path) -> list[dict]:
    data = path.read_text(encoding="utf-8", errors="replace")
    posts = []
    start = 0
    needle = "INSERT INTO `wp_posts` VALUES "
    while True:
        idx = data.find(needle, start)
        if idx < 0:
            break
        idx += len(needle)
        end = data.find(";\n", idx)
        if end < 0:
            end = data.find(";", idx)
        blob = data[idx:end]
        for fields in split_mysql_rows(blob):
            if len(fields) < 22:
                continue
            status = fields[7]
            ptype = fields[20]
            if status != "publish" or ptype != "post":
                continue
            posts.append(
                {
                    "title": html.unescape(fields[5] or ""),
                    "slug": fields[11] or slugify(fields[5] or "post"),
                    "date": (fields[2] or "")[:10],
                    "content": fields[4] or "",
                    "tags": [],
                    "categories": [],
                }
            )
        start = end + 1
    return posts


def rewrite_wp_images(html_body: str, copied: set[str], missing: list[str]) -> str:
    def repl(match: re.Match) -> str:
        url = match.group(0)
        name = Path(url.split("?")[0]).name
        year_month = re.search(r"/uploads/(\d{4}/\d{2})/", url)
        dest = PUBLIC_POSTS / name
        candidates = []
        if year_month and UPLOADS.exists():
            candidates.append(UPLOADS / year_month.group(1) / name)
        if UPLOADS.exists():
            candidates.extend(UPLOADS.glob(f"**/{name}"))
        src = next((c for c in candidates if c.exists() and c.is_file()), None)
        if src:
            if name not in copied:
                shutil.copy2(src, dest)
                copied.add(name)
            return f"/posts/{name}"
        missing.append(name)
        return match.group(0)

    return re.sub(
        r"https?://(?:www\.)?academiaobscura\.com/wp-content/uploads/[^\"'\s>]+",
        repl,
        html_body,
    )


def main() -> None:
    for old in BLOG.glob("*.md"):
        old.unlink()

    copied: set[str] = set()
    missing_imgs: list[str] = []
    personal_files: list[Path] = []
    personal_titles: set[str] = set()
    personal_slugs: set[str] = set()
    imported_personal = []

    wxr_posts = parse_wxr(WXR) if WXR.exists() else []
    wxr_title_keys = {norm_title(p["title"]) for p in wxr_posts}
    wxr_slugs = {p["slug"] for p in wxr_posts}

    for path in sorted(POSTS_SRC.glob("*.md")):
        raw = path.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_fm(raw)
        tags = fm.get("tags") or []
        cats = fm.get("categories") or []
        title = html.unescape(str(fm.get("title") or path.stem))
        slug = jekyll_slug(path)
        is_ao = (
            has_ao_tag(tags)
            or has_ao_category(cats)
            or norm_title(title) in wxr_title_keys
            or slug in wxr_slugs
        )
        if not is_ao:
            continue
        date = str(fm.get("date") or path.name[:10])[:10]
        body = rewrite_images(body, copied, missing_imgs)
        write_post(
            date=date,
            title=title,
            body=body,
            tags=tags,
            categories=cats,
            source="glenwright",
            original_slug=slug,
            description=str(fm.get("description") or "").strip(),
        )
        personal_files.append(path)
        personal_titles.add(title.strip().lower())
        personal_slugs.add(slug)
        imported_personal.append({"file": path.name, "title": title, "slug": slug, "date": date})

    wxr_gap = []
    personal_norm = {norm_title(t) for t in personal_titles}
    for p in wxr_posts:
        key = p["title"].strip().lower()
        if (
            key in personal_titles
            or p["slug"] in personal_slugs
            or norm_title(p["title"]) in personal_norm
        ):
            continue
        body = rewrite_wp_images(p["content"], copied, missing_imgs)
        write_post(
            date=p["date"],
            title=p["title"],
            body=body,
            tags=p["tags"] + ["AcademiaObscura"],
            categories=p["categories"],
            source="wxr",
            original_slug=p["slug"],
        )
        wxr_gap.append(p)
        personal_titles.add(key)
        personal_slugs.add(p["slug"])

    sql_gap = []
    if SQL.exists():
        try:
            sql_posts = parse_sql_posts(SQL)
        except Exception as exc:  # noqa: BLE001
            sql_posts = []
            sql_error = str(exc)
        else:
            sql_error = ""
        for p in sql_posts:
            key = p["title"].strip().lower()
            if (
                key in personal_titles
                or p["slug"] in personal_slugs
                or norm_title(p["title"]) in personal_norm
            ):
                continue
            if p["date"] < "2018-12-09":
                # already covered by WXR if published then
                continue
            body = rewrite_wp_images(p["content"], copied, missing_imgs)
            write_post(
                date=p["date"],
                title=p["title"],
                body=body,
                tags=["AcademiaObscura"],
                categories=[],
                source="sql",
                original_slug=p["slug"],
            )
            sql_gap.append(p)
            personal_titles.add(key)
    else:
        sql_error = "SQL dump not found"

    DELETE_LIST.write_text(
        "\n".join(str(p) for p in personal_files) + "\n", encoding="utf-8"
    )

    draft_count = len(list(BLOG.glob("*.md")))
    lines = [
        "# Academia Obscura draft migration",
        "",
        f"- Personal-site AO posts imported: **{len(imported_personal)}**",
        f"- WXR published posts (2018-12): **{len(wxr_posts)}**",
        f"- WXR-only drafts added: **{len(wxr_gap)}**",
        f"- SQL-only drafts after 2018-12: **{len(sql_gap)}**"
        + (f" (parse note: {sql_error})" if sql_error else ""),
        f"- Total draft files: **{draft_count}**",
        f"- Images copied to `public/posts/`: **{len(copied)}**",
        f"- Missing image names: **{len(set(missing_imgs))}**",
        "",
        "All imported posts have `draft: true`. They are not in the public sitemap, RSS, or blog index.",
        "",
        "## Personal-site files to delete",
        "",
        "Listed in `scripts/personal-posts-to-delete.txt`.",
        "",
        "## WXR-only titles",
        "",
    ]
    if wxr_gap:
        lines += [f"- {p['date']} — {p['title']}" for p in wxr_gap]
    else:
        lines.append("- (none)")
    lines += ["", "## SQL-only titles (post-2018-12)", ""]
    if sql_gap:
        lines += [f"- {p['date']} — {p['title']}" for p in sql_gap]
    else:
        lines.append("- (none)")
    if missing_imgs:
        lines += ["", "## Missing images (first 40)", ""]
        lines += [f"- {n}" for n in sorted(set(missing_imgs))[:40]]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT.read_text())


if __name__ == "__main__":
    main()
