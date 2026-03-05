#!/usr/bin/env python3
"""Generate SQL to import Ghost content directly into SQLite database."""

import json
import uuid

EXPORT_FILE = "/Users/robertnealan/Documents/projects/_archive/ghost-robertnealan/ghost-archive/ghost-export.json"
OUTPUT_FILE = "/Users/robertnealan/Documents/projects/robertnealan.com/import.sql"

with open(EXPORT_FILE) as f:
    export = json.load(f)

posts = export["data"]["posts"]
tags = export["data"]["tags"]
posts_tags = export["data"]["posts_tags"]
users = export["data"].get("users", [])
posts_authors = export["data"].get("posts_authors", [])


def sql_escape(val):
    if val is None:
        return "NULL"
    s = str(val).replace("'", "''")
    return f"'{s}'"


# Get the owner user ID from the new instance (we'll replace author references)
# We'll use a placeholder and replace it during execution
lines = []
lines.append("-- Ghost content import")
lines.append("-- Run with: sqlite3 /var/lib/ghost/content/data/ghost-dev.db < import.sql")
lines.append("")

# Import tags
lines.append("-- Tags")
for tag in tags:
    new_id = uuid.uuid4().hex[:24]
    tag["new_id"] = new_id
    lines.append(
        f"INSERT OR IGNORE INTO tags (id, name, slug, description, created_at, created_by, updated_at, updated_by) "
        f"VALUES ({sql_escape(new_id)}, {sql_escape(tag['name'])}, {sql_escape(tag['slug'])}, "
        f"{sql_escape(tag.get('description'))}, datetime('now'), '1', datetime('now'), '1');"
    )

# Build tag ID mapping (old -> new)
tag_id_map = {t["id"]: t["new_id"] for t in tags}

lines.append("")
lines.append("-- Posts")

for post in posts:
    new_id = uuid.uuid4().hex[:24]
    post["new_id"] = new_id

    html = post.get("html") or ""
    if html:
        html = html.replace("https://robertnealan.com/content/images/", "/content/images/")
        html = html.replace("https://robertnealan.com/content/", "/content/")

    mobiledoc = post.get("mobiledoc")
    if mobiledoc and isinstance(mobiledoc, str):
        mobiledoc = mobiledoc.replace("https://robertnealan.com/content/images/", "/content/images/")
        mobiledoc = mobiledoc.replace("https://robertnealan.com/content/", "/content/")

    feature_image = post.get("feature_image")
    if feature_image:
        feature_image = feature_image.replace("https://robertnealan.com/content/", "/content/")

    post_type = post.get("type", "post")
    status = post.get("status", "draft")
    visibility = post.get("visibility", "public")
    slug = post.get("slug", "")
    title = post.get("title", "")
    custom_excerpt = post.get("custom_excerpt")
    created_at = post.get("created_at", "2024-01-01 00:00:00")
    updated_at = post.get("updated_at", created_at)
    published_at = post.get("published_at")

    lines.append(
        f"INSERT INTO posts (id, uuid, title, slug, mobiledoc, html, plaintext, "
        f"feature_image, featured, type, status, visibility, email_recipient_filter, "
        f"created_at, created_by, updated_at, updated_by, published_at, published_by, custom_excerpt) "
        f"VALUES ({sql_escape(new_id)}, {sql_escape(uuid.uuid4().hex)}, {sql_escape(title)}, {sql_escape(slug)}, "
        f"{sql_escape(mobiledoc)}, {sql_escape(html)}, {sql_escape(post.get('plaintext'))}, "
        f"{sql_escape(feature_image)}, {post.get('featured', 0)}, {sql_escape(post_type)}, "
        f"{sql_escape(status)}, {sql_escape(visibility)}, 'all', "
        f"{sql_escape(created_at)}, '1', {sql_escape(updated_at)}, '1', "
        f"{sql_escape(published_at)}, {'NULL' if not published_at else sql_escape('1')}, "
        f"{sql_escape(custom_excerpt)});"
    )

# Build post ID mapping
post_id_map = {p["id"]: p["new_id"] for p in posts}

lines.append("")
lines.append("-- Posts-Tags relationships")
for pt in posts_tags:
    new_post_id = post_id_map.get(pt["post_id"])
    new_tag_id = tag_id_map.get(pt["tag_id"])
    if new_post_id and new_tag_id:
        new_id = uuid.uuid4().hex[:24]
        lines.append(
            f"INSERT OR IGNORE INTO posts_tags (id, post_id, tag_id, sort_order) "
            f"VALUES ({sql_escape(new_id)}, {sql_escape(new_post_id)}, {sql_escape(new_tag_id)}, {pt.get('sort_order', 0)});"
        )

# Link all posts to the owner user (first user in new instance)
lines.append("")
lines.append("-- Posts-Authors (link all to owner)")
for post in posts:
    new_id = uuid.uuid4().hex[:24]
    lines.append(
        f"INSERT OR IGNORE INTO posts_authors (id, post_id, author_id, sort_order) "
        f"VALUES ({sql_escape(new_id)}, {sql_escape(post['new_id'])}, "
        f"(SELECT id FROM users WHERE id = '1' OR slug != 'ghost' LIMIT 1), 0);"
    )

with open(OUTPUT_FILE, "w") as f:
    f.write("\n".join(lines))

print(f"Generated {OUTPUT_FILE}")
print(f"  {len(tags)} tags")
print(f"  {len(posts)} posts")
print(f"  {len(posts_tags)} post-tag relationships")
